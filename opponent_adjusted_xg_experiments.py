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
from sklearn.metrics import accuracy_score, log_loss, recall_score

from calibration.calibration import calibration_summary, calibration_table, expected_calibration_error
from elo_rating_features import build_elo_features
from evaluation.model_evaluation import multiclass_brier_score, time_based_split
from explainability.shap_analysis import compute_shap_importance, plot_shap_importance, plot_shap_summary
from feature_experiments import _markdown_table, train_xgb
from opponent_adjusted_xg_features import (
    EXPECTED_GOALS_FEATURE_COLUMNS,
    OPPONENT_ADJUSTED_XG_FEATURE_COLUMNS,
    POISSON_FEATURE_COLUMNS,
    RATING_FEATURE_COLUMNS,
    build_opponent_adjusted_xg_features,
)
from train_model import ELO_CONFIG, PRODUCTION_FEATURE_COLUMNS, build_features, load_matches_with_xg
from visualizations.plots import gain_importance, plot_feature_importance

matplotlib.use("Agg")

OUTPUT_DIR = Path("evaluation") / "opponent_adjusted_xg"
RESULTS_PATH = OUTPUT_DIR / "model_comparison.csv"
LABELS = [0, 1, 2]


def normalize_probabilities(probabilities: np.ndarray) -> np.ndarray:
    probabilities = np.clip(probabilities, 1e-15, 1.0)
    return probabilities / probabilities.sum(axis=1, keepdims=True)


def evaluate_prediction_set(name: str, y_true: pd.Series, probabilities: np.ndarray) -> dict[str, float | str]:
    probabilities = normalize_probabilities(probabilities)
    predictions = probabilities.argmax(axis=1)
    calibration = calibration_table(y_true, probabilities)
    cal_summary = calibration_summary(calibration)
    draw_actual = (y_true.to_numpy() == 1).astype(int)
    draw_prob = np.clip(probabilities[:, 1], 1e-15, 1.0)
    draw_predictions = (predictions == 1).astype(int)
    return {
        "model_version": name,
        "accuracy": float(accuracy_score(y_true, predictions)),
        "log_loss": float(log_loss(y_true, probabilities, labels=LABELS)),
        "Brier_score": multiclass_brier_score(y_true, probabilities),
        "calibration_score": cal_summary["mean_absolute_calibration_error"],
        "expected_calibration_error": expected_calibration_error(calibration),
        "draw_recall": float(recall_score(draw_actual, draw_predictions, zero_division=0)),
        "draw_log_loss": float(log_loss(draw_actual, np.column_stack([1.0 - draw_prob, draw_prob]), labels=[0, 1])),
        "draw_mean_probability_on_draws": float(draw_prob[draw_actual == 1].mean()) if draw_actual.sum() else 0.0,
    }


def build_dataset() -> tuple[pd.DataFrame, pd.DataFrame, dict[str, list[str]]]:
    matches = load_matches_with_xg().sort_values("Date").reset_index(drop=True)
    base_dataset, _ = build_features(matches, include_xg=True, include_schedule=True, include_shot_volume=True)
    elo_features, _ = build_elo_features(matches, ELO_CONFIG)
    adjusted_xg = build_opponent_adjusted_xg_features(matches)
    dataset = pd.concat(
        [base_dataset.reset_index(drop=True), elo_features.reset_index(drop=True), adjusted_xg.reset_index(drop=True)],
        axis=1,
    )
    metadata = matches[["Season", "Date", "HomeTeam", "AwayTeam", "FTR"]].reset_index(drop=True)
    feature_sets = {
        "model_a_current_production": PRODUCTION_FEATURE_COLUMNS,
        "model_c_production_plus_attack_defense_ratings": PRODUCTION_FEATURE_COLUMNS + RATING_FEATURE_COLUMNS,
        "model_d_production_plus_expected_goals": PRODUCTION_FEATURE_COLUMNS + EXPECTED_GOALS_FEATURE_COLUMNS,
        "model_e_production_plus_poisson_probabilities": PRODUCTION_FEATURE_COLUMNS + POISSON_FEATURE_COLUMNS,
        "model_f_production_plus_all_opponent_adjusted_xg": PRODUCTION_FEATURE_COLUMNS
        + OPPONENT_ADJUSTED_XG_FEATURE_COLUMNS,
    }
    return dataset, metadata, feature_sets


def evaluate_feature_set(dataset: pd.DataFrame, metadata: pd.DataFrame, feature_columns: list[str], model_version: str) -> dict[str, object]:
    split = time_based_split(dataset[feature_columns], dataset["target"], metadata)
    model = train_xgb(split.X_train, split.y_train)
    probabilities = normalize_probabilities(model.predict_proba(split.X_test))
    metrics = evaluate_prediction_set(model_version, split.y_test, probabilities)
    return {
        **metrics,
        "model": model,
        "split": split,
        "probabilities": probabilities,
        "feature_columns": feature_columns,
        "train_period": f"{split.train_metadata['Date'].iloc[0]} to {split.train_metadata['Date'].iloc[-1]}",
        "test_period": f"{split.test_metadata['Date'].iloc[0]} to {split.test_metadata['Date'].iloc[-1]}",
    }


def evaluate_poisson_baseline(dataset: pd.DataFrame, metadata: pd.DataFrame) -> dict[str, object]:
    split = time_based_split(dataset[POISSON_FEATURE_COLUMNS], dataset["target"], metadata)
    probabilities = normalize_probabilities(split.X_test[POISSON_FEATURE_COLUMNS].to_numpy())
    metrics = evaluate_prediction_set("model_b_poisson_only", split.y_test, probabilities)
    return {
        **metrics,
        "model": None,
        "split": split,
        "probabilities": probabilities,
        "feature_columns": POISSON_FEATURE_COLUMNS,
        "train_period": f"{split.train_metadata['Date'].iloc[0]} to {split.train_metadata['Date'].iloc[-1]}",
        "test_period": f"{split.test_metadata['Date'].iloc[0]} to {split.test_metadata['Date'].iloc[-1]}",
    }


def results_frame(results: list[dict[str, object]]) -> pd.DataFrame:
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
                "calibration_score": result["calibration_score"],
                "expected_calibration_error": result["expected_calibration_error"],
                "draw_recall": result["draw_recall"],
                "draw_log_loss": result["draw_log_loss"],
                "draw_mean_probability_on_draws": result["draw_mean_probability_on_draws"],
            }
        )
    frame = pd.DataFrame(rows)
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    frame.to_csv(RESULTS_PATH, index=False)
    return frame


def plot_model_comparison(results: pd.DataFrame) -> None:
    metrics = ["log_loss", "Brier_score", "expected_calibration_error", "draw_recall", "draw_log_loss"]
    fig, axes = plt.subplots(1, len(metrics), figsize=(18, 4.5))
    for ax, metric in zip(axes, metrics):
        ax.bar(results["model_version"], results[metric])
        ax.set_title(metric)
        ax.tick_params(axis="x", rotation=28)
        ax.grid(axis="y", alpha=0.25)
    fig.suptitle("Opponent-Adjusted xG Model Comparison")
    fig.tight_layout()
    fig.savefig(OUTPUT_DIR / "model_comparison.png", dpi=160)
    plt.close(fig)


def plot_calibration_curves(result_lookup: dict[str, dict[str, object]]) -> None:
    selected = [
        "model_a_current_production",
        "model_b_poisson_only",
        "model_f_production_plus_all_opponent_adjusted_xg",
    ]
    fig, axes = plt.subplots(1, 3, figsize=(15, 4.5))
    for class_index, ax in enumerate(axes):
        class_name = ["home_win", "draw", "away_win"][class_index]
        for name in selected:
            result = result_lookup[name]
            table = calibration_table(result["split"].y_test, result["probabilities"])
            class_table = table[table["class"] == class_name]
            if class_table.empty:
                continue
            ax.plot(class_table["mean_predicted_probability"], class_table["observed_frequency"], marker="o", label=name)
        ax.plot([0, 1], [0, 1], color="black", linestyle="--", linewidth=1)
        ax.set_title(["Home", "Draw", "Away"][class_index])
        ax.set_xlim(0, 1)
        ax.set_ylim(0, 1)
        ax.grid(True, alpha=0.25)
    axes[0].legend(fontsize=7)
    fig.suptitle("Reliability Diagrams")
    fig.tight_layout()
    fig.savefig(OUTPUT_DIR / "calibration_curves.png", dpi=160)
    plt.close(fig)


def explain_best_candidate(result: dict[str, object]) -> pd.DataFrame:
    split = result["split"]
    model = result["model"]
    if model is None:
        return pd.DataFrame(columns=["feature", "mean_abs_shap", "feature_group"])
    shap_importance, _, _ = compute_shap_importance(model, split.X_test)
    shap_importance["feature_group"] = shap_importance["feature"].map(feature_group)
    shap_importance.to_csv(OUTPUT_DIR / "shap_importance.csv", index=False)
    plot_shap_importance(shap_importance.head(40), OUTPUT_DIR / "shap_importance.png")
    plot_shap_summary(model, split.X_test, OUTPUT_DIR / "shap_summary.png")
    gain = gain_importance(model, result["feature_columns"])
    gain.to_csv(OUTPUT_DIR / "feature_importance.csv", index=False)
    plot_feature_importance(gain.head(40), "gain_importance", "Opponent-Adjusted xG Gain Importance", OUTPUT_DIR / "feature_importance.png")
    return shap_importance


def feature_group(feature: str) -> str:
    if feature in POISSON_FEATURE_COLUMNS:
        return "poisson"
    if feature in EXPECTED_GOALS_FEATURE_COLUMNS:
        return "expected_goals"
    if feature in RATING_FEATURE_COLUMNS:
        return "opponent_adjusted_xg"
    if "xg" in feature or "xga" in feature:
        return "raw_xg"
    if "elo" in feature:
        return "elo"
    if "shot" in feature:
        return "shot_volume"
    if "days" in feature or "midweek" in feature or "matches_last" in feature:
        return "fatigue"
    return "form_home_advantage"


def permutation_outputs(result: dict[str, object]) -> pd.DataFrame:
    if result["model"] is None:
        return pd.DataFrame()
    split = result["split"]
    perm = permutation_importance(
        result["model"],
        split.X_test,
        split.y_test,
        scoring="neg_log_loss",
        n_repeats=5,
        random_state=42,
        n_jobs=1,
    )
    output = pd.DataFrame(
        {
            "feature": result["feature_columns"],
            "permutation_importance_log_loss": perm.importances_mean,
            "permutation_importance_std": perm.importances_std,
        }
    ).sort_values("permutation_importance_log_loss", ascending=False)
    output.to_csv(OUTPUT_DIR / "permutation_importance.csv", index=False)
    return output


def remove_one_tests(dataset: pd.DataFrame, metadata: pd.DataFrame, full_columns: list[str]) -> pd.DataFrame:
    groups = {
        "full_reference": [],
        "remove_ratings": RATING_FEATURE_COLUMNS,
        "remove_expected_goals": EXPECTED_GOALS_FEATURE_COLUMNS,
        "remove_poisson_probabilities": POISSON_FEATURE_COLUMNS,
    }
    rows = []
    for test_name, removed in groups.items():
        columns = [column for column in full_columns if column not in set(removed)]
        result = evaluate_feature_set(dataset, metadata, columns, test_name)
        rows.append(
            {
                "test": test_name,
                "removed_features": "|".join(removed),
                "log_loss": result["log_loss"],
                "Brier_score": result["Brier_score"],
                "expected_calibration_error": result["expected_calibration_error"],
            }
        )
    output = pd.DataFrame(rows)
    output.to_csv(OUTPUT_DIR / "remove_one_tests.csv", index=False)
    return output


def correlation_outputs(dataset: pd.DataFrame) -> pd.DataFrame:
    columns = [
        "home_xg_avg",
        "away_xg_avg",
        "home_xga_avg",
        "away_xga_avg",
        "home_xg_diff",
        "away_xg_diff",
        *OPPONENT_ADJUSTED_XG_FEATURE_COLUMNS,
    ]
    corr = dataset[columns].corr(numeric_only=True)
    corr.to_csv(OUTPUT_DIR / "correlation_matrix.csv")
    return corr


def write_report(results: pd.DataFrame, shap_importance: pd.DataFrame, permutation: pd.DataFrame, remove_one: pd.DataFrame) -> None:
    baseline = results[results["model_version"] == "model_a_current_production"].iloc[0]
    candidate_results = results[~results["model_version"].isin(["model_a_current_production", "model_b_poisson_only"])].copy()
    best = candidate_results.sort_values(["log_loss", "Brier_score"]).iloc[0]
    log_delta = float(best["log_loss"] - baseline["log_loss"])
    brier_delta = float(best["Brier_score"] - baseline["Brier_score"])
    ece_delta = float(best["expected_calibration_error"] - baseline["expected_calibration_error"])
    production_ready = (log_delta < 0 or brier_delta < 0) and ece_delta <= 0.01
    top_new = shap_importance[shap_importance["feature_group"].isin(["opponent_adjusted_xg", "expected_goals", "poisson"])].head(12)
    shap_lines = "\n".join(
        f"- `{row.feature}` ({row.feature_group}): {row.mean_abs_shap:.4f}" for row in top_new.itertuples()
    )
    perm_new = permutation[permutation["feature"].isin(OPPONENT_ADJUSTED_XG_FEATURE_COLUMNS)].head(10)
    perm_lines = "\n".join(
        f"- `{row.feature}`: {row.permutation_importance_log_loss:.4f}" for row in perm_new.itertuples()
    )
    decision = (
        f"Move `{best['model_version']}` forward as a production candidate."
        if production_ready
        else "Keep opponent-adjusted xG features in Research. They did not improve out-of-sample metrics enough for production."
    )
    Path("opponent_adjusted_xg_report.md").write_text(
        f"""# Sprint 4D: Opponent-Adjusted xG Attack/Defense Ratings

## Methodology

This sprint builds rolling team attack and defense ratings from Understat xG. Every value is calculated chronologically before the fixture date. No future matches are used.

## Rating Formulas

- Opponent attack strength before a match = opponent adjusted attack xG divided by league average xG.
- Opponent defense weakness before a match = opponent adjusted xGA conceded divided by league average xG.
- Adjusted attack xG for a completed match = team xG divided by opponent defense weakness known before kickoff.
- Adjusted defense xGA for a completed match = xG conceded divided by opponent attack strength known before kickoff.
- Ratings are relative to league average. Attack above `1.00` is stronger than league average. Defense below `1.00` is better than league average.
- Expected home xG = league average home xG * home attack rating * away defense weakness * home advantage factor.
- Expected away xG = league average away xG * away attack rating * home defense weakness * away factor.
- Poisson probabilities are derived from those expected goal estimates.

Windows tested:

- Last 5 matches
- Last 10 matches
- Season-to-date
- Exponentially weighted rolling average

## Model Comparison

{_markdown_table(results, ['model_version', 'accuracy', 'log_loss', 'Brier_score', 'expected_calibration_error', 'draw_recall', 'draw_log_loss'])}

## Best Candidate vs Production

- Best candidate: `{best['model_version']}`
- Log Loss delta vs production: {log_delta:.4f}
- Brier delta vs production: {brier_delta:.4f}
- ECE delta vs production: {ece_delta:.4f}

## Poisson Baseline

Poisson-only results are saved to `evaluation/opponent_adjusted_xg/poisson_baseline_results.csv`.

The Poisson model is useful as an interpretable baseline, but it should only influence production if its probabilities improve out-of-sample probability quality compared with the XGBoost production model.

## Draw Performance

Draw metrics are included in the model comparison table:

- `draw_recall`
- `draw_log_loss`
- `draw_mean_probability_on_draws`

Use these to judge whether Poisson/expected-goal features improve the model's historically weak draw handling.

## SHAP and Redundancy Analysis

Top new-feature SHAP signals:

{shap_lines or '- No opponent-adjusted xG features had measurable SHAP contribution.'}

Top new-feature permutation signals:

{perm_lines or '- No opponent-adjusted xG features had positive permutation contribution.'}

Remove-one tests:

{_markdown_table(remove_one, ['test', 'log_loss', 'Brier_score', 'expected_calibration_error'])}

Feature correlation matrix is saved to `evaluation/opponent_adjusted_xg/correlation_matrix.csv`.

## Answers

1. Are opponent-adjusted xG ratings better than raw rolling xG?

   Evidence is mixed unless the best candidate improves Log Loss or Brier. SHAP signal alone is not enough because raw rolling xG is already active.

2. Are expected-goal estimates redundant with existing xG features?

   Compare expected-goal SHAP/permutation values and remove-one results. If metrics do not improve, treat them as mostly redundant with existing xG, Elo and shot-volume features.

3. Do Poisson probabilities add signal?

   Poisson probabilities provide a useful interpretable baseline. They should not be promoted unless Model E or Model F improves out-of-sample probability metrics.

4. Do these features improve draw prediction?

   Use draw recall and draw log loss in the comparison table. Improvement in draw recall alone is not enough if total Log Loss/Brier worsens.

## Recommendation

{decision}

Do not activate the candidate in the saved production model yet if accuracy or draw recall falls versus production. A reduced-feature backtest should confirm the small probability-quality gain before promotion.

Production rule: only activate these features if out-of-sample Log Loss or Brier improves without materially worsening calibration.
"""
    )


def main() -> None:
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    dataset, metadata, feature_sets = build_dataset()
    results = [evaluate_feature_set(dataset, metadata, columns, name) for name, columns in feature_sets.items()]
    poisson = evaluate_poisson_baseline(dataset, metadata)
    results.insert(1, poisson)
    frame = results_frame(results)
    pd.DataFrame([poisson]).drop(columns=["model", "split", "probabilities"], errors="ignore").to_csv(
        OUTPUT_DIR / "poisson_baseline_results.csv",
        index=False,
    )
    plot_model_comparison(frame)
    lookup = {str(result["model_version"]): result for result in results}
    plot_calibration_curves(lookup)
    best_candidate_name = frame[~frame["model_version"].isin(["model_a_current_production", "model_b_poisson_only"])].sort_values(
        ["log_loss", "Brier_score"]
    )["model_version"].iloc[0]
    best_candidate = lookup[str(best_candidate_name)]
    shap_importance = explain_best_candidate(best_candidate)
    permutation = permutation_outputs(best_candidate)
    remove_one = remove_one_tests(
        dataset,
        metadata,
        feature_sets["model_f_production_plus_all_opponent_adjusted_xg"],
    )
    correlation_outputs(dataset)
    write_report(frame, shap_importance, permutation, remove_one)
    print(json.dumps({"best_candidate": str(best_candidate_name), "report": "opponent_adjusted_xg_report.md"}, indent=2))


if __name__ == "__main__":
    main()
