# Market Intelligence Report

Bookmaker odds are converted from decimal odds to normalized implied probabilities:

- `market_home_prob`
- `market_draw_prob`
- `market_away_prob`
- `market_margin`
- `market_favorite_prob`

Edges are calculated as model probability minus market probability.

Important timing update: `market_odds_timing_discovery_report.md` is now the source of truth for column timing. football-data non-`C` 1X2 odds are documented as pre-closing odds, not opening odds. `C`-suffixed odds are closing odds. This historical model comparison remains useful, but production activation still requires a live/reproducible pre-closing odds feed and a fresh time-based model test.

Market mode evaluated in this run: `research`.

Safe pre-match odds fields currently verified: None.

## Model Comparison

| model | accuracy | log_loss | brier_score | calibration_score | ece |
| --- | --- | --- | --- | --- | --- |
| Model A: current production model | 0.4860 | 1.0488 | 0.6295 | 0.0528 | 0.0528 |
| Model B: market-only research model | 0.5121 | 1.0045 | 0.6017 | 0.0320 | 0.0320 |
| Model C: current model + research odds (research only) | 0.4486 | 1.3197 | 0.7397 | 0.1723 | 0.1723 |
| Model D: production + safe-prematch odds | nan | nan | nan | nan | nan |

Best model by log loss: `Model B: market-only research model`.

## 1. Does market information improve predictions?

Model C vs Model A:

- Log loss change: 0.2709
- Brier score change: 0.1101

Answer: No, adding market odds as model features did not improve the current model in this run.

## 2. Is the market stronger than the model?

Model B vs Model A:

- Log loss change: -0.0443
- Brier score change: -0.0278

Answer: Yes. Market-only probabilities are stronger than the current model on this historical test period.

## 3. Where does the model disagree with the market?

Disagreement summary:

| segment | matches | model_accuracy | market_accuracy | mean_abs_edge |
| --- | --- | --- | --- | --- |
| all_test_matches | 535 | 0.4860 | 0.5121 | 0.1078 |
| model_market_disagreements | 85 | 0.3059 | 0.4706 | 0.1707 |
| large_edges_top_quartile | 134 | 0.4701 | 0.5821 | 0.2017 |

Largest individual disagreements are saved to `evaluation/market_intelligence/market_disagreements.csv`.

## 4. Are disagreements predictive?

If model accuracy on disagreement segments is higher than market accuracy, the model has exploitable edge. In this run, inspect the disagreement summary above. If the market remains more accurate on disagreement rows, model disagreement is not yet a reliable signal.

## SHAP

Top market/edge SHAP features:

- `model_vs_market_draw_edge` (edge): 0.5383
- `market_home_prob` (market): 0.2554
- `model_vs_market_away_edge` (edge): 0.2306
- `market_away_prob` (market): 0.2000
- `model_vs_market_home_edge` (edge): 0.1471
- `market_draw_prob` (market): 0.0837
- `market_favorite_prob` (market): 0.0361
- `market_favorite_class` (market): 0.0106
- `market_margin` (market): 0.0066

Full SHAP outputs:

- `evaluation/market_intelligence/market_shap_feature_rankings.csv`
- `evaluation/market_intelligence/market_shap_group_rankings.csv`
- `evaluation/market_intelligence/market_shap_summary.png`

## Production Decision

Do not move market odds into production. Keep as benchmark/research-only until model + market improves out-of-sample and odds timing is controlled.
