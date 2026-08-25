# Calibration Improvement Report

Validation uses a strict chronological split. The model is fitted on the earlier training period, calibration methods are fitted on the latest slice of the training period, and final metrics are measured only on the held-out future test period.

## Results

| Method | Accuracy | Log Loss | Brier | ECE |
| --- | ---: | ---: | ---: | ---: |
| raw | 0.4673 | 1.0617 | 0.6364 | 0.0570 |
| sigmoid | 0.4766 | 1.0391 | 0.6268 | 0.0458 |
| isotonic | 0.4654 | 1.2345 | 0.6383 | 0.0602 |
| temperature_1.25 | 0.4673 | 1.0500 | 0.6303 | 0.0471 |

## Decision

- Best method by log loss: `sigmoid`.
- Deployed calibrated probability layer: Yes.
- Raw log loss/Brier: 1.0617 / 0.6364.
- Best log loss/Brier: 1.0391 / 0.6268.

A calibrator is saved only if it improves out-of-sample log loss or Brier score. If not, raw model probabilities remain the honest production output.

## Class-Level Note

Draw probabilities remain the most difficult class to calibrate because draws are both less frequent and less separable from narrow home/away outcomes.
