from __future__ import annotations

from pathlib import Path

import matplotlib
import numpy as np
import pandas as pd
import shap
from matplotlib import pyplot as plt

matplotlib.use("Agg")

CLASS_NAMES = ["home_win", "draw", "away_win"]


def shap_values_to_array(shap_values) -> np.ndarray:
    values = shap_values.values if hasattr(shap_values, "values") else shap_values
    if isinstance(values, list):
        return np.stack(values, axis=-1)
    values = np.asarray(values)
    if values.ndim == 2:
        return values[:, :, np.newaxis]
    return values


def compute_shap_importance(model, X: pd.DataFrame, sample_size: int = 300) -> tuple[pd.DataFrame, object, pd.DataFrame]:
    sample = X.sample(n=min(sample_size, len(X)), random_state=42)
    explainer = shap.TreeExplainer(model)
    shap_values = explainer(sample)
    shap_array = shap_values_to_array(shap_values)
    mean_abs_shap = np.abs(shap_array).mean(axis=(0, 2))
    importance = pd.DataFrame({"feature": sample.columns, "mean_abs_shap": mean_abs_shap})
    return importance.sort_values("mean_abs_shap", ascending=False).reset_index(drop=True), shap_values, sample


def compute_shap_class_importance(model, X: pd.DataFrame, sample_size: int = 300) -> pd.DataFrame:
    sample = X.sample(n=min(sample_size, len(X)), random_state=42)
    explainer = shap.TreeExplainer(model)
    shap_values = explainer(sample)
    shap_array = shap_values_to_array(shap_values)

    rows = []
    for class_index, class_name in enumerate(CLASS_NAMES):
        class_values = np.abs(shap_array[:, :, class_index]).mean(axis=0)
        for feature, value in zip(sample.columns, class_values):
            rows.append({"class": class_name, "feature": feature, "mean_abs_shap": float(value)})
    return pd.DataFrame(rows).sort_values(["class", "mean_abs_shap"], ascending=[True, False])


def plot_shap_importance(importance: pd.DataFrame, output_path: Path) -> None:
    plot_data = importance.sort_values("mean_abs_shap", ascending=True)
    fig, ax = plt.subplots(figsize=(8, 7))
    ax.barh(plot_data["feature"], plot_data["mean_abs_shap"])
    ax.set_title("SHAP Mean Absolute Contribution")
    ax.set_xlabel("Mean absolute SHAP value")
    fig.tight_layout()
    fig.savefig(output_path, dpi=160)
    plt.close(fig)


def plot_shap_summary(model, X: pd.DataFrame, output_path: Path, sample_size: int = 300) -> None:
    sample = X.sample(n=min(sample_size, len(X)), random_state=42)
    explainer = shap.TreeExplainer(model)
    shap_values = explainer(sample)
    shap.summary_plot(shap_values, sample, show=False)
    plt.tight_layout()
    plt.savefig(output_path, dpi=160, bbox_inches="tight")
    plt.close()


def plot_local_waterfall(model, X: pd.DataFrame, output_path: Path, row_index: int = 0, class_index: int = 0) -> None:
    explainer = shap.TreeExplainer(model)
    shap_values = explainer(X.iloc[[row_index]])
    if len(shap_values.values.shape) == 3:
        explanation = shap.Explanation(
            values=shap_values.values[0, :, class_index],
            base_values=shap_values.base_values[0, class_index],
            data=X.iloc[row_index].to_numpy(),
            feature_names=list(X.columns),
        )
    else:
        explanation = shap_values[0]

    shap.plots.waterfall(explanation, show=False, max_display=12)
    plt.tight_layout()
    plt.savefig(output_path, dpi=160, bbox_inches="tight")
    plt.close()
