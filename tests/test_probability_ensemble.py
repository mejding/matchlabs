from __future__ import annotations

import numpy as np
import pandas as pd

from probability_ensemble import BlendedProbabilityClassifier, TemperatureScaledPredictor


class FixedEstimator:
    def __init__(self, probabilities):
        self.probabilities = np.asarray(probabilities, dtype=float)
        self.classes_ = np.array([0, 1, 2])

    def predict_proba(self, features: pd.DataFrame) -> np.ndarray:
        return np.tile(self.probabilities, (len(features), 1))


def test_blended_classifier_averages_and_normalizes_probabilities() -> None:
    model = BlendedProbabilityClassifier(
        FixedEstimator([0.6, 0.3, 0.1]),
        FixedEstimator([0.2, 0.3, 0.5]),
        ("primary",),
        ("auxiliary",),
        0.5,
    )
    model.classes_ = np.array([0, 1, 2])
    probabilities = model.predict_proba(pd.DataFrame({"primary": [1.0], "auxiliary": [2.0]}))[0]

    np.testing.assert_allclose(probabilities, [0.4, 0.3, 0.3])
    assert probabilities.sum() == 1.0


def test_temperature_scaled_predictor_softens_probabilities() -> None:
    predictor = TemperatureScaledPredictor(FixedEstimator([0.7, 0.2, 0.1]), 1.5)
    probabilities = predictor.predict_proba(pd.DataFrame({"feature": [1.0]}))[0]

    assert probabilities[0] < 0.7
    assert probabilities[2] > 0.1
    np.testing.assert_allclose(probabilities.sum(), 1.0)
