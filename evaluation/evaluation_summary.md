# Football Model Evaluation

## Validation Setup

The evaluation uses a strict time-based split. No random train/test split is used.

- Training dates: 2019-08-09 to 2025-01-25
- Test dates: 2025-01-26 to 2026-05-24
- Train rows: 2125
- Test rows: 535

## Metrics

- Accuracy: 0.4822
- Multiclass log loss: 1.0453
- Multiclass Brier score: 0.6273
- Calibration error: 0.0475
- Expected Calibration Error: 0.0475

## Calibration

- `home_win`: reasonably calibrated
- `draw`: underconfident / underpredicted
- `away_win`: overconfident / overpredicted

Negative signed calibration error means the model is generally overpredicting that class. Positive signed calibration error means it is underpredicting that class.

## Confidence Intervals

Bootstrap interval example for `Crystal Palace vs Brentford`:

- `home_win`: mean 0.536, 95% CI 0.430-0.618
- `draw`: mean 0.239, 95% CI 0.162-0.329
- `away_win`: mean 0.225, 95% CI 0.155-0.287

Confidence label: Medium confidence

Uncertainty explanation: Moderate model disagreement; widest interval is for home_win.

Mean bootstrap standard deviation across the test set: 0.0637

Mean prediction stability score: 0.6459

## Feature Contributions

Top SHAP features:

- `home_shots_avg_season`: 0.0674
- `away_shots_on_target_avg_season`: 0.0661
- `home_xg_diff`: 0.0611
- `away_xga_avg`: 0.0571
- `home_shots_on_target_avg_season`: 0.0508
- `away_shots_avg_last10`: 0.0508
- `away_xg_diff`: 0.0456
- `home_elo`: 0.0454

The feature importance CSV files compare gain importance, permutation importance, and SHAP importance. Features with low or zero values across all three are candidates for removal or better data.

## Weak Spots

The weakest actual class by log loss is `draw` with actual-class log loss 1.5066.

The most overconfident confidence bin has mean confidence 0.6410, accuracy 0.5644, and 101 matches.

Inspect `evaluation/worst_predictions.csv` for the specific highest-loss predictions.
