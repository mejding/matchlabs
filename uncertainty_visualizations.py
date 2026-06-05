from __future__ import annotations

from pathlib import Path

import matplotlib
import numpy as np
import pandas as pd
from matplotlib import pyplot as plt

matplotlib.use("Agg")


def plot_bootstrap_histograms(predictions: np.ndarray, output_path: Path, row_index: int = 0) -> None:
    class_names = ["home_win", "draw", "away_win"]
    fig, axes = plt.subplots(1, 3, figsize=(12, 4), sharey=True)
    for class_index, class_name in enumerate(class_names):
        axes[class_index].hist(predictions[:, row_index, class_index], bins=12, alpha=0.75)
        axes[class_index].set_title(class_name)
        axes[class_index].set_xlabel("Probability")
        axes[class_index].set_xlim(0, 1)
    axes[0].set_ylabel("Bootstrap models")
    fig.suptitle("Bootstrap Prediction Distribution")
    fig.tight_layout()
    fig.savefig(output_path, dpi=160)
    plt.close(fig)


def plot_stability_over_time(metadata: pd.DataFrame, stability: pd.DataFrame, output_path: Path) -> None:
    rows = metadata.reset_index(drop=True).copy()
    rows["Date"] = pd.to_datetime(rows["Date"])
    rows["stability_score"] = stability["stability_score"].to_numpy()
    rolling = rows.set_index("Date")["stability_score"].rolling("60D").mean().dropna().reset_index()

    fig, ax = plt.subplots(figsize=(9, 4))
    ax.plot(rolling["Date"], rolling["stability_score"])
    ax.set_ylim(0, 1)
    ax.set_title("Rolling 60-Day Prediction Stability")
    ax.set_xlabel("Date")
    ax.set_ylabel("Stability score")
    ax.grid(True, alpha=0.25)
    fig.tight_layout()
    fig.savefig(output_path, dpi=160)
    plt.close(fig)
