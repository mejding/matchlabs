# Football Model Evaluation

## Validation Setup

The evaluation uses a strict time-based split. No random train/test split is used.

- Training dates: 2019-08-09 to 2025-04-06
- Test dates: 2025-04-07 to 2026-11-08
- Train rows: 2208
- Test rows: 552

## Metrics

- Accuracy: 0.4801
- Multiclass log loss: 1.0529
- Multiclass Brier score: 0.6315
- Calibration error: 0.0419
- Expected Calibration Error: 0.0419

## Calibration

- `home_win`: reasonably calibrated
- `draw`: underconfident / underpredicted
- `away_win`: overconfident / overpredicted

Negative signed calibration error means the model is generally overpredicting that class. Positive signed calibration error means it is underpredicting that class.

## Confidence Intervals

Bootstrap interval example for `Leicester vs Newcastle`:

- `home_win`: mean 0.222, 95% CI 0.100-0.344
- `draw`: mean 0.198, 95% CI 0.074-0.349
- `away_win`: mean 0.579, 95% CI 0.400-0.795

Confidence label: Medium confidence

Uncertainty explanation: Moderate model disagreement; widest interval is for away_win.

Mean bootstrap standard deviation across the test set: 0.0636

Mean prediction stability score: 0.6468

## Feature Contributions

Top SHAP features:

- `home_shots_avg_season`: 0.0830
- `away_shots_on_target_avg_season`: 0.0661
- `home_shots_on_target_avg_season`: 0.0622
- `away_xga_avg`: 0.0536
- `home_team_points_last_5`: 0.0465
- `away_xg_diff`: 0.0461
- `home_xg_diff`: 0.0447
- `away_goals_scored_avg`: 0.0432

The feature importance CSV files compare gain importance, permutation importance, and SHAP importance. Features with low or zero values across all three are candidates for removal or better data.

## Weak Spots

The weakest actual class by log loss is `draw` with actual-class log loss 1.5037.

The most overconfident confidence bin has mean confidence 0.8134, accuracy 0.5000, and 2 matches.

Inspect `evaluation/worst_predictions.csv` for the specific highest-loss predictions.
