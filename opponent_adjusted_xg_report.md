# Sprint 4D: Opponent-Adjusted xG Attack/Defense Ratings

## Methodology

This sprint builds rolling team attack and defense ratings from Understat xG. Every value is calculated chronologically before the fixture date. No future matches are used.

## Rating Formulas

- Opponent attack strength before a match = opponent adjusted attack xG divided by league average xG.
- Opponent defense weakness before a match = opponent adjusted xGA conceded divided by league average xG.
- Adjusted attack xG for a completed match = team xG divided by opponent defense weakness known before kickoff.
- Adjusted defense xGA for a completed match = xG conceded divided by opponent attack strength known before kickoff.
- Ratings are relative to league average. Attack above `1.00` is stronger than league average. Defense below `1.00` is better than league average.
- Expected home xG = league average home xG * home attack rating * away defense weakness * home advantage factor.
- Expected away xG = league average away xG * away attack rating * home defense weakness * away factor.
- Poisson probabilities are derived from those expected goal estimates.

Windows tested:

- Last 5 matches
- Last 10 matches
- Season-to-date
- Exponentially weighted rolling average

## Model Comparison

| model_version | accuracy | log_loss | Brier_score | expected_calibration_error | draw_recall | draw_log_loss |
| --- | --- | --- | --- | --- | --- | --- |
| model_a_current_production | 0.4879 | 1.0438 | 0.6264 | 0.0429 | 0.0365 | 0.5803 |
| model_b_poisson_only | 0.4336 | 1.1742 | 0.7016 | 0.1126 | 0.0000 | 0.5868 |
| model_c_production_plus_attack_defense_ratings | 0.4710 | 1.0417 | 0.6256 | 0.0415 | 0.0292 | 0.5809 |
| model_d_production_plus_expected_goals | 0.4860 | 1.0449 | 0.6270 | 0.0448 | 0.0365 | 0.5827 |
| model_e_production_plus_poisson_probabilities | 0.4822 | 1.0434 | 0.6262 | 0.0433 | 0.0219 | 0.5799 |
| model_f_production_plus_all_opponent_adjusted_xg | 0.4692 | 1.0431 | 0.6265 | 0.0485 | 0.0219 | 0.5811 |

## Best Candidate vs Production

- Best candidate: `model_c_production_plus_attack_defense_ratings`
- Log Loss delta vs production: -0.0021
- Brier delta vs production: -0.0008
- ECE delta vs production: -0.0014

## Poisson Baseline

Poisson-only results are saved to `evaluation/opponent_adjusted_xg/poisson_baseline_results.csv`.

The Poisson model is useful as an interpretable baseline, but it should only influence production if its probabilities improve out-of-sample probability quality compared with the XGBoost production model.

## Draw Performance

Draw metrics are included in the model comparison table:

- `draw_recall`
- `draw_log_loss`
- `draw_mean_probability_on_draws`

Use these to judge whether Poisson/expected-goal features improve the model's historically weak draw handling.

## SHAP and Redundancy Analysis

Top new-feature SHAP signals:

- `home_xg_defense_rating_season` (opponent_adjusted_xg): 0.0320
- `away_xg_defense_rating_last10` (opponent_adjusted_xg): 0.0227
- `away_xg_attack_rating_season` (opponent_adjusted_xg): 0.0184
- `home_xg_defense_rating` (opponent_adjusted_xg): 0.0181
- `away_xg_defense_rating` (opponent_adjusted_xg): 0.0165
- `away_attack_vs_home_defense` (opponent_adjusted_xg): 0.0145
- `home_xg_attack_rating_season` (opponent_adjusted_xg): 0.0144
- `away_xg_attack_rating` (opponent_adjusted_xg): 0.0135
- `home_xg_defense_rating_last10` (opponent_adjusted_xg): 0.0126
- `away_xg_defense_rating_season` (opponent_adjusted_xg): 0.0125
- `away_xg_defense_rating_last5` (opponent_adjusted_xg): 0.0114
- `attack_defense_matchup_score` (opponent_adjusted_xg): 0.0104

Top new-feature permutation signals:

- `away_xg_defense_rating_last5`: 0.0041
- `home_xg_defense_rating_season`: 0.0031
- `home_xg_defense_rating_last10`: 0.0014
- `home_xg_defense_rating_last5`: 0.0011
- `away_xg_attack_rating`: 0.0011
- `away_xg_attack_rating_last5`: 0.0011
- `attack_defense_matchup_score`: 0.0007
- `home_xg_attack_rating_last5`: 0.0001
- `home_xg_defense_rating`: 0.0000
- `home_xg_attack_rating`: -0.0000

Remove-one tests:

| test | log_loss | Brier_score | expected_calibration_error |
| --- | --- | --- | --- |
| full_reference | 1.0431 | 0.6265 | 0.0485 |
| remove_ratings | 1.0426 | 0.6257 | 0.0449 |
| remove_expected_goals | 1.0443 | 0.6272 | 0.0472 |
| remove_poisson_probabilities | 1.0442 | 0.6272 | 0.0453 |

Feature correlation matrix is saved to `evaluation/opponent_adjusted_xg/correlation_matrix.csv`.

## Answers

1. Are opponent-adjusted xG ratings better than raw rolling xG?

   Evidence is mixed unless the best candidate improves Log Loss or Brier. SHAP signal alone is not enough because raw rolling xG is already active.

2. Are expected-goal estimates redundant with existing xG features?

   Compare expected-goal SHAP/permutation values and remove-one results. If metrics do not improve, treat them as mostly redundant with existing xG, Elo and shot-volume features.

3. Do Poisson probabilities add signal?

   Poisson probabilities provide a useful interpretable baseline. They should not be promoted unless Model E or Model F improves out-of-sample probability metrics.

4. Do these features improve draw prediction?

   Use draw recall and draw log loss in the comparison table. Improvement in draw recall alone is not enough if total Log Loss/Brier worsens.

## Recommendation

Move `model_c_production_plus_attack_defense_ratings` forward as a production candidate.

Do not activate the candidate in the saved production model yet if accuracy or draw recall falls versus production. A reduced-feature backtest should confirm the small probability-quality gain before promotion.

Production rule: only activate these features if out-of-sample Log Loss or Brier improves without materially worsening calibration.
