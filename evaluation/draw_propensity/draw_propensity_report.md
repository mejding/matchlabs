# Draw Propensity Experiment

## Goal

Test whether pre-match signals for tight, low-event or draw-prone fixtures improve probability quality, especially draw calibration.

## Model Comparison

| model_version | accuracy | log_loss | Brier_score | expected_calibration_error | draw_recall | mean_draw_probability | actual_draw_rate | draw_log_loss | double_chance_hit_rate |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| model_a_current_production_sigmoid | 0.4740 | 1.0556 | 0.6349 | 0.0447 | 0.0210 | 0.2631 | 0.2658 | 0.5940 | 0.7156 |
| model_b_draw_primary_sigmoid | 0.4591 | 1.0568 | 0.6352 | 0.0508 | 0.0350 | 0.2658 | 0.2658 | 0.5967 | 0.7342 |
| model_c_draw_full_sigmoid | 0.4535 | 1.0594 | 0.6383 | 0.0494 | 0.0210 | 0.2631 | 0.2658 | 0.5945 | 0.7268 |
| model_a_current_production_raw | 0.4740 | 1.0595 | 0.6338 | 0.0509 | 0.0210 | 0.2262 | 0.2658 | 0.6055 | 0.7398 |
| model_b_draw_primary_raw | 0.4684 | 1.0613 | 0.6360 | 0.0581 | 0.0070 | 0.2239 | 0.2658 | 0.6053 | 0.7472 |
| model_c_draw_full_raw | 0.4721 | 1.0626 | 0.6370 | 0.0604 | 0.0140 | 0.2224 | 0.2658 | 0.6074 | 0.7472 |

## Best Draw Candidate

- Candidate: `model_b_draw_primary_sigmoid`
- Log Loss delta vs production: `0.0012`
- Brier delta vs production: `0.0003`
- ECE delta vs production: `0.0061`
- Draw log loss delta vs production: `0.0027`
- Double chance hit-rate delta vs production: `0.0186`

## Draw Feature Importance

No draw features had positive gain importance.

## Draw Feature Permutation Importance

| feature | permutation_importance_log_loss | permutation_importance_std |
| --- | --- | --- |
| form_points_similarity | 0.0010 | 0.0009 |
| team_strength_similarity | 0.0003 | 0.0005 |
| xg_diff_similarity | 0.0000 | 0.0000 |
| combined_draw_rate_last10 | -0.0005 | 0.0006 |
| low_total_goals_profile | -0.0013 | 0.0011 |
| draw_propensity_score | -0.0015 | 0.0010 |
| low_total_xg_profile | -0.0026 | 0.0006 |

## Decision

Do not promote draw-propensity features to production on this run.

Promotion rule: improve out-of-sample Log Loss, avoid Brier deterioration, and avoid material ECE deterioration. Accuracy alone is not enough.
