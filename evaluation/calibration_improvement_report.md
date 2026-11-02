# Calibration Improvement Report

Validation uses a strict chronological split. The model is fitted on the earlier training period, calibration methods are fitted on the latest slice of the training period, and final metrics are measured only on the held-out future test period.

## Results

| Method | Accuracy | Log Loss | Brier | ECE |
| --- | ---: | ---: | ---: | ---: |
| raw | 0.4582 | 1.0723 | 0.6447 | 0.0569 |
| sigmoid | 0.4582 | 1.0730 | 0.6473 | 0.0599 |
| isotonic | 0.4618 | 1.4419 | 0.6610 | 0.0802 |
| temperature_1.05 | 0.4582 | 1.0694 | 0.6431 | 0.0560 |

## Decision

- Best method by log loss: `temperature_1.05`.
- Deployed calibrated probability layer: Yes.
- Raw log loss/Brier: 1.0723 / 0.6447.
- Best log loss/Brier: 1.0694 / 0.6431.

A calibrator is saved only if it improves out-of-sample log loss or Brier score. If not, raw model probabilities remain the honest production output.

## Class-Level Note

Draw probabilities remain the most difficult class to calibrate because draws are both less frequent and less separable from narrow home/away outcomes.
