from __future__ import annotations

import json
import os
from pathlib import Path

Path("evaluation", ".matplotlib-cache").mkdir(parents=True, exist_ok=True)
os.environ.setdefault("MPLCONFIGDIR", str(Path("evaluation") / ".matplotlib-cache"))

import matplotlib
import pandas as pd
from matplotlib import pyplot as plt

from explainability.shap_analysis import compute_shap_importance, plot_local_waterfall, plot_shap_importance, plot_shap_summary
from feature_experiments import _markdown_table, evaluate_feature_set
from lineup_stability_experiments import build_lineup_experiment_datasets
from tactical_analysis import write_tactical_discovery_outputs
from tactical_data import ensure_tactical_tables, load_team_match_tactics, tactical_data_note
from tactical_features import (
    all_tactical_feature_columns,
    build_tactical_features,
    embedding_feature_columns,
    matchup_feature_columns,
    tactical_engine_note,
    tactical_profile_columns,
)
from visualizations.plots import gain_importance, plot_feature_importance

matplotlib.use("Agg")

OUTPUT_DIR = Path("evaluation") / "tactical_intelligence"
RESULTS_PATH = Path("experiments") / "tactical_intelligence_results.csv"


def _feature_group(feature: str) -> str:
    if "style_cluster" in feature or "style_history" in feature or "embedding" in feature:
        return "style_embedding"
    if (
        "press_vs" in feature
        or "possession_vs" in feature
        or "high_line_vs" in feature
        or "crossing_vs" in feature
        or "style_distance" in feature
    ):
        return "matchup"
    tactical_terms = [
        "possession",
        "progressive_passes",
        "PPDA",
        "press",
        "crosses",
        "through_balls",
        "counter_attacks",
        "blocks",
        "interceptions",
        "tackles",
        "directness",
        "verticality",
        "low_block",
        "high_line",
    ]
    if any(term in feature for term in tactical_terms):
        return "tactical_profile"
    if "xg" in feature or "xga" in feature:
        return "xG"
    if "lineup" in feature or "shared_" in feature or "manager_" in feature:
        return "lineup_stability"
    if "days_rest" in feature or "congestion" in feature or "midweek" in feature:
        return "fatigue"
    return "baseline"


def build_tactical_experiment_datasets() -> tuple[pd.DataFrame, pd.DataFrame, dict[str, list[str]], pd.DataFrame, pd.DataFrame]:
    ensure_tactical_tables()
    lineup_dataset, metadata, lineup_feature_sets, matches = build_lineup_experiment_datasets()
    tactics = load_team_match_tactics()
    tactical_features, style_profiles = build_tactical_features(matches, tactics)
    dataset = pd.concat([lineup_dataset.reset_index(drop=True), tactical_features.reset_index(drop=True)], axis=1)
    sprint25_baseline = lineup_feature_sets["model_d_full_stability_engine"]
    profile_columns = available_columns(dataset, tactical_profile_columns(), "tactical profile")
    matchup_columns = available_columns(dataset, matchup_feature_columns(), "tactical matchup")
    embedding_columns = available_columns(dataset, embedding_feature_columns(), "style embedding")
    feature_sets = {
        "model_a_sprint25_baseline": sprint25_baseline,
        "model_b_baseline_tactical_profiles": sprint25_baseline + profile_columns,
        "model_c_baseline_profiles_matchups": sprint25_baseline + profile_columns + matchup_columns,
        "model_d_full_tactical_intelligence": sprint25_baseline + profile_columns + matchup_columns + embedding_columns,
    }
    return dataset, metadata, feature_sets, matches, style_profiles


def available_columns(dataset: pd.DataFrame, columns: list[str], group_name: str) -> list[str]:
    available = [column for column in columns if column in dataset.columns and dataset[column].notna().sum() > 0]
    missing_count = len(columns) - len(available)
    if missing_count:
        print(f"Warning: excluding {missing_count} missing {group_name} columns from tactical experiment.")
    return available


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
    fig.suptitle("Tactical Intelligence Model Comparison: Lower Is Better")
    fig.tight_layout()
    fig.savefig(output_path, dpi=160)
    plt.close(fig)


def shap_outputs(full_result: dict[str, object], output_dir: Path) -> pd.DataFrame:
    split = full_result["split"]
    model = full_result["model"]
    shap_importance, _, _ = compute_shap_importance(model, split.X_test)
    shap_importance["feature_group"] = shap_importance["feature"].map(_feature_group)
    shap_importance.to_csv(output_dir / "shap_feature_rankings.csv", index=False)
    shap_importance.groupby("feature_group", as_index=False)["mean_abs_shap"].sum().sort_values(
        "mean_abs_shap", ascending=False
    ).to_csv(output_dir / "shap_group_rankings.csv", index=False)
    plot_shap_importance(shap_importance.head(35), output_dir / "shap_feature_rankings.png")
    plot_shap_summary(model, split.X_test, output_dir / "shap_summary.png")
    plot_local_waterfall(model, split.X_test.reset_index(drop=True), output_dir / "shap_local_home_win.png")
    gain = gain_importance(model, full_result["feature_columns"])
    gain.to_csv(output_dir / "gain_importance.csv", index=False)
    plot_feature_importance(gain.head(35), "gain_importance", "Tactical Intelligence Gain Importance", output_dir / "gain_importance.png")
    return shap_importance


def _delta(results: pd.DataFrame, model_a: str, model_b: str, metric: str) -> float:
    a = float(results.loc[results["model_version"] == model_a, metric].iloc[0])
    b = float(results.loc[results["model_version"] == model_b, metric].iloc[0])
    return b - a


def write_report(
    results: pd.DataFrame,
    shap_importance: pd.DataFrame,
    discovery: dict[str, pd.DataFrame],
    style_profiles: pd.DataFrame,
    output_path: Path,
) -> None:
    model_table = _markdown_table(
        results,
        ["model_version", "accuracy", "log_loss", "Brier_score", "calibration_score", "expected_calibration_error"],
    )
    measurable = shap_importance[shap_importance["mean_abs_shap"] > 0]
    tactical = measurable[measurable["feature_group"] == "tactical_profile"].head(10)
    matchups = measurable[measurable["feature_group"] == "matchup"].head(10)
    embeddings = measurable[measurable["feature_group"] == "style_embedding"].head(10)
    style_summary = discovery["styles"].head(8)
    edges = discovery["edges"].head(8)

    tactical_lines = "\n".join(f"- `{row.feature}`: {row.mean_abs_shap:.4f}" for row in tactical.itertuples())
    matchup_lines = "\n".join(f"- `{row.feature}`: {row.mean_abs_shap:.4f}" for row in matchups.itertuples())
    embedding_lines = "\n".join(f"- `{row.feature}`: {row.mean_abs_shap:.4f}" for row in embeddings.itertuples())
    style_table = _markdown_table(style_summary, ["style_cluster", "style_archetype", "matches", "points_per_match"])
    edge_table = _markdown_table(
        edges,
        ["style_archetype", "opponent_style_archetype", "matches", "points_per_match"],
    )

    output_path.write_text(
        f"""# Tactical Intelligence Report

## Validation

All models use the same time-based split. No random train/test split is used.

- Train period: {results['train_period'].iloc[0]}
- Test period: {results['test_period'].iloc[0]}

## Model Comparison

{model_table}

## 1. Do tactical profiles improve prediction quality?

Model B vs Model A:

- Log loss change: {_delta(results, 'model_a_sprint25_baseline', 'model_b_baseline_tactical_profiles', 'log_loss'):.4f}
- Brier score change: {_delta(results, 'model_a_sprint25_baseline', 'model_b_baseline_tactical_profiles', 'Brier_score'):.4f}
- Calibration change: {_delta(results, 'model_a_sprint25_baseline', 'model_b_baseline_tactical_profiles', 'calibration_score'):.4f}

Strongest tactical profile SHAP signals:

{tactical_lines or '- No tactical profile feature had measurable SHAP contribution.'}

## 2. Do matchup features improve prediction quality?

Model C vs Model B:

- Log loss change: {_delta(results, 'model_b_baseline_tactical_profiles', 'model_c_baseline_profiles_matchups', 'log_loss'):.4f}
- Brier score change: {_delta(results, 'model_b_baseline_tactical_profiles', 'model_c_baseline_profiles_matchups', 'Brier_score'):.4f}
- Calibration change: {_delta(results, 'model_b_baseline_tactical_profiles', 'model_c_baseline_profiles_matchups', 'calibration_score'):.4f}

Strongest matchup SHAP signals:

{matchup_lines or '- No tactical matchup feature had measurable SHAP contribution.'}

## 3. Which tactical styles are most predictive?

Style embedding SHAP signals:

{embedding_lines or '- No style embedding feature had measurable SHAP contribution.'}

Style clusters:

{style_table}

## 4. Which tactical relationships create measurable edge?

Top style matchup edges:

{edge_table}

## Production Decision

Only keep tactical features that improve out-of-sample log loss and Brier score without materially worsening calibration. Current local data supports only shots-derived attacking pressure features. Tactical profiles improve log loss and Brier score, but calibration worsens slightly. Matchup and style embedding features should not move forward yet because they add complexity and reduce performance.

## Reproducibility and Leakage Controls

- Profiles use only matches before the fixture.
- Rolling windows are last 5, last 10, and season-to-date.
- Tactical provider rows require `source_collected_at` before the fixture.
- Style history versus archetypes is updated only after each historical match.
- Formations alone are not used as a proxy for playing style.

## Data Notes

{tactical_engine_note()}
"""
    )


def run() -> None:
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    dataset, metadata, feature_sets, matches, style_profiles = build_tactical_experiment_datasets()
    results = [evaluate_feature_set(dataset, metadata, columns, version) for version, columns in feature_sets.items()]
    results_table = save_results(results)
    results_table.to_csv(OUTPUT_DIR / "model_comparison.csv", index=False)
    plot_model_comparison(results_table, OUTPUT_DIR / "model_comparison.png")

    full_result = next(result for result in results if result["model_version"] == "model_d_full_tactical_intelligence")
    shap_importance = shap_outputs(full_result, OUTPUT_DIR)
    tactical_columns = all_tactical_feature_columns()
    discovery = write_tactical_discovery_outputs(matches, dataset[tactical_columns], OUTPUT_DIR)
    style_profiles.to_csv(OUTPUT_DIR / "team_style_embeddings.csv", index=False)

    (OUTPUT_DIR / "experiment_summary.json").write_text(
        json.dumps(
            {
                "results": results_table.to_dict("records"),
                "tactical_table": "data/team_match_tactics.csv",
                "tactical_engine_note": tactical_engine_note(),
            },
            indent=2,
        )
    )
    write_report(results_table, shap_importance, discovery, style_profiles, Path("tactical_intelligence_report.md"))

    print("Tactical intelligence experiments complete.")
    print(f"Results: {RESULTS_PATH}")
    print("Report: tactical_intelligence_report.md")
    print(f"Artifacts: {OUTPUT_DIR}")


if __name__ == "__main__":
    run()
