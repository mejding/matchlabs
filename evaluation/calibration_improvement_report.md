# Calibration Improvement Report

Validation uses a strict chronological split. The model is fitted on the earlier training period, calibration methods are fitted on the latest slice of the training period, and final metrics are measured only on the held-out future test period.

## Results

| Method | Accuracy | Log Loss | Brier | ECE |
| --- | ---: | ---: | ---: | ---: |
| raw | 0.4617 | 1.0626 | 0.6398 | 0.0535 |
| sigmoid | 0.4617 | 1.0667 | 0.6436 | 0.0588 |
| isotonic | 0.4599 | 1.2484 | 0.6498 | 0.0657 |
| temperature_1.07 | 0.4617 | 1.0592 | 0.6378 | 0.0500 |

## Decision

- Best method by log loss: `temperature_1.07`.
- Deployed calibrated probability layer: Yes.
- Raw log loss/Brier: 1.0626 / 0.6398.
- Best log loss/Brier: 1.0592 / 0.6378.

A calibrator is saved only if it improves out-of-sample log loss or Brier score. If not, raw model probabilities remain the honest production output.

## Class-Level Note

Draw probabilities remain the most difficult class to calibrate because draws are both less frequent and less separable from narrow home/away outcomes.
