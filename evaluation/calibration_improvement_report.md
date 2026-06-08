# Calibration Improvement Report

Validation uses a strict chronological split. The model is fitted on the earlier training period, calibration methods are fitted on the latest slice of the training period, and final metrics are measured only on the held-out future test period.

## Results

| Method | Accuracy | Log Loss | Brier | ECE |
| --- | ---: | ---: | ---: | ---: |
| raw | 0.4841 | 1.0592 | 0.6355 | 0.0546 |
| sigmoid | 0.4748 | 1.0495 | 0.6323 | 0.0431 |
| isotonic | 0.4785 | 1.0644 | 0.6401 | 0.0668 |
| temperature_1.18 | 0.4841 | 1.0498 | 0.6303 | 0.0447 |

## Decision

- Best method by log loss: `sigmoid`.
- Deployed calibrated probability layer: Yes.
- Raw log loss/Brier: 1.0592 / 0.6355.
- Best log loss/Brier: 1.0495 / 0.6323.

A calibrator is saved only if it improves out-of-sample log loss or Brier score. If not, raw model probabilities remain the honest production output.

## Class-Level Note

Draw probabilities remain the most difficult class to calibrate because draws are both less frequent and less separable from narrow home/away outcomes.
