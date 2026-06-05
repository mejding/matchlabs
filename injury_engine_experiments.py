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
from injury_features import build_injury_features, historical_injury_pipeline_note, injury_feature_columns, load_historical_injuries
from tactical_data import ensure_tactical_tables, load_team_match_tactics
from tactical_features import build_tactical_features
from train_model import SCHEDULE_FEATURE_COLUMNS, build_features, load_matches_with_xg
from visualizations.plots import gain_importance, plot_feature_importance

matplotlib.use("Agg")

OUTPUT_DIR = Path("evaluation") / "injury_engine"
RESULTS_PATH = Path("experiments") / "injury_engine_results.csv"
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


def build_injury_experiment_dataset() -> tuple[pd.DataFrame, pd.DataFrame, dict[str, list[str]], pd.DataFrame]:
    matches = load_matches_with_xg().sort_values("Date").reset_index(drop=True)
    base_dataset, _ = build_features(matches, include_xg=True, include_schedule=True)
    injury_rows = build_injury_features(matches, load_historical_injuries())

    tactical_columns: list[str] = []
    try:
        ensure_tactical_tables()
        tactics = load_team_match_tactics()
        tactical_features, _ = build_tactical_features(matches, tactics)
        tactical_columns = available_columns(tactical_features, TACTICAL_PRESSURE_COLUMNS)
        dataset = pd.concat(
            [base_dataset.reset_index(drop=True), tactical_features[tactical_columns].reset_index(drop=True), injury_rows],
            axis=1,
        )
    except Exception as exc:
        print(f"Warning: tactical pressure unavailable for injury experiment: {exc}")
        dataset = pd.concat([base_dataset.reset_index(drop=True), injury_rows], axis=1)

    production_columns = SCHEDULE_FEATURE_COLUMNS + tactical_columns
    injury_columns = injury_feature_columns()
    feature_sets = {
        "model_a_current_production": production_columns,
        "model_b_production_injury_features": production_columns + injury_columns,
    }
    metadata = matches[["Season", "Date", "HomeTeam", "AwayTeam", "FTR"]].reset_index(drop=True)
    return dataset, metadata, feature_sets, matches


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
    fig, axes = plt.subplots(1, len(metrics), figsize=(16, 4))
    for ax, metric in zip(axes, metrics):
        ax.bar(results["model_version"], results[metric])
        ax.set_title(metric)
        ax.tick_params(axis="x", rotation=25)
        ax.grid(axis="y", alpha=0.25)
    fig.suptitle("Injury Engine Model Comparison")
    fig.tight_layout()
    fig.savefig(output_path, dpi=160)
    plt.close(fig)


def shap_outputs(result: dict[str, object]) -> pd.DataFrame:
    split = result["split"]
    model = result["model"]
    shap_importance, _, _ = compute_shap_importance(model, split.X_test)
    shap_importance["feature_group"] = shap_importance["feature"].map(
        lambda feature: "injury" if "injured" in feature or "suspended" in feature or "missing_" in feature else "baseline"
    )
    shap_importance.to_csv(OUTPUT_DIR / "shap_feature_rankings.csv", index=False)
    shap_importance.groupby("feature_group", as_index=False)["mean_abs_shap"].sum().sort_values(
        "mean_abs_shap", ascending=False
    ).to_csv(OUTPUT_DIR / "shap_group_rankings.csv", index=False)
    plot_shap_importance(shap_importance.head(35), OUTPUT_DIR / "shap_feature_rankings.png")
    plot_shap_summary(model, split.X_test, OUTPUT_DIR / "shap_summary.png")
    gain = gain_importance(model, result["feature_columns"])
    gain.to_csv(OUTPUT_DIR / "gain_importance.csv", index=False)
    plot_feature_importance(gain.head(35), "gain_importance", "Injury Engine Gain Importance", OUTPUT_DIR / "gain_importance.png")
    return shap_importance


def write_report(results: pd.DataFrame, shap_importance: pd.DataFrame, injury_rows_count: int) -> None:
    baseline = results[results["model_version"] == "model_a_current_production"].iloc[0]
    injury_model = results[results["model_version"] == "model_b_production_injury_features"].iloc[0]
    log_loss_delta = float(injury_model["log_loss"] - baseline["log_loss"])
    brier_delta = float(injury_model["Brier_score"] - baseline["Brier_score"])
    activate = injury_rows_count > 0 and log_loss_delta < 0 and brier_delta < 0
    injury_shap = shap_importance[shap_importance["feature_group"] == "injury"].head(12)
    injury_lines = "\n".join(f"- `{row.feature}`: {row.mean_abs_shap:.4f}" for row in injury_shap.itertuples())

    Path("injury_engine_report.md").write_text(
        f"""# Injury Data Engine Report

## Model Comparison

{_markdown_table(results, ['model_version', 'accuracy', 'log_loss', 'Brier_score', 'calibration_score', 'expected_calibration_error'])}

## Injury Data Coverage

- Historical injury/suspension rows available: {injury_rows_count}

## Performance Impact

- Log loss change: {log_loss_delta:.4f}
- Brier score change: {brier_delta:.4f}
- Calibration change: {float(injury_model['calibration_score'] - baseline['calibration_score']):.4f}
- ECE change: {float(injury_model['expected_calibration_error'] - baseline['expected_calibration_error']):.4f}

## SHAP

Top injury/suspension features:

{injury_lines or '- No injury feature had measurable SHAP contribution.'}

## Production Decision

{'Activate injury features as a production candidate.' if activate else 'Do not activate injury features. Keep them research-only until real historical rows exist and out-of-sample log loss/Brier improve.'}

## Leakage Controls

{historical_injury_pipeline_note()}
"""
    )


def main() -> None:
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    injuries = load_historical_injuries()
    dataset, metadata, feature_sets, _ = build_injury_experiment_dataset()
    results = [evaluate_feature_set(dataset, metadata, columns, version) for version, columns in feature_sets.items()]
    results_frame = save_results(results)
    plot_model_comparison(results_frame, OUTPUT_DIR / "model_comparison.png")
    injury_result = next(result for result in results if result["model_version"] == "model_b_production_injury_features")
    shap_importance = shap_outputs(injury_result)
    write_report(results_frame, shap_importance, len(injuries))
    print(json.dumps({"injury_rows": len(injuries), "activate": False if len(injuries) == 0 else None}, indent=2))


if __name__ == "__main__":
    main()
