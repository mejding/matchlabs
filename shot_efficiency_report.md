# Shot Efficiency Feature Evaluation

## Goal

Test whether shot volume, shot accuracy, finishing efficiency and defensive shot prevention improve the Premier League prediction model beyond the current production baseline.

## Data

Shot features use football-data.co.uk `HS`, `AS`, `HST`, and `AST` columns plus goals and Understat xG. Every feature is calculated chronologically from matches before kickoff. Rolling windows: last 5, last 10, and current season.

## Model Comparison

| model_version | accuracy | log_loss | Brier_score | expected_calibration_error | draw_recall | draw_log_loss |
| --- | --- | --- | --- | --- | --- | --- |
| model_a_current_production | 0.4860 | 1.0633 | 0.6369 | 0.0592 | 0.0219 | 0.5901 |
| model_b_shot_volume | 0.4766 | 1.0521 | 0.6309 | 0.0563 | 0.0219 | 0.5823 |
| model_c_shot_efficiency | 0.4710 | 1.0596 | 0.6358 | 0.0442 | 0.0073 | 0.5884 |
| model_d_defensive_shot_prevention | 0.4822 | 1.0574 | 0.6383 | 0.0571 | 0.0219 | 0.5776 |
| model_e_all_shot_features | 0.4673 | 1.0561 | 0.6365 | 0.0441 | 0.0000 | 0.5825 |

## Full Shot Model vs Production

- Log loss change: -0.0073
- Brier score change: -0.0004
- ECE change: -0.0151
- Draw recall change: -0.0219
- Draw log loss change: -0.0076

## Best Candidate

- Best log-loss model: `model_b_shot_volume`
- Best candidate log loss delta vs production: -0.0113
- Best candidate Brier delta vs production: -0.0060
- Best candidate ECE delta vs production: -0.0029
- Best Brier model: `model_b_shot_volume`

## SHAP Signal

Top shot SHAP features:

- `away_shot_accuracy_last10` (shot_efficiency): 0.0305
- `away_xga_per_shot_allowed_last5` (defensive_shot_prevention): 0.0280
- `home_xga_per_shot_allowed_last10` (defensive_shot_prevention): 0.0256
- `away_xga_per_shot_allowed_last10` (defensive_shot_prevention): 0.0251
- `away_goals_minus_xg_season` (shot_efficiency): 0.0219
- `away_opponent_shot_accuracy_last5` (defensive_shot_prevention): 0.0218
- `home_shot_accuracy_last10` (shot_efficiency): 0.0190
- `home_xga_per_shot_allowed_last5` (defensive_shot_prevention): 0.0173
- `home_opponent_shot_accuracy_season` (defensive_shot_prevention): 0.0172
- `away_opponent_shot_accuracy_season` (defensive_shot_prevention): 0.0165
- `away_xg_per_shot_last10` (shot_efficiency): 0.0161
- `away_shots_allowed_avg_season` (defensive_shot_prevention): 0.0154
- `away_shot_accuracy_season` (shot_efficiency): 0.0138
- `away_goals_minus_xg_last10` (shot_efficiency): 0.0130
- `home_shots_allowed_avg_last10` (defensive_shot_prevention): 0.0121

SHAP group totals:

| feature_group | mean_abs_shap |
| --- | --- |
| production | 0.6476 |
| shot_efficiency | 0.2685 |
| defensive_shot_prevention | 0.2440 |
| shot_volume | 0.0570 |

## Remove-One Tests

| test | log_loss | Brier_score | expected_calibration_error |
| --- | --- | --- | --- |
| full_all_shot_features_reference | 1.0561 | 0.6365 | 0.0441 |
| remove_shot_volume | 1.0599 | 0.6391 | 0.0566 |
| remove_shot_efficiency | 1.0523 | 0.6350 | 0.0480 |
| remove_defensive_shot_prevention | 1.0561 | 0.6342 | 0.0531 |
| remove_goals_minus_xg | 1.0542 | 0.6349 | 0.0483 |

## Special Analysis

1. Finishing efficiency features are only useful if they improve out-of-sample log loss/Brier. In this run, the dedicated shot-efficiency model improves calibration but is weaker than shot volume on log loss and Brier.
2. `goals_minus_xg` total SHAP contribution: 0.0566. Remove-one tests improve when `goals_minus_xg` is removed, so it should remain research-only for now.
3. Shot features overlap with xG/xGA and the existing tactical pressure proxy, so redundancy is expected.
4. Draw prediction only improves if draw log loss falls and draw recall rises together.
5. Full model status: The full all-shot model improves the baseline, but it is not the best candidate.

## Production Decision

Move shot volume features forward as a production candidate. Do not activate all shot efficiency features yet, because the simpler shot-volume model has the best out-of-sample log loss and Brier score.
