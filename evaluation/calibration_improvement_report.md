# Calibration Improvement Report

Validation uses a strict chronological split. The model is fitted on the earlier training period, calibration methods are fitted on the latest slice of the training period, and final metrics are measured only on the held-out future test period.

## Results

| Method | Accuracy | Log Loss | Brier | ECE |
| --- | ---: | ---: | ---: | ---: |
| raw | 0.4861 | 1.0776 | 0.6444 | 0.0629 |
| sigmoid | 0.4880 | 1.0544 | 0.6352 | 0.0488 |
| isotonic | 0.4824 | 1.2386 | 0.6408 | 0.0569 |
| temperature_1.23 | 0.4861 | 1.0635 | 0.6377 | 0.0465 |

## Decision

- Best method by log loss: `sigmoid`.
- Deployed calibrated probability layer: Yes.
- Raw log loss/Brier: 1.0776 / 0.6444.
- Best log loss/Brier: 1.0544 / 0.6352.

A calibrator is saved only if it improves out-of-sample log loss or Brier score. If not, raw model probabilities remain the honest production output.

## Class-Level Note

Draw probabilities remain the most difficult class to calibrate because draws are both less frequent and less separable from narrow home/away outcomes.
