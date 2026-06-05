from __future__ import annotations

from dataclasses import dataclass

import numpy as np
import pandas as pd

from bootstrap_confidence import train_xgb_model


@dataclass(frozen=True)
class EnsembleResult:
    predictions: np.ndarray
    mean: np.ndarray
    std: np.ndarray


def train_ensemble_predictions(
    X_train: pd.DataFrame,
    y_train: pd.Series,
    X_predict: pd.DataFrame,
    n_models: int = 30,
    train_fraction: float = 0.85,
    seed: int = 42,
) -> EnsembleResult:
    rng = np.random.default_rng(seed)
    predictions = []
    sample_size = max(1, int(len(X_train) * train_fraction))

    for model_index in range(n_models):
        sample_indices = rng.choice(len(X_train), size=sample_size, replace=False)
        model = train_xgb_model(
            X_train.iloc[sample_indices],
            y_train.iloc[sample_indices],
            seed + model_index,
        )
        predictions.append(model.predict_proba(X_predict))

    prediction_array = np.asarray(predictions)
    return EnsembleResult(
        predictions=prediction_array,
        mean=prediction_array.mean(axis=0),
        std=prediction_array.std(axis=0),
    )
