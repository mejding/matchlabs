from __future__ import annotations

from pathlib import Path

import matplotlib
import numpy as np
import pandas as pd
from matplotlib import pyplot as plt
from sklearn.preprocessing import label_binarize

matplotlib.use("Agg")

CLASS_NAMES = ["home_win", "draw", "away_win"]


def calibration_table(y_true: pd.Series, probabilities: np.ndarray, bins: int = 10) -> pd.DataFrame:
    y_one_hot = label_binarize(y_true, classes=[0, 1, 2])
    rows = []
    bin_edges = np.linspace(0.0, 1.0, bins + 1)

    for class_index, class_name in enumerate(CLASS_NAMES):
        class_probabilities = probabilities[:, class_index]
        class_actuals = y_one_hot[:, class_index]

        for bin_index in range(bins):
            lower = bin_edges[bin_index]
            upper = bin_edges[bin_index + 1]
            mask = (class_probabilities >= lower) & (class_probabilities <= upper) if bin_index == bins - 1 else (
                (class_probabilities >= lower) & (class_probabilities < upper)
            )

            if not np.any(mask):
                continue

            rows.append(
                {
                    "class": class_name,
                    "bin_lower": lower,
                    "bin_upper": upper,
                    "count": int(mask.sum()),
                    "mean_predicted_probability": float(class_probabilities[mask].mean()),
                    "observed_frequency": float(class_actuals[mask].mean()),
                }
            )

    return pd.DataFrame(rows)


def calibration_summary(calibration: pd.DataFrame) -> dict[str, object]:
    per_class = {}

    for class_name in CLASS_NAMES:
        class_calibration = calibration[calibration["class"] == class_name]
        errors = class_calibration["observed_frequency"] - class_calibration["mean_predicted_probability"]
        weighted_abs_errors = np.abs(errors) * class_calibration["count"]
        weighted_signed_errors = errors * class_calibration["count"]
        total_count = class_calibration["count"].sum()
        per_class[class_name] = {
            "mean_absolute_calibration_error": float(weighted_abs_errors.sum() / total_count),
            "mean_signed_calibration_error": float(weighted_signed_errors.sum() / total_count),
        }

    return {
        "mean_absolute_calibration_error": float(
            np.mean([item["mean_absolute_calibration_error"] for item in per_class.values()])
        ),
        "by_class": per_class,
    }


def expected_calibration_error(calibration: pd.DataFrame) -> float:
    errors = calibration["observed_frequency"] - calibration["mean_predicted_probability"]
    weighted_errors = np.abs(errors) * calibration["count"]
    return float(weighted_errors.sum() / calibration["count"].sum())


def calibration_diagnosis(summary: dict[str, object]) -> dict[str, str]:
    diagnosis = {}
    for class_name, values in summary["by_class"].items():
        signed_error = values["mean_signed_calibration_error"]
        if signed_error < -0.02:
            diagnosis[class_name] = "overconfident / overpredicted"
        elif signed_error > 0.02:
            diagnosis[class_name] = "underconfident / underpredicted"
        else:
            diagnosis[class_name] = "reasonably calibrated"
    return diagnosis


def plot_calibration_curve(calibration: pd.DataFrame, output_path: Path) -> None:
    fig, ax = plt.subplots(figsize=(8, 6))
    ax.plot([0, 1], [0, 1], linestyle="--", color="black", linewidth=1, label="Perfect calibration")

    for class_name in CLASS_NAMES:
        class_calibration = calibration[calibration["class"] == class_name]
        ax.plot(
            class_calibration["mean_predicted_probability"],
            class_calibration["observed_frequency"],
            marker="o",
            linewidth=1.8,
            label=class_name,
        )

    ax.set_title("Calibration Curve")
    ax.set_xlabel("Mean predicted probability")
    ax.set_ylabel("Observed frequency")
    ax.set_xlim(0, 1)
    ax.set_ylim(0, 1)
    ax.grid(True, alpha=0.25)
    ax.legend()
    fig.tight_layout()
    fig.savefig(output_path, dpi=160)
    plt.close(fig)


def plot_reliability_diagram(calibration: pd.DataFrame, output_path: Path) -> None:
    fig, axes = plt.subplots(1, 3, figsize=(13, 4), sharey=True)

    for ax, class_name in zip(axes, CLASS_NAMES):
        class_calibration = calibration[calibration["class"] == class_name]
        error = class_calibration["observed_frequency"] - class_calibration["mean_predicted_probability"]
        ax.bar(class_calibration["mean_predicted_probability"], error, width=0.06)
        ax.axhline(0, color="black", linewidth=1)
        ax.set_title(class_name)
        ax.set_xlabel("Mean predicted probability")
        ax.grid(axis="y", alpha=0.25)

    axes[0].set_ylabel("Observed - predicted")
    fig.suptitle("Reliability Diagram")
    fig.tight_layout()
    fig.savefig(output_path, dpi=160)
    plt.close(fig)


def plot_probability_histogram(probabilities: np.ndarray, output_path: Path) -> None:
    fig, ax = plt.subplots(figsize=(8, 5))

    for class_index, class_name in enumerate(CLASS_NAMES):
        ax.hist(probabilities[:, class_index], bins=20, alpha=0.45, label=class_name)

    ax.set_title("Predicted Probability Distribution")
    ax.set_xlabel("Predicted probability")
    ax.set_ylabel("Number of matches")
    ax.legend()
    fig.tight_layout()
    fig.savefig(output_path, dpi=160)
    plt.close(fig)
