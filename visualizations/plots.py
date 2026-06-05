from __future__ import annotations

from pathlib import Path

import matplotlib
import numpy as np
import pandas as pd
from matplotlib import pyplot as plt
from sklearn.inspection import permutation_importance
from sklearn.metrics import confusion_matrix

matplotlib.use("Agg")

CLASS_NAMES = ["home_win", "draw", "away_win"]


def plot_confusion_matrix(y_true: pd.Series, predictions: np.ndarray, output_path: Path) -> None:
    matrix = confusion_matrix(y_true, predictions, labels=[0, 1, 2])
    fig, ax = plt.subplots(figsize=(6.5, 5.5))
    image = ax.imshow(matrix, cmap="Blues")
    ax.set_title("Confusion Matrix")
    ax.set_xlabel("Predicted")
    ax.set_ylabel("Actual")
    ax.set_xticks(range(len(CLASS_NAMES)), CLASS_NAMES, rotation=30, ha="right")
    ax.set_yticks(range(len(CLASS_NAMES)), CLASS_NAMES)
    for row in range(matrix.shape[0]):
        for col in range(matrix.shape[1]):
            ax.text(col, row, matrix[row, col], ha="center", va="center", color="black")
    fig.colorbar(image, ax=ax, fraction=0.046, pad=0.04)
    fig.tight_layout()
    fig.savefig(output_path, dpi=160)
    plt.close(fig)


def plot_confidence_analysis(confidence: pd.DataFrame, output_path: Path) -> None:
    fig, ax1 = plt.subplots(figsize=(8, 5))
    ax1.plot(confidence["mean_confidence"], confidence["accuracy"], marker="o", linewidth=1.8, label="Accuracy")
    ax1.plot([0, 1], [0, 1], linestyle="--", color="black", linewidth=1, label="Ideal")
    ax1.set_title("Confidence vs Accuracy")
    ax1.set_xlabel("Mean predicted confidence")
    ax1.set_ylabel("Accuracy")
    ax1.set_xlim(0, 1)
    ax1.set_ylim(0, 1)
    ax1.grid(True, alpha=0.25)
    ax2 = ax1.twinx()
    ax2.bar(confidence["mean_confidence"], confidence["count"], width=0.055, alpha=0.18, color="gray", label="Matches")
    ax2.set_ylabel("Number of matches")
    lines, labels = ax1.get_legend_handles_labels()
    bars, bar_labels = ax2.get_legend_handles_labels()
    ax1.legend(lines + bars, labels + bar_labels, loc="upper left")
    fig.tight_layout()
    fig.savefig(output_path, dpi=160)
    plt.close(fig)


def plot_model_comparison(comparison: pd.DataFrame, output_path: Path) -> None:
    metrics = ["log_loss", "brier_score", "mean_absolute_calibration_error"]
    fig, axes = plt.subplots(1, 3, figsize=(13, 4))
    for ax, metric_name, title in zip(axes, metrics, ["Log Loss", "Brier Score", "Calibration Error"]):
        ax.bar(comparison["model"], comparison[metric_name])
        ax.set_title(title)
        ax.tick_params(axis="x", rotation=20)
        ax.grid(axis="y", alpha=0.25)
    fig.suptitle("Model Comparison: Lower Is Better")
    fig.tight_layout()
    fig.savefig(output_path, dpi=160)
    plt.close(fig)


def gain_importance(model, feature_columns: list[str]) -> pd.DataFrame:
    return pd.DataFrame({"feature": feature_columns, "gain_importance": model.feature_importances_}).sort_values(
        "gain_importance", ascending=False
    )


def plot_feature_importance(importance: pd.DataFrame, value_column: str, title: str, output_path: Path) -> None:
    plot_data = importance.sort_values(value_column, ascending=True)
    fig, ax = plt.subplots(figsize=(8, 7))
    ax.barh(plot_data["feature"], plot_data[value_column])
    ax.set_title(title)
    ax.set_xlabel(value_column)
    fig.tight_layout()
    fig.savefig(output_path, dpi=160)
    plt.close(fig)


def compute_permutation_importance(model, X_test: pd.DataFrame, y_test: pd.Series) -> pd.DataFrame:
    result = permutation_importance(
        model,
        X_test,
        y_test,
        scoring="neg_log_loss",
        n_repeats=10,
        random_state=42,
    )
    return pd.DataFrame(
        {
            "feature": X_test.columns,
            "permutation_importance": result.importances_mean,
            "permutation_importance_std": result.importances_std,
        }
    ).sort_values("permutation_importance", ascending=False)


def plot_prediction_distribution(intervals: pd.DataFrame, output_path: Path) -> None:
    fig, ax = plt.subplots(figsize=(7, 4))
    y_pos = np.arange(len(intervals))
    ax.barh(intervals["class"], intervals["mean_probability"], xerr=[
        intervals["mean_probability"] - intervals["lower_95"],
        intervals["upper_95"] - intervals["mean_probability"],
    ])
    ax.set_xlim(0, 1)
    ax.set_title("Bootstrap Prediction Intervals")
    ax.set_xlabel("Probability")
    fig.tight_layout()
    fig.savefig(output_path, dpi=160)
    plt.close(fig)


def plot_rolling_backtest(metadata: pd.DataFrame, y_true: pd.Series, probabilities: np.ndarray, output_path: Path) -> pd.DataFrame:
    actual_probabilities = probabilities[np.arange(len(y_true)), y_true.to_numpy()]
    rows = metadata.reset_index(drop=True).copy()
    rows["Date"] = pd.to_datetime(rows["Date"])
    rows["individual_log_loss"] = -np.log(np.clip(actual_probabilities, 1e-15, 1.0))
    rolling = rows.set_index("Date")["individual_log_loss"].rolling("60D").mean().dropna().reset_index()

    fig, ax = plt.subplots(figsize=(9, 4))
    ax.plot(rolling["Date"], rolling["individual_log_loss"])
    ax.set_title("Rolling 60-Day Test Log Loss")
    ax.set_xlabel("Date")
    ax.set_ylabel("Rolling log loss")
    ax.grid(True, alpha=0.25)
    fig.tight_layout()
    fig.savefig(output_path, dpi=160)
    plt.close(fig)
    return rolling
