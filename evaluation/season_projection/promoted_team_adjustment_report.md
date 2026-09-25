# Promoted-Team Adjustment Report

## Summary

- Adjusted promoted/low-history teams: `0`
- Teams using Championship data: `0`
- Teams using conservative baseline fallback: `0`

## Answers

### 1. Which promoted teams were adjusted?

_No rows._

### 2. Did they have Premier League data?

_No rows._

### 3. Was Championship data available?

_No rows._

### 4. If yes, how was it adjusted?

Adjustment factors:

- Recent form / points: Championship points last 5 x 0.55
- xG for: Championship xG x 0.75 when xG exists
- xGA: Championship xGA x 1.35 when xG exists
- Shot volume: Championship shots x 0.75
- Shots allowed: Championship shots allowed x 1.25 when used by future features

Current adjustment values:

_No rows._

### 5. If no, what fallback baseline was used?

| average_points | median_points | average_position | median_position | relegation_rate | goals_for_per_match | goals_against_per_match |
| --- | --- | --- | --- | --- | --- | --- |
| 28.4762 | 25.0000 | 15.7143 | 18.0000 | 0.5714 | 0.9085 | 1.6429 |

Baseline fallback teams:

_No rows._

### 6. Did the change prevent missing PL form from becoming zero?

Yes. Adjusted teams receive non-zero adjusted recent form from Championship data when available, or from the promoted-team baseline when Championship data is unavailable.

### 7. Did the change prevent Championship form from being treated as Premier League form?

Yes. Championship points, xG and shot volume are converted with explicit factors before entering the Season Projection feature rows.

### 8. How did expected points and relegation probability change?

_No rows._

## Notes

The current football-data Championship file provides results and shot volume, but not xG. Therefore Championship xG fields remain unavailable and xG/xGA are supplied by the transparent promoted-team baseline until a reliable Championship xG source is added.
