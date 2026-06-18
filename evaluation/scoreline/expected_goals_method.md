# Expected Goals Method For Scoreline Layer

## Purpose

The scoreline layer is an interpretation layer on top of the production 1X2 model. It does not replace the model target, which remains:

- home win
- draw
- away win

Correct-score probabilities are naturally low and should be treated as supporting context.

## Inputs

The first version uses existing pre-match features already available in the prediction row:

- `home_xg_avg`
- `away_xg_avg`
- `home_xga_avg`
- `away_xga_avg`
- displayed home/draw/away probabilities

The displayed probabilities are used after calibration when a calibration layer is active in the app.

## Expected Goals Estimate

Home expected goals are estimated from:

- the home team's recent attacking xG
- the away team's recent defensive xGA
- a small adjustment toward the displayed home-vs-away model balance

Away expected goals are estimated from:

- the away team's recent attacking xG
- the home team's recent defensive xGA
- a small adjustment toward the displayed away-vs-home model balance

Current formula:

```text
home_xg = 0.55 * home_xg_avg + 0.45 * away_xga_avg
away_xg = 0.55 * away_xg_avg + 0.45 * home_xga_avg
```

Then each side is nudged by the model's displayed home-away probability balance:

```text
win_balance = model_home_probability - model_away_probability
home_xg *= exp(0.22 * win_balance)
away_xg *= exp(-0.22 * win_balance)
```

Expected goals are clipped to the range `0.2` to `4.0` to avoid extreme values from sparse or unusual inputs.

## Missing Data Fallback

If xG/xGA values are missing or invalid, the layer falls back to simple Premier League-style defaults:

- home goals: `1.45`
- away goals: `1.15`

These are pragmatic defaults for app robustness, not a replacement for real historical data.

## Scoreline Probabilities

The module creates scoreline probabilities from 0-0 to 6-6.

The probability mass outside 6 goals is not shown directly. The displayed 0-6 grid is normalized before alignment. This is acceptable for a compact v1 UI, but the limitation should be kept in mind for very high-scoring fixtures.

## 1X2 Alignment

After raw scoreline probabilities are generated, they are aligned with the production model's displayed 1X2 probabilities:

- all home-win scorelines are scaled to sum to the displayed home-win probability
- all draw scorelines are scaled to sum to the displayed draw probability
- all away-win scorelines are scaled to sum to the displayed away-win probability

This prevents the scoreline layer from contradicting the main model.

## Production Status

The scoreline layer is display/supporting context only. It is not a separate trained betting model and should not be presented as a correct-score edge.

The app shows related but different ideas:

- `Top scorelines for model's most likely outcome`: a small set of likely scorelines within the model's most likely 1X2 outcome bucket.
- `Highest individual scoreline`: the single exact scoreline with the highest individual probability.

These can differ. For example, a home win may be the most likely 1X2 outcome, while `1-1` can still be the highest single exact scoreline because the home-win probability is spread across many possible home-win scores.
