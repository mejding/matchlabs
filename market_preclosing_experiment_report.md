# Pre-Closing Market Odds Experiment

## Goal

Test whether football-data.co.uk non-`C` 1X2 odds improve the Premier League prediction model.

These columns are documented by football-data as pre-closing odds, not opening odds:

- `B365H/B365D/B365A`
- `PSH/PSD/PSA`
- `AvgH/AvgD/AvgA`
- `MaxH/MaxD/MaxA`
- equivalent non-`C` bookmaker columns

The experiment uses `market_mode=preclosing`.

## Timing Policy

Pre-closing odds do not leak the final match result. They may still create timestamp leakage if the production app predicts before the equivalent odds collection time or if no live/reproducible pre-closing odds feed exists.

Therefore, these odds are a production candidate only after live timing is controlled.

## Model Comparison

| model | accuracy | log_loss | brier_score | ece |
| --- | --- | --- | --- | --- |
| Current production model | 0.4860 | 1.0488 | 0.6295 | 0.0528 |
| Market-only preclosing model | 0.5178 | 1.0018 | 0.6006 | 0.0298 |
| Production + preclosing odds as XGBoost features | 0.4467 | 1.3175 | 0.7386 | 0.1740 |
| Calibrated model-market blend | 0.4860 | 1.1382 | 0.6763 | 0.1263 |

## Findings

1. Market-only preclosing probabilities are stronger than the current production model.

   Log Loss improves by `-0.0470`, Brier improves by `-0.0290`, and ECE improves by `-0.0230`.

2. Directly adding market odds and model-vs-market edge features to XGBoost makes the model materially worse.

   This likely means the model is overfitting to highly predictive market variables rather than learning a stable combination.

3. The calibrated blend did not improve performance.

   The internal validation selected a model-heavy blend, and the resulting test performance worsened Log Loss, Brier and calibration.

4. Model disagreements with the market are not predictive yet.

   On model/market disagreement rows, market accuracy was `0.4762` while model accuracy was `0.2738`.

## SHAP

Market and edge features have strong SHAP values in the research model:

- `model_vs_market_draw_edge`
- `market_home_prob`
- `model_vs_market_away_edge`
- `market_away_prob`
- `model_vs_market_home_edge`

This confirms that market odds contain signal, but the direct feature approach is not production-safe or performance-positive.

## Production Decision

Do not activate preclosing odds as XGBoost production features yet.

Recommended next production path:

1. Keep market odds as benchmark/fair-odds context in the app.
2. Build a live/reproducible pre-closing odds feed before any production activation.
3. Test a simpler market-overlay architecture:
   - show market-implied probabilities next to model probabilities,
   - optionally create a separate `market-informed probability` output,
   - do not mix market edge features directly into XGBoost unless a future time-based test improves Log Loss or Brier.

## Recommendation

Market odds are the strongest candidate feature family discovered so far, but they should move forward as a separate probability layer, not as raw XGBoost input yet.
