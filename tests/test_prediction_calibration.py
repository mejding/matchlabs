from __future__ import annotations

import joblib
import numpy as np
import pandas as pd

from predict import apply_probability_calibration


class DummyCalibrator:
    def predict_proba(self, features: pd.DataFrame) -> np.ndarray:
        return np.array([[0.55, 0.27, 0.18]])


def test_apply_probability_calibration_uses_matching_calibration_layer(tmp_path) -> None:
    features = pd.DataFrame([{"feature_a": 1.0, "feature_b": 2.0}])
    calibration_path = tmp_path / "calibrated_probability_layer.joblib"
    joblib.dump(
        {
            "method": "sigmoid",
            "feature_columns": ["feature_a", "feature_b"],
            "calibrator": DummyCalibrator(),
        },
        calibration_path,
    )

    probabilities, is_calibrated, method = apply_probability_calibration(
        np.array([0.68, 0.20, 0.12]),
        features,
        calibration_path=calibration_path,
    )

    assert is_calibrated
    assert method == "sigmoid"
    assert probabilities.tolist() == [0.55, 0.27, 0.18]


def test_apply_probability_calibration_falls_back_on_feature_mismatch(tmp_path) -> None:
    raw = np.array([0.68, 0.20, 0.12])
    features = pd.DataFrame([{"feature_a": 1.0, "feature_b": 2.0}])
    calibration_path = tmp_path / "calibrated_probability_layer.joblib"
    joblib.dump(
        {
            "method": "sigmoid",
            "feature_columns": ["feature_a"],
            "calibrator": DummyCalibrator(),
        },
        calibration_path,
    )

    probabilities, is_calibrated, method = apply_probability_calibration(raw, features, calibration_path=calibration_path)

    assert not is_calibrated
    assert method == "raw"
    assert probabilities is raw
