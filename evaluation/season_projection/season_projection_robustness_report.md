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

- Validation status: `Warning`
- Non-promoted max feature difference: `0.00000000`
- Intentional promoted adjustment rows: `600`

## Promoted-Team Handling

| average_points | median_points | average_position | median_position | relegation_rate | goals_for_per_match | goals_against_per_match |
| --- | --- | --- | --- | --- | --- | --- |
| 27.9524 | 25.0000 | 15.3810 | 18.0000 | 0.5714 | 0.8960 | 1.6165 |

Baseline fallback teams:

_No rows._

## Tottenham / Coventry / Hull Audit

Feature audit:

| team | local_pl_match_count | fallback_used | source_league | raw_recent_form_points_last5 | recent_form_points_last5 | raw_xg_strength_last5 | xg_strength_last5 | raw_xga_strength_last5 | xga_strength_last5 | raw_shots_avg_last5 | shots_avg_last5 | elo_rating |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| Coventry | 1 | False | Championship adjusted to Premier League equivalent | 0.0000 | 6.0500 | 0.5583 | 0.8512 | 1.8542 | 1.9607 | 4.0000 | 12.0000 | 1496.4176 |
| Hull | 1 | False | Championship adjusted to Premier League equivalent | 3.0000 | 2.7500 | 1.4963 | 0.8512 | 1.7787 | 1.9607 | 8.0000 | 10.0500 | 1519.2038 |
| Tottenham | 267 | False | Premier League historical data | 7.0000 | 7.0000 | 1.3854 | 1.3854 | 1.5764 | 1.5764 | 13.0000 | 13.0000 | 1465.3653 |

Projection:

| team | expected_points | expected_position | projected_position | relegation_probability |
| --- | --- | --- | --- | --- |
| Hull | 53.5360 | 9.2833 | 6 | 0.0289 |
| Tottenham | 42.1480 | 15.3162 | 18 | 0.3481 |
| Coventry | 32.2454 | 18.7005 | 20 | 0.8158 |

## Remaining Limitations

- The project has football-data Championship results and shot volume, but not Championship xG. Promoted-team xG/xGA therefore still use a transparent conservative PL baseline until a reliable Championship xG source is added.
- The neutral fixture skeleton fallback remains available, but official fixtures are preferred when valid.
- Season Projection is a forward projection from the latest completed local data. Completed current-season matches are included as actual table points, and remaining fixtures are simulated from feature values available at refresh time.
