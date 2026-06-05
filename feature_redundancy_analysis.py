from __future__ import annotations

import json
import os
from pathlib import Path

Path("evaluation", ".matplotlib-cache").mkdir(parents=True, exist_ok=True)
os.environ.setdefault("MPLCONFIGDIR", str(Path("evaluation") / ".matplotlib-cache"))

import matplotlib
import numpy as np
import pandas as pd
from matplotlib import pyplot as plt

from calibration.calibration import calibration_summary, calibration_table, expected_calibration_error
from evaluation.model_evaluation import evaluate_probabilities, time_based_split
from explainability.shap_analysis import compute_shap_importance, plot_shap_importance, plot_shap_summary
from feature_experiments import _markdown_table, train_xgb
from tactical_data import ensure_tactical_tables, load_team_match_tactics
from tactical_features import build_tactical_features
from train_model import SCHEDULE_FEATURE_COLUMNS, build_features, load_matches_with_xg
from venue_specific_feature_experiments import VENUE_FEATURE_COLUMNS, build_venue_specific_features
from visualizations.plots import compute_permutation_importance, plot_feature_importance

matplotlib.use("Agg")

OUTPUT_DIR = Path("evaluation") / "feature_redundancy"
TACTICAL_PRESSURE_COLUMNS = [
    "home_attacking_pressure_score_last5",
    "home_attacking_pressure_score_last10",
    "home_attacking_pressure_score_season",
    "away_attacking_pressure_score_last5",
    "away_attacking_pressure_score_last10",
    "away_attacking_pressure_score_season",
]

FEATURE_GROUPS = {
    "Form": [
        "home_team_points_last_5",
        "away_team_points_last_5",
        "home_goals_scored_avg",
        "away_goals_scored_avg",
        "home_advantage",
    ],
    "xG": ["home_xg_avg", "away_xg_avg"],
    "xGA": ["home_xga_avg", "away_xga_avg"],
    "xG differential": ["home_xg_diff", "away_xg_diff"],
    "Fatigue": [
        "home_days_rest",
        "away_days_rest",
        "home_matches_last_14_days",
        "away_matches_last_14_days",
        "home_had_midweek_match",
        "away_had_midweek_match",
        "home_days_since_last_match",
        "away_days_since_last_match",
    ],
    "Tactical pressure": TACTICAL_PRESSURE_COLUMNS,
    "Venue-specific features": VENUE_FEATURE_COLUMNS,
}


def available_columns(dataset: pd.DataFrame, columns: list[str]) -> list[str]:
    return [
        column
        for column in columns
        if column in dataset.columns and dataset[column].notna().sum() > 0 and float(dataset[column].fillna(0).abs().sum()) > 0
    ]


def build_dataset() -> tuple[pd.DataFrame, pd.DataFrame, dict[str, list[str]]]:
    matches = load_matches_with_xg().sort_values("Date").reset_index(drop=True)
    base_dataset, _ = build_features(matches, include_xg=True, include_schedule=True)
    venue_features = build_venue_specific_features(matches)
    dataset = pd.concat([base_dataset.reset_index(drop=True), venue_features.reset_index(drop=True)], axis=1)

    try:
        ensure_tactical_tables()
        tactics = load_team_match_tactics()
        tactical_features, _ = build_tactical_features(matches, tactics)
        tactical_columns = available_columns(tactical_features, TACTICAL_PRESSURE_COLUMNS)
        if tactical_columns:
            dataset = pd.concat([dataset.reset_index(drop=True), tactical_features[tactical_columns].reset_index(drop=True)], axis=1)
    except Exception as exc:
        print(f"Warning: tactical pressure features unavailable: {exc}")

    groups = {group: available_columns(dataset, columns) for group, columns in FEATURE_GROUPS.items()}
    metadata = matches[["Season", "Date", "HomeTeam", "AwayTeam", "FTR"]].reset_index(drop=True)
    return dataset, metadata, groups


def evaluate_columns(dataset: pd.DataFrame, metadata: pd.DataFrame, columns: list[str], model_name: str) -> dict[str, object]:
    split = time_based_split(dataset[columns], dataset["target"], metadata)
    model = train_xgb(split.X_train, split.y_train)
    probabilities = model.predict_proba(split.X_test)
    predictions = model.predict(split.X_test)
    metrics = evaluate_probabilities(split.y_test, probabilities, predictions)
    calibration = calibration_table(split.y_test, probabilities)
    cal_summary = calibration_summary(calibration)
    return {
        "model_name": model_name,
        "model": model,
        "split": split,
        "feature_columns": columns,
        "probabilities": probabilities,
        "accuracy": metrics["accuracy"],
        "log_loss": metrics["log_loss"],
        "brier_score": metrics["brier_score_multiclass"],
        "calibration_score": cal_summary["mean_absolute_calibration_error"],
        "ece": expected_calibration_error(calibration),
    }


def add_one_group_analysis(dataset: pd.DataFrame, metadata: pd.DataFrame, groups: dict[str, list[str]]) -> pd.DataFrame:
    form_columns = groups["Form"]
    form_result = evaluate_columns(dataset, metadata, form_columns, "reference_form")
    rows = [
        {
            "feature_group": "Form",
            "features": len(form_columns),
            "reference": "form_only",
            "accuracy": form_result["accuracy"],
            "log_loss": form_result["log_loss"],
            "brier_score": form_result["brier_score"],
            "calibration_score": form_result["calibration_score"],
            "ece": form_result["ece"],
            "log_loss_delta_vs_form": 0.0,
            "brier_delta_vs_form": 0.0,
        }
    ]
    for group, columns in groups.items():
        if group == "Form" or not columns:
            continue
        candidate_columns = form_columns + columns
        result = evaluate_columns(dataset, metadata, candidate_columns, f"form_plus_{group}")
        rows.append(
            {
                "feature_group": group,
                "features": len(columns),
                "reference": "form_plus_group",
                "accuracy": result["accuracy"],
                "log_loss": result["log_loss"],
                "brier_score": result["brier_score"],
                "calibration_score": result["calibration_score"],
                "ece": result["ece"],
                "log_loss_delta_vs_form": float(result["log_loss"] - form_result["log_loss"]),
                "brier_delta_vs_form": float(result["brier_score"] - form_result["brier_score"]),
            }
        )
    return pd.DataFrame(rows)


def remove_one_group_analysis(dataset: pd.DataFrame, metadata: pd.DataFrame, groups: dict[str, list[str]]) -> tuple[pd.DataFrame, dict[str, object]]:
    full_columns = [column for columns in groups.values() for column in columns]
    full_result = evaluate_columns(dataset, metadata, full_columns, "full_research_model")
    rows = [
        {
            "feature_group": "Full model",
            "features_removed": 0,
            "accuracy": full_result["accuracy"],
            "log_loss": full_result["log_loss"],
            "brier_score": full_result["brier_score"],
            "calibration_score": full_result["calibration_score"],
            "ece": full_result["ece"],
            "log_loss_delta_vs_full": 0.0,
            "brier_delta_vs_full": 0.0,
        }
    ]
    for group, columns in groups.items():
        if not columns:
            continue
        remaining = [column for column in full_columns if column not in columns]
        result = evaluate_columns(dataset, metadata, remaining, f"full_minus_{group}")
        rows.append(
            {
                "feature_group": group,
                "features_removed": len(columns),
                "accuracy": result["accuracy"],
                "log_loss": result["log_loss"],
                "brier_score": result["brier_score"],
                "calibration_score": result["calibration_score"],
                "ece": result["ece"],
                "log_loss_delta_vs_full": float(result["log_loss"] - full_result["log_loss"]),
                "brier_delta_vs_full": float(result["brier_score"] - full_result["brier_score"]),
            }
        )
    return pd.DataFrame(rows), full_result


def correlation_analysis(dataset: pd.DataFrame, groups: dict[str, list[str]]) -> pd.DataFrame:
    all_columns = [column for columns in groups.values() for column in columns]
    corr = dataset[all_columns].corr(numeric_only=True).abs()
    corr.to_csv(OUTPUT_DIR / "feature_correlation_matrix.csv")
    rows = []
    for group, columns in groups.items():
        if not columns:
            rows.append(
                {
                    "feature_group": group,
                    "features": 0,
                    "mean_abs_corr_with_other_features": np.nan,
                    "max_abs_corr_with_other_features": np.nan,
                    "high_corr_pairs_ge_0_80": 0,
                }
            )
            continue
        other_columns = [column for column in all_columns if column not in columns]
        cross_corr = corr.loc[columns, other_columns] if other_columns else pd.DataFrame()
        rows.append(
            {
                "feature_group": group,
                "features": len(columns),
                "mean_abs_corr_with_other_features": float(cross_corr.stack().mean()) if not cross_corr.empty else 0.0,
                "max_abs_corr_with_other_features": float(cross_corr.stack().max()) if not cross_corr.empty else 0.0,
                "high_corr_pairs_ge_0_80": int((cross_corr >= 0.80).sum().sum()) if not cross_corr.empty else 0,
            }
        )
    return pd.DataFrame(rows)


def group_importance(feature_importance: pd.DataFrame, value_column: str, groups: dict[str, list[str]]) -> pd.DataFrame:
    feature_to_group = {feature: group for group, columns in groups.items() for feature in columns}
    frame = feature_importance.copy()
    frame["feature_group"] = frame["feature"].map(feature_to_group).fillna("Other")
    return frame.groupby("feature_group", as_index=False)[value_column].sum().sort_values(value_column, ascending=False)


def plot_group_bars(frame: pd.DataFrame, value_column: str, title: str, output_path: Path) -> None:
    plot_data = frame.sort_values(value_column, ascending=True)
    fig, ax = plt.subplots(figsize=(8, 5))
    ax.barh(plot_data["feature_group"], plot_data[value_column])
    ax.set_title(title)
    ax.set_xlabel(value_column)
    fig.tight_layout()
    fig.savefig(output_path, dpi=160)
    plt.close(fig)


def write_report(
    groups: dict[str, list[str]],
    add_one: pd.DataFrame,
    remove_one: pd.DataFrame,
    correlations: pd.DataFrame,
    shap_group: pd.DataFrame,
    perm_group: pd.DataFrame,
) -> None:
    candidates = remove_one[remove_one["feature_group"] != "Full model"].copy()
    unique_groups = candidates[
        (candidates["log_loss_delta_vs_full"] > 0) & (candidates["brier_delta_vs_full"] > 0)
    ].sort_values(["log_loss_delta_vs_full", "brier_delta_vs_full"], ascending=False)
    mixed_groups = candidates[
        ((candidates["log_loss_delta_vs_full"] > 0) & (candidates["brier_delta_vs_full"] <= 0))
        | ((candidates["log_loss_delta_vs_full"] <= 0) & (candidates["brier_delta_vs_full"] > 0))
    ].sort_values("log_loss_delta_vs_full", ascending=False)
    redundant_groups = candidates.sort_values("log_loss_delta_vs_full", ascending=True)
    dominant_shap = shap_group.iloc[0]["feature_group"] if not shap_group.empty else "N/A"
    dominant_perm = perm_group.iloc[0]["feature_group"] if not perm_group.empty else "N/A"
    high_corr_total = int(correlations["high_corr_pairs_ge_0_80"].sum())
    tactical_status = "available" if groups.get("Tactical pressure") else "not available with non-zero local data"

    future_families = [
        "verified pre-match market odds or opening odds, because market prices summarize broad public and private information",
        "reliable player availability/lineup data, because it is orthogonal to team-level rolling xG",
        "team strength ratings such as Elo/SPI-style priors, because they add long-horizon quality separate from last-5 form",
        "true event-data tactical metrics if coverage is complete, because current tactical pressure is limited by data availability",
    ]
    future_lines = "\n".join(f"- {item}" for item in future_families)

    Path("feature_redundancy_report.md").write_text(
        f"""# Feature Redundancy Analysis

## Scope

This analysis tests whether the current model is approaching feature saturation across these groups:

- Form
- xG
- xGA
- xG differential
- Fatigue
- Tactical pressure
- Venue-specific features

Tactical pressure status: `{tactical_status}`.

All evaluations use a strict time-based split. Lower is better for log loss, Brier score, calibration score and ECE.

## 1. Marginal Improvement When Added Individually

Reference model: Form features only.

{_markdown_table(add_one, ['feature_group', 'features', 'accuracy', 'log_loss', 'brier_score', 'calibration_score', 'ece', 'log_loss_delta_vs_form', 'brier_delta_vs_form'])}

Negative delta means the group improved over form-only.

## 2. Marginal Impact When Removed

Reference model: full research model with all available groups.

{_markdown_table(remove_one, ['feature_group', 'features_removed', 'accuracy', 'log_loss', 'brier_score', 'calibration_score', 'ece', 'log_loss_delta_vs_full', 'brier_delta_vs_full'])}

Positive delta means removing the group made performance worse, so the group contains useful information. Negative delta means removing the group improved performance, suggesting noise or redundancy.

## 3. Correlation With Existing Features

{_markdown_table(correlations, ['feature_group', 'features', 'mean_abs_corr_with_other_features', 'max_abs_corr_with_other_features', 'high_corr_pairs_ge_0_80'])}

High-correlation pairs at `abs(correlation) >= 0.80`: `{high_corr_total}`.

## 4. SHAP Importance

{_markdown_table(shap_group, ['feature_group', 'mean_abs_shap'])}

Dominant SHAP group: `{dominant_shap}`.

## 5. Permutation Importance

{_markdown_table(perm_group, ['feature_group', 'permutation_importance'])}

Dominant permutation group: `{dominant_perm}`.

## Answers

### 1. Which features provide unique information?

The strongest candidates for unique information are the groups where removing them increases both log loss and Brier score. In this run:

{_markdown_table(unique_groups.head(5), ['feature_group', 'log_loss_delta_vs_full', 'brier_delta_vs_full']) if not unique_groups.empty else 'No feature group cleanly worsened both log loss and Brier score when removed from the full research model.'}

Mixed-signal groups, where one metric improves and another worsens:

{_markdown_table(mixed_groups.head(5), ['feature_group', 'log_loss_delta_vs_full', 'brier_delta_vs_full']) if not mixed_groups.empty else 'No mixed-signal groups.'}

### 2. Which features are largely redundant?

Groups where removal improves or barely changes log loss are likely redundant or noisy in the current model:

{_markdown_table(redundant_groups.head(5), ['feature_group', 'log_loss_delta_vs_full', 'brier_delta_vs_full'])}

### 3. Which feature groups dominate model performance?

SHAP dominance: `{dominant_shap}`.  
Permutation dominance: `{dominant_perm}`.

Use SHAP as contribution attribution and permutation importance as performance sensitivity. If they disagree, trust permutation more for redundancy decisions.

### 4. Is the model becoming saturated with highly correlated features?

Answer: {'Yes, there are signs of saturation: multiple groups are correlated and some removals improve or barely hurt log loss.' if high_corr_total > 0 or (redundant_groups['log_loss_delta_vs_full'] <= 0.001).any() else 'Not strongly. Correlations and removal tests do not show severe saturation in this run.'}

The most important warning sign is not just correlation, but that adding more rolling variants does not reliably improve out-of-sample log loss.

### 5. Which future feature families are most likely to add genuinely new information?

{future_lines}

## Production Guidance

Do not add future features merely because they have SHAP signal. Promote only if they improve out-of-sample log loss or Brier score and do not materially worsen calibration.

## Artifacts

- `evaluation/feature_redundancy/add_one_group_results.csv`
- `evaluation/feature_redundancy/remove_one_group_results.csv`
- `evaluation/feature_redundancy/correlation_summary.csv`
- `evaluation/feature_redundancy/feature_correlation_matrix.csv`
- `evaluation/feature_redundancy/shap_feature_rankings.csv`
- `evaluation/feature_redundancy/shap_group_importance.csv`
- `evaluation/feature_redundancy/permutation_feature_importance.csv`
- `evaluation/feature_redundancy/permutation_group_importance.csv`
- `evaluation/feature_redundancy/shap_group_importance.png`
- `evaluation/feature_redundancy/permutation_group_importance.png`
"""
    )


def run_analysis() -> dict[str, object]:
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    dataset, metadata, groups = build_dataset()
    groups = {group: columns for group, columns in groups.items() if columns}

    add_one = add_one_group_analysis(dataset, metadata, groups)
    remove_one, full_result = remove_one_group_analysis(dataset, metadata, groups)
    correlations = correlation_analysis(dataset, groups)

    shap_importance, _, _ = compute_shap_importance(full_result["model"], full_result["split"].X_test)
    shap_importance.to_csv(OUTPUT_DIR / "shap_feature_rankings.csv", index=False)
    plot_shap_importance(shap_importance.head(35), OUTPUT_DIR / "shap_feature_rankings.png")
    plot_shap_summary(full_result["model"], full_result["split"].X_test, OUTPUT_DIR / "shap_summary.png")
    shap_group = group_importance(shap_importance, "mean_abs_shap", groups)
    shap_group.to_csv(OUTPUT_DIR / "shap_group_importance.csv", index=False)
    plot_group_bars(shap_group, "mean_abs_shap", "SHAP Importance by Feature Group", OUTPUT_DIR / "shap_group_importance.png")

    permutation = compute_permutation_importance(full_result["model"], full_result["split"].X_test, full_result["split"].y_test)
    permutation.to_csv(OUTPUT_DIR / "permutation_feature_importance.csv", index=False)
    plot_feature_importance(
        permutation.head(35),
        "permutation_importance",
        "Permutation Importance",
        OUTPUT_DIR / "permutation_feature_importance.png",
    )
    perm_group = group_importance(permutation, "permutation_importance", groups)
    perm_group.to_csv(OUTPUT_DIR / "permutation_group_importance.csv", index=False)
    plot_group_bars(
        perm_group,
        "permutation_importance",
        "Permutation Importance by Feature Group",
        OUTPUT_DIR / "permutation_group_importance.png",
    )

    add_one.to_csv(OUTPUT_DIR / "add_one_group_results.csv", index=False)
    remove_one.to_csv(OUTPUT_DIR / "remove_one_group_results.csv", index=False)
    correlations.to_csv(OUTPUT_DIR / "correlation_summary.csv", index=False)
    write_report(groups, add_one, remove_one, correlations, shap_group, perm_group)
    return {"groups": groups, "best_remove": remove_one.sort_values("log_loss").iloc[0].to_dict()}


def main() -> None:
    result = run_analysis()
    print(json.dumps({"available_groups": list(result["groups"].keys()), "best_model_variant": result["best_remove"]["feature_group"]}, indent=2))


if __name__ == "__main__":
    main()
