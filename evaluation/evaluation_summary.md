# Football Model Evaluation

## Validation Setup

The evaluation uses a strict time-based split. No random train/test split is used.

- Training dates: 2019-08-09 to 2025-03-10
- Test dates: 2025-03-15 to 2026-10-19
- Train rows: 2181
- Test rows: 549

## Metrics

- Accuracy: 0.4681
- Multiclass log loss: 1.0678
- Multiclass Brier score: 0.6412
- Calibration error: 0.0574
- Expected Calibration Error: 0.0574

## Calibration

- `home_win`: reasonably calibrated
- `draw`: underconfident / underpredicted
- `away_win`: overconfident / overpredicted

Negative signed calibration error means the model is generally overpredicting that class. Positive signed calibration error means it is underpredicting that class.

## Confidence Intervals

Bootstrap interval example for `Bournemouth vs Brentford`:

- `home_win`: mean 0.355, 95% CI 0.233-0.474
- `draw`: mean 0.251, 95% CI 0.162-0.410
- `away_win`: mean 0.394, 95% CI 0.290-0.569

Confidence label: Medium confidence

Uncertainty explanation: Moderate model disagreement; widest interval is for away_win.

Mean bootstrap standard deviation across the test set: 0.0612

Mean prediction stability score: 0.6602

## Feature Contributions

Top SHAP features:

- `home_shots_avg_season`: 0.0832
- `away_shots_on_target_avg_season`: 0.0677
- `away_xga_avg`: 0.0585
- `home_xg_diff`: 0.0537
- `home_shots_on_target_avg_season`: 0.0520
- `home_elo`: 0.0490
- `away_xg_diff`: 0.0453
- `elo_recent_change`: 0.0450

The feature importance CSV files compare gain importance, permutation importance, and SHAP importance. Features with low or zero values across all three are candidates for removal or better data.

## Weak Spots

The weakest actual class by log loss is `draw` with actual-class log loss 1.5584.

The most overconfident confidence bin has mean confidence 0.7441, accuracy 0.5000, and 28 matches.

Inspect `evaluation/worst_predictions.csv` for the specific highest-loss predictions.
