from __future__ import annotations

import numpy as np
import pandas as pd
from sklearn.base import BaseEstimator, ClassifierMixin, clone


def normalize_probabilities(probabilities: np.ndarray) -> np.ndarray:
    values = np.clip(np.asarray(probabilities, dtype=float), 1e-15, 1.0)
    return values / values.sum(axis=1, keepdims=True)


def temperature_scale(probabilities: np.ndarray, temperature: float) -> np.ndarray:
    logits = np.log(normalize_probabilities(probabilities)) / float(temperature)
    logits -= logits.max(axis=1, keepdims=True)
    return normalize_probabilities(np.exp(logits))


class BlendedProbabilityClassifier(ClassifierMixin, BaseEstimator):
    def __init__(
        self,
        primary_estimator,
        auxiliary_estimator,
        primary_features: tuple[str, ...],
        auxiliary_features: tuple[str, ...],
        primary_weight: float = 0.5,
    ):
        self.primary_estimator = primary_estimator
        self.auxiliary_estimator = auxiliary_estimator
        self.primary_features = primary_features
        self.auxiliary_features = auxiliary_features
        self.primary_weight = primary_weight

    def fit(self, X: pd.DataFrame, y: pd.Series):
        self.primary_estimator_ = clone(self.primary_estimator).fit(X[list(self.primary_features)], y)
        self.auxiliary_estimator_ = clone(self.auxiliary_estimator).fit(X[list(self.auxiliary_features)], y)
        self.classes_ = np.asarray(self.primary_estimator_.classes_)
        return self

    def _primary(self):
        return getattr(self, "primary_estimator_", self.primary_estimator)

    def _auxiliary(self):
        return getattr(self, "auxiliary_estimator_", self.auxiliary_estimator)

    def predict_proba(self, X: pd.DataFrame) -> np.ndarray:
        primary = normalize_probabilities(self._primary().predict_proba(X[list(self.primary_features)]))
        auxiliary = normalize_probabilities(self._auxiliary().predict_proba(X[list(self.auxiliary_features)]))
        blended = float(self.primary_weight) * primary + (1.0 - float(self.primary_weight)) * auxiliary
        return normalize_probabilities(blended)

    def predict(self, X: pd.DataFrame) -> np.ndarray:
        return self.classes_[self.predict_proba(X).argmax(axis=1)]


class TemperatureScaledPredictor:
    def __init__(self, estimator, temperature: float):
        self.estimator = estimator
        self.temperature = float(temperature)

    def predict_proba(self, X: pd.DataFrame) -> np.ndarray:
        return temperature_scale(self.estimator.predict_proba(X), self.temperature)


def calibrated_predictor(estimator, layer: dict | None, feature_columns: list[str]):
    if not layer or list(layer.get("feature_columns", [])) != list(feature_columns):
        return None, "raw"
    method = str(layer.get("method", "raw"))
    if method in {"sigmoid", "isotonic"}:
        return layer["calibrator"], method
    if method == "temperature":
        return TemperatureScaledPredictor(estimator, float(layer["temperature"])), method
    return None, "raw"
