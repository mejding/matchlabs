# Manager Consistency Report

## Question

Does manager consistency improve the Premier League prediction model beyond form, xG, fatigue, tactical pressure and Elo?

## Model Comparison

| model_version | accuracy | log_loss | Brier_score | expected_calibration_error | draw_recall | draw_log_loss |
| --- | --- | --- | --- | --- | --- | --- |
| model_a_current_production | 0.4860 | 1.0633 | 0.6369 | 0.0592 | 0.0219 | 0.5901 |
| model_b_basic_manager | 0.4766 | 1.0679 | 0.6404 | 0.0684 | 0.0438 | 0.5928 |
| model_c_manager_continuity | 0.4729 | 1.0672 | 0.6401 | 0.0695 | 0.0365 | 0.5923 |
| model_d_full_manager_intelligence | 0.4822 | 1.0689 | 0.6410 | 0.0602 | 0.0365 | 0.5954 |

## Full Manager Model vs Production

- Log loss change: 0.0056
- Brier score change: 0.0041
- ECE change: 0.0010
- Draw recall change: 0.0146
- Draw log loss change: 0.0052

## Manager Feature Signal

Top manager SHAP features:

- `away_manager_tenure_days` (manager_continuity): 0.0445
- `away_manager_elo_change_since_appointment` (manager_performance): 0.0365
- `manager_xg_diff_gap` (manager_performance): 0.0091
- `home_manager_team_form_since_appointment` (manager_performance): 0.0074
- `home_manager_tenure_days` (manager_continuity): 0.0073
- `home_manager_xg_diff_before_match` (manager_performance): 0.0067
- `manager_ppg_gap` (manager_performance): 0.0048
- `home_manager_elo_change_since_appointment` (manager_performance): 0.0038
- `away_manager_xg_diff_before_match` (manager_performance): 0.0032
- `home_manager_points_per_game_before_match` (manager_change): 0.0024
- `home_manager_matches_in_charge` (manager_continuity): 0.0014
- `away_manager_points_per_game_before_match` (manager_change): 0.0012

## Interpretation

The experiment is conservative: manager identity for the current fixture is used, but manager performance and continuity statistics are calculated only from prior matches. The current local data covers 2024/25 only, so this is a first evidence check rather than a final production decision.

## Production Decision

Do not activate manager consistency yet. The current test has only one full season of manager rows, and production activation requires out-of-sample log loss or Brier improvement without calibration damage.
