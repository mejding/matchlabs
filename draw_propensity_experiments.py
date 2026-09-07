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
from sklearn.base import clone
from sklearn.calibration import CalibratedClassifierCV
from sklearn.frozen import FrozenEstimator
from sklearn.inspection import permutation_importance

from calibration.calibration import calibration_summary, calibration_table, expected_calibration_error
from draw_propensity_features import build_draw_propensity_features, draw_propensity_feature_columns
from elo_rating_features import build_elo_features
from evaluation.model_evaluation import multiclass_brier_score, time_based_split
from feature_experiments import _markdown_table, train_xgb
from train_model import ELO_CONFIG, PRODUCTION_FEATURE_COLUMNS, build_features, load_matches_with_xg
from visualizations.plots import gain_importance, plot_feature_importance

matplotlib.use("Agg")

OUTPUT_DIR = Path("evaluation") / "draw_propensity"
RESULTS_PATH = Path("experiments") / "draw_propensity_results.csv"
PRIMARY_DRAW_COLUMNS = [
    "combined_draw_rate_last10",
    "team_strength_similarity",
    "xg_diff_similarity",
    "form_points_similarity",
    "low_total_xg_profile",
    "low_total_goals_profile",
    "draw_propensity_score",
]


def normalize_probabilities(probabilities: np.ndarray) -> np.ndarray:
    probabilities = np.clip(probabilities, 1e-15, 1.0)
    return probabilities / probabilities.sum(axis=1, keepdims=True)


def evaluate_probs(y_true: pd.Series, probabilities: np.ndarray) -> dict[str, float]:
    probabilities = normalize_probabilities(probabilities)
    predictions = probabilities.argmax(axis=1)
    draw_actual = (y_true.to_numpy() == 1).astype(int)
    draw_prob = probabilities[:, 1]
    draw_pred = (predictions == 1).astype(int)
    calibration = calibration_table(y_true, probabilities)
    top2 = np.argsort(probabilities, axis=1)[:, -2:]
    double_chance_hit = np.array([int(actual in top_pair) for actual, top_pair in zip(y_true.to_numpy(), top2)])
    return {
        "accuracy": float((predictions == y_true.to_numpy()).mean()),
        "log_loss": float(-np.log(probabilities[np.arange(len(y_true)), y_true.to_numpy()]).mean()),
        "Brier_score": multiclass_brier_score(y_true, probabilities),
        "expected_calibration_error": expected_calibration_error(calibration),
        "calibration_score": calibration_summary(calibration)["mean_absolute_calibration_error"],
        "draw_recall": float(((draw_pred == 1) & (draw_actual == 1)).sum() / draw_actual.sum()) if draw_actual.sum() else 0.0,
        "draw_top2_rate": float(np.mean([1 in top_pair for top_pair in top2])),
        "actual_draw_rate": float(draw_actual.mean()),
        "predicted_draw_top1_rate": float(draw_pred.mean()),
        "mean_draw_probability": float(draw_prob.mean()),
        "draw_probability_gap": float(draw_prob.mean() - draw_actual.mean()),
        "draw_log_loss": float(-np.mean(draw_actual * np.log(draw_prob) + (1 - draw_actual) * np.log(1 - draw_prob))),
        "double_chance_hit_rate": float(double_chance_hit.mean()),
    }


def build_dataset() -> tuple[pd.DataFrame, pd.DataFrame, dict[str, list[str]]]:
    matches = load_matches_with_xg().sort_values("Date").reset_index(drop=True)
    base, _ = build_features(matches, include_xg=True, include_schedule=True, include_shot_volume=True)
    elo, _ = build_elo_features(matches, ELO_CONFIG)
    draw = build_draw_propensity_features(matches)
    dataset = pd.concat([base.reset_index(drop=True), elo.reset_index(drop=True), draw.reset_index(drop=True)], axis=1)
    dataset["target"] = base["target"].to_numpy()
    metadata = matches[["Season", "Date", "HomeTeam", "AwayTeam", "FTR"]].reset_index(drop=True)
    feature_sets = {
        "model_a_current_production": PRODUCTION_FEATURE_COLUMNS,
        "model_b_draw_primary": PRODUCTION_FEATURE_COLUMNS + PRIMARY_DRAW_COLUMNS,
        "model_c_draw_full": PRODUCTION_FEATURE_COLUMNS + draw_propensity_feature_columns(),
    }
    return dataset, metadata, feature_sets


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


def split_fit_and_calibration(
    X: pd.DataFrame,
    y: pd.Series,
    dates: pd.Series,
) -> tuple[pd.DataFrame, pd.DataFrame, pd.Series, pd.Series]:
    split_index = int(len(X) * 0.8)
    cutoff = dates.iloc[split_index]
    fit_mask = dates < cutoff
    calibration_mask = dates >= cutoff
    return X.loc[fit_mask], X.loc[calibration_mask], y.loc[fit_mask], y.loc[calibration_mask]


def evaluate_calibrated_feature_set(dataset: pd.DataFrame, metadata: pd.DataFrame, columns: list[str], model_version: str) -> dict[str, object]:
    split = time_based_split(dataset[columns], dataset["target"], metadata)
    raw_model = train_xgb(split.X_train, split.y_train)
    X_fit, X_cal, y_fit, y_cal = split_fit_and_calibration(
        split.X_train,
        split.y_train,
        split.train_metadata["Date"].reset_index(drop=True),
    )
    fit_model = clone(raw_model)
    fit_model.fit(X_fit, y_fit)
    calibrator = CalibratedClassifierCV(FrozenEstimator(fit_model), method="sigmoid")
    calibrator.fit(X_cal, y_cal)
    probabilities = normalize_probabilities(calibrator.predict_proba(split.X_test))
    metrics = evaluate_probs(split.y_test, probabilities)
    return {
        "model_version": model_version,
        "model": calibrator,
        "split": split,
        "probabilities": probabilities,
        "feature_columns": columns,
        "train_period": f"{split.train_metadata['Date'].iloc[0]} to {split.train_metadata['Date'].iloc[-1]}",
        "test_period": f"{split.test_metadata['Date'].iloc[0]} to {split.test_metadata['Date'].iloc[-1]}",
        **metrics,
    }


def compare_models(dataset: pd.DataFrame, metadata: pd.DataFrame, feature_sets: dict[str, list[str]]) -> tuple[pd.DataFrame, dict[str, dict[str, object]]]:
    rows = []
    lookup = {}
    for name, columns in feature_sets.items():
        for calibrated in [False, True]:
            result_name = f"{name}_{'sigmoid' if calibrated else 'raw'}"
            result = (
                evaluate_calibrated_feature_set(dataset, metadata, columns, result_name)
                if calibrated
                else evaluate_feature_set(dataset, metadata, columns, result_name)
            )
            lookup[result_name] = result
            rows.append(
                {
                    "model_version": result_name,
                    "train_period": result["train_period"],
                    "test_period": result["test_period"],
                    "accuracy": result["accuracy"],
                    "log_loss": result["log_loss"],
                    "Brier_score": result["Brier_score"],
                    "expected_calibration_error": result["expected_calibration_error"],
                    "draw_recall": result["draw_recall"],
                    "draw_top2_rate": result["draw_top2_rate"],
                    "actual_draw_rate": result["actual_draw_rate"],
                    "predicted_draw_top1_rate": result["predicted_draw_top1_rate"],
                    "mean_draw_probability": result["mean_draw_probability"],
                    "draw_probability_gap": result["draw_probability_gap"],
                    "draw_log_loss": result["draw_log_loss"],
                    "double_chance_hit_rate": result["double_chance_hit_rate"],
                }
            )
    results = pd.DataFrame(rows).sort_values(["log_loss", "Brier_score"])
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    results.to_csv(OUTPUT_DIR / "model_comparison.csv", index=False)
    RESULTS_PATH.parent.mkdir(exist_ok=True)
    results.to_csv(RESULTS_PATH, index=False)
    return results, lookup


def plot_model_comparison(results: pd.DataFrame) -> None:
    metrics = ["log_loss", "Brier_score", "expected_calibration_error", "draw_log_loss", "double_chance_hit_rate"]
    fig, axes = plt.subplots(1, len(metrics), figsize=(18, 4.5))
    for ax, metric in zip(axes, metrics):
        ax.bar(results["model_version"], results[metric])
        ax.set_title(metric)
        ax.tick_params(axis="x", rotation=30)
        ax.grid(axis="y", alpha=0.25)
    fig.suptitle("Draw Propensity Model Comparison")
    fig.tight_layout()
    fig.savefig(OUTPUT_DIR / "model_comparison.png", dpi=160)
    plt.close(fig)


def explain_best_draw_model(best_result: dict[str, object]) -> tuple[pd.DataFrame, pd.DataFrame]:
    try:
        gain = gain_importance(best_result["model"], best_result["feature_columns"])
    except Exception:
        gain = pd.DataFrame(columns=["feature", "gain_importance"])
    gain.to_csv(OUTPUT_DIR / "feature_importance.csv", index=False)
    if not gain.empty:
        plot_feature_importance(gain.head(35), "gain_importance", "Draw Propensity Gain Importance", OUTPUT_DIR / "feature_importance.png")
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
    return gain, permutation


def production_decision(results: pd.DataFrame) -> tuple[bool, pd.Series, dict[str, float]]:
    baseline = results[results["model_version"] == "model_a_current_production_sigmoid"].iloc[0]
    candidates = results[
        results["model_version"].str.contains("_draw_", regex=False)
        & results["model_version"].str.endswith("_sigmoid")
    ].copy()
    best = candidates.sort_values(["log_loss", "Brier_score"]).iloc[0]
    deltas = {
        "log_loss": float(best["log_loss"] - baseline["log_loss"]),
        "Brier_score": float(best["Brier_score"] - baseline["Brier_score"]),
        "expected_calibration_error": float(best["expected_calibration_error"] - baseline["expected_calibration_error"]),
        "draw_log_loss": float(best["draw_log_loss"] - baseline["draw_log_loss"]),
        "double_chance_hit_rate": float(best["double_chance_hit_rate"] - baseline["double_chance_hit_rate"]),
    }
    promote = deltas["log_loss"] < 0 and deltas["Brier_score"] <= 0 and deltas["expected_calibration_error"] <= 0.01
    return promote, best, deltas


def write_report(results: pd.DataFrame, gain: pd.DataFrame, permutation: pd.DataFrame, best: pd.Series, deltas: dict[str, float], promote: bool) -> None:
    draw_features = set(draw_propensity_feature_columns())
    draw_gain = gain[gain["feature"].isin(draw_features)].head(15)
    draw_perm = permutation[permutation["feature"].isin(draw_features)].head(15)
    decision = (
        f"Promote `{best['model_version']}` to production: it improves Log Loss and Brier without material calibration deterioration."
        if promote
        else "Do not promote draw-propensity features to production on this run."
    )
    lines = [
        "# Draw Propensity Experiment",
        "",
        "## Goal",
        "",
        "Test whether pre-match signals for tight, low-event or draw-prone fixtures improve probability quality, especially draw calibration.",
        "",
        "## Model Comparison",
        "",
        _markdown_table(
            results,
            [
                "model_version",
                "accuracy",
                "log_loss",
                "Brier_score",
                "expected_calibration_error",
                "draw_recall",
                "mean_draw_probability",
                "actual_draw_rate",
                "draw_log_loss",
                "double_chance_hit_rate",
            ],
        ),
        "",
        "## Best Draw Candidate",
        "",
        f"- Candidate: `{best['model_version']}`",
        f"- Log Loss delta vs production: `{deltas['log_loss']:.4f}`",
        f"- Brier delta vs production: `{deltas['Brier_score']:.4f}`",
        f"- ECE delta vs production: `{deltas['expected_calibration_error']:.4f}`",
        f"- Draw log loss delta vs production: `{deltas['draw_log_loss']:.4f}`",
        f"- Double chance hit-rate delta vs production: `{deltas['double_chance_hit_rate']:.4f}`",
        "",
        "## Draw Feature Importance",
        "",
        _markdown_table(draw_gain, ["feature", "gain_importance"]) if not draw_gain.empty else "No draw features had positive gain importance.",
        "",
        "## Draw Feature Permutation Importance",
        "",
        _markdown_table(draw_perm, ["feature", "permutation_importance_log_loss", "permutation_importance_std"])
        if not draw_perm.empty
        else "No draw features had positive permutation importance.",
        "",
        "## Decision",
        "",
        decision,
        "",
        "Promotion rule: improve out-of-sample Log Loss, avoid Brier deterioration, and avoid material ECE deterioration. Accuracy alone is not enough.",
    ]
    (OUTPUT_DIR / "draw_propensity_report.md").write_text("\n".join(lines) + "\n", encoding="utf-8")
    (OUTPUT_DIR / "decision.json").write_text(
        json.dumps({"promote": promote, "best_model": str(best["model_version"]), "deltas": deltas}, indent=2),
        encoding="utf-8",
    )


def main() -> None:
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    dataset, metadata, feature_sets = build_dataset()
    results, lookup = compare_models(dataset, metadata, feature_sets)
    promote, best, deltas = production_decision(results)
    best_result = lookup[str(best["model_version"])]
    gain, permutation = explain_best_draw_model(best_result)
    plot_model_comparison(results)
    write_report(results, gain, permutation, best, deltas, promote)
    print(results.to_string(index=False))
    print(f"Promotion decision: {'promote' if promote else 'do not promote'} {best['model_version']}")
    print(f"Wrote {OUTPUT_DIR / 'draw_propensity_report.md'}")


if __name__ == "__main__":
    main()
