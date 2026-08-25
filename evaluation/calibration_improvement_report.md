# Calibration Improvement Report

Validation uses a strict chronological split. The model is fitted on the earlier training period, calibration methods are fitted on the latest slice of the training period, and final metrics are measured only on the held-out future test period.

## Results

| Method | Accuracy | Log Loss | Brier | ECE |
| --- | ---: | ---: | ---: | ---: |
| raw | 0.4598 | 1.0570 | 0.6335 | 0.0624 |
| sigmoid | 0.4710 | 1.0363 | 0.6250 | 0.0418 |
| isotonic | 0.4804 | 1.0371 | 0.6265 | 0.0557 |
| temperature_1.27 | 0.4598 | 1.0456 | 0.6275 | 0.0553 |

## Decision

- Best method by log loss: `sigmoid`.
- Deployed calibrated probability layer: Yes.
- Raw log loss/Brier: 1.0570 / 0.6335.
- Best log loss/Brier: 1.0363 / 0.6250.

A calibrator is saved only if it improves out-of-sample log loss or Brier score. If not, raw model probabilities remain the honest production output.

## Class-Level Note

Draw probabilities remain the most difficult class to calibrate because draws are both less frequent and less separable from narrow home/away outcomes.
