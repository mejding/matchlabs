# Football Model Evaluation

## Validation Setup

The evaluation uses a strict time-based split. No random train/test split is used.

- Training dates: 2019-08-09 to 2025-02-01
- Test dates: 2025-02-02 to 2026-08-24
- Train rows: 2135
- Test rows: 535

## Metrics

- Accuracy: 0.4692
- Multiclass log loss: 1.0459
- Multiclass Brier score: 0.6277
- Calibration error: 0.0537
- Expected Calibration Error: 0.0537

## Calibration

- `home_win`: reasonably calibrated
- `draw`: underconfident / underpredicted
- `away_win`: overconfident / overpredicted

Negative signed calibration error means the model is generally overpredicting that class. Positive signed calibration error means it is underpredicting that class.

## Confidence Intervals

Bootstrap interval example for `Brentford vs Tottenham`:

- `home_win`: mean 0.555, 95% CI 0.313-0.682
- `draw`: mean 0.153, 95% CI 0.077-0.296
- `away_win`: mean 0.292, 95% CI 0.150-0.494

Confidence label: Medium confidence

Uncertainty explanation: Moderate model disagreement; widest interval is for home_win.

Mean bootstrap standard deviation across the test set: 0.0646

Mean prediction stability score: 0.6410

## Feature Contributions

Top SHAP features:

- `away_shots_on_target_avg_season`: 0.0752
- `home_elo`: 0.0600
- `home_shots_avg_season`: 0.0582
- `away_xg_diff`: 0.0572
- `home_xg_diff`: 0.0560
- `home_shots_on_target_avg_season`: 0.0484
- `away_shots_avg_last10`: 0.0479
- `away_xga_avg`: 0.0478

The feature importance CSV files compare gain importance, permutation importance, and SHAP importance. Features with low or zero values across all three are candidates for removal or better data.

## Weak Spots

The weakest actual class by log loss is `draw` with actual-class log loss 1.5224.

The most overconfident confidence bin has mean confidence 0.8314, accuracy 0.2500, and 4 matches.

Inspect `evaluation/worst_predictions.csv` for the specific highest-loss predictions.
