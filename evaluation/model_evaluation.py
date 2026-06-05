from __future__ import annotations

from dataclasses import dataclass

import numpy as np
import pandas as pd
from sklearn.metrics import accuracy_score, confusion_matrix, log_loss
from sklearn.preprocessing import label_binarize


CLASS_NAMES = ["home_win", "draw", "away_win"]
LABEL_TO_RESULT = {0: "home_win", 1: "draw", 2: "away_win"}


@dataclass(frozen=True)
class TimeSplit:
    X_train: pd.DataFrame
    X_test: pd.DataFrame
    y_train: pd.Series
    y_test: pd.Series
    train_metadata: pd.DataFrame
    test_metadata: pd.DataFrame
    cutoff_date: object


def time_based_split(
    X: pd.DataFrame,
    y: pd.Series,
    metadata: pd.DataFrame,
    test_size: float = 0.2,
) -> TimeSplit:
    split_index = int(len(X) * (1 - test_size))
    cutoff_date = metadata["Date"].iloc[split_index]
    train_mask = metadata["Date"] < cutoff_date
    test_mask = metadata["Date"] >= cutoff_date

    return TimeSplit(
        X_train=X.loc[train_mask],
        X_test=X.loc[test_mask],
        y_train=y.loc[train_mask],
        y_test=y.loc[test_mask],
        train_metadata=metadata.loc[train_mask],
        test_metadata=metadata.loc[test_mask],
        cutoff_date=cutoff_date,
    )


def multiclass_brier_score(y_true: pd.Series, probabilities: np.ndarray) -> float:
    y_one_hot = label_binarize(y_true, classes=[0, 1, 2])
    return float(np.mean(np.sum((probabilities - y_one_hot) ** 2, axis=1)))


def per_class_brier_scores(y_true: pd.Series, probabilities: np.ndarray) -> dict[str, float]:
    y_one_hot = label_binarize(y_true, classes=[0, 1, 2])
    return {
        class_name: float(np.mean((probabilities[:, class_index] - y_one_hot[:, class_index]) ** 2))
        for class_index, class_name in enumerate(CLASS_NAMES)
    }


def evaluate_probabilities(
    y_true: pd.Series,
    probabilities: np.ndarray,
    predictions: np.ndarray,
) -> dict[str, object]:
    return {
        "accuracy": float(accuracy_score(y_true, predictions)),
        "log_loss": float(log_loss(y_true, probabilities, labels=[0, 1, 2])),
        "brier_score_multiclass": multiclass_brier_score(y_true, probabilities),
        "brier_score_by_class": per_class_brier_scores(y_true, probabilities),
        "confusion_matrix": confusion_matrix(y_true, predictions, labels=[0, 1, 2]).tolist(),
    }


def class_performance(y_true: pd.Series, probabilities: np.ndarray, predictions: np.ndarray) -> pd.DataFrame:
    rows = []
    y_one_hot = label_binarize(y_true, classes=[0, 1, 2])

    for class_index, class_name in enumerate(CLASS_NAMES):
        mask = y_true == class_index
        rows.append(
            {
                "class": class_name,
                "support": int(mask.sum()),
                "one_vs_rest_brier": float(np.mean((probabilities[:, class_index] - y_one_hot[:, class_index]) ** 2)),
                "actual_class_accuracy": float(np.mean(predictions[mask] == class_index)) if np.any(mask) else 0.0,
                "actual_class_mean_probability": float(probabilities[mask, class_index].mean()) if np.any(mask) else 0.0,
                "actual_class_log_loss": float(
                    -np.mean(np.log(np.clip(probabilities[mask, class_index], 1e-15, 1.0)))
                )
                if np.any(mask)
                else 0.0,
            }
        )

    return pd.DataFrame(rows)


def confidence_table(y_true: pd.Series, probabilities: np.ndarray, predictions: np.ndarray, bins: int = 10) -> pd.DataFrame:
    confidence = probabilities.max(axis=1)
    correct = predictions == y_true.to_numpy()
    rows = []
    bin_edges = np.linspace(0.0, 1.0, bins + 1)

    for bin_index in range(bins):
        lower = bin_edges[bin_index]
        upper = bin_edges[bin_index + 1]
        mask = (confidence >= lower) & (confidence <= upper) if bin_index == bins - 1 else (
            (confidence >= lower) & (confidence < upper)
        )

        if not np.any(mask):
            continue

        rows.append(
            {
                "bin_lower": lower,
                "bin_upper": upper,
                "count": int(mask.sum()),
                "mean_confidence": float(confidence[mask].mean()),
                "accuracy": float(correct[mask].mean()),
                "confidence_minus_accuracy": float(confidence[mask].mean() - correct[mask].mean()),
            }
        )

    return pd.DataFrame(rows)


def worst_predictions(
    metadata: pd.DataFrame,
    y_true: pd.Series,
    probabilities: np.ndarray,
    predictions: np.ndarray,
    limit: int = 25,
) -> pd.DataFrame:
    actual_probabilities = probabilities[np.arange(len(y_true)), y_true.to_numpy()]
    rows = metadata.reset_index(drop=True).copy()
    rows["actual"] = y_true.map(LABEL_TO_RESULT).reset_index(drop=True)
    rows["predicted"] = pd.Series(predictions).map(LABEL_TO_RESULT)
    rows["predicted_confidence"] = probabilities.max(axis=1)
    rows["actual_probability"] = actual_probabilities
    rows["home_win_probability"] = probabilities[:, 0]
    rows["draw_probability"] = probabilities[:, 1]
    rows["away_win_probability"] = probabilities[:, 2]
    rows["individual_log_loss"] = -np.log(np.clip(actual_probabilities, 1e-15, 1.0))
    return rows.sort_values("individual_log_loss", ascending=False).head(limit)
