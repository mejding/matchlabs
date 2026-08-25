# Promoted-Team Baseline Report

## Baseline

The project does not currently contain reliable Championship xG, shot volume or form data that can be treated as Premier League-equivalent. For teams with zero local Premier League history, Season Projection uses a conservative Premier League baseline estimated from teams entering a Premier League season without having appeared in the immediately previous local PL season.

| average_points | median_points | average_position | median_position | relegation_rate | goals_for_per_match | goals_against_per_match |
| --- | --- | --- | --- | --- | --- | --- |
| 27.9524 | 25.0000 | 15.3810 | 18.0000 | 0.5714 | 0.8960 | 1.6165 |

## Current Baseline Fallback Teams

_No rows._

## Adjustment Policy

- Championship form is not copied into the Premier League model as-is.
- Attacking form, xG and shot volume are down-weighted through a conservative promoted-team baseline.
- Defensive weakness/xGA is up-adjusted relative to the league median and historical promoted-team goals-against profile.
- Elo is preferred when local Elo exists; otherwise the neutral Elo fallback is flagged.
- Fallback teams carry higher uncertainty until they play enough Premier League matches.
