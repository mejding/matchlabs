# Calibration Improvement Report

Validation uses a strict chronological split. The model is fitted on the earlier training period, calibration methods are fitted on the latest slice of the training period, and final metrics are measured only on the held-out future test period.

## Results

| Method | Accuracy | Log Loss | Brier | ECE |
| --- | ---: | ---: | ---: | ---: |
| raw | 0.4536 | 1.0881 | 0.6558 | 0.0710 |
| sigmoid | 0.4153 | 1.0917 | 0.6608 | 0.0817 |
| isotonic | 0.4444 | 1.4059 | 0.6763 | 0.0928 |
| temperature_1.12 | 0.4536 | 1.0785 | 0.6503 | 0.0565 |

## Decision

- Best method by log loss: `temperature_1.12`.
- Deployed calibrated probability layer: Yes.
- Raw log loss/Brier: 1.0881 / 0.6558.
- Best log loss/Brier: 1.0785 / 0.6503.

A calibrator is saved only if it improves out-of-sample log loss or Brier score. If not, raw model probabilities remain the honest production output.

## Class-Level Note

Draw probabilities remain the most difficult class to calibrate because draws are both less frequent and less separable from narrow home/away outcomes.
