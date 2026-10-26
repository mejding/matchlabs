# Robust Match Prediction Experiment

## Method

Each test season is predicted using only earlier seasons for training. The candidate combines the feature-rich production model with the simpler recent-form/xG model. A fixed 50/50 blend was selected as the conservative midpoint because the complex model wins the two older seasons while the xG model wins the latest season.

## Three-season average

| Model | Accuracy | Log loss | Brier |
| --- | ---: | ---: | ---: |
| Complex model | 0.5088 | 1.0218 | 0.6115 |
| 50/50 robust ensemble | 0.4974 | 1.0146 | 0.6067 |

## Decision

Adopt the 50/50 ensemble. It reduces average log loss by -0.0072 and Brier score by -0.0048. Accuracy is treated as secondary because the product displays probabilities rather than only a hard class prediction.

Temperature calibration is fitted after ensembling and must be applied consistently in the Prediction tab, forecast snapshots and Season Projection.
