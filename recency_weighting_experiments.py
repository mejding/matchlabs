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
from sklearn.inspection import permutation_importance

from calibration.calibration import calibration_summary, calibration_table, expected_calibration_error
from elo_rating_features import build_elo_features
from evaluation.model_evaluation import multiclass_brier_score, time_based_split
from explainability.shap_analysis import compute_shap_importance, plot_shap_importance, plot_shap_summary
from feature_experiments import _markdown_table, train_xgb
from recency_weighted_features import WEIGHTING_SCHEMES, all_weighted_feature_columns, build_recency_weighted_features, weighted_feature_columns
from train_model import ELO_CONFIG, PRODUCTION_FEATURE_COLUMNS, SHOT_VOLUME_FEATURE_COLUMNS, build_features
from train_model import load_matches_with_xg
from visualizations.plots import gain_importance, plot_feature_importance

matplotlib.use("Agg")

OUTPUT_DIR = Path("evaluation") / "recency_weighting"
ROLLING_RAW_COLUMNS = [
    "home_team_points_last_5",
    "away_team_points_last_5",
    "home_goals_scored_avg",
    "away_goals_scored_avg",
    "home_xg_avg",
    "away_xg_avg",
    "home_xga_avg",
    "away_xga_avg",
    "home_xg_diff",
    "away_xg_diff",
    *SHOT_VOLUME_FEATURE_COLUMNS,
]
NON_ROLLING_PRODUCTION_COLUMNS = [column for column in PRODUCTION_FEATURE_COLUMNS if column not in set(ROLLING_RAW_COLUMNS)]


def normalize_probabilities(probabilities: np.ndarray) -> np.ndarray:
    probabilities = np.clip(probabilities, 1e-15, 1.0)
    return probabilities / probabilities.sum(axis=1, keepdims=True)


def evaluate_probs(y_true: pd.Series, probabilities: np.ndarray) -> dict[str, float]:
    probabilities = normalize_probabilities(probabilities)
    predictions = probabilities.argmax(axis=1)
    calibration = calibration_table(y_true, probabilities)
    draw_actual = (y_true.to_numpy() == 1).astype(int)
    draw_prob = np.clip(probabilities[:, 1], 1e-15, 1.0)
    draw_pred = (predictions == 1).astype(int)
    return {
        "accuracy": float((predictions == y_true.to_numpy()).mean()),
        "log_loss": float(-np.log(probabilities[np.arange(len(y_true)), y_true.to_numpy()]).mean()),
        "Brier_score": multiclass_brier_score(y_true, probabilities),
        "expected_calibration_error": expected_calibration_error(calibration),
        "calibration_score": calibration_summary(calibration)["mean_absolute_calibration_error"],
        "draw_recall": float(((draw_pred == 1) & (draw_actual == 1)).sum() / draw_actual.sum()) if draw_actual.sum() else 0.0,
        "draw_log_loss": float(-np.mean(draw_actual * np.log(draw_prob) + (1 - draw_actual) * np.log(1 - draw_prob))),
        "draw_mean_probability_on_draws": float(draw_prob[draw_actual == 1].mean()) if draw_actual.sum() else 0.0,
    }


def build_dataset() -> tuple[pd.DataFrame, pd.DataFrame, dict[str, list[str]]]:
    matches = load_matches_with_xg().sort_values("Date").reset_index(drop=True)
    for column in ["HS", "AS", "HST", "AST"]:
        if column not in matches.columns:
            matches[column] = 0.0
        matches[column] = pd.to_numeric(matches[column], errors="coerce").fillna(0.0)
    base, _ = build_features(matches, include_xg=True, include_schedule=True, include_shot_volume=True)
    elo, _ = build_elo_features(matches, ELO_CONFIG)
    weighted = build_recency_weighted_features(matches)
    dataset = pd.concat([base.reset_index(drop=True), elo.reset_index(drop=True), weighted.drop(columns=["target"]).reset_index(drop=True)], axis=1)
    dataset["target"] = base["target"].to_numpy()
    metadata = matches[["Season", "Date", "HomeTeam", "AwayTeam", "FTR"]].reset_index(drop=True)

    feature_sets: dict[str, list[str]] = {"model_a_current_production": PRODUCTION_FEATURE_COLUMNS}
    for scheme in WEIGHTING_SCHEMES:
        feature_sets[f"model_replace_{scheme}"] = NON_ROLLING_PRODUCTION_COLUMNS + weighted_feature_columns(scheme)
    for scheme in WEIGHTING_SCHEMES:
        feature_sets[f"model_hybrid_raw_plus_{scheme}"] = PRODUCTION_FEATURE_COLUMNS + weighted_feature_columns(scheme)
    feature_sets["model_hybrid_all_weighted"] = PRODUCTION_FEATURE_COLUMNS + all_weighted_feature_columns()
    return dataset, metadata, feature_sets


def write_inventory() -> None:
    rows = []
    for column in ROLLING_RAW_COLUMNS:
        if "points" in column:
            family = "form_points"
            method = "Total points from the team's latest 5 matches before kickoff; all venues; equal weight."
        elif "goals_scored" in column:
            family = "goals"
            method = "Average goals scored across the team's latest 5 matches before kickoff; all venues; equal weight."
        elif "xga" in column:
            family = "xGA"
            method = "Average expected goals allowed across the team's latest 5 matches before kickoff; all venues; equal weight."
        elif "xg_diff" in column:
            family = "xG_diff"
            method = "Latest-5 xG average minus latest-5 xGA average before kickoff; all venues; equal weight."
        elif "xg" in column:
            family = "xG"
            method = "Average expected goals across the team's latest 5 matches before kickoff; all venues; equal weight."
        elif "shots_on_target" in column:
            family = "shots_on_target"
            if column.endswith("_season"):
                method = "Season-to-date shots on target average before kickoff; all venues; equal weight."
            elif column.endswith("_last10"):
                method = "Average shots on target across the team's latest 10 matches before kickoff; all venues; equal weight."
            else:
                method = "Average shots on target across the team's latest 5 matches before kickoff; all venues; equal weight."
        elif "shots" in column:
            family = "shots"
            if column.endswith("_season"):
                method = "Season-to-date shots average before kickoff; all venues; equal weight."
            elif column.endswith("_last10"):
                method = "Average shots across the team's latest 10 matches before kickoff; all venues; equal weight."
            else:
                method = "Average shots across the team's latest 5 matches before kickoff; all venues; equal weight."
        else:
            family = "rolling"
            method = "Chronological pre-match rolling feature; equal weight."
        rows.append({"feature": column, "family": family, "current_method": method})
    frame = pd.DataFrame(rows)
    lines = [
        "# Current Rolling Feature Inventory",
        "",
        "These production features are based on rolling or season-to-date team history and are tested against recency-weighted versions.",
        "",
        _markdown_table(frame, ["feature", "family", "current_method"]),
    ]
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    (OUTPUT_DIR / "current_rolling_features.md").write_text("\n".join(lines))


def evaluate_feature_set(dataset: pd.DataFrame, metadata: pd.DataFrame, columns: list[str], model_version: str) -> dict[str, object]:
    split = time_based_split(dataset[columns], dataset["target"], metadata)
    model = train_xgb(split.X_train, split.y_train)
    probabilities = normalize_probabilities(model.predict_proba(split.X_test))
    metrics = evaluate_probs(split.y_test, probabilities)
    return {
        "model_version": model_version,
        "model": model,
        "split": split,
        "probabilities": probabilities,
        "feature_columns": columns,
        "train_period": f"{split.train_metadata['Date'].iloc[0]} to {split.train_metadata['Date'].iloc[-1]}",
        "test_period": f"{split.test_metadata['Date'].iloc[0]} to {split.test_metadata['Date'].iloc[-1]}",
        **metrics,
    }


def compare_models(dataset: pd.DataFrame, metadata: pd.DataFrame, feature_sets: dict[str, list[str]]) -> tuple[pd.DataFrame, dict[str, dict[str, object]]]:
    results = []
    lookup = {}
    for name, columns in feature_sets.items():
        result = evaluate_feature_set(dataset, metadata, columns, name)
        results.append(result)
        lookup[name] = result
    rows = []
    for result in results:
        rows.append(
            {
                "model_version": result["model_version"],
                "train_period": result["train_period"],
                "test_period": result["test_period"],
                "accuracy": result["accuracy"],
                "log_loss": result["log_loss"],
                "Brier_score": result["Brier_score"],
                "expected_calibration_error": result["expected_calibration_error"],
                "draw_recall": result["draw_recall"],
                "draw_log_loss": result["draw_log_loss"],
                "draw_mean_probability_on_draws": result["draw_mean_probability_on_draws"],
            }
        )
    output = pd.DataFrame(rows).sort_values(["log_loss", "Brier_score"])
    output.to_csv(OUTPUT_DIR / "model_comparison.csv", index=False)
    return output, lookup


def feature_group(feature: str) -> str:
    if "_linear" in feature:
        return "weighted_linear"
    if "_exponential" in feature:
        return "weighted_exponential"
    if "_halflife3" in feature:
        return "weighted_halflife3"
    if "_halflife5" in feature:
        return "weighted_halflife5"
    if feature in ROLLING_RAW_COLUMNS:
        return "raw_rolling"
    if "elo" in feature:
        return "elo"
    if "days" in feature or "midweek" in feature or "matches_last" in feature:
        return "fatigue"
    return "other_production"


def shap_and_importance(best_result: dict[str, object]) -> pd.DataFrame:
    shap_importance, _, _ = compute_shap_importance(best_result["model"], best_result["split"].X_test)
    shap_importance["feature_group"] = shap_importance["feature"].map(feature_group)
    shap_importance.to_csv(OUTPUT_DIR / "shap_importance.csv", index=False)
    shap_importance.groupby("feature_group", as_index=False)["mean_abs_shap"].sum().sort_values(
        "mean_abs_shap", ascending=False
    ).to_csv(OUTPUT_DIR / "shap_group_importance.csv", index=False)
    plot_shap_importance(shap_importance.head(40), OUTPUT_DIR / "shap_importance.png")
    plot_shap_summary(best_result["model"], best_result["split"].X_test, OUTPUT_DIR / "shap_summary.png")
    gain = gain_importance(best_result["model"], best_result["feature_columns"])
    gain.to_csv(OUTPUT_DIR / "feature_importance.csv", index=False)
    plot_feature_importance(gain.head(40), "gain_importance", "Recency Weighting Gain Importance", OUTPUT_DIR / "feature_importance.png")
    perm = permutation_importance(
        best_result["model"],
        best_result["split"].X_test,
        best_result["split"].y_test,
        scoring="neg_log_loss",
        n_repeats=5,
        random_state=42,
        n_jobs=1,
    )
    permutation = pd.DataFrame(
        {
            "feature": best_result["feature_columns"],
            "permutation_importance_log_loss": perm.importances_mean,
            "permutation_importance_std": perm.importances_std,
        }
    ).sort_values("permutation_importance_log_loss", ascending=False)
    permutation.to_csv(OUTPUT_DIR / "permutation_importance.csv", index=False)
    return shap_importance


def correlation_analysis(dataset: pd.DataFrame) -> pd.DataFrame:
    pairs = []
    mapping = [
        ("home_team_points_last_5", "home_points_weighted"),
        ("away_team_points_last_5", "away_points_weighted"),
        ("home_goals_scored_avg", "home_goals_scored_weighted"),
        ("away_goals_scored_avg", "away_goals_scored_weighted"),
        ("home_xg_avg", "home_xg_weighted"),
        ("away_xg_avg", "away_xg_weighted"),
        ("home_xga_avg", "home_xga_weighted"),
        ("away_xga_avg", "away_xga_weighted"),
        ("home_shots_avg_last5", "home_shots_weighted"),
        ("away_shots_avg_last5", "away_shots_weighted"),
    ]
    for raw, weighted_base in mapping:
        for scheme in WEIGHTING_SCHEMES:
            weighted = f"{weighted_base}_{scheme}"
            pairs.append(
                {
                    "raw_feature": raw,
                    "weighted_feature": weighted,
                    "scheme": scheme,
                    "pearson_correlation": float(dataset[raw].corr(dataset[weighted])),
                    "absolute_correlation": float(abs(dataset[raw].corr(dataset[weighted]))),
                }
            )
    output = pd.DataFrame(pairs).sort_values("absolute_correlation", ascending=False)
    output.to_csv(OUTPUT_DIR / "correlation_analysis.csv", index=False)
    return output


def remove_one_tests(dataset: pd.DataFrame, metadata: pd.DataFrame, best_name: str, best_columns: list[str]) -> pd.DataFrame:
    groups = {
        "full_best_reference": [],
        "remove_weighted_points": [column for column in best_columns if "points_weighted" in column],
        "remove_weighted_goals": [column for column in best_columns if "goals_scored_weighted" in column],
        "remove_weighted_xg": [column for column in best_columns if "xg_weighted" in column or "xga_weighted" in column or "xg_diff_weighted" in column],
        "remove_weighted_shots": [column for column in best_columns if "shots_weighted" in column or "shots_on_target_weighted" in column],
        "remove_weighted_ratings": [column for column in best_columns if "rating_weighted" in column],
    }
    rows = []
    for name, removed in groups.items():
        columns = [column for column in best_columns if column not in set(removed)]
        result = evaluate_feature_set(dataset, metadata, columns, f"{best_name}_{name}")
        rows.append(
            {
                "test": name,
                "removed_count": len(removed),
                "log_loss": result["log_loss"],
                "Brier_score": result["Brier_score"],
                "expected_calibration_error": result["expected_calibration_error"],
                "draw_recall": result["draw_recall"],
                "draw_log_loss": result["draw_log_loss"],
            }
        )
    output = pd.DataFrame(rows)
    output.to_csv(OUTPUT_DIR / "remove_one_tests.csv", index=False)
    return output


def regime_change_analysis(dataset: pd.DataFrame, metadata: pd.DataFrame) -> pd.DataFrame:
    rows = []
    for side in ("home", "away"):
        for idx, meta in metadata.iterrows():
            team = meta["HomeTeam"] if side == "home" else meta["AwayTeam"]
            raw_points = dataset.loc[idx, f"{side}_team_points_last_5"] if f"{side}_team_points_last_5" in dataset.columns else 0.0
            weighted_points = dataset.loc[idx, f"{side}_points_weighted_exponential"]
            raw_xg = dataset.loc[idx, f"{side}_xg_avg"]
            weighted_xg = dataset.loc[idx, f"{side}_xg_weighted_exponential"]
            rows.append(
                {
                    "Date": meta["Date"],
                    "Season": meta["Season"],
                    "team": team,
                    "side": side,
                    "points_recency_gap": float(weighted_points - (raw_points / 5.0)),
                    "xg_recency_gap": float(weighted_xg - raw_xg),
                }
            )
    frame = pd.DataFrame(rows)
    summary = (
        frame.groupby("team", as_index=False)
        .agg(
            mean_abs_points_recency_gap=("points_recency_gap", lambda values: float(np.mean(np.abs(values)))),
            mean_abs_xg_recency_gap=("xg_recency_gap", lambda values: float(np.mean(np.abs(values)))),
            max_abs_points_recency_gap=("points_recency_gap", lambda values: float(np.max(np.abs(values)))),
            max_abs_xg_recency_gap=("xg_recency_gap", lambda values: float(np.max(np.abs(values)))),
        )
        .sort_values(["mean_abs_xg_recency_gap", "mean_abs_points_recency_gap"], ascending=False)
    )
    summary.to_csv(OUTPUT_DIR / "regime_change_analysis.csv", index=False)
    lines = [
        "# Regime Change Analysis",
        "",
        "This analysis identifies teams where recency-weighted features diverge most from equal-weight rolling features. Large gaps suggest recent improvement or decline that ordinary rolling averages react to more slowly.",
        "",
        _markdown_table(summary.head(20), ["team", "mean_abs_points_recency_gap", "mean_abs_xg_recency_gap", "max_abs_points_recency_gap", "max_abs_xg_recency_gap"]),
    ]
    (OUTPUT_DIR / "regime_change_analysis.md").write_text("\n".join(lines))
    return summary


def plot_model_comparison(results: pd.DataFrame) -> None:
    metrics = ["log_loss", "Brier_score", "expected_calibration_error", "draw_recall", "draw_log_loss"]
    fig, axes = plt.subplots(1, len(metrics), figsize=(18, 4.5))
    for ax, metric in zip(axes, metrics):
        ax.bar(results["model_version"], results[metric])
        ax.set_title(metric)
        ax.tick_params(axis="x", rotation=30)
        ax.grid(axis="y", alpha=0.25)
    fig.suptitle("Recency Weighting Model Comparison")
    fig.tight_layout()
    fig.savefig(OUTPUT_DIR / "model_comparison.png", dpi=160)
    plt.close(fig)


def write_report(
    results: pd.DataFrame,
    shap_importance: pd.DataFrame,
    remove_one: pd.DataFrame,
    correlations: pd.DataFrame,
    analyzed_weighted_model: str,
) -> None:
    baseline = results[results["model_version"] == "model_a_current_production"].iloc[0]
    best = results.sort_values(["log_loss", "Brier_score"]).iloc[0]
    best_weighted = results[results["model_version"] == analyzed_weighted_model].iloc[0]
    best_delta_log = float(best["log_loss"] - baseline["log_loss"])
    best_delta_brier = float(best["Brier_score"] - baseline["Brier_score"])
    best_delta_ece = float(best["expected_calibration_error"] - baseline["expected_calibration_error"])
    weighted_delta_log = float(best_weighted["log_loss"] - baseline["log_loss"])
    weighted_delta_brier = float(best_weighted["Brier_score"] - baseline["Brier_score"])
    weighted_delta_ece = float(best_weighted["expected_calibration_error"] - baseline["expected_calibration_error"])
    production_ready = (best_delta_log < 0 or best_delta_brier < 0) and best_delta_ece <= 0.01 and best["model_version"] != "model_a_current_production"
    weighted_shap = shap_importance[shap_importance["feature_group"].str.startswith("weighted", na=False)].head(15)
    shap_lines = "\n".join(f"- `{row.feature}` ({row.feature_group}): {row.mean_abs_shap:.4f}" for row in weighted_shap.itertuples())
    shap_groups = (
        shap_importance.groupby("feature_group", as_index=False)["mean_abs_shap"]
        .sum()
        .sort_values("mean_abs_shap", ascending=False)
    )
    avg_corr = float(correlations["absolute_correlation"].mean())
    decision = (
        f"Move `{best['model_version']}` forward as a production candidate after rolling-split confirmation."
        if production_ready
        else "Do not move recency weighting into production. Keep current equal-weight rolling features."
    )
    Path(OUTPUT_DIR / "recency_weighting_report.md").write_text(
        f"""# Sprint 4G: Recency-Weighted Form and xG Evaluation

## Goal

Determine whether recent matches should receive greater weight than older matches inside rolling form, xG/xGA and shot-volume windows.

## Model Comparison

{_markdown_table(results, ['model_version', 'accuracy', 'log_loss', 'Brier_score', 'expected_calibration_error', 'draw_recall', 'draw_log_loss'])}

## Best Model

- Best model by Log Loss: `{best['model_version']}`
- Log Loss delta vs production: {best_delta_log:.4f}
- Brier delta vs production: {best_delta_brier:.4f}
- ECE delta vs production: {best_delta_ece:.4f}

## SHAP

SHAP was run on the best non-production recency model: `{analyzed_weighted_model}`.

Top weighted feature signals:

{shap_lines or '- No weighted features were among the strongest SHAP signals.'}

Feature group SHAP importance:

{_markdown_table(shap_groups, ['feature_group', 'mean_abs_shap'])}

## Correlation and Redundancy

Average absolute correlation between raw and weighted counterparts: {avg_corr:.4f}.

High correlation means weighted features mostly describe the same information. Lower correlation means they may react differently to form changes.

## Remove-One Tests

Remove-one tests were run on `{analyzed_weighted_model}`.

{_markdown_table(remove_one, ['test', 'removed_count', 'log_loss', 'Brier_score', 'expected_calibration_error', 'draw_recall', 'draw_log_loss'])}

Best recency model delta vs production:

- Log Loss delta: {weighted_delta_log:.4f}
- Brier delta: {weighted_delta_brier:.4f}
- ECE delta: {weighted_delta_ece:.4f}

## Answers

1. Does recency weighting improve the model?

   {'Yes, the best weighted model improved the primary probability metrics on this split.' if production_ready else 'No, not enough to justify production on this split.'}

2. Which weighting scheme performs best?

   `{best['model_version']}`.

3. Does recency weighting improve draw prediction?

   Compare `draw_recall` and `draw_log_loss` above. Production promotion requires no material deterioration.

4. Does recency weighting improve calibration?

   Best-model ECE delta vs production: {best_delta_ece:.4f}.

5. Can weighted features replace existing rolling averages?

   Replacement is only acceptable if a replace-model beats production on Log Loss or Brier without worsening calibration. The table above is the evidence.

6. Recommended production configuration:

   {decision}

Production optimization priority: Log Loss, Brier Score, Calibration/ECE. Accuracy is secondary.
"""
    )


def main() -> None:
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    write_inventory()
    dataset, metadata, feature_sets = build_dataset()
    results, lookup = compare_models(dataset, metadata, feature_sets)
    plot_model_comparison(results)
    best_name = str(results.iloc[0]["model_version"])
    weighted_results = results[results["model_version"] != "model_a_current_production"]
    analyzed_weighted_name = str(weighted_results.iloc[0]["model_version"])
    shap_importance = shap_and_importance(lookup[analyzed_weighted_name])
    correlations = correlation_analysis(dataset)
    remove_one = remove_one_tests(dataset, metadata, analyzed_weighted_name, lookup[analyzed_weighted_name]["feature_columns"])
    regime_change_analysis(dataset, metadata)
    write_report(results, shap_importance, remove_one, correlations, analyzed_weighted_name)
    print(
        json.dumps(
            {
                "best_model": best_name,
                "analyzed_weighted_model": analyzed_weighted_name,
                "report": str(OUTPUT_DIR / "recency_weighting_report.md"),
            },
            indent=2,
        )
    )


if __name__ == "__main__":
    main()
