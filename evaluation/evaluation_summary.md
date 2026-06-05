# Football Model Evaluation

## Validation Setup

The evaluation uses a strict time-based split. No random train/test split is used.

- Training dates: 2019-08-09 to 2024-04-04
- Test dates: 2024-04-06 to 2025-05-25
- Train rows: 1823
- Test rows: 457

## Metrics

- Accuracy: 0.5142
- Multiclass log loss: 1.0112
- Multiclass Brier score: 0.6047
- Calibration error: 0.0421
- Expected Calibration Error: 0.0421

## Calibration

- `home_win`: overconfident / overpredicted
- `draw`: reasonably calibrated
- `away_win`: underconfident / underpredicted

Negative signed calibration error means the model is generally overpredicting that class. Positive signed calibration error means it is underpredicting that class.

## Confidence Intervals

Bootstrap interval example for `Crystal Palace vs Man City`:

- `home_win`: mean 0.328, 95% CI 0.210-0.460
- `draw`: mean 0.170, 95% CI 0.110-0.240
- `away_win`: mean 0.502, 95% CI 0.386-0.621

Confidence label: Medium confidence

Uncertainty explanation: Moderate model disagreement; widest interval is for home_win.

Mean bootstrap standard deviation across the test set: 0.0668

Mean prediction stability score: 0.6288

## Feature Contributions

Top SHAP features:

- `home_xg_diff`: 0.1119
- `away_xg_diff`: 0.1011
- `away_xg_avg`: 0.0841
- `home_team_points_last_5`: 0.0715
- `home_xg_avg`: 0.0697
- `away_xga_avg`: 0.0633
- `home_xga_avg`: 0.0588
- `away_goals_scored_avg`: 0.0368

The feature importance CSV files compare gain importance, permutation importance, and SHAP importance. Features with low or zero values across all three are candidates for removal or better data.

## Weak Spots

The weakest actual class by log loss is `draw` with actual-class log loss 1.5429.

The most overconfident confidence bin has mean confidence 0.8282, accuracy 0.6000, and 15 matches.

Inspect `evaluation/worst_predictions.csv` for the specific highest-loss predictions.
