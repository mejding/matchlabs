# Manager Redundancy Report

## Summary

Manager features are tested against a production baseline that already contains rolling form, xG/xGA, fatigue, tactical pressure and Elo. They should only be considered unique if the combined model improves out-of-sample log loss or Brier score.

## SHAP Group Importance

| feature_group | mean_abs_shap |
| --- | --- |
| production | 0.8774 |
| manager_performance | 0.0719 |
| manager_continuity | 0.0542 |
| manager_change | 0.0037 |

## Redundancy Decision

Do not activate manager consistency yet. The current test has only one full season of manager rows, and production activation requires out-of-sample log loss or Brier improvement without calibration damage.
