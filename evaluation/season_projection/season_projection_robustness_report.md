# Season Projection Robustness Report

## What Was Fixed

- Season Projection now populates shot-volume features using the same active production feature family used by the Prediction tab.
- Season Projection validates active feature groups before running and exposes Championship-adjusted or fallback rows instead of silently filling missing active features.
- Teams with zero local Premier League history use adjusted Championship data when available.
- If Championship data is missing, teams receive a conservative promoted-team Premier League baseline.
- Championship performance is not treated as Premier League-equivalent input without conversion.
- Early-season shot-volume season averages use a recent-history fallback until a team has at least five current-season matches.

## Shot Volume

Shot volume is now populated in Season Projection. The feature parity audit checks `shots` and `shots_on_target` columns against the Prediction tab logic.

For last-5 and last-10 features, the first completed matches of a new season are added to the previous season's recent history. For season-average shot-volume fields, the model uses the current season only after at least five team matches are available; before then it falls back to the latest 10 available matches across seasons.

## Feature Parity

- Validation status: `Ready`
- Non-promoted max feature difference: `0.00000000`
- Intentional promoted adjustment rows: `0`

## Promoted-Team Handling

| average_points | median_points | average_position | median_position | relegation_rate | goals_for_per_match | goals_against_per_match |
| --- | --- | --- | --- | --- | --- | --- |
| 28.9048 | 25.0000 | 15.9048 | 18.0000 | 0.5714 | 0.9248 | 1.6604 |

Baseline fallback teams:

_No rows._

## Tottenham / Coventry / Hull Audit

Feature audit:

| team | local_pl_match_count | fallback_used | source_league | raw_recent_form_points_last5 | recent_form_points_last5 | raw_xg_strength_last5 | xg_strength_last5 | raw_xga_strength_last5 | xga_strength_last5 | raw_shots_avg_last5 | shots_avg_last5 | elo_rating |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| Coventry | 8 | False | Premier League historical data | 6.0000 | 6.0000 | 0.9905 | 0.9905 | 1.5694 | 1.5694 | 11.6000 | 11.6000 | 1467.8840 |
| Hull | 8 | False | Premier League historical data | 3.0000 | 3.0000 | 1.3127 | 1.3127 | 1.8732 | 1.8732 | 12.4000 | 12.4000 | 1514.5586 |
| Tottenham | 274 | False | Premier League historical data | 8.0000 | 8.0000 | 1.2889 | 1.2889 | 1.1564 | 1.1564 | 15.4000 | 15.4000 | 1491.8331 |

Projection:

| team | expected_points | expected_position | projected_position | relegation_probability |
| --- | --- | --- | --- | --- |
| Tottenham | 43.3993 | 14.4498 | 15 | 0.2023 |
| Hull | 42.0969 | 14.8717 | 16 | 0.2492 |
| Coventry | 38.6505 | 16.2731 | 17 | 0.4093 |

## Remaining Limitations

- The project has football-data Championship results and shot volume, but not Championship xG. Promoted-team xG/xGA therefore still use a transparent conservative PL baseline until a reliable Championship xG source is added.
- The neutral fixture skeleton fallback remains available, but official fixtures are preferred when valid.
- Season Projection is a forward projection from the latest completed local data. Completed current-season matches are included as actual table points, and remaining fixtures are simulated from feature values available at refresh time.
