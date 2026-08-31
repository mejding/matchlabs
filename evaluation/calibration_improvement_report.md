# Calibration Improvement Report

Validation uses a strict chronological split. The model is fitted on the earlier training period, calibration methods are fitted on the latest slice of the training period, and final metrics are measured only on the held-out future test period.

## Results

| Method | Accuracy | Log Loss | Brier | ECE |
| --- | ---: | ---: | ---: | ---: |
| raw | 0.4842 | 1.0541 | 0.6313 | 0.0628 |
| sigmoid | 0.4675 | 1.0395 | 0.6260 | 0.0474 |
| isotonic | 0.4657 | 1.2842 | 0.6315 | 0.0575 |
| temperature_1.27 | 0.4842 | 1.0429 | 0.6256 | 0.0523 |

## Decision

- Best method by log loss: `sigmoid`.
- Deployed calibrated probability layer: Yes.
- Raw log loss/Brier: 1.0541 / 0.6313.
- Best log loss/Brier: 1.0395 / 0.6260.

A calibrator is saved only if it improves out-of-sample log loss or Brier score. If not, raw model probabilities remain the honest production output.

## Class-Level Note

Draw probabilities remain the most difficult class to calibrate because draws are both less frequent and less separable from narrow home/away outcomes.
