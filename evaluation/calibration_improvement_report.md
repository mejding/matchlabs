# Calibration Improvement Report

Validation uses a strict chronological split. The model is fitted on the earlier training period, calibration methods are fitted on the latest slice of the training period, and final metrics are measured only on the held-out future test period.

## Results

| Method | Accuracy | Log Loss | Brier | ECE |
| --- | ---: | ---: | ---: | ---: |
| raw | 0.4580 | 1.0799 | 0.6507 | 0.0698 |
| sigmoid | 0.4434 | 1.0791 | 0.6517 | 0.0765 |
| isotonic | 0.4489 | 1.1532 | 0.6588 | 0.0796 |
| temperature_1.12 | 0.4580 | 1.0716 | 0.6458 | 0.0571 |

## Decision

- Best method by log loss: `temperature_1.12`.
- Deployed calibrated probability layer: Yes.
- Raw log loss/Brier: 1.0799 / 0.6507.
- Best log loss/Brier: 1.0716 / 0.6458.

A calibrator is saved only if it improves out-of-sample log loss or Brier score. If not, raw model probabilities remain the honest production output.

## Class-Level Note

Draw probabilities remain the most difficult class to calibrate because draws are both less frequent and less separable from narrow home/away outcomes.
