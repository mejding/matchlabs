# Sprint 4G: Recency-Weighted Form and xG Evaluation

## Goal

Determine whether recent matches should receive greater weight than older matches inside rolling form, xG/xGA and shot-volume windows.

## Model Comparison

| model_version | accuracy | log_loss | Brier_score | expected_calibration_error | draw_recall | draw_log_loss |
| --- | --- | --- | --- | --- | --- | --- |
| model_a_current_production | 0.4879 | 1.0438 | 0.6264 | 0.0429 | 0.0365 | 0.5803 |
| model_hybrid_all_weighted | 0.4822 | 1.0439 | 0.6258 | 0.0473 | 0.0219 | 0.5785 |
| model_hybrid_raw_plus_halflife5 | 0.4692 | 1.0483 | 0.6287 | 0.0495 | 0.0000 | 0.5828 |
| model_hybrid_raw_plus_halflife3 | 0.4785 | 1.0484 | 0.6281 | 0.0546 | 0.0219 | 0.5829 |
| model_hybrid_raw_plus_linear | 0.4748 | 1.0487 | 0.6288 | 0.0487 | 0.0073 | 0.5830 |
| model_hybrid_raw_plus_exponential | 0.4785 | 1.0487 | 0.6283 | 0.0474 | 0.0146 | 0.5839 |
| model_replace_halflife5 | 0.4467 | 1.0703 | 0.6452 | 0.0340 | 0.0000 | 0.5774 |
| model_replace_halflife3 | 0.4505 | 1.0733 | 0.6475 | 0.0383 | 0.0219 | 0.5777 |
| model_replace_exponential | 0.4486 | 1.0747 | 0.6483 | 0.0416 | 0.0000 | 0.5800 |
| model_replace_linear | 0.4411 | 1.0777 | 0.6503 | 0.0408 | 0.0146 | 0.5787 |

## Best Model

- Best model by Log Loss: `model_a_current_production`
- Log Loss delta vs production: 0.0000
- Brier delta vs production: 0.0000
- ECE delta vs production: 0.0000

## SHAP

SHAP was run on the best non-production recency model: `model_hybrid_all_weighted`.

Top weighted feature signals:

- `away_goals_scored_weighted_exponential` (weighted_exponential): 0.0203
- `home_goals_scored_weighted_exponential` (weighted_exponential): 0.0179
- `away_xga_weighted_halflife3` (weighted_halflife3): 0.0165
- `home_goals_scored_weighted_linear` (weighted_linear): 0.0162
- `home_xga_weighted_halflife5` (weighted_halflife5): 0.0161
- `away_shots_on_target_weighted_halflife3` (weighted_halflife3): 0.0141
- `home_goals_scored_weighted_halflife3` (weighted_halflife3): 0.0137
- `home_defense_rating_weighted_halflife5` (weighted_halflife5): 0.0133
- `away_shots_on_target_weighted_halflife5` (weighted_halflife5): 0.0123
- `home_attack_rating_weighted_linear` (weighted_linear): 0.0122
- `home_points_weighted_halflife5` (weighted_halflife5): 0.0121
- `home_defense_rating_weighted_exponential` (weighted_exponential): 0.0115
- `away_attack_rating_weighted_linear` (weighted_linear): 0.0114
- `away_defense_rating_weighted_linear` (weighted_linear): 0.0095
- `home_shots_on_target_weighted_exponential` (weighted_exponential): 0.0082

Feature group SHAP importance:

| feature_group | mean_abs_shap |
| --- | --- |
| raw_rolling | 0.5808 |
| elo | 0.1339 |
| weighted_halflife5 | 0.1278 |
| weighted_exponential | 0.1138 |
| weighted_linear | 0.1116 |
| weighted_halflife3 | 0.0873 |
| fatigue | 0.0468 |
| other_production | 0.0000 |

## Correlation and Redundancy

Average absolute correlation between raw and weighted counterparts: 0.5149.

High correlation means weighted features mostly describe the same information. Lower correlation means they may react differently to form changes.

## Remove-One Tests

Remove-one tests were run on `model_hybrid_all_weighted`.

| test | removed_count | log_loss | Brier_score | expected_calibration_error | draw_recall | draw_log_loss |
| --- | --- | --- | --- | --- | --- | --- |
| full_best_reference | 0 | 1.0439 | 0.6258 | 0.0473 | 0.0219 | 0.5785 |
| remove_weighted_points | 8 | 1.0481 | 0.6287 | 0.0566 | 0.0146 | 0.5807 |
| remove_weighted_goals | 8 | 1.0473 | 0.6292 | 0.0540 | 0.0146 | 0.5795 |
| remove_weighted_xg | 24 | 1.0489 | 0.6286 | 0.0466 | 0.0292 | 0.5820 |
| remove_weighted_shots | 16 | 1.0474 | 0.6280 | 0.0509 | 0.0146 | 0.5794 |
| remove_weighted_ratings | 16 | 1.0472 | 0.6278 | 0.0479 | 0.0365 | 0.5821 |

Best recency model delta vs production:

- Log Loss delta: 0.0001
- Brier delta: -0.0006
- ECE delta: 0.0045

## Answers

1. Does recency weighting improve the model?

   No, not enough to justify production on this split.

2. Which weighting scheme performs best?

   `model_a_current_production`.

3. Does recency weighting improve draw prediction?

   Compare `draw_recall` and `draw_log_loss` above. Production promotion requires no material deterioration.

4. Does recency weighting improve calibration?

   Best-model ECE delta vs production: 0.0000.

5. Can weighted features replace existing rolling averages?

   Replacement is only acceptable if a replace-model beats production on Log Loss or Brier without worsening calibration. The table above is the evidence.

6. Recommended production configuration:

   Do not move recency weighting into production. Keep current equal-weight rolling features.

Production optimization priority: Log Loss, Brier Score, Calibration/ECE. Accuracy is secondary.
