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
from sklearn.metrics import log_loss, precision_score, recall_score

from calibration.calibration import calibration_summary, calibration_table, expected_calibration_error
from elo_rating_features import EloConfig, build_elo_features, elo_feature_columns
from evaluation.model_evaluation import evaluate_probabilities, time_based_split
from explainability.shap_analysis import compute_shap_importance, plot_shap_importance, plot_shap_summary
from feature_experiments import _markdown_table, train_xgb
from train_model import SCHEDULE_FEATURE_COLUMNS, build_features, load_matches_with_xg
from visualizations.plots import compute_permutation_importance, plot_feature_importance

matplotlib.use("Agg")

OUTPUT_DIR = Path("evaluation") / "elo"
CLASS_NAMES = ["home_win", "draw", "away_win"]


def normalize_probabilities(probabilities: np.ndarray) -> np.ndarray:
    clipped = np.clip(probabilities, 1e-15, 1.0)
    return clipped / clipped.sum(axis=1, keepdims=True)


def temperature_scale(probabilities: np.ndarray, temperature: float) -> np.ndarray:
    logits = np.log(normalize_probabilities(probabilities)) / temperature
    logits -= logits.max(axis=1, keepdims=True)
    exp_values = np.exp(logits)
    return exp_values / exp_values.sum(axis=1, keepdims=True)


def choose_temperature(y_true: pd.Series, probabilities: np.ndarray) -> float:
    candidates = np.linspace(0.6, 2.6, 81)
    losses = [log_loss(y_true, temperature_scale(probabilities, float(candidate)), labels=[0, 1, 2]) for candidate in candidates]
    return float(candidates[int(np.argmin(losses))])


def evaluate_columns(dataset: pd.DataFrame, metadata: pd.DataFrame, columns: list[str], model_name: str) -> dict[str, object]:
    split = time_based_split(dataset[columns], dataset["target"], metadata)
    model = train_xgb(split.X_train, split.y_train)
    probabilities = normalize_probabilities(model.predict_proba(split.X_test))
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
        "predictions": predictions,
        "accuracy": metrics["accuracy"],
        "log_loss": metrics["log_loss"],
        "brier_score": metrics["brier_score_multiclass"],
        "calibration_score": cal_summary["mean_absolute_calibration_error"],
        "ece": expected_calibration_error(calibration),
        "train_period": f"{split.train_metadata['Date'].iloc[0]} to {split.train_metadata['Date'].iloc[-1]}",
        "test_period": f"{split.test_metadata['Date'].iloc[0]} to {split.test_metadata['Date'].iloc[-1]}",
    }


def evaluate_calibrated(result: dict[str, object]) -> dict[str, object]:
    split = result["split"]
    model = result["model"]
    train_probs = normalize_probabilities(model.predict_proba(split.X_train))
    test_probs = result["probabilities"]
    temperature = choose_temperature(split.y_train, train_probs)
    calibrated = temperature_scale(test_probs, temperature)
    predictions = calibrated.argmax(axis=1)
    metrics = evaluate_probabilities(split.y_test, calibrated, predictions)
    calibration = calibration_table(split.y_test, calibrated)
    cal_summary = calibration_summary(calibration)
    return {
        "model_name": "current_model_plus_elo_calibrated",
        "accuracy": metrics["accuracy"],
        "log_loss": metrics["log_loss"],
        "brier_score": metrics["brier_score_multiclass"],
        "calibration_score": cal_summary["mean_absolute_calibration_error"],
        "ece": expected_calibration_error(calibration),
        "train_period": result["train_period"],
        "test_period": result["test_period"],
        "temperature": temperature,
        "probabilities": calibrated,
        "predictions": predictions,
        "split": split,
    }


def config_grid() -> list[EloConfig]:
    configs = []
    for k_factor in [10, 20, 30, 40]:
        for home_advantage in [0, 50, 75, 100]:
            for mov in [False, True]:
                configs.append(EloConfig(k_factor=float(k_factor), home_advantage=float(home_advantage), margin_of_victory=mov))
    return configs


def parameter_search(base_dataset: pd.DataFrame, matches: pd.DataFrame, metadata: pd.DataFrame) -> tuple[pd.DataFrame, EloConfig, pd.DataFrame]:
    rows = []
    best_config = None
    best_features = None
    best_loss = float("inf")
    for config in config_grid():
        elo_features, _ = build_elo_features(matches, config)
        dataset = pd.concat([base_dataset.reset_index(drop=True), elo_features.reset_index(drop=True)], axis=1)
        result = evaluate_columns(dataset, metadata, elo_feature_columns(), config.name)
        row = {
            "elo_config": config.name,
            "k_factor": config.k_factor,
            "home_advantage": config.home_advantage,
            "margin_of_victory": config.margin_of_victory,
            "accuracy": result["accuracy"],
            "log_loss": result["log_loss"],
            "brier_score": result["brier_score"],
            "calibration_score": result["calibration_score"],
            "ece": result["ece"],
        }
        rows.append(row)
        if float(result["log_loss"]) < best_loss:
            best_loss = float(result["log_loss"])
            best_config = config
            best_features = elo_features
    assert best_config is not None and best_features is not None
    search = pd.DataFrame(rows).sort_values(["log_loss", "brier_score"]).reset_index(drop=True)
    return search, best_config, best_features


def plot_model_comparison(results: pd.DataFrame, output_path: Path) -> None:
    metrics = ["accuracy", "log_loss", "brier_score", "calibration_score", "ece"]
    fig, axes = plt.subplots(1, len(metrics), figsize=(16, 4))
    for ax, metric in zip(axes, metrics):
        ax.bar(results["model_name"], results[metric])
        ax.set_title(metric)
        ax.tick_params(axis="x", rotation=25)
        ax.grid(axis="y", alpha=0.25)
    fig.suptitle("Elo Layer Model Comparison")
    fig.tight_layout()
    fig.savefig(output_path, dpi=160)
    plt.close(fig)


def draw_metrics(result: dict[str, object], probabilities: np.ndarray | None = None, predictions: np.ndarray | None = None) -> dict[str, object]:
    split = result["split"]
    probs = probabilities if probabilities is not None else result["probabilities"]
    preds = predictions if predictions is not None else result["predictions"]
    y_true = split.y_test.to_numpy()
    draw_mask = y_true == 1
    calibration = calibration_table(split.y_test, probs)
    draw_cal = calibration[calibration["class"] == "draw"]
    return {
        "model_name": result["model_name"],
        "draw_recall": float(recall_score(y_true, preds, labels=[1], average="micro", zero_division=0)),
        "draw_precision": float(precision_score(y_true, preds, labels=[1], average="micro", zero_division=0)),
        "draw_log_loss": float(-np.mean(np.log(np.clip(probs[draw_mask, 1], 1e-15, 1.0)))) if np.any(draw_mask) else np.nan,
        "draw_calibration_error": float(
            np.average(
                np.abs(draw_cal["observed_frequency"] - draw_cal["mean_predicted_probability"]),
                weights=draw_cal["count"],
            )
        )
        if not draw_cal.empty
        else np.nan,
    }


def correlation_summary(dataset: pd.DataFrame, current_columns: list[str], elo_columns: list[str]) -> pd.DataFrame:
    corr = dataset[current_columns + elo_columns].corr(numeric_only=True).abs()
    corr.to_csv(OUTPUT_DIR / "elo_correlation_matrix.csv")
    cross = corr.loc[elo_columns, current_columns]
    rows = []
    for feature in elo_columns:
        rows.append(
            {
                "elo_feature": feature,
                "mean_abs_corr_with_current": float(cross.loc[feature].mean()),
                "max_abs_corr_with_current": float(cross.loc[feature].max()),
                "most_correlated_current_feature": str(cross.loc[feature].idxmax()),
            }
        )
    return pd.DataFrame(rows).sort_values("max_abs_corr_with_current", ascending=False)


def remove_elo_tests(dataset: pd.DataFrame, metadata: pd.DataFrame, current_columns: list[str], elo_columns: list[str], full_result: dict[str, object]) -> pd.DataFrame:
    without_elo = evaluate_columns(dataset, metadata, current_columns, "full_minus_elo")
    without_current = evaluate_columns(dataset, metadata, elo_columns, "full_minus_current")
    rows = []
    for result in [full_result, without_elo, without_current]:
        rows.append(
            {
                "model_name": result["model_name"],
                "accuracy": result["accuracy"],
                "log_loss": result["log_loss"],
                "brier_score": result["brier_score"],
                "calibration_score": result["calibration_score"],
                "ece": result["ece"],
                "log_loss_delta_vs_full": float(result["log_loss"] - full_result["log_loss"]),
                "brier_delta_vs_full": float(result["brier_score"] - full_result["brier_score"]),
            }
        )
    return pd.DataFrame(rows)


def group_importance(frame: pd.DataFrame, value_column: str) -> pd.DataFrame:
    grouped = frame.copy()
    grouped["feature_group"] = grouped["feature"].map(lambda feature: "Elo" if feature in elo_feature_columns() else "Current model")
    return grouped.groupby("feature_group", as_index=False)[value_column].sum().sort_values(value_column, ascending=False)


def write_parameter_report(search: pd.DataFrame, best_config: EloConfig) -> None:
    Path("elo_parameter_search_report.md").write_text(
        f"""# Elo Parameter Search Report

Best configuration by Elo-only out-of-sample log loss: `{best_config.name}`.

## Top Configurations

{_markdown_table(search.head(12), ['elo_config', 'k_factor', 'home_advantage', 'margin_of_victory', 'accuracy', 'log_loss', 'brier_score', 'calibration_score', 'ece'])}

The search tests K-factor, fixed home Elo bonus, and margin-of-victory update multiplier. Ratings are calculated chronologically before each match, then updated after the match result.
"""
    )


def write_report(
    search: pd.DataFrame,
    best_config: EloConfig,
    results: pd.DataFrame,
    draw: pd.DataFrame,
    corr: pd.DataFrame,
    remove: pd.DataFrame,
    shap_group: pd.DataFrame,
    shap_features: pd.DataFrame,
    perm_group: pd.DataFrame,
) -> None:
    current = results[results["model_name"] == "current_production_model"].iloc[0]
    combined = results[results["model_name"] == "current_model_plus_elo"].iloc[0]
    calibrated = results[results["model_name"] == "current_model_plus_elo_calibrated"].iloc[0]
    improves = (
        float(combined["log_loss"]) < float(current["log_loss"])
        or float(combined["brier_score"]) < float(current["brier_score"])
    ) and float(combined["calibration_score"]) <= float(current["calibration_score"]) + 0.01
    best_elo_feature = shap_features[shap_features["feature"].isin(elo_feature_columns())].iloc[0]["feature"]
    elo_shap = float(shap_group.loc[shap_group["feature_group"] == "Elo", "mean_abs_shap"].sum())
    current_shap = float(shap_group.loc[shap_group["feature_group"] == "Current model", "mean_abs_shap"].sum())
    high_corr = int((corr["max_abs_corr_with_current"] >= 0.70).sum())
    current_draw = draw[draw["model_name"] == "current_production_model"].iloc[0]
    combined_draw = draw[draw["model_name"] == "current_model_plus_elo"].iloc[0]

    Path("elo_evaluation_report.md").write_text(
        f"""# Elo Rating Layer Evaluation

## Best Elo Configuration

Best Elo config: `{best_config.name}`.

{_markdown_table(search.head(8), ['elo_config', 'accuracy', 'log_loss', 'brier_score', 'calibration_score', 'ece'])}

## Model Comparison

{_markdown_table(results, ['model_name', 'accuracy', 'log_loss', 'brier_score', 'calibration_score', 'ece', 'train_period', 'test_period'])}

Current + Elo deltas versus current model:

- Log loss: {float(combined['log_loss'] - current['log_loss']):.4f}
- Brier score: {float(combined['brier_score'] - current['brier_score']):.4f}
- Calibration score: {float(combined['calibration_score'] - current['calibration_score']):.4f}
- ECE: {float(combined['ece'] - current['ece']):.4f}

Calibrated current + Elo deltas versus current model:

- Log loss: {float(calibrated['log_loss'] - current['log_loss']):.4f}
- Brier score: {float(calibrated['brier_score'] - current['brier_score']):.4f}
- Calibration score: {float(calibrated['calibration_score'] - current['calibration_score']):.4f}
- ECE: {float(calibrated['ece'] - current['ece']):.4f}

## Draw Analysis

{_markdown_table(draw, ['model_name', 'draw_recall', 'draw_precision', 'draw_log_loss', 'draw_calibration_error'])}

## Redundancy Tests

Remove-one comparison:

{_markdown_table(remove, ['model_name', 'accuracy', 'log_loss', 'brier_score', 'calibration_score', 'ece', 'log_loss_delta_vs_full', 'brier_delta_vs_full'])}

Elo correlation with current features:

{_markdown_table(corr, ['elo_feature', 'mean_abs_corr_with_current', 'max_abs_corr_with_current', 'most_correlated_current_feature'])}

Number of Elo features with max correlation >= 0.70 against current features: `{high_corr}`.

## SHAP and Permutation

SHAP group importance:

{_markdown_table(shap_group, ['feature_group', 'mean_abs_shap'])}

Permutation group importance:

{_markdown_table(perm_group, ['feature_group', 'permutation_importance'])}

Top Elo SHAP features:

{_markdown_table(shap_features[shap_features['feature'].isin(elo_feature_columns())].head(8), ['feature', 'mean_abs_shap'])}

## Answers

### 1. Does Elo improve prediction quality?

Answer: {'Yes, Elo meets the success criteria in this run.' if improves else 'No, Elo does not meet the success criteria in this run.'}

### 2. Which Elo feature matters most?

Answer: `{best_elo_feature}` has the highest SHAP contribution among Elo features.

### 3. Does Elo improve draw prediction?

Draw recall delta: {float(combined_draw['draw_recall'] - current_draw['draw_recall']):.4f}  
Draw log loss delta: {float(combined_draw['draw_log_loss'] - current_draw['draw_log_loss']):.4f}

Answer: {'Yes, draw recall or draw log loss improves.' if (float(combined_draw['draw_recall']) > float(current_draw['draw_recall']) or float(combined_draw['draw_log_loss']) < float(current_draw['draw_log_loss'])) else 'No, Elo does not improve draw prediction in this run.'}

### 4. Does Elo add unique information beyond xG and form?

Elo SHAP total: {elo_shap:.4f}  
Current feature SHAP total: {current_shap:.4f}

Answer: {'Some, because Elo has measurable SHAP/permutation contribution and low-to-moderate correlation with current features.' if high_corr <= 2 and elo_shap > 0 else 'Limited. Elo appears mostly redundant or weak in this setup.'}

### 5. Does Elo improve calibration?

Answer: {'Yes, combined Elo improves calibration score.' if float(combined['calibration_score']) < float(current['calibration_score']) else 'No, combined Elo does not improve calibration score before calibration.'}

### 6. Should Elo move into production?

Answer: {'Yes, as a production candidate, subject to one more backtest after the next data refresh.' if improves else 'No. Keep Elo research-only until it improves out-of-sample log loss or Brier without hurting calibration.'}

### 7. What is the expected production benefit?

Expected benefit is the out-of-sample delta shown above. Do not extrapolate beyond that; if deltas are tiny, the practical production benefit is likely small.

## Artifacts

- `data/elo_history.csv`
- `evaluation/elo/elo_parameter_search.csv`
- `evaluation/elo/model_comparison.csv`
- `evaluation/elo/draw_analysis.csv`
- `evaluation/elo/elo_correlation_summary.csv`
- `evaluation/elo/remove_one_results.csv`
- `evaluation/elo/shap_feature_rankings.csv`
- `evaluation/elo/shap_group_importance.csv`
- `evaluation/elo/permutation_feature_importance.csv`
- `evaluation/elo/permutation_group_importance.csv`
- `evaluation/elo/model_comparison.png`
- `evaluation/elo/shap_summary.png`
"""
    )


def run_evaluation() -> pd.DataFrame:
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    matches = load_matches_with_xg().sort_values("Date").reset_index(drop=True)
    base_dataset, _ = build_features(matches, include_xg=True, include_schedule=True)
    metadata = matches[["Season", "Date", "HomeTeam", "AwayTeam", "FTR"]].reset_index(drop=True)

    search, best_config, elo_features = parameter_search(base_dataset, matches, metadata)
    search.to_csv(OUTPUT_DIR / "elo_parameter_search.csv", index=False)
    write_parameter_report(search, best_config)

    dataset = pd.concat([base_dataset.reset_index(drop=True), elo_features.reset_index(drop=True)], axis=1)
    current = evaluate_columns(dataset, metadata, SCHEDULE_FEATURE_COLUMNS, "current_production_model")
    elo_only = evaluate_columns(dataset, metadata, elo_feature_columns(), "elo_only_model")
    combined = evaluate_columns(dataset, metadata, SCHEDULE_FEATURE_COLUMNS + elo_feature_columns(), "current_model_plus_elo")
    calibrated = evaluate_calibrated(combined)

    results = pd.DataFrame(
        [
            {key: value for key, value in current.items() if key not in {"model", "split", "feature_columns", "probabilities", "predictions"}},
            {key: value for key, value in elo_only.items() if key not in {"model", "split", "feature_columns", "probabilities", "predictions"}},
            {key: value for key, value in combined.items() if key not in {"model", "split", "feature_columns", "probabilities", "predictions"}},
            {key: value for key, value in calibrated.items() if key not in {"split", "probabilities", "predictions"}},
        ]
    )
    results.to_csv(OUTPUT_DIR / "model_comparison.csv", index=False)
    plot_model_comparison(results, OUTPUT_DIR / "model_comparison.png")

    draw = pd.DataFrame(
        [
            draw_metrics(current),
            draw_metrics(elo_only),
            draw_metrics(combined),
            draw_metrics(calibrated, calibrated["probabilities"], calibrated["predictions"]),
        ]
    )
    draw.to_csv(OUTPUT_DIR / "draw_analysis.csv", index=False)

    corr = correlation_summary(dataset, SCHEDULE_FEATURE_COLUMNS, elo_feature_columns())
    corr.to_csv(OUTPUT_DIR / "elo_correlation_summary.csv", index=False)
    remove = remove_elo_tests(dataset, metadata, SCHEDULE_FEATURE_COLUMNS, elo_feature_columns(), combined)
    remove.to_csv(OUTPUT_DIR / "remove_one_results.csv", index=False)

    shap_features, _, _ = compute_shap_importance(combined["model"], combined["split"].X_test)
    shap_features.to_csv(OUTPUT_DIR / "shap_feature_rankings.csv", index=False)
    plot_shap_importance(shap_features.head(35), OUTPUT_DIR / "shap_feature_rankings.png")
    plot_shap_summary(combined["model"], combined["split"].X_test, OUTPUT_DIR / "shap_summary.png")
    shap_group = group_importance(shap_features, "mean_abs_shap")
    shap_group.to_csv(OUTPUT_DIR / "shap_group_importance.csv", index=False)

    permutation = compute_permutation_importance(combined["model"], combined["split"].X_test, combined["split"].y_test)
    permutation.to_csv(OUTPUT_DIR / "permutation_feature_importance.csv", index=False)
    plot_feature_importance(
        permutation.head(35),
        "permutation_importance",
        "Elo Layer Permutation Importance",
        OUTPUT_DIR / "permutation_feature_importance.png",
    )
    perm_group = group_importance(permutation, "permutation_importance")
    perm_group.to_csv(OUTPUT_DIR / "permutation_group_importance.csv", index=False)

    write_report(search, best_config, results, draw, corr, remove, shap_group, shap_features, perm_group)
    return results


def main() -> None:
    results = run_evaluation()
    best = results.sort_values("log_loss").iloc[0]
    print(json.dumps({"best_model": str(best["model_name"]), "log_loss": float(best["log_loss"])}, indent=2))


if __name__ == "__main__":
    main()
