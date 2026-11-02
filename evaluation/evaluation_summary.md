# Football Model Evaluation

## Validation Setup

The evaluation uses a strict time-based split. No random train/test split is used.

- Training dates: 2019-08-09 to 2025-04-03
- Test dates: 2025-04-05 to 2026-11-01
- Train rows: 2199
- Test rows: 550

## Metrics

- Accuracy: 0.4527
- Multiclass log loss: 1.0639
- Multiclass Brier score: 0.6397
- Calibration error: 0.0529
- Expected Calibration Error: 0.0529

## Calibration

- `home_win`: reasonably calibrated
- `draw`: underconfident / underpredicted
- `away_win`: overconfident / overpredicted

Negative signed calibration error means the model is generally overpredicting that class. Positive signed calibration error means it is underpredicting that class.

## Confidence Intervals

Bootstrap interval example for `Aston Villa vs Nott'm Forest`:

- `home_win`: mean 0.545, 95% CI 0.437-0.687
- `draw`: mean 0.255, 95% CI 0.159-0.357
- `away_win`: mean 0.200, 95% CI 0.123-0.271

Confidence label: Medium confidence

Uncertainty explanation: Moderate model disagreement; widest interval is for home_win.

Mean bootstrap standard deviation across the test set: 0.0647

Mean prediction stability score: 0.6408

## Feature Contributions

Top SHAP features:

- `home_shots_avg_season`: 0.0886
- `away_xga_avg`: 0.0649
- `away_shots_on_target_avg_season`: 0.0623
- `elo_ratio`: 0.0562
- `home_shots_on_target_avg_season`: 0.0542
- `elo_recent_change`: 0.0527
- `away_xg_diff`: 0.0445
- `elo_difference`: 0.0401

The feature importance CSV files compare gain importance, permutation importance, and SHAP importance. Features with low or zero values across all three are candidates for removal or better data.

## Weak Spots

The weakest actual class by log loss is `draw` with actual-class log loss 1.5044.

The most overconfident confidence bin has mean confidence 0.8099, accuracy 0.5000, and 2 matches.

Inspect `evaluation/worst_predictions.csv` for the specific highest-loss predictions.
