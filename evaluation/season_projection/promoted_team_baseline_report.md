# Promoted-Team Baseline Report

## Baseline

The project does not currently contain reliable Championship xG, shot volume or form data that can be treated as Premier League-equivalent. For teams with zero local Premier League history, Season Projection uses a conservative Premier League baseline estimated from teams entering a Premier League season without having appeared in the immediately previous local PL season.

| average_points | median_points | average_position | median_position | relegation_rate | goals_for_per_match | goals_against_per_match |
| --- | --- | --- | --- | --- | --- | --- |
| 32.2778 | 26.0000 | 16.2778 | 18.0000 | 0.6111 | 1.0395 | 1.8801 |

## Current Fallback Teams

| team | local_pl_match_count | source_league | fallback_reason | recent_form_points_last5 | xg_strength_last5 | xga_strength_last5 | shots_avg_last5 | elo_rating |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| Coventry | 0 | Promoted-team conservative Premier League baseline | No local Premier League history; Championship data is not treated as Premier League-equivalent. | 3.4211 | 0.9875 | 1.7861 | 10.6600 | 1500.0000 |
| Hull | 0 | Promoted-team conservative Premier League baseline | No local Premier League history; Championship data is not treated as Premier League-equivalent. | 3.4211 | 0.9875 | 1.7861 | 10.6600 | 1500.0000 |

## Adjustment Policy

- Championship form is not copied into the Premier League model as-is.
- Attacking form, xG and shot volume are down-weighted through a conservative promoted-team baseline.
- Defensive weakness/xGA is up-adjusted relative to the league median and historical promoted-team goals-against profile.
- Elo is preferred when local Elo exists; otherwise the neutral Elo fallback is flagged.
- Fallback teams carry higher uncertainty until they play enough Premier League matches.
