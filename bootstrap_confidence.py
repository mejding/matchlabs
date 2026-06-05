from __future__ import annotations

from dataclasses import dataclass

import numpy as np
import pandas as pd
from xgboost import XGBClassifier


@dataclass(frozen=True)
class BootstrapResult:
    predictions: np.ndarray
    mean: np.ndarray
    std: np.ndarray
    lower_95: np.ndarray
    upper_95: np.ndarray


def train_xgb_model(X_train: pd.DataFrame, y_train: pd.Series, seed: int) -> XGBClassifier:
    model = XGBClassifier(
        objective="multi:softprob",
        num_class=3,
        n_estimators=150,
        max_depth=3,
        learning_rate=0.05,
        subsample=0.9,
        colsample_bytree=1.0,
        eval_metric="mlogloss",
        random_state=seed,
    )
    model.fit(X_train, y_train)
    return model


def bootstrap_prediction_intervals(
    X_train: pd.DataFrame,
    y_train: pd.Series,
    X_predict: pd.DataFrame,
    n_models: int = 40,
    seed: int = 42,
) -> BootstrapResult:
    rng = np.random.default_rng(seed)
    predictions = []

    for model_index in range(n_models):
        sample_indices = rng.choice(len(X_train), size=len(X_train), replace=True)
        X_sample = X_train.iloc[sample_indices]
        y_sample = y_train.iloc[sample_indices]
        model = train_xgb_model(X_sample, y_sample, seed + model_index)
        predictions.append(model.predict_proba(X_predict))

    prediction_array = np.asarray(predictions)
    return BootstrapResult(
        predictions=prediction_array,
        mean=prediction_array.mean(axis=0),
        std=prediction_array.std(axis=0),
        lower_95=np.quantile(prediction_array, 0.025, axis=0),
        upper_95=np.quantile(prediction_array, 0.975, axis=0),
    )


def summarize_prediction_intervals(result: BootstrapResult, row_index: int = 0) -> pd.DataFrame:
    class_names = ["home_win", "draw", "away_win"]
    rows = []
    for class_index, class_name in enumerate(class_names):
        rows.append(
            {
                "class": class_name,
                "mean_probability": float(result.mean[row_index, class_index]),
                "std_probability": float(result.std[row_index, class_index]),
                "lower_95": float(result.lower_95[row_index, class_index]),
                "upper_95": float(result.upper_95[row_index, class_index]),
            }
        )
    return pd.DataFrame(rows)
