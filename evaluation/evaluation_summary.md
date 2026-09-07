# Football Model Evaluation

## Validation Setup

The evaluation uses a strict time-based split. No random train/test split is used.

- Training dates: 2019-08-09 to 2025-02-21
- Test dates: 2025-02-22 to 2026-09-06
- Train rows: 2152
- Test rows: 538

## Metrics

- Accuracy: 0.4796
- Multiclass log loss: 1.0598
- Multiclass Brier score: 0.6344
- Calibration error: 0.0481
- Expected Calibration Error: 0.0481

## Calibration

- `home_win`: reasonably calibrated
- `draw`: underconfident / underpredicted
- `away_win`: overconfident / overpredicted

Negative signed calibration error means the model is generally overpredicting that class. Positive signed calibration error means it is underpredicting that class.

## Confidence Intervals

Bootstrap interval example for `Everton vs Man United`:

- `home_win`: mean 0.436, 95% CI 0.223-0.680
- `draw`: mean 0.140, 95% CI 0.073-0.225
- `away_win`: mean 0.424, 95% CI 0.206-0.622

Confidence label: Low confidence

Uncertainty explanation: High model disagreement; widest interval is for home_win.

Mean bootstrap standard deviation across the test set: 0.0633

Mean prediction stability score: 0.6481

## Feature Contributions

Top SHAP features:

- `home_shots_avg_season`: 0.0859
- `away_shots_on_target_avg_season`: 0.0654
- `away_xga_avg`: 0.0578
- `home_shots_on_target_avg_season`: 0.0552
- `home_xg_diff`: 0.0491
- `away_elo`: 0.0429
- `away_xg_diff`: 0.0417
- `elo_difference`: 0.0369

The feature importance CSV files compare gain importance, permutation importance, and SHAP importance. Features with low or zero values across all three are candidates for removal or better data.

## Weak Spots

The weakest actual class by log loss is `draw` with actual-class log loss 1.5619.

The most overconfident confidence bin has mean confidence 0.7394, accuracy 0.6071, and 28 matches.

Inspect `evaluation/worst_predictions.csv` for the specific highest-loss predictions.
