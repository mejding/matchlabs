# Market Intelligence Report

Bookmaker odds are converted from decimal odds to normalized implied probabilities:

- `market_home_prob`
- `market_draw_prob`
- `market_away_prob`
- `market_margin`
- `market_favorite_prob`

Edges are calculated as model probability minus market probability.

Important timing note: football-data non-C 1X2 odds are documented as pre-closing odds, not opening odds. C-suffixed odds are closing odds. Pre-closing odds do not leak the final result, but they are only production-safe if the live prediction path uses an equivalent pre-closing feed before kickoff.

Market mode evaluated in this run: `preclosing`.

Safe pre-match odds fields currently verified: None.

Blend parameters: model weight=1.00, temperature=0.60.

## Model Comparison

| model | accuracy | log_loss | brier_score | calibration_score | ece |
| --- | --- | --- | --- | --- | --- |
| Model A: current production model | 0.4860 | 1.0488 | 0.6295 | 0.0528 | 0.0528 |
| Model B: market-only preclosing model | 0.5178 | 1.0018 | 0.6006 | 0.0298 | 0.0298 |
| Model C: current model + preclosing odds (research only) | 0.4467 | 1.3175 | 0.7386 | 0.1740 | 0.1740 |
| Model D: calibrated model-market blend (preclosing) | 0.4860 | 1.1382 | 0.6763 | 0.1263 | 0.1263 |
| Model E: production + safe-prematch odds | nan | nan | nan | nan | nan |

Best model by log loss: `Model B: market-only preclosing model`.

## 1. Does market information improve predictions?

Model C vs Model A:

- Log loss change: 0.2687
- Brier score change: 0.1090

Answer: No, adding market odds as model features did not improve the current model in this run.

## 1b. Does a calibrated model-market blend improve predictions?

Answer: No, the calibrated blend does not pass the production promotion rule in this run.

## 2. Is the market stronger than the model?

Model B vs Model A:

- Log loss change: -0.0470
- Brier score change: -0.0290

Answer: Yes. Market-only probabilities are stronger than the current model on this historical test period.

## 3. Where does the model disagree with the market?

Disagreement summary:

| segment | matches | model_accuracy | market_accuracy | mean_abs_edge |
| --- | --- | --- | --- | --- |
| all_test_matches | 535 | 0.4860 | 0.5178 | 0.1079 |
| model_market_disagreements | 84 | 0.2738 | 0.4762 | 0.1702 |
| large_edges_top_quartile | 134 | 0.4925 | 0.6045 | 0.2021 |

Largest individual disagreements are saved to `evaluation/market_intelligence/market_disagreements.csv`.

## 4. Are disagreements predictive?

If model accuracy on disagreement segments is higher than market accuracy, the model has exploitable edge. In this run, inspect the disagreement summary above. If the market remains more accurate on disagreement rows, model disagreement is not yet a reliable signal.

## SHAP

Top market/edge SHAP features:

- `model_vs_market_draw_edge` (edge): 0.5416
- `market_home_prob` (market): 0.2874
- `model_vs_market_away_edge` (edge): 0.2232
- `market_away_prob` (market): 0.1697
- `model_vs_market_home_edge` (edge): 0.1525
- `market_draw_prob` (market): 0.0593
- `market_favorite_prob` (market): 0.0493
- `market_margin` (market): 0.0294
- `market_favorite_class` (market): 0.0087

Full SHAP outputs:

- `evaluation/market_intelligence/market_shap_feature_rankings.csv`
- `evaluation/market_intelligence/market_shap_group_rankings.csv`
- `evaluation/market_intelligence/market_shap_summary.png`

## Production Decision

Do not activate market odds as XGBoost production features. Keep them as benchmark/fair-odds context and test a separate market-overlay probability layer once live pre-closing odds timing is controlled.
