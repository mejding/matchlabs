# Elo Rating Layer Evaluation

## Best Elo Configuration

Best Elo config: `k30_ha75_nomov`.

| elo_config | accuracy | log_loss | brier_score | calibration_score | ece |
| --- | --- | --- | --- | --- | --- |
| k30_ha75_nomov | 0.4542 | 1.0776 | 0.6498 | 0.0471 | 0.0471 |
| k30_ha100_nomov | 0.4598 | 1.0778 | 0.6509 | 0.0501 | 0.0501 |
| k30_ha100_mov | 0.4654 | 1.0800 | 0.6513 | 0.0480 | 0.0480 |
| k40_ha75_mov | 0.4449 | 1.0817 | 0.6509 | 0.0416 | 0.0416 |
| k30_ha50_mov | 0.4598 | 1.0819 | 0.6513 | 0.0480 | 0.0480 |
| k40_ha100_nomov | 0.4505 | 1.0823 | 0.6524 | 0.0506 | 0.0506 |
| k30_ha75_mov | 0.4654 | 1.0825 | 0.6520 | 0.0433 | 0.0433 |
| k30_ha50_nomov | 0.4561 | 1.0827 | 0.6525 | 0.0453 | 0.0453 |

## Model Comparison

| model_name | accuracy | log_loss | brier_score | calibration_score | ece | train_period | test_period |
| --- | --- | --- | --- | --- | --- | --- | --- |
| current_production_model | 0.4822 | 1.0572 | 0.6366 | 0.0475 | 0.0475 | 2019-08-09 to 2025-01-25 | 2025-01-26 to 2026-05-24 |
| elo_only_model | 0.4542 | 1.0776 | 0.6498 | 0.0471 | 0.0471 | 2019-08-09 to 2025-01-25 | 2025-01-26 to 2026-05-24 |
| current_model_plus_elo | 0.4822 | 1.0520 | 0.6327 | 0.0479 | 0.0479 | 2019-08-09 to 2025-01-25 | 2025-01-26 to 2026-05-24 |
| current_model_plus_elo_calibrated | 0.4822 | 1.1353 | 0.6736 | 0.1206 | 0.1206 | 2019-08-09 to 2025-01-25 | 2025-01-26 to 2026-05-24 |

Current + Elo deltas versus current model:

- Log loss: -0.0052
- Brier score: -0.0039
- Calibration score: 0.0005
- ECE: 0.0005

Calibrated current + Elo deltas versus current model:

- Log loss: 0.0781
- Brier score: 0.0370
- Calibration score: 0.0731
- ECE: 0.0731

## Draw Analysis

| model_name | draw_recall | draw_precision | draw_log_loss | draw_calibration_error |
| --- | --- | --- | --- | --- |
| current_production_model | 0.0292 | 0.5000 | 1.5062 | 0.0555 |
| elo_only_model | 0.0292 | 0.4000 | 1.5467 | 0.0412 |
| current_model_plus_elo | 0.0219 | 0.5000 | 1.5237 | 0.0534 |
| current_model_plus_elo_calibrated | 0.0219 | 0.5000 | 1.9176 | 0.1147 |

## Redundancy Tests

Remove-one comparison:

| model_name | accuracy | log_loss | brier_score | calibration_score | ece | log_loss_delta_vs_full | brier_delta_vs_full |
| --- | --- | --- | --- | --- | --- | --- | --- |
| current_model_plus_elo | 0.4822 | 1.0520 | 0.6327 | 0.0479 | 0.0479 | 0.0000 | 0.0000 |
| full_minus_elo | 0.4822 | 1.0572 | 0.6366 | 0.0475 | 0.0475 | 0.0052 | 0.0039 |
| full_minus_current | 0.4542 | 1.0776 | 0.6498 | 0.0471 | 0.0471 | 0.0256 | 0.0171 |

Elo correlation with current features:

| elo_feature | mean_abs_corr_with_current | max_abs_corr_with_current | most_correlated_current_feature |
| --- | --- | --- | --- |
| away_elo_trend | 0.0641 | 0.3470 | away_team_points_last_5 |
| away_elo | 0.1010 | 0.3468 | away_team_points_last_5 |
| home_elo_trend | 0.0699 | 0.3246 | home_team_points_last_5 |
| home_elo | 0.1028 | 0.3237 | home_xg_avg |
| elo_ratio | 0.1386 | 0.2731 | away_team_points_last_5 |
| elo_difference | 0.1390 | 0.2723 | away_team_points_last_5 |
| elo_recent_change | 0.0930 | 0.2693 | away_team_points_last_5 |
| rolling_elo_form | 0.0930 | 0.2693 | away_team_points_last_5 |
| elo_gap_bucket | 0.1353 | 0.2690 | away_team_points_last_5 |

Number of Elo features with max correlation >= 0.70 against current features: `0`.

## SHAP and Permutation

SHAP group importance:

| feature_group | mean_abs_shap |
| --- | --- |
| Current model | 0.5797 |
| Elo | 0.2793 |

Permutation group importance:

| feature_group | permutation_importance |
| --- | --- |
| Current model | 0.0349 |
| Elo | 0.0075 |

Top Elo SHAP features:

| feature | mean_abs_shap |
| --- | --- |
| elo_recent_change | 0.0606 |
| home_elo | 0.0570 |
| home_elo_trend | 0.0411 |
| elo_difference | 0.0397 |
| away_elo | 0.0342 |
| elo_ratio | 0.0276 |
| away_elo_trend | 0.0192 |
| elo_gap_bucket | 0.0000 |

## Answers

### 1. Does Elo improve prediction quality?

Answer: Yes, Elo meets the success criteria in this run.

### 2. Which Elo feature matters most?

Answer: `elo_recent_change` has the highest SHAP contribution among Elo features.

### 3. Does Elo improve draw prediction?

Draw recall delta: -0.0073  
Draw log loss delta: 0.0175

Answer: No, Elo does not improve draw prediction in this run.

### 4. Does Elo add unique information beyond xG and form?

Elo SHAP total: 0.2793  
Current feature SHAP total: 0.5797

Answer: Some, because Elo has measurable SHAP/permutation contribution and low-to-moderate correlation with current features.

### 5. Does Elo improve calibration?

Answer: No, combined Elo does not improve calibration score before calibration.

### 6. Should Elo move into production?

Answer: Yes, as a production candidate, subject to one more backtest after the next data refresh.

### 7. What is the expected production benefit?

Expected benefit is the out-of-sample delta shown above. Do not extrapolate beyond that; if deltas are tiny, the practical production benefit is likely small.

## Artifacts

- `data/elo_history.csv`
- `evaluation/elo/elo_parameter_search.csv`
- `evaluation/elo/model_comparison.csv`
- `evaluation/elo/draw_analysis.csv`
- `evaluation/elo/elo_correlation_summary.csv`
- `evaluation/elo/remove_one_results.csv`
- `evaluation/elo/shap_feature_rankings.csv`
- `evaluation/elo/shap_group_importance.csv`
- `evaluation/elo/permutation_feature_importance.csv`
- `evaluation/elo/permutation_group_importance.csv`
- `evaluation/elo/model_comparison.png`
- `evaluation/elo/shap_summary.png`
