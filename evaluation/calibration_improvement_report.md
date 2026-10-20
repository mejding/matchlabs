# Calibration Improvement Report

Validation uses a strict chronological split. The model is fitted on the earlier training period, calibration methods are fitted on the latest slice of the training period, and final metrics are measured only on the held-out future test period.

## Results

| Method | Accuracy | Log Loss | Brier | ECE |
| --- | ---: | ---: | ---: | ---: |
| raw | 0.4736 | 1.0769 | 0.6467 | 0.0643 |
| sigmoid | 0.4718 | 1.0619 | 0.6409 | 0.0605 |
| isotonic | 0.4536 | 1.0800 | 0.6503 | 0.0699 |
| temperature_1.18 | 0.4736 | 1.0651 | 0.6401 | 0.0521 |

## Decision

- Best method by log loss: `sigmoid`.
- Deployed calibrated probability layer: Yes.
- Raw log loss/Brier: 1.0769 / 0.6467.
- Best log loss/Brier: 1.0619 / 0.6409.

A calibrator is saved only if it improves out-of-sample log loss or Brier score. If not, raw model probabilities remain the honest production output.

## Class-Level Note

Draw probabilities remain the most difficult class to calibrate because draws are both less frequent and less separable from narrow home/away outcomes.
