# Calibration Improvement Report

Validation uses a strict chronological split. The model is fitted on the earlier training period, calibration methods are fitted on the latest slice of the training period, and final metrics are measured only on the held-out future test period.

## Results

| Method | Accuracy | Log Loss | Brier | ECE |
| --- | ---: | ---: | ---: | ---: |
| raw | 0.4766 | 1.0683 | 0.6411 | 0.0642 |
| sigmoid | 0.4673 | 1.0557 | 0.6362 | 0.0471 |
| isotonic | 0.4673 | 1.2655 | 0.6534 | 0.0688 |
| temperature_1.15 | 0.4766 | 1.0583 | 0.6359 | 0.0402 |

## Decision

- Best method by log loss: `sigmoid`.
- Deployed calibrated probability layer: Yes.
- Raw log loss/Brier: 1.0683 / 0.6411.
- Best log loss/Brier: 1.0557 / 0.6362.

A calibrator is saved only if it improves out-of-sample log loss or Brier score. If not, raw model probabilities remain the honest production output.

## Class-Level Note

Draw probabilities remain the most difficult class to calibrate because draws are both less frequent and less separable from narrow home/away outcomes.
