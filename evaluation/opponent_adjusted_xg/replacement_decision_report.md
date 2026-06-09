# Sprint 4E: Replacement Decision Report

## Goal

Determine whether opponent-adjusted ratings should be added on top of raw xG, replace raw xG, or remain research-only.

## Model Comparison

| model_version | accuracy | log_loss | Brier_score | expected_calibration_error | draw_recall | draw_log_loss |
| --- | --- | --- | --- | --- | --- | --- |
| model_a_current_production | 0.4879 | 1.0438 | 0.6264 | 0.0429 | 0.0365 | 0.5803 |
| model_b_no_raw_xg_plus_ratings | 0.4673 | 1.0442 | 0.6280 | 0.0467 | 0.0219 | 0.5805 |
| model_c_no_xg_diff_plus_ratings | 0.4748 | 1.0401 | 0.6239 | 0.0413 | 0.0219 | 0.5811 |
| model_d_production_plus_ratings | 0.4710 | 1.0417 | 0.6256 | 0.0415 | 0.0292 | 0.5809 |
| model_e_no_xg_xga_avgs_plus_ratings | 0.4617 | 1.0450 | 0.6287 | 0.0463 | 0.0292 | 0.5798 |
| model_f_ratings_only_xg_representation | 0.4673 | 1.0442 | 0.6280 | 0.0467 | 0.0219 | 0.5805 |

## Correlation Summary

| raw_xg_feature | opponent_adjusted_feature | pearson_correlation | absolute_correlation |
| --- | --- | --- | --- |
| away_xg_avg | away_xg_attack_rating | 0.4213 | 0.4213 |
| home_xg_avg | home_xg_attack_rating | 0.3916 | 0.3916 |
| home_xga_avg | home_xg_defense_rating | 0.3701 | 0.3701 |
| away_xga_avg | away_xg_defense_rating | 0.3558 | 0.3558 |
| away_xg_diff | attack_defense_matchup_score | -0.3276 | 0.3276 |
| home_xg_diff | attack_defense_matchup_score | 0.2999 | 0.2999 |

Average absolute correlation across inspected pairs: 0.3610.

## SHAP Summary

- Raw xG-family SHAP total in best comparison model: 0.1813
- Opponent-adjusted rating SHAP total in best comparison model: 0.2497

## Answers

1. Are opponent-adjusted ratings mostly redundant with raw xG? Not strongly by simple pairwise correlation, based on pairwise correlations and overlapping SHAP signal.

2. Can attack/defense ratings replace xG averages? No. The best tested model kept xG averages active.

3. Can attack/defense ratings replace xGA averages? No. The best tested model kept xGA averages active.

4. Can attack/defense ratings replace xG differential? Yes as a candidate: Model C improved Log Loss, Brier and ECE versus production.

5. Best Log Loss: `model_c_no_xg_diff_plus_ratings` at 1.0401.

6. Best Brier Score: `model_c_no_xg_diff_plus_ratings` at 0.6239.

7. Best draw performance by draw log loss: `model_e_no_xg_xga_avgs_plus_ratings` at 0.5798.

8. Recommended production configuration: CASE 1 variant: ratings should not replace all raw xG, but they may replace xG differential. Best tested setup keeps xG/xGA averages, removes xG-diff columns, and adds opponent-adjusted ratings.

Important caution: Model C lowers Log Loss/Brier/ECE, but accuracy and draw recall fall. Treat it as a production candidate only after confirming on additional rolling splits.

## Decision Framework Result

CASE 1 variant: ratings should not replace all raw xG, but they may replace xG differential. Best tested setup keeps xG/xGA averages, removes xG-diff columns, and adds opponent-adjusted ratings.

Production optimization priority remains: Log Loss, Brier Score, Calibration/ECE. Accuracy is secondary.