# Football Model Evaluation

## Validation Setup

The evaluation uses a strict time-based split. No random train/test split is used.

- Training dates: 2019-08-09 to 2025-02-14
- Test dates: 2025-02-15 to 2026-08-31
- Train rows: 2141
- Test rows: 539

## Metrics

- Accuracy: 0.4861
- Multiclass log loss: 1.0470
- Multiclass Brier score: 0.6269
- Calibration error: 0.0598
- Expected Calibration Error: 0.0598

## Calibration

- `home_win`: reasonably calibrated
- `draw`: underconfident / underpredicted
- `away_win`: overconfident / overpredicted

Negative signed calibration error means the model is generally overpredicting that class. Positive signed calibration error means it is underpredicting that class.

## Confidence Intervals

Bootstrap interval example for `Crystal Palace vs Everton`:

- `home_win`: mean 0.454, 95% CI 0.299-0.636
- `draw`: mean 0.215, 95% CI 0.133-0.335
- `away_win`: mean 0.331, 95% CI 0.238-0.447

Confidence label: Medium confidence

Uncertainty explanation: Moderate model disagreement; widest interval is for home_win.

Mean bootstrap standard deviation across the test set: 0.0638

Mean prediction stability score: 0.6457

## Feature Contributions

Top SHAP features:

- `home_shots_avg_season`: 0.0747
- `away_shots_on_target_avg_season`: 0.0649
- `home_elo`: 0.0590
- `away_xga_avg`: 0.0551
- `away_elo`: 0.0550
- `home_shots_on_target_avg_season`: 0.0544
- `home_xg_diff`: 0.0491
- `away_xg_diff`: 0.0398

The feature importance CSV files compare gain importance, permutation importance, and SHAP importance. Features with low or zero values across all three are candidates for removal or better data.

## Weak Spots

The weakest actual class by log loss is `draw` with actual-class log loss 1.5851.

The most overconfident confidence bin has mean confidence 0.8456, accuracy 0.6250, and 8 matches.

Inspect `evaluation/worst_predictions.csv` for the specific highest-loss predictions.
