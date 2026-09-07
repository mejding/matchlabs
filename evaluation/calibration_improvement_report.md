# Calibration Improvement Report

Validation uses a strict chronological split. The model is fitted on the earlier training period, calibration methods are fitted on the latest slice of the training period, and final metrics are measured only on the held-out future test period.

## Results

| Method | Accuracy | Log Loss | Brier | ECE |
| --- | ---: | ---: | ---: | ---: |
| raw | 0.4851 | 1.0729 | 0.6414 | 0.0577 |
| sigmoid | 0.4796 | 1.0582 | 0.6362 | 0.0514 |
| isotonic | 0.4703 | 1.3246 | 0.6498 | 0.0604 |
| temperature_1.25 | 0.4851 | 1.0589 | 0.6346 | 0.0358 |

## Decision

- Best method by log loss: `sigmoid`.
- Deployed calibrated probability layer: Yes.
- Raw log loss/Brier: 1.0729 / 0.6414.
- Best log loss/Brier: 1.0582 / 0.6362.

A calibrator is saved only if it improves out-of-sample log loss or Brier score. If not, raw model probabilities remain the honest production output.

## Class-Level Note

Draw probabilities remain the most difficult class to calibrate because draws are both less frequent and less separable from narrow home/away outcomes.
