# Calibration Improvement Report

Validation uses a strict chronological split. The model is fitted on the earlier training period, calibration methods are fitted on the latest slice of the training period, and final metrics are measured only on the held-out future test period.

## Results

| Method | Accuracy | Log Loss | Brier | ECE |
| --- | ---: | ---: | ---: | ---: |
| raw | 0.4661 | 1.0801 | 0.6482 | 0.0643 |
| sigmoid | 0.4661 | 1.0719 | 0.6461 | 0.0580 |
| isotonic | 0.4697 | 1.3721 | 0.6488 | 0.0696 |
| temperature_1.12 | 0.4661 | 1.0705 | 0.6430 | 0.0584 |

## Decision

- Best method by log loss: `temperature_1.12`.
- Deployed calibrated probability layer: Yes.
- Raw log loss/Brier: 1.0801 / 0.6482.
- Best log loss/Brier: 1.0705 / 0.6430.

A calibrator is saved only if it improves out-of-sample log loss or Brier score. If not, raw model probabilities remain the honest production output.

## Class-Level Note

Draw probabilities remain the most difficult class to calibrate because draws are both less frequent and less separable from narrow home/away outcomes.
