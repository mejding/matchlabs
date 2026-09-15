# Football Model Evaluation

## Validation Setup

The evaluation uses a strict time-based split. No random train/test split is used.

- Training dates: 2019-08-09 to 2025-02-22
- Test dates: 2025-02-23 to 2026-09-14
- Train rows: 2159
- Test rows: 541

## Metrics

- Accuracy: 0.4898
- Multiclass log loss: 1.0614
- Multiclass Brier score: 0.6367
- Calibration error: 0.0514
- Expected Calibration Error: 0.0514

## Calibration

- `home_win`: reasonably calibrated
- `draw`: underconfident / underpredicted
- `away_win`: overconfident / overpredicted

Negative signed calibration error means the model is generally overpredicting that class. Positive signed calibration error means it is underpredicting that class.

## Confidence Intervals

Bootstrap interval example for `Man City vs Liverpool`:

- `home_win`: mean 0.604, 95% CI 0.479-0.756
- `draw`: mean 0.161, 95% CI 0.093-0.220
- `away_win`: mean 0.234, 95% CI 0.134-0.363

Confidence label: Medium confidence

Uncertainty explanation: Moderate model disagreement; widest interval is for home_win.

Mean bootstrap standard deviation across the test set: 0.0640

Mean prediction stability score: 0.6446

## Feature Contributions

Top SHAP features:

- `away_shots_on_target_avg_season`: 0.0826
- `home_shots_avg_season`: 0.0817
- `home_elo`: 0.0632
- `away_xga_avg`: 0.0599
- `home_shots_on_target_avg_season`: 0.0582
- `home_xg_diff`: 0.0510
- `away_xg_diff`: 0.0427
- `home_team_points_last_5`: 0.0412

The feature importance CSV files compare gain importance, permutation importance, and SHAP importance. Features with low or zero values across all three are candidates for removal or better data.

## Weak Spots

The weakest actual class by log loss is `draw` with actual-class log loss 1.5386.

The most overconfident confidence bin has mean confidence 0.7305, accuracy 0.5926, and 27 matches.

Inspect `evaluation/worst_predictions.csv` for the specific highest-loss predictions.
