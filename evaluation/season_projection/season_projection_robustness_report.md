# Season Projection Robustness Report

## What Was Fixed

- Season Projection now populates shot-volume features using the same active production feature family used by the Prediction tab.
- Season Projection validates active feature groups before running and exposes Championship-adjusted or fallback rows instead of silently filling missing active features.
- Teams with zero local Premier League history use adjusted Championship data when available.
- If Championship data is missing, teams receive a conservative promoted-team Premier League baseline.
- Championship performance is not treated as Premier League-equivalent input without conversion.

## Shot Volume

Shot volume is now populated in Season Projection. The feature parity audit checks `shots` and `shots_on_target` columns against the Prediction tab logic.

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
| Hull | 52.9424 | 9.7928 | 9 | 0.0294 |
| Tottenham | 38.4466 | 16.7140 | 19 | 0.5013 |
| Coventry | 30.6765 | 18.8865 | 20 | 0.8431 |

## Remaining Limitations

- The project has football-data Championship results and shot volume, but not Championship xG. Promoted-team xG/xGA therefore still use a transparent conservative PL baseline until a reliable Championship xG source is added.
- The neutral fixture skeleton fallback remains available, but official fixtures are preferred when valid.
- Season Projection is a preseason forecast, not a match-by-match simulated form updater; team strength features are fixed at season start while schedule/fatigue uses fixture timing.
