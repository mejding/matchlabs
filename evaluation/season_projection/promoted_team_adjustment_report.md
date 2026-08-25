# Promoted-Team Adjustment Report

## Summary

- Adjusted promoted/low-history teams: `2`
- Teams using Championship data: `2`
- Teams using conservative baseline fallback: `0`

## Answers

### 1. Which promoted teams were adjusted?

| team | source_league | local_pl_match_count | championship_match_count | promotion_adjustment_applied | fallback_used |
| --- | --- | --- | --- | --- | --- |
| Coventry | Championship adjusted to Premier League equivalent | 1 | 46 | True | False |
| Hull | Championship adjusted to Premier League equivalent | 1 | 46 | True | False |

### 2. Did they have Premier League data?

| team | local_pl_match_count | championship_data_available |
| --- | --- | --- |
| Coventry | 1 | True |
| Hull | 1 | True |

### 3. Was Championship data available?

| team | championship_data_available | championship_match_count | championship_latest_match |
| --- | --- | --- | --- |
| Coventry | True | 46 | 2026-05-02 |
| Hull | True | 46 | 2026-05-02 |

### 4. If yes, how was it adjusted?

Adjustment factors:

- Recent form / points: Championship points last 5 x 0.55
- xG for: Championship xG x 0.75 when xG exists
- xGA: Championship xGA x 1.35 when xG exists
- Shot volume: Championship shots x 0.75
- Shots allowed: Championship shots allowed x 1.25 when used by future features

Current adjustment values:

| team | raw_recent_form | adjusted_recent_form | raw_xg | adjusted_xg | raw_xga | adjusted_xga | raw_shot_volume | adjusted_shot_volume |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| Coventry | 11.0000 | 6.0500 |  | 0.8512 |  | 1.9607 | 16.0000 | 12.0000 |
| Hull | 5.0000 | 2.7500 |  | 0.8512 |  | 1.9607 | 13.4000 | 10.0500 |

### 5. If no, what fallback baseline was used?

| average_points | median_points | average_position | median_position | relegation_rate | goals_for_per_match | goals_against_per_match |
| --- | --- | --- | --- | --- | --- | --- |
| 27.9524 | 25.0000 | 15.3810 | 18.0000 | 0.5714 | 0.8960 | 1.6165 |

Baseline fallback teams:

_No rows._

### 6. Did the change prevent missing PL form from becoming zero?

Yes. Adjusted teams receive non-zero adjusted recent form from Championship data when available, or from the promoted-team baseline when Championship data is unavailable.

### 7. Did the change prevent Championship form from being treated as Premier League form?

Yes. Championship points, xG and shot volume are converted with explicit factors before entering the Season Projection feature rows.

### 8. How did expected points and relegation probability change?

| team | expected_points_before_adjustment | expected_points | relegation_probability_before_adjustment | relegation_probability |
| --- | --- | --- | --- | --- |
| Coventry | 26.5668 | 30.6765 | 0.9416 | 0.8431 |
| Hull | 56.1653 | 52.9424 | 0.0125 | 0.0294 |

## Notes

The current football-data Championship file provides results and shot volume, but not xG. Therefore Championship xG fields remain unavailable and xG/xGA are supplied by the transparent promoted-team baseline until a reliable Championship xG source is added.
