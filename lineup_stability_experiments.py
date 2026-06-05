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

from evaluation.model_evaluation import evaluate_probabilities, time_based_split
from explainability.shap_analysis import compute_shap_importance, plot_local_waterfall, plot_shap_importance, plot_shap_summary
from feature_experiments import build_experiment_datasets, evaluate_feature_set, _markdown_table
from lineup_data import ensure_lineup_tables, lineup_data_note, load_manager_history, load_player_appearances
from lineup_stability_features import (
    all_lineup_stability_columns,
    build_lineup_stability_features,
    familiarity_feature_columns,
    lineup_engine_note,
    lineup_feature_columns,
    stability_feature_columns,
)
from train_model import points_for_team
from visualizations.plots import gain_importance, plot_feature_importance

matplotlib.use("Agg")

OUTPUT_DIR = Path("evaluation") / "lineup_stability"
RESULTS_PATH = Path("experiments") / "lineup_stability_results.csv"
RANDOM_SEED = 42


def _lineup_feature_group(feature: str) -> str:
    if "shared_" in feature or "familiarity" in feature:
        return "familiarity"
    if "manager_" in feature or "rotation" in feature or "squad_consistency" in feature:
        return "stability"
    if "last_win" in feature or "days_since_last_win" in feature:
        return "last_win"
    if "lineup" in feature or "starting_xi" in feature or "same_" in feature:
        return "continuity"
    if "xg" in feature or "xga" in feature:
        return "xG"
    if "days_rest" in feature or "midweek" in feature or "matches_last" in feature or "congestion" in feature:
        return "fatigue"
    if "injured" in feature or "missing" in feature or "availability" in feature:
        return "availability"
    return "baseline"


def build_lineup_experiment_datasets() -> tuple[pd.DataFrame, pd.DataFrame, dict[str, list[str]], pd.DataFrame]:
    ensure_lineup_tables()
    sprint2_dataset, metadata, sprint2_feature_sets, matches = build_experiment_datasets()
    appearances = load_player_appearances()
    managers = load_manager_history()
    lineup_features = build_lineup_stability_features(matches, appearances, managers)

    dataset = pd.concat([sprint2_dataset.reset_index(drop=True), lineup_features.reset_index(drop=True)], axis=1)
    sprint2_baseline = sprint2_feature_sets["model_d_baseline_fatigue_europe_injury"]
    feature_sets = {
        "model_a_sprint2_baseline": sprint2_baseline,
        "model_b_baseline_lineup_continuity": sprint2_baseline + lineup_feature_columns(),
        "model_c_baseline_continuity_familiarity": (
            sprint2_baseline + lineup_feature_columns() + familiarity_feature_columns()
        ),
        "model_d_full_stability_engine": sprint2_baseline + all_lineup_stability_columns(),
    }
    return dataset, metadata, feature_sets, matches


def save_results(results: list[dict[str, object]]) -> pd.DataFrame:
    rows = []
    for result in results:
        rows.append(
            {
                "experiment_id": f"{result['model_version']}_{pd.Timestamp.now(tz='UTC').strftime('%Y%m%d_%H%M%S')}",
                "model_version": result["model_version"],
                "features_added": "|".join(result["feature_columns"]),
                "train_period": result["train_period"],
                "test_period": result["test_period"],
                "accuracy": result["accuracy"],
                "log_loss": result["log_loss"],
                "Brier_score": result["brier_score"],
                "calibration_score": result["calibration_score"],
                "expected_calibration_error": result["expected_calibration_error"],
            }
        )
    output = pd.DataFrame(rows)
    RESULTS_PATH.parent.mkdir(exist_ok=True)
    output.to_csv(RESULTS_PATH, index=False)
    return output


def plot_model_comparison(results: pd.DataFrame, output_path: Path) -> None:
    metrics = ["log_loss", "Brier_score", "calibration_score", "expected_calibration_error"]
    fig, axes = plt.subplots(1, 4, figsize=(15, 4))
    for ax, metric in zip(axes, metrics):
        ax.bar(results["model_version"], results[metric])
        ax.set_title(metric)
        ax.tick_params(axis="x", rotation=35)
        ax.grid(axis="y", alpha=0.25)
    fig.suptitle("Lineup Stability Model Comparison: Lower Is Better")
    fig.tight_layout()
    fig.savefig(output_path, dpi=160)
    plt.close(fig)


def shap_outputs(full_result: dict[str, object], output_dir: Path) -> pd.DataFrame:
    split = full_result["split"]
    model = full_result["model"]
    shap_importance, _, _ = compute_shap_importance(model, split.X_test)
    shap_importance["feature_group"] = shap_importance["feature"].map(_lineup_feature_group)
    shap_importance.to_csv(output_dir / "shap_feature_rankings.csv", index=False)
    shap_importance.groupby("feature_group", as_index=False)["mean_abs_shap"].sum().sort_values(
        "mean_abs_shap", ascending=False
    ).to_csv(output_dir / "shap_group_rankings.csv", index=False)
    plot_shap_importance(shap_importance.head(30), output_dir / "shap_feature_rankings.png")
    plot_shap_summary(model, split.X_test, output_dir / "shap_summary.png")
    plot_local_waterfall(model, split.X_test.reset_index(drop=True), output_dir / "shap_local_home_win.png")
    gain = gain_importance(model, full_result["feature_columns"])
    gain.to_csv(output_dir / "gain_importance.csv", index=False)
    plot_feature_importance(gain.head(30), "gain_importance", "Lineup Stability Gain Importance", output_dir / "gain_importance.png")
    return shap_importance


def _team_rows(matches: pd.DataFrame, features: pd.DataFrame) -> pd.DataFrame:
    rows = []
    joined = pd.concat([matches.reset_index(drop=True), features.reset_index(drop=True)], axis=1)
    for _, row in joined.iterrows():
        for side, team_col in (("home", "HomeTeam"), ("away", "AwayTeam")):
            rows.append(
                {
                    "Date": row["Date"],
                    "team": row[team_col],
                    "points": points_for_team(row, row[team_col]),
                    "repeat_pct": float(row.get(f"{side}_starting_xi_repeat_pct", 0.0)),
                    "lineup_changes": float(row.get(f"{side}_lineup_changes", 0.0)),
                    "last_win_similarity": float(row.get(f"{side}_lineup_similarity_last_win", 0.0)),
                    "familiarity": float(row.get(f"{side}_lineup_familiarity_score", 0.0)),
                }
            )
    return pd.DataFrame(rows)


def discovery_outputs(matches: pd.DataFrame, lineup_features: pd.DataFrame, output_dir: Path) -> dict[str, pd.DataFrame]:
    team_rows = _team_rows(matches, lineup_features)
    rows = []
    for team, group in team_rows.groupby("team"):
        high_continuity = group[group["repeat_pct"] >= 0.75]
        rotated = group[group["repeat_pct"] < 0.75]
        winning_lineup = group[group["last_win_similarity"] >= 0.75]
        other = group[group["last_win_similarity"] < 0.75]
        rows.append(
            {
                "team": team,
                "matches": int(len(group)),
                "high_continuity_matches": int(len(high_continuity)),
                "points_high_continuity": float(high_continuity["points"].mean()) if len(high_continuity) else np.nan,
                "points_rotated": float(rotated["points"].mean()) if len(rotated) else np.nan,
                "continuity_points_delta": (
                    float(high_continuity["points"].mean() - rotated["points"].mean())
                    if len(high_continuity) and len(rotated)
                    else np.nan
                ),
                "points_kept_winning_lineup": float(winning_lineup["points"].mean()) if len(winning_lineup) else np.nan,
                "points_other_lineups": float(other["points"].mean()) if len(other) else np.nan,
                "winning_lineup_points_delta": (
                    float(winning_lineup["points"].mean() - other["points"].mean())
                    if len(winning_lineup) and len(other)
                    else np.nan
                ),
                "familiarity_points_correlation": (
                    float(group["familiarity"].corr(group["points"]))
                    if len(group) >= 10 and group["familiarity"].nunique() > 1
                    else np.nan
                ),
            }
        )
    summary = pd.DataFrame(rows).sort_values("continuity_points_delta", ascending=False, na_position="last")
    summary.to_csv(output_dir / "team_lineup_continuity_analysis.csv", index=False)

    plot_data = summary.dropna(subset=["continuity_points_delta"]).head(12).sort_values("continuity_points_delta")
    fig, ax = plt.subplots(figsize=(8, 6))
    ax.barh(plot_data["team"], plot_data["continuity_points_delta"])
    ax.axvline(0, color="black", linewidth=1)
    ax.set_title("Teams Benefiting From Lineup Continuity")
    ax.set_xlabel("Points per match delta")
    fig.tight_layout()
    fig.savefig(output_dir / "team_lineup_continuity_analysis.png", dpi=160)
    plt.close(fig)
    return {"team_continuity": summary}


def _delta(results: pd.DataFrame, model_a: str, model_b: str, metric: str) -> float:
    a = float(results.loc[results["model_version"] == model_a, metric].iloc[0])
    b = float(results.loc[results["model_version"] == model_b, metric].iloc[0])
    return b - a


def write_report(
    results: pd.DataFrame,
    shap_importance: pd.DataFrame,
    discovery: dict[str, pd.DataFrame],
    output_path: Path,
) -> None:
    model_table = _markdown_table(
        results,
        ["model_version", "accuracy", "log_loss", "Brier_score", "calibration_score", "expected_calibration_error"],
    )
    measurable_shap = shap_importance[shap_importance["mean_abs_shap"] > 0]
    continuity = measurable_shap[measurable_shap["feature_group"] == "continuity"].head(8)
    familiarity = measurable_shap[measurable_shap["feature_group"] == "familiarity"].head(8)
    stability = measurable_shap[measurable_shap["feature_group"].isin(["stability", "last_win"])].head(8)
    lineup_shap = shap_importance[
        shap_importance["feature_group"].isin(["continuity", "familiarity", "stability", "last_win"])
    ].head(12)
    team_continuity = discovery["team_continuity"].dropna(subset=["continuity_points_delta"]).head(5)

    continuity_lines = "\n".join(f"- `{row.feature}`: {row.mean_abs_shap:.4f}" for row in continuity.itertuples())
    familiarity_lines = "\n".join(f"- `{row.feature}`: {row.mean_abs_shap:.4f}" for row in familiarity.itertuples())
    stability_lines = "\n".join(f"- `{row.feature}`: {row.mean_abs_shap:.4f}" for row in stability.itertuples())
    team_lines = "\n".join(
        f"- {row.team}: {row.continuity_points_delta:.3f} points per match delta"
        for row in team_continuity.itertuples()
    )

    output_path.write_text(
        f"""# Lineup Stability Report

## Validation

All models use the same time-based split. No random train/test split is used.

- Train period: {results['train_period'].iloc[0]}
- Test period: {results['test_period'].iloc[0]}

## Model Comparison

{model_table}

## 1. Does lineup continuity improve predictions?

Model B vs Model A:

- Log loss change: {_delta(results, 'model_a_sprint2_baseline', 'model_b_baseline_lineup_continuity', 'log_loss'):.4f}
- Brier score change: {_delta(results, 'model_a_sprint2_baseline', 'model_b_baseline_lineup_continuity', 'Brier_score'):.4f}
- Calibration change: {_delta(results, 'model_a_sprint2_baseline', 'model_b_baseline_lineup_continuity', 'calibration_score'):.4f}

Top continuity SHAP features:

{continuity_lines or '- No lineup continuity feature had measurable SHAP contribution.'}

## 2. Does squad familiarity improve predictions?

Model C vs Model B:

- Log loss change: {_delta(results, 'model_b_baseline_lineup_continuity', 'model_c_baseline_continuity_familiarity', 'log_loss'):.4f}
- Brier score change: {_delta(results, 'model_b_baseline_lineup_continuity', 'model_c_baseline_continuity_familiarity', 'Brier_score'):.4f}
- Calibration change: {_delta(results, 'model_b_baseline_lineup_continuity', 'model_c_baseline_continuity_familiarity', 'calibration_score'):.4f}

Top familiarity SHAP features:

{familiarity_lines or '- No familiarity feature had measurable SHAP contribution.'}

## 3. Does keeping a winning lineup matter?

Last-win and stability SHAP features:

{stability_lines or '- No last-win or squad stability feature had measurable SHAP contribution.'}

Team-level continuity leaders:

{team_lines or '- Not enough populated lineup history to identify team-level continuity effects.'}

## 4. Which continuity features are most predictive?

Top lineup/stability SHAP rows:

{_markdown_table(lineup_shap[['feature', 'mean_abs_shap', 'feature_group']], ['feature', 'mean_abs_shap', 'feature_group']) if not lineup_shap.empty and float(lineup_shap['mean_abs_shap'].max()) > 0 else 'No lineup stability features created measurable predictive signal.'}

## Production Decision

Only keep features that improve out-of-sample log loss and Brier score without worsening calibration. With the current local data, lineup tables are templates, so lineup features do not improve performance yet. This is a data availability result, not evidence that lineup stability is unimportant.

## Reproducibility and Leakage Controls

- Actual current-match starting XIs are not used as pre-match features.
- Expected/projected lineups must have `source_collected_at` before the fixture.
- Historical actual appearances are used only for matches before the fixture.
- Manager rows are active only when start/end dates cover the fixture date.
- Random seed: {RANDOM_SEED}

## Structured Tables

- `data/match_lineups.csv`
- `data/player_appearances.csv`
- `data/formation_history.csv`
- `data/match_substitutions.csv`
- `data/manager_history.csv`

{lineup_engine_note()}
"""
    )


def run() -> None:
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    dataset, metadata, feature_sets, matches = build_lineup_experiment_datasets()
    results = [evaluate_feature_set(dataset, metadata, columns, version) for version, columns in feature_sets.items()]
    results_table = save_results(results)
    results_table.to_csv(OUTPUT_DIR / "model_comparison.csv", index=False)
    plot_model_comparison(results_table, OUTPUT_DIR / "model_comparison.png")

    full_result = next(result for result in results if result["model_version"] == "model_d_full_stability_engine")
    shap_importance = shap_outputs(full_result, OUTPUT_DIR)
    lineup_features = dataset[all_lineup_stability_columns()]
    discovery = discovery_outputs(matches, lineup_features, OUTPUT_DIR)

    (OUTPUT_DIR / "experiment_summary.json").write_text(
        json.dumps(
            {
                "results": results_table.to_dict("records"),
                "lineup_tables": [
                    "data/match_lineups.csv",
                    "data/player_appearances.csv",
                    "data/formation_history.csv",
                    "data/match_substitutions.csv",
                    "data/manager_history.csv",
                ],
                "lineup_engine_note": lineup_engine_note(),
            },
            indent=2,
        )
    )
    write_report(results_table, shap_importance, discovery, Path("lineup_stability_report.md"))

    print("Lineup stability experiments complete.")
    print(f"Results: {RESULTS_PATH}")
    print("Report: lineup_stability_report.md")
    print(f"Artifacts: {OUTPUT_DIR}")


if __name__ == "__main__":
    run()
