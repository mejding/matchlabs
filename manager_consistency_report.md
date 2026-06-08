# Manager Consistency Report

## Question

Does manager consistency improve the Premier League prediction model beyond form, xG, fatigue, tactical pressure and Elo?

## Model Comparison

| model_version | accuracy | log_loss | Brier_score | expected_calibration_error | draw_recall | draw_log_loss |
| --- | --- | --- | --- | --- | --- | --- |
| model_a_current_production | 0.4860 | 1.0488 | 0.6295 | 0.0528 | 0.0000 | 0.5844 |
| model_b_basic_manager | 0.4860 | 1.0608 | 0.6357 | 0.0645 | 0.0073 | 0.5969 |
| model_c_manager_continuity | 0.4841 | 1.0618 | 0.6359 | 0.0679 | 0.0073 | 0.5993 |
| model_d_full_manager_intelligence | 0.4804 | 1.0598 | 0.6343 | 0.0695 | 0.0073 | 0.5998 |

## Full Manager Model vs Production

- Log loss change: 0.0110
- Brier score change: 0.0048
- ECE change: 0.0168
- Draw recall change: 0.0073
- Draw log loss change: 0.0154

## Manager Feature Signal

Top manager SHAP features:

- `away_manager_tenure_days` (manager_continuity): 0.0749
- `away_manager_elo_change_since_appointment` (manager_performance): 0.0184
- `manager_continuity_gap` (manager_continuity): 0.0153
- `manager_experience_gap` (manager_continuity): 0.0079
- `manager_ppg_gap` (manager_performance): 0.0072
- `away_manager_points_per_game_before_match` (manager_change): 0.0066
- `away_manager_matches_in_charge` (manager_continuity): 0.0065
- `manager_xg_diff_gap` (manager_performance): 0.0064
- `home_manager_elo_change_since_appointment` (manager_performance): 0.0052
- `away_manager_xg_diff_before_match` (manager_performance): 0.0037
- `home_manager_points_per_game_before_match` (manager_change): 0.0037
- `home_manager_xg_diff_before_match` (manager_performance): 0.0037

## Interpretation

The experiment is conservative: manager identity for the current fixture is used, but manager performance and continuity statistics are calculated only from prior matches. The current local manager cache covers 760 matches across seasons 2324, 2425, so this is broader than the first one-season check but still not full-project coverage.

## Production Decision

Do not activate manager consistency yet. The current test has manager rows for 760 matches across seasons 2324, 2425, and production activation requires out-of-sample log loss or Brier improvement without calibration damage.
