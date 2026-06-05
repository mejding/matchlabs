# Market Intelligence Report

Bookmaker odds are converted from decimal odds to normalized implied probabilities:

- `market_home_prob`
- `market_draw_prob`
- `market_away_prob`
- `market_margin`
- `market_favorite_prob`

Edges are calculated as model probability minus market probability.

Important timing note: benchmark mode uses audited benchmark-only prices, preferring average closing odds when available. Closing, average and maximum prices may contain information unavailable at early prediction time, so market odds should not be used in live production until odds timing is controlled.

Safe pre-match odds fields currently verified: None.

## Model Comparison

| model | accuracy | log_loss | brier_score | calibration_score | ece |
| --- | --- | --- | --- | --- | --- |
| Model A: current production model | 0.5142 | 0.9946 | 0.5946 | 0.0499 | 0.0499 |
| Model B: market-only benchmark model | 0.5733 | 0.9467 | 0.5603 | 0.0416 | 0.0416 |
| Model C: current model + benchmark odds (research only) | 0.5098 | 1.1793 | 0.6738 | 0.1233 | 0.1233 |
| Model D: production + safe-prematch odds | nan | nan | nan | nan | nan |

Best model by log loss: `Model B: market-only benchmark model`.

## 1. Does market information improve predictions?

Model C vs Model A:

- Log loss change: 0.1846
- Brier score change: 0.0792

Answer: No, adding market odds as model features did not improve the current model in this run.

## 2. Is the market stronger than the model?

Model B vs Model A:

- Log loss change: -0.0479
- Brier score change: -0.0343

Answer: Yes. Market-only probabilities are stronger than the current model on this historical test period.

## 3. Where does the model disagree with the market?

Disagreement summary:

| segment | matches | model_accuracy | market_accuracy | mean_abs_edge |
| --- | --- | --- | --- | --- |
| all_test_matches | 457 | 0.5142 | 0.5733 | 0.1314 |
| model_market_disagreements | 99 | 0.2323 | 0.5051 | 0.1966 |
| large_edges_top_quartile | 115 | 0.4609 | 0.6087 | 0.2507 |

Largest individual disagreements are saved to `evaluation/market_intelligence/market_disagreements.csv`.

## 4. Are disagreements predictive?

If model accuracy on disagreement segments is higher than market accuracy, the model has exploitable edge. In this run, inspect the disagreement summary above. If the market remains more accurate on disagreement rows, model disagreement is not yet a reliable signal.

## SHAP

Top market/edge SHAP features:

- `model_vs_market_draw_edge` (edge): 0.4589
- `market_home_prob` (market): 0.2809
- `model_vs_market_away_edge` (edge): 0.2107
- `market_away_prob` (market): 0.1923
- `model_vs_market_home_edge` (edge): 0.1614
- `market_draw_prob` (market): 0.1183
- `market_favorite_prob` (market): 0.0550
- `market_favorite_class` (market): 0.0369
- `market_margin` (market): 0.0122

Full SHAP outputs:

- `evaluation/market_intelligence/market_shap_feature_rankings.csv`
- `evaluation/market_intelligence/market_shap_group_rankings.csv`
- `evaluation/market_intelligence/market_shap_summary.png`

## Production Decision

Do not move market odds into production. Keep as benchmark/research-only until model + market improves out-of-sample and odds timing is controlled.
