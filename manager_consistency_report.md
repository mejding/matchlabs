# Manager Consistency Report

## Question

Does manager consistency improve the Premier League prediction model beyond form, xG, fatigue, tactical pressure and Elo?

## Model Comparison

| model_version | accuracy | log_loss | Brier_score | expected_calibration_error | draw_recall | draw_log_loss |
| --- | --- | --- | --- | --- | --- | --- |
| model_a_current_production | 0.4870 | 1.0580 | 0.6331 | 0.0494 | 0.0000 | 0.6072 |
| model_b_basic_manager | 0.4907 | 1.0648 | 0.6363 | 0.0594 | 0.0140 | 0.6126 |
| model_c_manager_continuity | 0.4833 | 1.0660 | 0.6372 | 0.0640 | 0.0070 | 0.6124 |
| model_d_full_manager_intelligence | 0.4888 | 1.0655 | 0.6371 | 0.0648 | 0.0070 | 0.6126 |

## Full Manager Model vs Production

- Log loss change: 0.0074
- Brier score change: 0.0040
- ECE change: 0.0155
- Draw recall change: 0.0070
- Draw log loss change: 0.0054

## Manager Feature Signal

Top manager SHAP features:

- `away_manager_tenure_days` (manager_continuity): 0.0483
- `home_manager_elo_change_since_appointment` (manager_performance): 0.0109
- `manager_ppg_gap` (manager_performance): 0.0086
- `home_manager_team_form_since_appointment` (manager_performance): 0.0081
- `manager_continuity_gap` (manager_continuity): 0.0060
- `home_manager_points_per_game_before_match` (manager_change): 0.0060
- `home_manager_xg_diff_before_match` (manager_performance): 0.0050
- `home_manager_matches_in_charge` (manager_continuity): 0.0049
- `home_manager_tenure_days` (manager_continuity): 0.0042
- `manager_experience_gap` (manager_continuity): 0.0036
- `away_manager_points_per_game_before_match` (manager_change): 0.0029
- `manager_xg_diff_gap` (manager_performance): 0.0029

## New Manager Segment Test

This checks whether manager features help specifically in the short post-change window, instead of judging them only across all fixtures.

| model_version | segment | matches | accuracy | log_loss | Brier_score | expected_calibration_error |
| --- | --- | --- | --- | --- | --- | --- |
| model_a_current_production | all_test_matches | 538.0000 | 0.4870 | 1.0580 | 0.6331 | 0.0494 |
| model_a_current_production | any_new_manager_first_5 | 5.0000 | 0.6000 | 1.0574 | 0.6503 | 0.3012 |
| model_a_current_production | any_new_manager_first_10 | 18.0000 | 0.5000 | 1.1241 | 0.6659 | 0.2157 |
| model_a_current_production | no_new_manager_first_10 | 520.0000 | 0.4865 | 1.0558 | 0.6320 | 0.0507 |
| model_b_basic_manager | all_test_matches | 538.0000 | 0.4907 | 1.0648 | 0.6363 | 0.0594 |
| model_b_basic_manager | any_new_manager_first_5 | 5.0000 | 0.6000 | 1.2299 | 0.7244 | 0.3420 |
| model_b_basic_manager | any_new_manager_first_10 | 18.0000 | 0.5556 | 1.1401 | 0.6673 | 0.1840 |
| model_b_basic_manager | no_new_manager_first_10 | 520.0000 | 0.4885 | 1.0621 | 0.6352 | 0.0603 |
| model_c_manager_continuity | all_test_matches | 538.0000 | 0.4833 | 1.0660 | 0.6372 | 0.0640 |
| model_c_manager_continuity | any_new_manager_first_5 | 5.0000 | 0.4000 | 1.2589 | 0.7414 | 0.3480 |
| model_c_manager_continuity | any_new_manager_first_10 | 18.0000 | 0.4444 | 1.1660 | 0.6809 | 0.1773 |
| model_c_manager_continuity | no_new_manager_first_10 | 520.0000 | 0.4846 | 1.0625 | 0.6357 | 0.0640 |
| model_d_full_manager_intelligence | all_test_matches | 538.0000 | 0.4888 | 1.0655 | 0.6371 | 0.0648 |
| model_d_full_manager_intelligence | any_new_manager_first_5 | 5.0000 | 0.6000 | 1.2802 | 0.7534 | 0.3751 |
| model_d_full_manager_intelligence | any_new_manager_first_10 | 18.0000 | 0.5000 | 1.1405 | 0.6699 | 0.1996 |
| model_d_full_manager_intelligence | no_new_manager_first_10 | 520.0000 | 0.4885 | 1.0629 | 0.6360 | 0.0650 |

## Interpretation

The experiment is conservative: manager identity for the current fixture is used, but manager performance and continuity statistics are calculated only from prior matches. The current local manager cache covers 760 matches across seasons 2324, 2425, so this is broader than the first one-season check but still not full-project coverage.

## Production Decision

Do not activate manager consistency yet. The current test has manager rows for 760 matches across seasons 2324, 2425, and production activation requires out-of-sample log loss or Brier improvement without calibration damage.
