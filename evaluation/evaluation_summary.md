# Football Model Evaluation

## Validation Setup

The evaluation uses a strict time-based split. No random train/test split is used.

- Training dates: 2019-08-09 to 2025-02-27
- Test dates: 2025-03-08 to 2026-10-12
- Train rows: 2171
- Test rows: 549

## Metrics

- Accuracy: 0.4627
- Multiclass log loss: 1.0760
- Multiclass Brier score: 0.6475
- Calibration error: 0.0627
- Expected Calibration Error: 0.0627

## Calibration

- `home_win`: reasonably calibrated
- `draw`: underconfident / underpredicted
- `away_win`: overconfident / overpredicted

Negative signed calibration error means the model is generally overpredicting that class. Positive signed calibration error means it is underpredicting that class.

## Confidence Intervals

Bootstrap interval example for `Wolves vs Everton`:

- `home_win`: mean 0.531, 95% CI 0.367-0.669
- `draw`: mean 0.179, 95% CI 0.113-0.306
- `away_win`: mean 0.289, 95% CI 0.180-0.479

Confidence label: Medium confidence

Uncertainty explanation: Moderate model disagreement; widest interval is for home_win.

Mean bootstrap standard deviation across the test set: 0.0641

Mean prediction stability score: 0.6439

## Feature Contributions

Top SHAP features:

- `home_shots_avg_season`: 0.0783
- `away_elo`: 0.0736
- `home_shots_on_target_avg_season`: 0.0613
- `away_shots_on_target_avg_season`: 0.0563
- `away_xga_avg`: 0.0552
- `home_xg_diff`: 0.0478
- `away_xg_diff`: 0.0422
- `away_goals_scored_avg`: 0.0410

The feature importance CSV files compare gain importance, permutation importance, and SHAP importance. Features with low or zero values across all three are candidates for removal or better data.

## Weak Spots

The weakest actual class by log loss is `draw` with actual-class log loss 1.5414.

The most overconfident confidence bin has mean confidence 0.7350, accuracy 0.5714, and 28 matches.

Inspect `evaluation/worst_predictions.csv` for the specific highest-loss predictions.
