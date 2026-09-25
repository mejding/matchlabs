# Football Model Evaluation

## Validation Setup

The evaluation uses a strict time-based split. No random train/test split is used.

- Training dates: 2019-08-09 to 2025-02-25
- Test dates: 2025-02-26 to 2026-09-20
- Train rows: 2165
- Test rows: 545

## Metrics

- Accuracy: 0.4716
- Multiclass log loss: 1.0632
- Multiclass Brier score: 0.6389
- Calibration error: 0.0668
- Expected Calibration Error: 0.0668

## Calibration

- `home_win`: reasonably calibrated
- `draw`: underconfident / underpredicted
- `away_win`: overconfident / overpredicted

Negative signed calibration error means the model is generally overpredicting that class. Positive signed calibration error means it is underpredicting that class.

## Confidence Intervals

Bootstrap interval example for `Liverpool vs Newcastle`:

- `home_win`: mean 0.807, 95% CI 0.667-0.903
- `draw`: mean 0.110, 95% CI 0.049-0.213
- `away_win`: mean 0.084, 95% CI 0.041-0.126

Confidence label: Medium confidence

Uncertainty explanation: Moderate model disagreement; widest interval is for home_win.

Mean bootstrap standard deviation across the test set: 0.0625

Mean prediction stability score: 0.6528

## Feature Contributions

Top SHAP features:

- `home_shots_avg_season`: 0.0801
- `away_shots_on_target_avg_season`: 0.0788
- `home_shots_on_target_avg_season`: 0.0597
- `home_elo`: 0.0594
- `away_xga_avg`: 0.0581
- `away_elo`: 0.0479
- `home_xg_diff`: 0.0449
- `away_xg_diff`: 0.0417

The feature importance CSV files compare gain importance, permutation importance, and SHAP importance. Features with low or zero values across all three are candidates for removal or better data.

## Weak Spots

The weakest actual class by log loss is `draw` with actual-class log loss 1.5558.

The most overconfident confidence bin has mean confidence 0.8327, accuracy 0.6000, and 10 matches.

Inspect `evaluation/worst_predictions.csv` for the specific highest-loss predictions.
