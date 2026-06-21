# Season Projection Robustness Report

## What Was Fixed

- Season Projection now populates shot-volume features using the same active production feature family used by the Prediction tab.
- Season Projection validates active feature groups before running and exposes fallback rows instead of silently filling missing active features.
- Teams with zero local Premier League history are marked as fallback teams and receive a conservative promoted-team Premier League baseline.
- Championship performance is not treated as Premier League-equivalent input.

## Shot Volume

Shot volume is now populated in Season Projection. The feature parity audit checks `shots` and `shots_on_target` columns against the Prediction tab logic.

## Feature Parity

- Validation status: `Warning`
- Non-promoted max feature difference: `0.00000000`
- Intentional promoted adjustment rows: `600`

## Promoted-Team Handling

| average_points | median_points | average_position | median_position | relegation_rate | goals_for_per_match | goals_against_per_match |
| --- | --- | --- | --- | --- | --- | --- |
| 32.2778 | 26.0000 | 16.2778 | 18.0000 | 0.6111 | 1.0395 | 1.8801 |

Fallback teams:

| team | source_league | fallback_reason | local_pl_match_count |
| --- | --- | --- | --- |
| Coventry | Promoted-team conservative Premier League baseline | No local Premier League history; Championship data is not treated as Premier League-equivalent. | 0 |
| Hull | Promoted-team conservative Premier League baseline | No local Premier League history; Championship data is not treated as Premier League-equivalent. | 0 |

## Tottenham / Coventry / Hull Audit

Feature audit:

| team | local_pl_match_count | fallback_used | source_league | raw_recent_form_points_last5 | recent_form_points_last5 | raw_xg_strength_last5 | xg_strength_last5 | raw_xga_strength_last5 | xga_strength_last5 | raw_shots_avg_last5 | shots_avg_last5 | elo_rating |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| Coventry | 0 | True | Promoted-team conservative Premier League baseline | 0.0000 | 3.4211 | 0.0000 | 0.9875 | 0.0000 | 1.7861 | 0.0000 | 10.6600 | 1500.0000 |
| Hull | 0 | True | Promoted-team conservative Premier League baseline | 0.0000 | 3.4211 | 0.0000 | 0.9875 | 0.0000 | 1.7861 | 0.0000 | 10.6600 | 1500.0000 |
| Tottenham | 266 | False | Premier League historical data | 10.0000 | 10.0000 | 1.4470 | 1.4470 | 0.9206 | 0.9206 | 13.4000 | 13.4000 | 1473.2938 |

Projection:

| team | expected_points | expected_position | projected_position | relegation_probability |
| --- | --- | --- | --- | --- |
| Tottenham | 45.7489 | 13.1979 | 13 | 0.1629 |
| Coventry | 42.0463 | 14.6852 | 16 | 0.2710 |
| Hull | 42.0409 | 14.8426 | 18 | 0.2863 |

## Remaining Limitations

- The project still lacks reliable historical Championship xG and shot-volume data, so promoted-team inputs use a transparent conservative PL baseline.
- The neutral fixture skeleton fallback remains available, but official fixtures are preferred when valid.
- Season Projection is a preseason forecast, not a match-by-match simulated form updater; team strength features are fixed at season start while schedule/fatigue uses fixture timing.
