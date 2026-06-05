# Venue-Specific Features Report

## Model Comparison

| model_name | accuracy | log_loss | brier_score | calibration_score | ece | train_period | test_period |
| --- | --- | --- | --- | --- | --- | --- | --- |
| current_model | 0.4822 | 1.0572 | 0.6366 | 0.0475 | 0.0475 | 2019-08-09 to 2025-01-25 | 2025-01-26 to 2026-05-24 |
| current_model_plus_venue_specific | 0.4542 | 1.0623 | 0.6392 | 0.0447 | 0.0447 | 2019-08-09 to 2025-01-25 | 2025-01-26 to 2026-05-24 |

Metric deltas, venue model minus current model:

- Accuracy: -0.0280
- Log loss: 0.0051
- Brier score: 0.0025
- Calibration score: -0.0027
- ECE: -0.0027

Lower is better for log loss, Brier score, calibration score and ECE.

## SHAP

Top venue-specific features:

| feature | mean_abs_shap |
| --- | --- |
| home_xg_last_5_home_matches | 0.1131 |
| away_xg_last_5_away_matches | 0.0756 |
| away_xga_last_5_away_matches | 0.0436 |
| home_xga_last_5_home_matches | 0.0374 |
| home_goal_diff_home_matches | 0.0296 |
| away_goal_diff_away_matches | 0.0187 |
| away_points_last_5_away_matches | 0.0178 |
| home_points_last_5_home_matches | 0.0167 |

Venue feature group total SHAP: 0.3524  
Home venue feature SHAP total: 0.1968  
Away venue feature SHAP total: 0.1557

## 1. Do venue-specific features improve prediction quality?

Answer: No. The venue-specific feature set does not improve both out-of-sample log loss and Brier score in this run.

## 2. Which venue-specific features matter most?

Answer: The highest-ranked venue-specific SHAP features are listed above. These are the only venue-specific signals with measurable contribution in this experiment.

## 3. Are away-performance features particularly important?

Answer: No. Away venue features do not dominate home venue features in total SHAP contribution in this run.

## 4. Should venue-specific features move into production?

Answer: No. Keep them research-only until they improve out-of-sample log loss and Brier score robustly.

## Artifacts

- `evaluation/venue_specific_features/model_comparison.csv`
- `evaluation/venue_specific_features/model_comparison.png`
- `evaluation/venue_specific_features/shap_feature_rankings.csv`
- `evaluation/venue_specific_features/shap_group_rankings.csv`
- `evaluation/venue_specific_features/shap_feature_rankings.png`
- `evaluation/venue_specific_features/shap_summary.png`
- `evaluation/venue_specific_features/gain_importance.csv`
- `evaluation/venue_specific_features/gain_importance.png`
