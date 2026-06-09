# Market Overlay Experiment Report

## Goal

Test whether pre-closing market odds can improve probability quality without feeding raw odds directly into XGBoost.

## Models Tested

- Production model: current football model without odds.
- Market-only preclosing: normalized implied probabilities from football-data non-`C` 1X2 odds.
- Best validation blend: weighted average of model and market probabilities, fitted on an internal latest training slice.
- Residual overlay: starts from market probabilities and applies a conservative model residual when validation supports it.
- Logistic stacking overlay: a regularized multinomial logistic meta-model using model probabilities, market probabilities and small edge descriptors.

## Results

| model | accuracy | log_loss | brier_score | ece |
| --- | --- | --- | --- | --- |
| Market-only preclosing | 0.5178 | 1.0018 | 0.6006 | 0.0298 |
| Best validation blend | 0.5178 | 1.0018 | 0.6006 | 0.0298 |
| Residual market overlay | 0.5121 | 1.0020 | 0.6009 | 0.0358 |
| Logistic stacking overlay | 0.4804 | 1.0203 | 0.6132 | 0.0567 |
| Production model | 0.4860 | 1.0488 | 0.6295 | 0.0528 |

## Learned Overlay Parameters

- Best blend model weight: `0.00`. A value of `0.00` means pure market; `1.00` means pure model.
- Best residual weight: `-0.17`.

## Coefficients

| feature | mean_abs_coefficient |
| --- | --- |
| market_home_logit_vs_draw | 0.2131 |
| market_draw_prob | 0.1452 |
| market_favorite_prob | 0.1082 |
| model_minus_market_favorite | 0.1016 |
| market_away_prob | 0.0959 |
| market_home_prob | 0.0881 |
| edge_away | 0.0753 |
| model_home_prob | 0.0725 |
| model_draw_prob | 0.0660 |
| edge_home | 0.0634 |
| model_favorite_prob | 0.0541 |
| model_away_prob | 0.0521 |

## Conclusions

- Best model by Log Loss: `Market-only preclosing`.
- Market-only beats production: yes.
- Logistic overlay improves Log Loss and Brier versus production: yes.
- Logistic overlay passes the calibration promotion rule: no.

The goal is maximum probability quality, not protecting the existing model. If market-only remains best, the honest answer is that the market should be treated as the stronger probability benchmark.

## Production Decision

Do not activate odds inside XGBoost. The current evidence supports showing market-implied probabilities as a separate benchmark/overlay candidate, pending live pre-closing feed timing.