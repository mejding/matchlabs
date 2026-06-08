# Market Intelligence Report

Bookmaker odds are converted from decimal odds to normalized implied probabilities:

- `market_home_prob`
- `market_draw_prob`
- `market_away_prob`
- `market_margin`
- `market_favorite_prob`

Edges are calculated as model probability minus market probability.

Important timing note: benchmark mode uses audited benchmark-only prices, preferring average closing odds when available. Research mode uses listed football-data odds with unknown timing. Opening mode requires a separate verified opening-odds file. Closing, average and maximum prices may contain information unavailable at early prediction time, so market odds should not be used in live production until odds timing is controlled.

Market mode evaluated in this run: `benchmark`.

Safe pre-match odds fields currently verified: None.

## Model Comparison

| model | accuracy | log_loss | brier_score | calibration_score | ece |
| --- | --- | --- | --- | --- | --- |
| Model A: current production model | 0.4860 | 1.0488 | 0.6295 | 0.0528 | 0.0528 |
| Model B: market-only benchmark model | 0.5178 | 0.9980 | 0.5976 | 0.0253 | 0.0253 |
| Model C: current model + benchmark odds (research only) | 0.4355 | 1.3589 | 0.7569 | 0.1859 | 0.1859 |
| Model D: production + safe-prematch odds | nan | nan | nan | nan | nan |

Best model by log loss: `Model B: market-only benchmark model`.

## 1. Does market information improve predictions?

Model C vs Model A:

- Log loss change: 0.3101
- Brier score change: 0.1274

Answer: No, adding market odds as model features did not improve the current model in this run.

## 2. Is the market stronger than the model?

Model B vs Model A:

- Log loss change: -0.0507
- Brier score change: -0.0319

Answer: Yes. Market-only probabilities are stronger than the current model on this historical test period.

## 3. Where does the model disagree with the market?

Disagreement summary:

| segment | matches | model_accuracy | market_accuracy | mean_abs_edge |
| --- | --- | --- | --- | --- |
| all_test_matches | 535 | 0.4860 | 0.5178 | 0.1103 |
| model_market_disagreements | 88 | 0.2955 | 0.4886 | 0.1710 |
| large_edges_top_quartile | 134 | 0.4851 | 0.5821 | 0.2040 |

Largest individual disagreements are saved to `evaluation/market_intelligence/market_disagreements.csv`.

## 4. Are disagreements predictive?

If model accuracy on disagreement segments is higher than market accuracy, the model has exploitable edge. In this run, inspect the disagreement summary above. If the market remains more accurate on disagreement rows, model disagreement is not yet a reliable signal.

## SHAP

Top market/edge SHAP features:

- `model_vs_market_draw_edge` (edge): 0.5547
- `market_home_prob` (market): 0.3082
- `model_vs_market_away_edge` (edge): 0.2194
- `model_vs_market_home_edge` (edge): 0.1582
- `market_away_prob` (market): 0.1542
- `market_draw_prob` (market): 0.0764
- `market_favorite_prob` (market): 0.0525
- `market_margin` (market): 0.0364
- `market_favorite_class` (market): 0.0127

Full SHAP outputs:

- `evaluation/market_intelligence/market_shap_feature_rankings.csv`
- `evaluation/market_intelligence/market_shap_group_rankings.csv`
- `evaluation/market_intelligence/market_shap_summary.png`

## Production Decision

Do not move market odds into production. Keep as benchmark/research-only until model + market improves out-of-sample and odds timing is controlled.
