# Market Odds Production Decision Report

## Executive Summary

Market information is valuable, but it should not move into production model features yet.

The strongest evidence is:

- Market-only probabilities beat the current production model on benchmark and research-mode tests.
- Adding market odds directly as XGBoost features makes the model worse out-of-sample.
- No verified opening/pre-match odds dataset exists locally yet.
- OddsPortal opening odds remain a strong candidate, but they need a reproducible and permitted data path before they can be used.

Production decision: keep market odds as `Benchmark only`. Do not train production predictions with odds yet.

## Modes Tested

| Mode | Data Source | Timing Safety | Production Eligible |
| --- | --- | --- | --- |
| `opening` | `data/oddsportal_opening_odds.csv` if present | Potentially safe | No data available yet |
| `benchmark` | football-data closing/average odds | Not safe for live predictions | No |
| `research` | football-data listed single-bookmaker odds | Unknown timing | No |

## Results

### Opening Odds Mode

No verified opening odds dataset exists at `data/oddsportal_opening_odds.csv`.

| model | accuracy | log_loss | brier_score | calibration_score | ece |
| --- | --- | --- | --- | --- | --- |
| Current production model | 0.4860 | 1.0488 | 0.6295 | 0.0528 | 0.0528 |
| Market-only opening model | n/a | n/a | n/a | n/a | n/a |
| Production + opening odds | n/a | n/a | n/a | n/a | n/a |

Conclusion: cannot activate opening odds yet because no verified opening dataset exists locally.

### Benchmark Mode

Benchmark mode uses football-data closing/average odds. These are useful for comparison, but not safe for production predictions.

| model | accuracy | log_loss | brier_score | calibration_score | ece |
| --- | --- | --- | --- | --- | --- |
| Current production model | 0.4860 | 1.0488 | 0.6295 | 0.0528 | 0.0528 |
| Market-only benchmark model | 0.5178 | 0.9980 | 0.5976 | 0.0253 | 0.0253 |
| Production + benchmark odds | 0.4355 | 1.3589 | 0.7569 | 0.1859 | 0.1859 |
| Calibrated model-market blend benchmark | 0.4841 | 1.0317 | 0.6204 | 0.0634 | 0.0634 |

Conclusion: the market benchmark is stronger than the current model, but adding benchmark odds directly as features harms performance and creates leakage risk.

### Research Mode

Research mode uses listed football-data single-bookmaker odds. Timing is unknown, so these are not production-safe.

| model | accuracy | log_loss | brier_score | calibration_score | ece |
| --- | --- | --- | --- | --- | --- |
| Current production model | 0.4860 | 1.0488 | 0.6295 | 0.0528 | 0.0528 |
| Market-only research model | 0.5121 | 1.0045 | 0.6017 | 0.0320 | 0.0320 |
| Production + research odds | 0.4486 | 1.3197 | 0.7397 | 0.1723 | 0.1723 |

Conclusion: listed odds again show that market prices contain signal, but direct model integration is worse and timing remains unverified.

## SHAP Findings

In the research-mode model, market and edge features have strong SHAP values:

- Edge feature group: `0.9159`
- Production feature group: `0.6147`
- Market feature group: `0.5924`

Top market-related features:

- `model_vs_market_draw_edge`
- `market_home_prob`
- `model_vs_market_away_edge`
- `market_away_prob`
- `model_vs_market_home_edge`

Interpretation: market odds clearly carry information, but the combined XGBoost model is not using them in a way that improves out-of-sample probability quality.

## Production Decision

Do not activate market odds as production model features yet.

Reasons:

1. No verified opening odds dataset exists locally.
2. Existing benchmark odds are likely closing/average prices and may leak late information.
3. Existing listed odds have unknown timing.
4. Directly adding odds features worsened Log Loss, Brier Score and calibration.
5. The market-only benchmark is stronger, which means odds are useful as a comparison layer, but not automatically useful inside the current model architecture.

## Recommended Next Step

Build a small opening-odds proof of concept before any production activation:

1. Obtain or manually verify one full season of opening 1X2 odds.
2. Save it as `data/oddsportal_opening_odds.csv`.
3. Rerun:

```bash
python market_intelligence_experiments.py --market-mode opening
```

4. Promote only if:
   - opening odds improve out-of-sample Log Loss or Brier,
   - calibration does not materially worsen,
   - timing is proven pre-match,
   - the data source is reproducible and permitted.

Until then, keep the frontend status as `Benchmark only`.
