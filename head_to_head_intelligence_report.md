# Head-to-Head Intelligence Report

## Validation Setup

All models use strict time-based validation. No random split is used.

- Train period: 2019-08-09 to 2024-04-04
- Test period: 2024-04-06 to 2025-05-25

## Model Comparison

| model_version | accuracy | log_loss | Brier_score | calibration_score | expected_calibration_error | draw_log_loss | draw_recall | draw_calibration_error |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| model_a_current_production | 0.5142 | 0.9946 | 0.5946 | 0.0499 | 0.0499 | 1.5185 | 0.0374 | 0.0191 |
| model_b_core_h2h | 0.4967 | 1.0007 | 0.5987 | 0.0519 | 0.0519 | 1.4674 | 0.0374 | 0.0049 |
| model_c_recent_h2h | 0.4923 | 0.9987 | 0.5972 | 0.0578 | 0.0578 | 1.4747 | 0.0187 | 0.0079 |
| model_d_venue_h2h | 0.5164 | 1.0043 | 0.6012 | 0.0589 | 0.0589 | 1.4653 | 0.0374 | 0.0023 |
| model_e_all_h2h | 0.4967 | 0.9996 | 0.5983 | 0.0541 | 0.0541 | 1.4663 | 0.0561 | 0.0041 |

## 1. Do head-to-head features improve prediction quality?

Best model by log loss: `model_a_current_production`.

Model E vs Model A:

- Log loss change: 0.0050
- Brier score change: 0.0037
- Calibration change: 0.0042
- ECE change: 0.0042

Production decision: Keep H2H research-only for now.

## 2. Which H2H features matter most?

Top H2H SHAP features:

- `h2h_last_3_xg_diff` (h2h_recent): 0.0727
- `h2h_matches_count` (h2h_core): 0.0519
- `h2h_last_5_xg_diff` (h2h_recent): 0.0460
- `h2h_last_5_goal_diff` (h2h_recent): 0.0226
- `h2h_home_venue_xg_diff` (h2h_venue): 0.0215
- `h2h_points_home_team` (h2h_core): 0.0184
- `h2h_last_3_goal_diff` (h2h_recent): 0.0144
- `h2h_points_away_team` (h2h_core): 0.0134
- `h2h_draws` (h2h_core): 0.0132
- `h2h_last_5_points_home_team` (h2h_recent): 0.0112
- `h2h_home_venue_points` (h2h_venue): 0.0108
- `h2h_last_3_points_home` (h2h_recent): 0.0082

SHAP contribution by group:

| feature_group | mean_abs_shap |
| --- | --- |
| xG | 0.3712 |
| tactical_pressure | 0.2105 |
| h2h_recent | 0.1752 |
| baseline | 0.1208 |
| h2h_core | 0.1088 |
| fatigue | 0.0755 |
| h2h_venue | 0.0365 |

## 3. Do venue-specific H2H features help?

Model D vs Model B:

- Log loss change: 0.0037
- Brier score change: 0.0025
- Calibration change: 0.0069

Venue-specific H2H should only move forward if it improves log loss or Brier without worsening calibration.

## 4. Do H2H features improve draw prediction?

Model E vs Model A draw metrics:

- Draw log loss change: -0.0522
- Draw recall change: 0.0187
- Draw calibration error change: -0.0150

## 5. Are H2H features useful after controlling for xG and form?

The baseline already includes form, xG, xGA, xG differential, home advantage, schedule/fatigue and available shots-based tactical pressure. H2H only counts as genuine new signal if it improves Model A on out-of-sample log loss or Brier score and has non-zero SHAP contribution.

## Leakage Controls

Head-to-head features are generated chronologically. For every fixture, only previous meetings between the two teams are visible. Recent windows use the last 3 and last 5 historical meetings. Venue features use only prior meetings where the current home team was also at home. `h2h_data_strength_score` is 0.0 for no meetings, 0.25 for 1-2 meetings, 0.60 for 3-5 meetings and 1.0 for 6+ meetings.
