# SHAP Replacement Report

This report compares the predictive contribution of raw xG/xGA/xG-differential features against opponent-adjusted attack/defense ratings.

## Group Importance

| feature_group | mean_abs_shap |
| --- | --- |
| shot_volume | 0.3354 |
| elo | 0.1447 |
| defense_ratings | 0.1410 |
| attack_ratings | 0.1087 |
| raw_xga | 0.1032 |
| raw_xg | 0.0781 |
| form_home_advantage | 0.0772 |
| fatigue | 0.0557 |

## Top xG-Representation Features

| feature | mean_abs_shap | feature_group |
| --- | --- | --- |
| away_xga_avg | 0.0690 | raw_xga |
| away_xg_avg | 0.0422 | raw_xg |
| home_xg_avg | 0.0359 | raw_xg |
| home_xga_avg | 0.0342 | raw_xga |
| home_xg_defense_rating_season | 0.0335 | defense_ratings |
| away_xg_defense_rating_last10 | 0.0214 | defense_ratings |
| home_xg_defense_rating | 0.0187 | defense_ratings |
| away_xg_attack_rating_season | 0.0184 | attack_ratings |
| away_xg_defense_rating_season | 0.0173 | defense_ratings |
| away_xg_defense_rating | 0.0168 | defense_ratings |
| home_xg_attack_rating_season | 0.0147 | attack_ratings |
| home_xg_defense_rating_last10 | 0.0141 | defense_ratings |
| away_attack_vs_home_defense | 0.0125 | attack_ratings |
| away_xg_attack_rating | 0.0121 | attack_ratings |
| away_xg_defense_rating_last5 | 0.0116 | defense_ratings |
| attack_defense_matchup_score | 0.0107 | attack_ratings |
| home_attack_vs_away_defense | 0.0099 | attack_ratings |
| home_xg_attack_rating_last5 | 0.0092 | attack_ratings |
| home_xg_defense_rating_last5 | 0.0076 | defense_ratings |
| away_xg_attack_rating_last10 | 0.0070 | attack_ratings |