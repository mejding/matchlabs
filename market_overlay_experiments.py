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
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import log_loss
from sklearn.preprocessing import StandardScaler

from calibration.calibration import calibration_summary, calibration_table, expected_calibration_error
from evaluation.model_evaluation import multiclass_brier_score, time_based_split
from feature_experiments import _markdown_table, train_xgb
from market_intelligence_experiments import MARKET_PROB_COLUMNS, build_market_dataset, normalize_probabilities

matplotlib.use("Agg")

OUTPUT_DIR = Path("evaluation") / "market_overlay"


def evaluate_probabilities(name: str, y_true: pd.Series, probabilities: np.ndarray) -> dict[str, float | str]:
    probabilities = normalize_probabilities(probabilities)
    predictions = probabilities.argmax(axis=1)
    calibration = calibration_table(y_true, probabilities)
    cal_summary = calibration_summary(calibration)
    return {
        "model": name,
        "accuracy": float((predictions == y_true.to_numpy()).mean()),
        "log_loss": float(log_loss(y_true, probabilities, labels=[0, 1, 2])),
        "brier_score": multiclass_brier_score(y_true, probabilities),
        "calibration_score": cal_summary["mean_absolute_calibration_error"],
        "ece": expected_calibration_error(calibration),
    }


def logit_features(probabilities: np.ndarray, prefix: str) -> pd.DataFrame:
    clipped = np.clip(normalize_probabilities(probabilities), 1e-6, 1.0 - 1e-6)
    logits = np.log(clipped / clipped[:, [1]])
    return pd.DataFrame(
        {
            f"{prefix}_home_logit_vs_draw": logits[:, 0],
            f"{prefix}_away_logit_vs_draw": logits[:, 2],
            f"{prefix}_home_prob": clipped[:, 0],
            f"{prefix}_draw_prob": clipped[:, 1],
            f"{prefix}_away_prob": clipped[:, 2],
            f"{prefix}_favorite_prob": clipped.max(axis=1),
        }
    )


def build_meta_features(model_probs: np.ndarray, market_probs: np.ndarray) -> pd.DataFrame:
    model = logit_features(model_probs, "model")
    market = logit_features(market_probs, "market")
    edge = pd.DataFrame(
        {
            "edge_home": model_probs[:, 0] - market_probs[:, 0],
            "edge_draw": model_probs[:, 1] - market_probs[:, 1],
            "edge_away": model_probs[:, 2] - market_probs[:, 2],
            "abs_edge_max": np.abs(model_probs - market_probs).max(axis=1),
            "model_minus_market_favorite": model_probs.max(axis=1) - market_probs.max(axis=1),
        }
    )
    return pd.concat([model, market, edge], axis=1)


def internal_time_split(X: pd.DataFrame, y: pd.Series, metadata: pd.DataFrame, validation_size: float = 0.2):
    split_index = int(len(X) * (1 - validation_size))
    cutoff_date = metadata["Date"].iloc[split_index]
    train_mask = metadata["Date"] < cutoff_date
    validation_mask = metadata["Date"] >= cutoff_date
    return (
        X.loc[train_mask],
        X.loc[validation_mask],
        y.loc[train_mask],
        y.loc[validation_mask],
        metadata.loc[train_mask],
        metadata.loc[validation_mask],
    )


def fit_logistic_stack(
    validation_y: pd.Series,
    validation_model_probs: np.ndarray,
    validation_market_probs: np.ndarray,
    test_model_probs: np.ndarray,
    test_market_probs: np.ndarray,
) -> tuple[np.ndarray, LogisticRegression]:
    X_validation = build_meta_features(validation_model_probs, validation_market_probs)
    X_test = build_meta_features(test_model_probs, test_market_probs)
    scaler = StandardScaler()
    X_validation_scaled = scaler.fit_transform(X_validation)
    X_test_scaled = scaler.transform(X_test)
    model = LogisticRegression(
        solver="lbfgs",
        C=0.2,
        max_iter=1000,
        random_state=42,
    )
    model.fit(X_validation_scaled, validation_y)
    probabilities = normalize_probabilities(model.predict_proba(X_test_scaled))
    model.feature_names_in_ = np.asarray(X_validation.columns, dtype=object)
    model.overlay_scaler_ = scaler
    return probabilities, model


def fit_best_blend(
    validation_y: pd.Series,
    validation_model_probs: np.ndarray,
    validation_market_probs: np.ndarray,
    test_model_probs: np.ndarray,
    test_market_probs: np.ndarray,
) -> tuple[np.ndarray, float]:
    weights = np.linspace(0.0, 1.0, 101)
    losses = [
        log_loss(
            validation_y,
            normalize_probabilities((float(weight) * validation_model_probs) + ((1.0 - float(weight)) * validation_market_probs)),
            labels=[0, 1, 2],
        )
        for weight in weights
    ]
    best_weight = float(weights[int(np.argmin(losses))])
    test_probs = normalize_probabilities((best_weight * test_model_probs) + ((1.0 - best_weight) * test_market_probs))
    return test_probs, best_weight


def fit_residual_adjustment(
    validation_y: pd.Series,
    validation_model_probs: np.ndarray,
    validation_market_probs: np.ndarray,
    test_model_probs: np.ndarray,
    test_market_probs: np.ndarray,
) -> tuple[np.ndarray, float]:
    """Apply a conservative model residual on top of market probabilities."""
    residual = validation_model_probs - validation_market_probs
    weights = np.linspace(-0.5, 0.5, 101)
    losses = [
        log_loss(
            validation_y,
            normalize_probabilities(validation_market_probs + (float(weight) * residual)),
            labels=[0, 1, 2],
        )
        for weight in weights
    ]
    best_weight = float(weights[int(np.argmin(losses))])
    test_probs = normalize_probabilities(test_market_probs + (best_weight * (test_model_probs - test_market_probs)))
    return test_probs, best_weight


def plot_results(results: pd.DataFrame) -> None:
    metrics = ["log_loss", "brier_score", "ece", "accuracy"]
    fig, axes = plt.subplots(1, len(metrics), figsize=(16, 4))
    for ax, metric in zip(axes, metrics):
        ax.bar(results["model"], results[metric])
        ax.set_title(metric)
        ax.tick_params(axis="x", rotation=25)
        ax.grid(axis="y", alpha=0.25)
    fig.suptitle("Market Overlay Experiment")
    fig.tight_layout()
    fig.savefig(OUTPUT_DIR / "market_overlay_model_comparison.png", dpi=160)
    plt.close(fig)


def write_report(results: pd.DataFrame, blend_weight: float, residual_weight: float, stack_model: LogisticRegression) -> None:
    production = results[results["model"] == "Production model"].iloc[0]
    best = results.sort_values(["log_loss", "brier_score"]).iloc[0]
    market = results[results["model"] == "Market-only preclosing"].iloc[0]
    stack = results[results["model"] == "Logistic stacking overlay"].iloc[0]
    coefficients = pd.DataFrame(stack_model.coef_, columns=stack_model.feature_names_in_)
    coefficient_summary = (
        coefficients.abs()
        .mean(axis=0)
        .sort_values(ascending=False)
        .reset_index()
        .rename(columns={"index": "feature", 0: "mean_abs_coefficient"})
    )
    coefficient_summary.to_csv(OUTPUT_DIR / "logistic_stack_coefficients.csv", index=False)

    overlay_improves_probability = float(stack["log_loss"]) < float(production["log_loss"]) and float(stack["brier_score"]) < float(production["brier_score"])
    overlay_passes_promotion = overlay_improves_probability and float(stack["ece"]) <= float(production["ece"]) + 0.002
    market_beats_production = float(market["log_loss"]) < float(production["log_loss"]) and float(market["brier_score"]) < float(production["brier_score"])
    lines = [
        "# Market Overlay Experiment Report",
        "",
        "## Goal",
        "",
        "Test whether pre-closing market odds can improve probability quality without feeding raw odds directly into XGBoost.",
        "",
        "## Models Tested",
        "",
        "- Production model: current football model without odds.",
        "- Market-only preclosing: normalized implied probabilities from football-data non-`C` 1X2 odds.",
        "- Best validation blend: weighted average of model and market probabilities, fitted on an internal latest training slice.",
        "- Residual overlay: starts from market probabilities and applies a conservative model residual when validation supports it.",
        "- Logistic stacking overlay: a regularized multinomial logistic meta-model using model probabilities, market probabilities and small edge descriptors.",
        "",
        "## Results",
        "",
        _markdown_table(results, ["model", "accuracy", "log_loss", "brier_score", "ece"]),
        "",
        "## Learned Overlay Parameters",
        "",
        f"- Best blend model weight: `{blend_weight:.2f}`. A value of `0.00` means pure market; `1.00` means pure model.",
        f"- Best residual weight: `{residual_weight:.2f}`.",
        "",
        "## Coefficients",
        "",
        _markdown_table(coefficient_summary.head(12), ["feature", "mean_abs_coefficient"]),
        "",
        "## Conclusions",
        "",
        f"- Best model by Log Loss: `{best['model']}`.",
        f"- Market-only beats production: {'yes' if market_beats_production else 'no'}.",
        f"- Logistic overlay improves Log Loss and Brier versus production: {'yes' if overlay_improves_probability else 'no'}.",
        f"- Logistic overlay passes the calibration promotion rule: {'yes' if overlay_passes_promotion else 'no'}.",
        "",
        "The goal is maximum probability quality, not protecting the existing model. If market-only remains best, the honest answer is that the market should be treated as the stronger probability benchmark.",
        "",
        "## Production Decision",
        "",
    ]
    if str(best["model"]) == "Market-only preclosing":
        lines.append(
            "Do not activate odds inside XGBoost. The current evidence supports showing market-implied probabilities as a separate benchmark/overlay candidate, pending live pre-closing feed timing."
        )
    elif overlay_passes_promotion:
        lines.append(
            "Move the logistic overlay forward as a production candidate, but only after a rolling season validation and a live pre-closing odds feed are available."
        )
    else:
        lines.append(
            "Keep market odds benchmark-only. The logistic overlay improves Log Loss and Brier, but it does not beat market-only and does not pass the calibration promotion rule."
        )
    (OUTPUT_DIR / "market_overlay_report.md").write_text("\n".join(lines))


def run_overlay_experiment() -> pd.DataFrame:
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    dataset, metadata, production_columns = build_market_dataset(market_mode="preclosing")
    if not all(column in dataset.columns for column in MARKET_PROB_COLUMNS):
        raise ValueError("Pre-closing market probabilities are unavailable.")

    split = time_based_split(dataset[production_columns], dataset["target"], metadata)
    X_internal_train, X_validation, y_internal_train, y_validation, _, _ = internal_time_split(
        split.X_train,
        split.y_train,
        split.train_metadata,
    )
    base_validation_model = train_xgb(X_internal_train, y_internal_train)
    validation_model_probs = normalize_probabilities(base_validation_model.predict_proba(X_validation))
    validation_market_probs = dataset.loc[X_validation.index, MARKET_PROB_COLUMNS].to_numpy()

    production_model = train_xgb(split.X_train, split.y_train)
    test_model_probs = normalize_probabilities(production_model.predict_proba(split.X_test))
    test_market_probs = dataset.loc[split.X_test.index, MARKET_PROB_COLUMNS].to_numpy()

    blend_probs, blend_weight = fit_best_blend(
        y_validation,
        validation_model_probs,
        validation_market_probs,
        test_model_probs,
        test_market_probs,
    )
    residual_probs, residual_weight = fit_residual_adjustment(
        y_validation,
        validation_model_probs,
        validation_market_probs,
        test_model_probs,
        test_market_probs,
    )
    stack_probs, stack_model = fit_logistic_stack(
        y_validation,
        validation_model_probs,
        validation_market_probs,
        test_model_probs,
        test_market_probs,
    )

    results = pd.DataFrame(
        [
            evaluate_probabilities("Production model", split.y_test, test_model_probs),
            evaluate_probabilities("Market-only preclosing", split.y_test, test_market_probs),
            evaluate_probabilities("Best validation blend", split.y_test, blend_probs),
            evaluate_probabilities("Residual market overlay", split.y_test, residual_probs),
            evaluate_probabilities("Logistic stacking overlay", split.y_test, stack_probs),
        ]
    ).sort_values(["log_loss", "brier_score"])
    results.to_csv(OUTPUT_DIR / "market_overlay_model_comparison.csv", index=False)
    plot_results(results)
    write_report(results, blend_weight, residual_weight, stack_model)
    return results


def main() -> None:
    results = run_overlay_experiment()
    best = results.iloc[0]
    print(json.dumps({"best_model": str(best["model"]), "log_loss": float(best["log_loss"])}, indent=2))


if __name__ == "__main__":
    main()
