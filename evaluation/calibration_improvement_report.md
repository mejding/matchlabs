# Calibration Improvement Report

Validation uses a strict chronological split. The model is fitted on the earlier training period, calibration methods are fitted on the latest slice of the training period, and final metrics are measured only on the held-out future test period.

## Results

| Method | Accuracy | Log Loss | Brier | ECE |
| --- | ---: | ---: | ---: | ---: |
| raw | 0.4746 | 1.0647 | 0.6390 | 0.0427 |
| sigmoid | 0.4620 | 1.0636 | 0.6405 | 0.0506 |
| isotonic | 0.4583 | 1.1276 | 0.6447 | 0.0624 |
| temperature_1.07 | 0.4746 | 1.0615 | 0.6375 | 0.0373 |

## Decision

- Best method by log loss: `temperature_1.07`.
- Deployed calibrated probability layer: Yes.
- Raw log loss/Brier: 1.0647 / 0.6390.
- Best log loss/Brier: 1.0615 / 0.6375.

A calibrator is saved only if it improves out-of-sample log loss or Brier score. If not, raw model probabilities remain the honest production output.

## Class-Level Note

Draw probabilities remain the most difficult class to calibrate because draws are both less frequent and less separable from narrow home/away outcomes.
