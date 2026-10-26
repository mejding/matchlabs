# Football Model Evaluation

## Validation Setup

The evaluation uses a strict time-based split. No random train/test split is used.

- Training dates: 2019-08-09 to 2025-04-01
- Test dates: 2025-04-02 to 2026-10-25
- Train rows: 2192
- Test rows: 548

## Metrics

- Accuracy: 0.4544
- Multiclass log loss: 1.0637
- Multiclass Brier score: 0.6408
- Calibration error: 0.0594
- Expected Calibration Error: 0.0594

## Calibration

- `home_win`: reasonably calibrated
- `draw`: underconfident / underpredicted
- `away_win`: overconfident / overpredicted

Negative signed calibration error means the model is generally overpredicting that class. Positive signed calibration error means it is underpredicting that class.

## Confidence Intervals

Bootstrap interval example for `Liverpool vs Everton`:

- `home_win`: mean 0.788, 95% CI 0.629-0.889
- `draw`: mean 0.128, 95% CI 0.054-0.261
- `away_win`: mean 0.084, 95% CI 0.042-0.149

Confidence label: Medium confidence

Uncertainty explanation: Moderate model disagreement; widest interval is for home_win.

Mean bootstrap standard deviation across the test set: 0.0623

Mean prediction stability score: 0.6540

## Feature Contributions

Top SHAP features:

- `home_shots_avg_season`: 0.0923
- `away_shots_on_target_avg_season`: 0.0671
- `away_xga_avg`: 0.0624
- `home_shots_on_target_avg_season`: 0.0593
- `home_xg_diff`: 0.0471
- `away_xg_diff`: 0.0447
- `elo_recent_change`: 0.0382
- `home_team_points_last_5`: 0.0356

The feature importance CSV files compare gain importance, permutation importance, and SHAP importance. Features with low or zero values across all three are candidates for removal or better data.

## Weak Spots

The weakest actual class by log loss is `draw` with actual-class log loss 1.4962.

The most overconfident confidence bin has mean confidence 0.8453, accuracy 0.6000, and 5 matches.

Inspect `evaluation/worst_predictions.csv` for the specific highest-loss predictions.
