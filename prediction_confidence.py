from __future__ import annotations

from dataclasses import dataclass

import numpy as np
import pandas as pd

from bootstrap_confidence import BootstrapResult, summarize_prediction_intervals


CLASS_NAMES = ["home_win", "draw", "away_win"]


@dataclass(frozen=True)
class PredictionConfidence:
    label: str
    score: float
    explanation: str


def prediction_stability_score(std_probabilities: np.ndarray) -> float:
    mean_std = float(np.mean(std_probabilities))
    return float(max(0.0, min(1.0, 1.0 - (mean_std / 0.18))))


def confidence_label(score: float) -> str:
    if score >= 0.75:
        return "High confidence"
    if score >= 0.5:
        return "Medium confidence"
    return "Low confidence"


def uncertainty_explanation(intervals: pd.DataFrame, score: float) -> str:
    widest = intervals.assign(width=intervals["upper_95"] - intervals["lower_95"]).sort_values(
        "width", ascending=False
    ).iloc[0]
    label = confidence_label(score)
    if label == "High confidence":
        return f"Bootstrap models are stable; widest interval is for {widest['class']}."
    if label == "Medium confidence":
        return f"Moderate model disagreement; widest interval is for {widest['class']}."
    return f"High model disagreement; widest interval is for {widest['class']}."


def match_level_confidence(result: BootstrapResult, row_index: int = 0) -> tuple[pd.DataFrame, PredictionConfidence]:
    intervals = summarize_prediction_intervals(result, row_index=row_index)
    score = prediction_stability_score(result.std[row_index])
    confidence = PredictionConfidence(
        label=confidence_label(score),
        score=score,
        explanation=uncertainty_explanation(intervals, score),
    )
    return intervals, confidence


def batch_stability_table(result: BootstrapResult) -> pd.DataFrame:
    rows = []
    for row_index in range(result.mean.shape[0]):
        score = prediction_stability_score(result.std[row_index])
        rows.append(
            {
                "row_index": row_index,
                "stability_score": score,
                "confidence_label": confidence_label(score),
                "mean_probability_std": float(result.std[row_index].mean()),
                "max_probability_std": float(result.std[row_index].max()),
            }
        )
    return pd.DataFrame(rows)
