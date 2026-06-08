# Manager Redundancy Report

## Summary

Manager features are tested against a production baseline that already contains rolling form, xG/xGA, fatigue, tactical pressure and Elo. They should only be considered unique if the combined model improves out-of-sample log loss or Brier score.

## SHAP Group Importance

| feature_group | mean_abs_shap |
| --- | --- |
| production | 0.9474 |
| manager_continuity | 0.1102 |
| manager_performance | 0.0471 |
| manager_change | 0.0117 |

## Redundancy Decision

Do not activate manager consistency yet. The current test has manager rows for 760 matches across seasons 2324, 2425, and production activation requires out-of-sample log loss or Brier improvement without calibration damage.
