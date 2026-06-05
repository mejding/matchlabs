from __future__ import annotations

import json
import os
from pathlib import Path

Path("evaluation", ".matplotlib-cache").mkdir(parents=True, exist_ok=True)
os.environ.setdefault("MPLCONFIGDIR", str(Path("evaluation") / ".matplotlib-cache"))

import joblib
import pandas as pd

from bootstrap_confidence import bootstrap_prediction_intervals, summarize_prediction_intervals
from calibration.calibration import (
    calibration_diagnosis,
    calibration_summary,
    calibration_table,
    expected_calibration_error,
    plot_calibration_curve,
    plot_probability_histogram,
    plot_reliability_diagram,
)
from ensemble_predictor import train_ensemble_predictions
from evaluation.model_evaluation import (
    class_performance,
    confidence_table,
    evaluate_probabilities,
    time_based_split,
    worst_predictions,
)
from experiment_tracker import append_experiment
from explainability.shap_analysis import (
    compute_shap_class_importance,
    compute_shap_importance,
    plot_local_waterfall,
    plot_shap_importance,
    plot_shap_summary,
)
from elo_rating_features import EloConfig, build_elo_features
from train_model import (
    MODEL_DIR,
    MODEL_PATH,
    add_injury_features,
    build_features,
    load_injury_reports,
    load_matches_with_xg,
)
from prediction_confidence import batch_stability_table, match_level_confidence
from uncertainty_visualizations import plot_bootstrap_histograms, plot_stability_over_time
from visualizations.plots import (
    compute_permutation_importance,
    gain_importance,
    plot_confidence_analysis,
    plot_confusion_matrix,
    plot_feature_importance,
    plot_model_comparison,
    plot_prediction_distribution,
    plot_rolling_backtest,
)


EVALUATION_DIR = Path("evaluation")
CLASS_NAMES = ["home_win", "draw", "away_win"]
RANDOM_SEED = 42
BOOTSTRAP_MODELS = 30


def has_injury_features(feature_columns: list[str]) -> bool:
    return any("injured" in feature or "missing_" in feature for feature in feature_columns)


def has_schedule_features(feature_columns: list[str]) -> bool:
    return any(
        "days_rest" in feature
        or "matches_last_14_days" in feature
        or "had_midweek_match" in feature
        or "days_since_last_match" in feature
        for feature in feature_columns
    )


def has_elo_features(feature_columns: list[str]) -> bool:
    return any("elo" in feature for feature in feature_columns)


def load_current_dataset(feature_columns: list[str]) -> tuple[pd.DataFrame, pd.DataFrame]:
    matches = load_matches_with_xg()
    if has_injury_features(feature_columns):
        matches = add_injury_features(matches, load_injury_reports())

    dataset, _ = build_features(
        matches,
        include_xg=any("xg" in feature for feature in feature_columns),
        include_schedule=has_schedule_features(feature_columns),
        include_injuries=has_injury_features(feature_columns),
    )
    if has_elo_features(feature_columns):
        elo_features, _ = build_elo_features(
            matches,
            EloConfig(k_factor=30.0, home_advantage=75.0, margin_of_victory=False),
        )
        dataset = pd.concat([dataset.reset_index(drop=True), elo_features.reset_index(drop=True)], axis=1)
    metadata = matches[["Season", "Date", "HomeTeam", "AwayTeam", "FTR"]].reset_index(drop=True)
    return dataset, metadata


def model_comparison_from_metrics() -> pd.DataFrame:
    metrics_path = MODEL_DIR / "metrics.json"
    if not metrics_path.exists():
        return pd.DataFrame()

    metrics = json.loads(metrics_path.read_text())
    rows = []
    labels = {
        "baseline": "Baseline",
        "xg_model": "xG",
        "xg_schedule_model": "xG + schedule",
        "xg_schedule_elo_model": "XG + schedule + Elo",
        "xg_schedule_injury_model": "xG + schedule + injuries",
    }
    for key, label in labels.items():
        if key not in metrics:
            continue
        rows.append(
            {
                "model": label,
                "log_loss": metrics[key]["log_loss"],
                "brier_score": metrics[key]["brier_score"],
                "mean_absolute_calibration_error": metrics[key]["mean_absolute_calibration_error"],
            }
        )
    return pd.DataFrame(rows)


def write_markdown_report(report: dict[str, object], output_path: Path) -> None:
    shap_top = report["top_features_by_shap"][:8]
    shap_lines = "\n".join(f"- `{row['feature']}`: {row['mean_abs_shap']:.4f}" for row in shap_top)
    class_perf = report["class_performance"]
    poorest_class = max(class_perf, key=lambda row: row["actual_class_log_loss"])
    weakest_confidence_bin = max(report["confidence_analysis"], key=lambda row: row["confidence_minus_accuracy"])
    calibration_lines = "\n".join(
        f"- `{class_name}`: {diagnosis}"
        for class_name, diagnosis in report["calibration_diagnosis"].items()
    )
    interval_lines = "\n".join(
        f"- `{row['class']}`: mean {row['mean_probability']:.3f}, "
        f"95% CI {row['lower_95']:.3f}-{row['upper_95']:.3f}"
        for row in report["example_prediction_intervals"]
    )

    output_path.write_text(
        f"""# Football Model Evaluation

## Validation Setup

The evaluation uses a strict time-based split. No random train/test split is used.

- Training dates: {report['validation']['train_start_date']} to {report['validation']['train_end_date']}
- Test dates: {report['validation']['test_start_date']} to {report['validation']['test_end_date']}
- Train rows: {report['validation']['train_rows']}
- Test rows: {report['validation']['test_rows']}

## Metrics

- Accuracy: {report['accuracy']:.4f}
- Multiclass log loss: {report['log_loss']:.4f}
- Multiclass Brier score: {report['brier_score_multiclass']:.4f}
- Calibration error: {report['calibration']['mean_absolute_calibration_error']:.4f}
- Expected Calibration Error: {report['expected_calibration_error']:.4f}

## Calibration

{calibration_lines}

Negative signed calibration error means the model is generally overpredicting that class. Positive signed calibration error means it is underpredicting that class.

## Confidence Intervals

Bootstrap interval example for `{report['example_fixture']}`:

{interval_lines}

Confidence label: {report['example_confidence']['label']}

Uncertainty explanation: {report['example_confidence']['explanation']}

Mean bootstrap standard deviation across the test set: {report['ensemble']['bootstrap_mean_probability_std']:.4f}

Mean prediction stability score: {report['stability']['mean_stability_score']:.4f}

## Feature Contributions

Top SHAP features:

{shap_lines}

The feature importance CSV files compare gain importance, permutation importance, and SHAP importance. Features with low or zero values across all three are candidates for removal or better data.

## Weak Spots

The weakest actual class by log loss is `{poorest_class['class']}` with actual-class log loss {poorest_class['actual_class_log_loss']:.4f}.

The most overconfident confidence bin has mean confidence {weakest_confidence_bin['mean_confidence']:.4f}, accuracy {weakest_confidence_bin['accuracy']:.4f}, and {weakest_confidence_bin['count']} matches.

Inspect `evaluation/worst_predictions.csv` for the specific highest-loss predictions.
"""
    )


def evaluate() -> None:
    if not MODEL_PATH.exists():
        raise FileNotFoundError("Model not found. Run `python train_model.py` first.")

    EVALUATION_DIR.mkdir(exist_ok=True)
    artifact = joblib.load(MODEL_PATH)
    model = artifact["model"]
    feature_columns = artifact["feature_columns"]
    model_version = "xg_schedule_injury"

    dataset, metadata = load_current_dataset(feature_columns)
    X = dataset[feature_columns]
    y = dataset["target"]
    split = time_based_split(X, y, metadata)

    probabilities = model.predict_proba(split.X_test)
    predictions = model.predict(split.X_test)
    metrics = evaluate_probabilities(split.y_test, probabilities, predictions)

    calibration = calibration_table(split.y_test, probabilities)
    calibration.to_csv(EVALUATION_DIR / "calibration_table.csv", index=False)
    cal_summary = calibration_summary(calibration)
    ece = expected_calibration_error(calibration)
    cal_diagnosis = calibration_diagnosis(cal_summary)

    confidence = confidence_table(split.y_test, probabilities, predictions)
    confidence.to_csv(EVALUATION_DIR / "confidence_analysis.csv", index=False)

    class_metrics = class_performance(split.y_test, probabilities, predictions)
    class_metrics.to_csv(EVALUATION_DIR / "class_performance.csv", index=False)

    worst = worst_predictions(split.test_metadata, split.y_test, probabilities, predictions)
    worst.to_csv(EVALUATION_DIR / "worst_predictions.csv", index=False)

    gain = gain_importance(model, feature_columns)
    gain.to_csv(EVALUATION_DIR / "gain_importance.csv", index=False)
    plot_feature_importance(gain, "gain_importance", "XGBoost Gain Importance", EVALUATION_DIR / "feature_importance.png")

    permutation = compute_permutation_importance(model, split.X_test, split.y_test)
    permutation.to_csv(EVALUATION_DIR / "permutation_importance.csv", index=False)
    plot_feature_importance(
        permutation,
        "permutation_importance",
        "Permutation Importance: Log Loss Impact",
        EVALUATION_DIR / "permutation_importance.png",
    )

    shap_importance, _, _ = compute_shap_importance(model, split.X_test)
    shap_importance.to_csv(EVALUATION_DIR / "shap_importance.csv", index=False)
    plot_shap_importance(shap_importance, EVALUATION_DIR / "shap_importance.png")
    compute_shap_class_importance(model, split.X_test).to_csv(EVALUATION_DIR / "shap_class_importance.csv", index=False)
    plot_shap_summary(model, split.X_test, EVALUATION_DIR / "shap_summary.png")
    plot_local_waterfall(model, split.X_test.reset_index(drop=True), EVALUATION_DIR / "shap_waterfall_home_win.png", row_index=0, class_index=0)

    plot_calibration_curve(calibration, EVALUATION_DIR / "calibration_curve.png")
    plot_reliability_diagram(calibration, EVALUATION_DIR / "reliability_diagram.png")
    plot_probability_histogram(probabilities, EVALUATION_DIR / "probability_histogram.png")
    plot_confidence_analysis(confidence, EVALUATION_DIR / "confidence_accuracy.png")
    plot_confusion_matrix(split.y_test, predictions, EVALUATION_DIR / "confusion_matrix.png")
    rolling = plot_rolling_backtest(split.test_metadata, split.y_test, probabilities, EVALUATION_DIR / "rolling_backtest_log_loss.png")
    rolling.to_csv(EVALUATION_DIR / "rolling_backtest_log_loss.csv", index=False)

    comparison = model_comparison_from_metrics()
    if not comparison.empty:
        comparison.to_csv(EVALUATION_DIR / "model_comparison.csv", index=False)
        plot_model_comparison(comparison, EVALUATION_DIR / "model_comparison.png")

    bootstrap = bootstrap_prediction_intervals(
        split.X_train,
        split.y_train,
        split.X_test.reset_index(drop=True),
        n_models=BOOTSTRAP_MODELS,
        seed=RANDOM_SEED,
    )
    example_intervals, example_confidence = match_level_confidence(bootstrap, row_index=0)
    example_intervals.to_csv(EVALUATION_DIR / "bootstrap_prediction_intervals.csv", index=False)
    stability = batch_stability_table(bootstrap)
    stability.to_csv(EVALUATION_DIR / "prediction_stability.csv", index=False)
    plot_prediction_distribution(example_intervals, EVALUATION_DIR / "prediction_intervals.png")
    plot_bootstrap_histograms(bootstrap.predictions, EVALUATION_DIR / "bootstrap_prediction_histograms.png", row_index=0)
    plot_stability_over_time(split.test_metadata, stability, EVALUATION_DIR / "rolling_prediction_stability.png")

    ensemble = train_ensemble_predictions(
        split.X_train,
        split.y_train,
        split.X_test.reset_index(drop=True),
        n_models=BOOTSTRAP_MODELS,
        train_fraction=0.85,
        seed=RANDOM_SEED,
    )

    example_metadata = split.test_metadata.reset_index(drop=True).iloc[0]
    example_fixture = f"{example_metadata['HomeTeam']} vs {example_metadata['AwayTeam']}"

    report = {
        "experiment_id": f"{model_version}_{pd.Timestamp.now(tz='UTC').strftime('%Y%m%d_%H%M%S')}",
        "model_version": model_version,
        "features_included": feature_columns,
        "validation": {
            "split": "time_based_80_20_date_boundary_no_shuffle",
            "train_rows": int(len(split.X_train)),
            "test_rows": int(len(split.X_test)),
            "train_start_date": str(split.train_metadata["Date"].iloc[0]),
            "train_end_date": str(split.train_metadata["Date"].iloc[-1]),
            "test_start_date": str(split.test_metadata["Date"].iloc[0]),
            "test_end_date": str(split.test_metadata["Date"].iloc[-1]),
        },
        **metrics,
        "calibration": cal_summary,
        "expected_calibration_error": ece,
        "calibration_diagnosis": cal_diagnosis,
        "class_performance": class_metrics.to_dict("records"),
        "confidence_analysis": confidence.to_dict("records"),
        "top_features_by_gain": gain.head(10).to_dict("records"),
        "top_features_by_permutation": permutation.head(10).to_dict("records"),
        "top_features_by_shap": shap_importance.head(10).to_dict("records"),
        "ensemble": {
            "n_models": BOOTSTRAP_MODELS,
            "bootstrap_mean_probability_std": float(bootstrap.std.mean()),
            "bootstrap_max_probability_std": float(bootstrap.std.max()),
            "subset_ensemble_mean_probability_std": float(ensemble.std.mean()),
            "subset_ensemble_max_probability_std": float(ensemble.std.max()),
        },
        "stability": {
            "mean_stability_score": float(stability["stability_score"].mean()),
            "low_confidence_predictions": int((stability["confidence_label"] == "Low confidence").sum()),
            "medium_confidence_predictions": int((stability["confidence_label"] == "Medium confidence").sum()),
            "high_confidence_predictions": int((stability["confidence_label"] == "High confidence").sum()),
        },
        "example_fixture": example_fixture,
        "example_prediction_intervals": example_intervals.to_dict("records"),
        "example_confidence": {
            "label": example_confidence.label,
            "score": example_confidence.score,
            "explanation": example_confidence.explanation,
        },
        "notes": "Professional probabilistic evaluation with time-based validation, calibration, uncertainty, and explainability.",
    }

    (EVALUATION_DIR / "evaluation_report.json").write_text(json.dumps(report, indent=2))
    write_markdown_report(report, EVALUATION_DIR / "evaluation_summary.md")

    append_experiment(
        {
            "experiment_id": report["experiment_id"],
            "model_version": model_version,
            "features_included": "|".join(feature_columns),
            "train_period": f"{report['validation']['train_start_date']} to {report['validation']['train_end_date']}",
            "test_period": f"{report['validation']['test_start_date']} to {report['validation']['test_end_date']}",
            "accuracy": report["accuracy"],
            "log_loss": report["log_loss"],
            "brier_score": report["brier_score_multiclass"],
            "calibration_score": report["calibration"]["mean_absolute_calibration_error"],
            "expected_calibration_error": report["expected_calibration_error"],
            "bootstrap_runs": BOOTSTRAP_MODELS,
            "prediction_variance": report["ensemble"]["bootstrap_mean_probability_std"],
            "notes": report["notes"],
        }
    )

    print("Validation: time-based split, no random train/test split")
    print(f"Train: {report['validation']['train_start_date']} to {report['validation']['train_end_date']}")
    print(f"Test:  {report['validation']['test_start_date']} to {report['validation']['test_end_date']}")
    print(f"Rows evaluated: {report['validation']['test_rows']}")
    print(f"Accuracy: {report['accuracy']:.4f}")
    print(f"Log loss: {report['log_loss']:.4f}")
    print(f"Brier score: {report['brier_score_multiclass']:.4f}")
    print(f"Calibration error: {report['calibration']['mean_absolute_calibration_error']:.4f}")
    print(f"Expected calibration error: {report['expected_calibration_error']:.4f}")
    print(f"Bootstrap models: {BOOTSTRAP_MODELS}")
    print(f"Mean bootstrap std: {report['ensemble']['bootstrap_mean_probability_std']:.4f}")
    print(f"Mean stability score: {report['stability']['mean_stability_score']:.4f}")
    print(f"Saved evaluation outputs to: {EVALUATION_DIR}")


if __name__ == "__main__":
    evaluate()
