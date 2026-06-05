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
from sklearn.metrics import log_loss, recall_score
from sklearn.preprocessing import label_binarize

from calibration.calibration import calibration_summary, calibration_table, expected_calibration_error
from evaluation.model_evaluation import evaluate_probabilities, time_based_split
from explainability.shap_analysis import compute_shap_importance, plot_shap_importance, plot_shap_summary
from feature_experiments import _markdown_table, train_xgb
from head_to_head_features import (
    ALL_H2H_COLUMNS,
    CORE_H2H_COLUMNS,
    RECENT_H2H_COLUMNS,
    VENUE_H2H_COLUMNS,
    build_head_to_head_features,
    h2h_methodology_note,
)
from tactical_data import ensure_tactical_tables, load_team_match_tactics
from tactical_features import build_tactical_features
from train_model import SCHEDULE_FEATURE_COLUMNS, build_features, load_matches_with_xg
from visualizations.plots import gain_importance, plot_feature_importance

matplotlib.use("Agg")

OUTPUT_DIR = Path("evaluation") / "head_to_head_intelligence"
RESULTS_PATH = Path("experiments") / "head_to_head_intelligence_results.csv"
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


def build_h2h_experiment_dataset() -> tuple[pd.DataFrame, pd.DataFrame, dict[str, list[str]], pd.DataFrame]:
    matches = load_matches_with_xg().sort_values("Date").reset_index(drop=True)
    base_dataset, _ = build_features(matches, include_xg=True, include_schedule=True)
    h2h_features = build_head_to_head_features(matches)

    tactical_columns: list[str] = []
    try:
        ensure_tactical_tables()
        tactics = load_team_match_tactics()
        tactical_features, _ = build_tactical_features(matches, tactics)
        tactical_columns = available_columns(tactical_features, TACTICAL_PRESSURE_COLUMNS)
        dataset = pd.concat(
            [base_dataset.reset_index(drop=True), tactical_features[tactical_columns].reset_index(drop=True), h2h_features],
            axis=1,
        )
    except Exception as exc:
        print(f"Warning: tactical pressure features unavailable for H2H experiment: {exc}")
        dataset = pd.concat([base_dataset.reset_index(drop=True), h2h_features], axis=1)

    production_columns = SCHEDULE_FEATURE_COLUMNS + tactical_columns
    feature_sets = {
        "model_a_current_production": production_columns,
        "model_b_core_h2h": production_columns + CORE_H2H_COLUMNS,
        "model_c_recent_h2h": production_columns + CORE_H2H_COLUMNS + RECENT_H2H_COLUMNS,
        "model_d_venue_h2h": production_columns + CORE_H2H_COLUMNS + VENUE_H2H_COLUMNS,
        "model_e_all_h2h": production_columns + ALL_H2H_COLUMNS,
    }
    metadata = matches[["Season", "Date", "HomeTeam", "AwayTeam", "FTR"]].reset_index(drop=True)
    return dataset, metadata, feature_sets, matches


def draw_metrics(y_true: pd.Series, probabilities: np.ndarray, predictions: np.ndarray) -> dict[str, float]:
    draw_mask = y_true.to_numpy() == 1
    if not draw_mask.any():
        return {"draw_log_loss": 0.0, "draw_recall": 0.0, "draw_calibration_error": 0.0}
    y_one_hot = label_binarize(y_true, classes=[0, 1, 2])
    draw_probability = np.clip(probabilities[:, 1], 1e-15, 1.0)
    return {
        "draw_log_loss": float(-np.mean(np.log(draw_probability[draw_mask]))),
        "draw_recall": float(recall_score(y_true, predictions, labels=[1], average="micro", zero_division=0)),
        "draw_calibration_error": float(abs(y_one_hot[:, 1].mean() - probabilities[:, 1].mean())),
    }


def evaluate_feature_set(
    dataset: pd.DataFrame,
    metadata: pd.DataFrame,
    feature_columns: list[str],
    model_version: str,
) -> dict[str, object]:
    X = dataset[feature_columns]
    y = dataset["target"]
    split = time_based_split(X, y, metadata)
    model = train_xgb(split.X_train, split.y_train)
    probabilities = model.predict_proba(split.X_test)
    probabilities = np.clip(probabilities, 1e-15, 1.0)
    probabilities = probabilities / probabilities.sum(axis=1, keepdims=True)
    predictions = probabilities.argmax(axis=1)
    metrics = evaluate_probabilities(split.y_test, probabilities, predictions)
    calibration = calibration_table(split.y_test, probabilities)
    cal_summary = calibration_summary(calibration)
    draws = draw_metrics(split.y_test, probabilities, predictions)

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
        "draw_log_loss": draws["draw_log_loss"],
        "draw_recall": draws["draw_recall"],
        "draw_calibration_error": draws["draw_calibration_error"],
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
                "draw_log_loss": result["draw_log_loss"],
                "draw_recall": result["draw_recall"],
                "draw_calibration_error": result["draw_calibration_error"],
            }
        )
    output = pd.DataFrame(rows)
    RESULTS_PATH.parent.mkdir(exist_ok=True)
    output.to_csv(RESULTS_PATH, index=False)
    output.to_csv(OUTPUT_DIR / "model_comparison.csv", index=False)
    return output


def plot_model_comparison(results: pd.DataFrame, output_path: Path) -> None:
    metrics = ["log_loss", "Brier_score", "calibration_score", "draw_log_loss", "draw_recall"]
    fig, axes = plt.subplots(1, len(metrics), figsize=(18, 4))
    for ax, metric in zip(axes, metrics):
        ax.bar(results["model_version"], results[metric])
        ax.set_title(metric)
        ax.tick_params(axis="x", rotation=35)
        ax.grid(axis="y", alpha=0.25)
    fig.suptitle("Head-to-Head Intelligence Model Comparison")
    fig.tight_layout()
    fig.savefig(output_path, dpi=160)
    plt.close(fig)


def _feature_group(feature: str) -> str:
    if feature in CORE_H2H_COLUMNS:
        return "h2h_core"
    if feature in RECENT_H2H_COLUMNS:
        return "h2h_recent"
    if feature in VENUE_H2H_COLUMNS:
        return "h2h_venue"
    if "attacking_pressure" in feature:
        return "tactical_pressure"
    if "xg" in feature or "xga" in feature:
        return "xG"
    if "days_rest" in feature or "matches_last" in feature or "midweek" in feature:
        return "fatigue"
    return "baseline"


def shap_outputs(full_result: dict[str, object]) -> pd.DataFrame:
    split = full_result["split"]
    model = full_result["model"]
    shap_importance, _, _ = compute_shap_importance(model, split.X_test)
    shap_importance["feature_group"] = shap_importance["feature"].map(_feature_group)
    shap_importance.to_csv(OUTPUT_DIR / "shap_feature_rankings.csv", index=False)
    shap_importance.groupby("feature_group", as_index=False)["mean_abs_shap"].sum().sort_values(
        "mean_abs_shap", ascending=False
    ).to_csv(OUTPUT_DIR / "shap_group_rankings.csv", index=False)
    plot_shap_importance(shap_importance.head(35), OUTPUT_DIR / "shap_feature_rankings.png")
    plot_shap_summary(model, split.X_test, OUTPUT_DIR / "shap_summary.png")
    gain = gain_importance(model, full_result["feature_columns"])
    gain.to_csv(OUTPUT_DIR / "gain_importance.csv", index=False)
    plot_feature_importance(gain.head(35), "gain_importance", "H2H Intelligence Gain Importance", OUTPUT_DIR / "gain_importance.png")
    return shap_importance


def _delta(results: pd.DataFrame, model_a: str, model_b: str, metric: str) -> float:
    a = float(results.loc[results["model_version"] == model_a, metric].iloc[0])
    b = float(results.loc[results["model_version"] == model_b, metric].iloc[0])
    return b - a


def write_report(results: pd.DataFrame, shap_importance: pd.DataFrame, output_path: Path) -> None:
    model_table = _markdown_table(
        results,
        [
            "model_version",
            "accuracy",
            "log_loss",
            "Brier_score",
            "calibration_score",
            "expected_calibration_error",
            "draw_log_loss",
            "draw_recall",
            "draw_calibration_error",
        ],
    )
    group_importance = (
        shap_importance.groupby("feature_group", as_index=False)["mean_abs_shap"]
        .sum()
        .sort_values("mean_abs_shap", ascending=False)
    )
    h2h_importance = shap_importance[shap_importance["feature_group"].str.startswith("h2h")].head(12)
    best = results.sort_values(["log_loss", "Brier_score"]).iloc[0]
    baseline = "model_a_current_production"
    all_h2h = "model_e_all_h2h"
    production_ready = (
        str(best["model_version"]) == all_h2h
        and _delta(results, baseline, all_h2h, "log_loss") < 0
        and _delta(results, baseline, all_h2h, "Brier_score") < 0
    )
    h2h_lines = "\n".join(
        f"- `{row.feature}` ({row.feature_group}): {row.mean_abs_shap:.4f}"
        for row in h2h_importance.itertuples()
    )
    group_table = _markdown_table(group_importance, ["feature_group", "mean_abs_shap"])

    output_path.write_text(
        f"""# Head-to-Head Intelligence Report

## Validation Setup

All models use strict time-based validation. No random split is used.

- Train period: {results['train_period'].iloc[0]}
- Test period: {results['test_period'].iloc[0]}

## Model Comparison

{model_table}

## 1. Do head-to-head features improve prediction quality?

Best model by log loss: `{best['model_version']}`.

Model E vs Model A:

- Log loss change: {_delta(results, baseline, all_h2h, 'log_loss'):.4f}
- Brier score change: {_delta(results, baseline, all_h2h, 'Brier_score'):.4f}
- Calibration change: {_delta(results, baseline, all_h2h, 'calibration_score'):.4f}
- ECE change: {_delta(results, baseline, all_h2h, 'expected_calibration_error'):.4f}

Production decision: {'Move H2H forward as a production candidate.' if production_ready else 'Keep H2H research-only for now.'}

## 2. Which H2H features matter most?

Top H2H SHAP features:

{h2h_lines or '- No H2H feature had meaningful SHAP contribution.'}

SHAP contribution by group:

{group_table}

## 3. Do venue-specific H2H features help?

Model D vs Model B:

- Log loss change: {_delta(results, 'model_b_core_h2h', 'model_d_venue_h2h', 'log_loss'):.4f}
- Brier score change: {_delta(results, 'model_b_core_h2h', 'model_d_venue_h2h', 'Brier_score'):.4f}
- Calibration change: {_delta(results, 'model_b_core_h2h', 'model_d_venue_h2h', 'calibration_score'):.4f}

Venue-specific H2H should only move forward if it improves log loss or Brier without worsening calibration.

## 4. Do H2H features improve draw prediction?

Model E vs Model A draw metrics:

- Draw log loss change: {_delta(results, baseline, all_h2h, 'draw_log_loss'):.4f}
- Draw recall change: {_delta(results, baseline, all_h2h, 'draw_recall'):.4f}
- Draw calibration error change: {_delta(results, baseline, all_h2h, 'draw_calibration_error'):.4f}

## 5. Are H2H features useful after controlling for xG and form?

The baseline already includes form, xG, xGA, xG differential, home advantage, schedule/fatigue and available shots-based tactical pressure. H2H only counts as genuine new signal if it improves Model A on out-of-sample log loss or Brier score and has non-zero SHAP contribution.

## Leakage Controls

{h2h_methodology_note()}
"""
    )


def main() -> None:
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    dataset, metadata, feature_sets, _ = build_h2h_experiment_dataset()
    results = [
        evaluate_feature_set(dataset, metadata, columns, model_version)
        for model_version, columns in feature_sets.items()
    ]
    results_frame = save_results(results)
    plot_model_comparison(results_frame, OUTPUT_DIR / "model_comparison.png")
    full_result = next(result for result in results if result["model_version"] == "model_e_all_h2h")
    shap_importance = shap_outputs(full_result)
    write_report(results_frame, shap_importance, Path("head_to_head_intelligence_report.md"))
    print(json.dumps({"best_model": str(results_frame.sort_values("log_loss").iloc[0]["model_version"])}, indent=2))


if __name__ == "__main__":
    main()
