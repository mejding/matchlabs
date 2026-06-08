from __future__ import annotations

import json
import os
from pathlib import Path

Path("evaluation", ".matplotlib-cache").mkdir(parents=True, exist_ok=True)
os.environ.setdefault("MPLCONFIGDIR", str(Path("evaluation") / ".matplotlib-cache"))

import matplotlib
import pandas as pd
from matplotlib import pyplot as plt

from calibration.calibration import calibration_summary, calibration_table, expected_calibration_error
from evaluation.model_evaluation import evaluate_probabilities, time_based_split
from explainability.shap_analysis import compute_shap_importance, plot_shap_importance, plot_shap_summary
from feature_experiments import _markdown_table, train_xgb
from lineup_data import ensure_lineup_tables, load_manager_history, load_player_appearances
from lineup_stability_features import (
    all_lineup_stability_columns,
    build_lineup_stability_features,
    familiarity_feature_columns,
    lineup_engine_note,
    lineup_feature_columns,
    stability_feature_columns,
)
from tactical_data import ensure_tactical_tables, load_team_match_tactics
from tactical_features import build_tactical_features
from train_model import ELO_CONFIG, PRODUCTION_FEATURE_COLUMNS, build_features, load_matches_with_xg
from elo_rating_features import build_elo_features
from visualizations.plots import gain_importance, plot_feature_importance

matplotlib.use("Agg")

OUTPUT_DIR = Path("evaluation") / "lineup_stability_engine"
RESULTS_PATH = Path("experiments") / "lineup_stability_engine_results.csv"
TACTICAL_PRESSURE_COLUMNS = [
    "home_attacking_pressure_score_last5",
    "home_attacking_pressure_score_last10",
    "home_attacking_pressure_score_season",
    "away_attacking_pressure_score_last5",
    "away_attacking_pressure_score_last10",
    "away_attacking_pressure_score_season",
]


def available_columns(dataset: pd.DataFrame, columns: list[str]) -> list[str]:
    return [column for column in columns if column in dataset.columns and dataset[column].notna().sum() > 0]


def build_lineup_dataset() -> tuple[pd.DataFrame, pd.DataFrame, dict[str, list[str]], pd.DataFrame, int]:
    ensure_lineup_tables()
    matches = load_matches_with_xg().sort_values("Date").reset_index(drop=True)
    base_dataset, _ = build_features(matches, include_xg=True, include_schedule=True)
    elo_features, _ = build_elo_features(matches, ELO_CONFIG)
    appearances = load_player_appearances()
    managers = load_manager_history()
    lineup_features = build_lineup_stability_features(matches, appearances, managers)

    tactical_columns: list[str] = []
    try:
        ensure_tactical_tables()
        tactics = load_team_match_tactics()
        tactical_features, _ = build_tactical_features(matches, tactics)
        tactical_columns = available_columns(tactical_features, TACTICAL_PRESSURE_COLUMNS)
        dataset = pd.concat(
            [
                base_dataset.reset_index(drop=True),
                elo_features.reset_index(drop=True),
                tactical_features[tactical_columns].reset_index(drop=True),
                lineup_features,
            ],
            axis=1,
        )
    except Exception as exc:
        print(f"Warning: tactical pressure unavailable for lineup experiment: {exc}")
        dataset = pd.concat([base_dataset.reset_index(drop=True), elo_features.reset_index(drop=True), lineup_features], axis=1)

    production_columns = PRODUCTION_FEATURE_COLUMNS + tactical_columns
    feature_sets = {
        "model_a_current_production": production_columns,
        "model_b_lineup_continuity": production_columns + lineup_feature_columns(),
        "model_c_continuity_familiarity": production_columns + lineup_feature_columns() + familiarity_feature_columns(),
        "model_d_full_lineup_stability": production_columns + all_lineup_stability_columns(),
    }
    metadata = matches[["Season", "Date", "HomeTeam", "AwayTeam", "FTR"]].reset_index(drop=True)
    return dataset, metadata, feature_sets, matches, len(appearances)


def evaluate_feature_set(dataset: pd.DataFrame, metadata: pd.DataFrame, feature_columns: list[str], model_version: str) -> dict[str, object]:
    X = dataset[feature_columns]
    y = dataset["target"]
    split = time_based_split(X, y, metadata)
    model = train_xgb(split.X_train, split.y_train)
    probabilities = model.predict_proba(split.X_test)
    predictions = probabilities.argmax(axis=1)
    metrics = evaluate_probabilities(split.y_test, probabilities, predictions)
    calibration = calibration_table(split.y_test, probabilities)
    cal_summary = calibration_summary(calibration)
    return {
        "model_version": model_version,
        "model": model,
        "split": split,
        "probabilities": probabilities,
        "predictions": predictions,
        "feature_columns": feature_columns,
        "accuracy": metrics["accuracy"],
        "log_loss": metrics["log_loss"],
        "brier_score": metrics["brier_score_multiclass"],
        "calibration_score": cal_summary["mean_absolute_calibration_error"],
        "expected_calibration_error": expected_calibration_error(calibration),
        "train_period": f"{split.train_metadata['Date'].iloc[0]} to {split.train_metadata['Date'].iloc[-1]}",
        "test_period": f"{split.test_metadata['Date'].iloc[0]} to {split.test_metadata['Date'].iloc[-1]}",
    }


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
    output.to_csv(OUTPUT_DIR / "model_comparison.csv", index=False)
    return output


def plot_model_comparison(results: pd.DataFrame, output_path: Path) -> None:
    metrics = ["accuracy", "log_loss", "Brier_score", "calibration_score", "expected_calibration_error"]
    fig, axes = plt.subplots(1, len(metrics), figsize=(17, 4))
    for ax, metric in zip(axes, metrics):
        ax.bar(results["model_version"], results[metric])
        ax.set_title(metric)
        ax.tick_params(axis="x", rotation=30)
        ax.grid(axis="y", alpha=0.25)
    fig.suptitle("Historical Lineup Stability Model Comparison")
    fig.tight_layout()
    fig.savefig(output_path, dpi=160)
    plt.close(fig)


def _feature_group(feature: str) -> str:
    if "shared_" in feature or "familiarity" in feature:
        return "familiarity"
    if "manager_" in feature or "rotation" in feature or "squad_consistency" in feature:
        return "stability"
    if "lineup" in feature or "starting_xi" in feature or "same_" in feature:
        return "continuity"
    return "production"


def shap_outputs(result: dict[str, object]) -> pd.DataFrame:
    split = result["split"]
    model = result["model"]
    shap_importance, _, _ = compute_shap_importance(model, split.X_test)
    shap_importance["feature_group"] = shap_importance["feature"].map(_feature_group)
    shap_importance.to_csv(OUTPUT_DIR / "shap_feature_rankings.csv", index=False)
    shap_importance.groupby("feature_group", as_index=False)["mean_abs_shap"].sum().sort_values(
        "mean_abs_shap", ascending=False
    ).to_csv(OUTPUT_DIR / "shap_group_rankings.csv", index=False)
    plot_shap_importance(shap_importance.head(35), OUTPUT_DIR / "shap_feature_rankings.png")
    plot_shap_summary(model, split.X_test, OUTPUT_DIR / "shap_summary.png")
    gain = gain_importance(model, result["feature_columns"])
    gain.to_csv(OUTPUT_DIR / "gain_importance.csv", index=False)
    plot_feature_importance(gain.head(35), "gain_importance", "Lineup Stability Gain Importance", OUTPUT_DIR / "gain_importance.png")
    return shap_importance


def _delta(results: pd.DataFrame, model_a: str, model_b: str, metric: str) -> float:
    a = float(results.loc[results["model_version"] == model_a, metric].iloc[0])
    b = float(results.loc[results["model_version"] == model_b, metric].iloc[0])
    return b - a


def write_report(results: pd.DataFrame, shap_importance: pd.DataFrame, appearance_rows: int) -> None:
    full = "model_d_full_lineup_stability"
    baseline = "model_a_current_production"
    production_ready = (
        appearance_rows > 0
        and _delta(results, baseline, full, "log_loss") < 0
        and _delta(results, baseline, full, "Brier_score") < 0
    )
    lineup_shap = shap_importance[shap_importance["feature_group"].isin(["continuity", "familiarity", "stability"])].head(12)
    lineup_lines = "\n".join(f"- `{row.feature}` ({row.feature_group}): {row.mean_abs_shap:.4f}" for row in lineup_shap.itertuples())

    Path("lineup_stability_report.md").write_text(
        f"""# Lineup Stability Report

## Data Coverage

- Historical player appearance rows available: {appearance_rows}

## Model Comparison

{_markdown_table(results, ['model_version', 'accuracy', 'log_loss', 'Brier_score', 'calibration_score', 'expected_calibration_error'])}

## Does lineup continuity create genuine predictive signal?

Model D vs Model A:

- Log loss change: {_delta(results, baseline, full, 'log_loss'):.4f}
- Brier score change: {_delta(results, baseline, full, 'Brier_score'):.4f}
- Calibration change: {_delta(results, baseline, full, 'calibration_score'):.4f}

Top lineup SHAP features:

{lineup_lines or '- No lineup feature had measurable SHAP contribution.'}

## Production Decision

{'Move lineup stability forward as a production candidate.' if production_ready else 'Do not activate lineup stability features. Keep them research-only until real historical lineup rows exist and improve out-of-sample log loss/Brier.'}

## Leakage Controls

{lineup_engine_note()}
"""
    )


def main() -> None:
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    dataset, metadata, feature_sets, _, appearance_rows = build_lineup_dataset()
    results = [evaluate_feature_set(dataset, metadata, columns, version) for version, columns in feature_sets.items()]
    results_frame = save_results(results)
    plot_model_comparison(results_frame, OUTPUT_DIR / "model_comparison.png")
    full_result = next(result for result in results if result["model_version"] == "model_d_full_lineup_stability")
    shap_importance = shap_outputs(full_result)
    write_report(results_frame, shap_importance, appearance_rows)
    print(json.dumps({"appearance_rows": appearance_rows, "activate": False if appearance_rows == 0 else None}, indent=2))


if __name__ == "__main__":
    main()
