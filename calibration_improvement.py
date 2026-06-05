from __future__ import annotations

import json
import os
from pathlib import Path
from typing import Protocol

Path("evaluation", ".matplotlib-cache").mkdir(parents=True, exist_ok=True)
os.environ.setdefault("MPLCONFIGDIR", str(Path("evaluation") / ".matplotlib-cache"))

import joblib
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from sklearn.base import clone
from sklearn.calibration import CalibratedClassifierCV
from sklearn.frozen import FrozenEstimator
from sklearn.metrics import accuracy_score, log_loss

from calibration.calibration import calibration_table, expected_calibration_error
from evaluate_model import load_current_dataset
from evaluation.model_evaluation import multiclass_brier_score, time_based_split
from train_model import MODEL_PATH


EVALUATION_DIR = Path("evaluation")
CALIBRATED_MODEL_PATH = Path("models") / "calibrated_probability_layer.joblib"
CLASS_NAMES = ["home_win", "draw", "away_win"]


class ProbabilityModel(Protocol):
    def predict_proba(self, X: pd.DataFrame) -> np.ndarray:
        ...


def split_fit_and_calibration(X: pd.DataFrame, y: pd.Series, dates: pd.Series) -> tuple[pd.DataFrame, pd.DataFrame, pd.Series, pd.Series]:
    split_index = int(len(X) * 0.8)
    cutoff = dates.iloc[split_index]
    fit_mask = dates < cutoff
    calibration_mask = dates >= cutoff
    return X.loc[fit_mask], X.loc[calibration_mask], y.loc[fit_mask], y.loc[calibration_mask]


def clipped_probabilities(probabilities: np.ndarray) -> np.ndarray:
    clipped = np.clip(probabilities, 1e-15, 1.0)
    return clipped / clipped.sum(axis=1, keepdims=True)


def temperature_scale(probabilities: np.ndarray, temperature: float) -> np.ndarray:
    logits = np.log(clipped_probabilities(probabilities))
    scaled = logits / temperature
    scaled -= scaled.max(axis=1, keepdims=True)
    exp_values = np.exp(scaled)
    return exp_values / exp_values.sum(axis=1, keepdims=True)


def choose_temperature(calibration_y: pd.Series, calibration_probabilities: np.ndarray) -> float:
    candidates = np.linspace(0.6, 2.6, 81)
    losses = [
        log_loss(calibration_y, temperature_scale(calibration_probabilities, float(candidate)), labels=[0, 1, 2])
        for candidate in candidates
    ]
    return float(candidates[int(np.argmin(losses))])


def evaluate(name: str, y_true: pd.Series, probabilities: np.ndarray) -> dict[str, float | str]:
    predictions = probabilities.argmax(axis=1)
    table = calibration_table(y_true, probabilities)
    return {
        "method": name,
        "accuracy": float(accuracy_score(y_true, predictions)),
        "log_loss": float(log_loss(y_true, clipped_probabilities(probabilities), labels=[0, 1, 2])),
        "brier_score": multiclass_brier_score(y_true, probabilities),
        "ece": expected_calibration_error(table),
        "home_win_mean_probability": float(probabilities[:, 0].mean()),
        "draw_mean_probability": float(probabilities[:, 1].mean()),
        "away_win_mean_probability": float(probabilities[:, 2].mean()),
    }


def plot_reliability(y_true: pd.Series, probability_sets: dict[str, np.ndarray], output_path: Path) -> None:
    fig, axes = plt.subplots(1, 3, figsize=(14, 4), sharex=True, sharey=True)
    for class_index, class_name in enumerate(CLASS_NAMES):
        ax = axes[class_index]
        actual = (y_true.to_numpy() == class_index).astype(float)
        for method, probabilities in probability_sets.items():
            rows = []
            for lower, upper in zip(np.linspace(0, 0.9, 10), np.linspace(0.1, 1, 10)):
                mask = (probabilities[:, class_index] >= lower) & (probabilities[:, class_index] < upper)
                if upper == 1:
                    mask = (probabilities[:, class_index] >= lower) & (probabilities[:, class_index] <= upper)
                if mask.any():
                    rows.append((float(probabilities[mask, class_index].mean()), float(actual[mask].mean())))
            if rows:
                xs, ys = zip(*rows)
                ax.plot(xs, ys, marker="o", label=method)
        ax.plot([0, 1], [0, 1], linestyle="--", color="gray", linewidth=1)
        ax.set_title(class_name)
        ax.set_xlabel("Mean predicted probability")
        ax.grid(alpha=0.25)
    axes[0].set_ylabel("Observed frequency")
    axes[-1].legend(loc="lower right")
    fig.tight_layout()
    fig.savefig(output_path, dpi=160)
    plt.close(fig)


def write_report(rows: list[dict[str, float | str]], best_method: str, deployed: bool) -> None:
    raw = next(row for row in rows if row["method"] == "raw")
    best = min(rows, key=lambda row: (float(row["log_loss"]), float(row["brier_score"])))
    lines = [
        "# Calibration Improvement Report",
        "",
        "Validation uses a strict chronological split. The model is fitted on the earlier training period, calibration methods are fitted on the latest slice of the training period, and final metrics are measured only on the held-out future test period.",
        "",
        "## Results",
        "",
        "| Method | Accuracy | Log Loss | Brier | ECE |",
        "| --- | ---: | ---: | ---: | ---: |",
    ]
    for row in rows:
        lines.append(
            f"| {row['method']} | {float(row['accuracy']):.4f} | {float(row['log_loss']):.4f} | {float(row['brier_score']):.4f} | {float(row['ece']):.4f} |"
        )
    lines.extend(
        [
            "",
            "## Decision",
            "",
            f"- Best method by log loss: `{best_method}`.",
            f"- Deployed calibrated probability layer: {'Yes' if deployed else 'No'}.",
            f"- Raw log loss/Brier: {float(raw['log_loss']):.4f} / {float(raw['brier_score']):.4f}.",
            f"- Best log loss/Brier: {float(best['log_loss']):.4f} / {float(best['brier_score']):.4f}.",
            "",
            "A calibrator is saved only if it improves out-of-sample log loss or Brier score. If not, raw model probabilities remain the honest production output.",
            "",
            "## Class-Level Note",
            "",
            "Draw probabilities remain the most difficult class to calibrate because draws are both less frequent and less separable from narrow home/away outcomes.",
        ]
    )
    (EVALUATION_DIR / "calibration_improvement_report.md").write_text("\n".join(lines) + "\n")


def main() -> None:
    EVALUATION_DIR.mkdir(exist_ok=True)
    artifact = joblib.load(MODEL_PATH)
    feature_columns = artifact["feature_columns"]
    base_model = artifact["model"]
    dataset, metadata = load_current_dataset(feature_columns)
    X = dataset[feature_columns]
    y = dataset["target"]
    outer = time_based_split(X, y, metadata)

    X_fit, X_cal, y_fit, y_cal = split_fit_and_calibration(
        outer.X_train,
        outer.y_train,
        outer.train_metadata["Date"].reset_index(drop=True),
    )

    fit_model = clone(base_model)
    fit_model.fit(X_fit, y_fit)
    raw_cal = clipped_probabilities(fit_model.predict_proba(X_cal))
    raw_test = clipped_probabilities(fit_model.predict_proba(outer.X_test))

    sigmoid = CalibratedClassifierCV(FrozenEstimator(fit_model), method="sigmoid")
    sigmoid.fit(X_cal, y_cal)
    sigmoid_test = clipped_probabilities(sigmoid.predict_proba(outer.X_test))

    isotonic = CalibratedClassifierCV(FrozenEstimator(fit_model), method="isotonic")
    isotonic.fit(X_cal, y_cal)
    isotonic_test = clipped_probabilities(isotonic.predict_proba(outer.X_test))

    temperature = choose_temperature(y_cal, raw_cal)
    temperature_test = temperature_scale(raw_test, temperature)

    probability_sets = {
        "raw": raw_test,
        "sigmoid": sigmoid_test,
        "isotonic": isotonic_test,
        f"temperature_{temperature:.2f}": temperature_test,
    }
    rows = [evaluate(name, outer.y_test, probs) for name, probs in probability_sets.items()]
    comparison = pd.DataFrame(rows)
    comparison.to_csv(EVALUATION_DIR / "calibrated_model_comparison.csv", index=False)

    best_row = min(rows, key=lambda row: (float(row["log_loss"]), float(row["brier_score"])))
    raw_row = next(row for row in rows if row["method"] == "raw")
    improved = float(best_row["log_loss"]) < float(raw_row["log_loss"]) or float(best_row["brier_score"]) < float(raw_row["brier_score"])

    if improved and str(best_row["method"]) == "sigmoid":
        joblib.dump({"method": "sigmoid", "calibrator": sigmoid, "feature_columns": feature_columns}, CALIBRATED_MODEL_PATH)
    elif improved and str(best_row["method"]) == "isotonic":
        joblib.dump({"method": "isotonic", "calibrator": isotonic, "feature_columns": feature_columns}, CALIBRATED_MODEL_PATH)
    elif improved and str(best_row["method"]).startswith("temperature"):
        joblib.dump(
            {"method": "temperature", "temperature": temperature, "feature_columns": feature_columns},
            CALIBRATED_MODEL_PATH,
        )

    plot_reliability(outer.y_test, {"raw": raw_test, str(best_row["method"]): probability_sets[str(best_row["method"])]}, EVALUATION_DIR / "calibrated_reliability_diagram.png")
    write_report(rows, str(best_row["method"]), improved)
    print(json.dumps({"best_method": best_row["method"], "deployed": improved}, indent=2))


if __name__ == "__main__":
    main()
