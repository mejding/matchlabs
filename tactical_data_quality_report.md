# Tactical Data Quality Report

## Source Discovery

Existing local football-data CSV files contain these usable tactical/stat fields:

| field | source_columns |
| --- | --- |
| shots | HS\|AS |
| shots_on_target | HST\|AST |

Fields requested but not available in local football-data CSVs are left null.

## Ingested Rows

- Team-match rows: 4560
- Unique matches: 2280
- Duplicate `(match_id, team)` rows: 0
- Matches without exactly two team rows: 0

## Season Coverage

| season | team_rows | matches | matches_with_two_team_rows |
| --- | --- | --- | --- |
| 1920 | 760 | 380 | 380 |
| 2021 | 760 | 380 | 380 |
| 2122 | 760 | 380 | 380 |
| 2223 | 760 | 380 | 380 |
| 2324 | 760 | 380 | 380 |
| 2425 | 760 | 380 | 380 |

## Available Fields

`attacking_pressure_score`, `shots`, `shots_on_target`, `venue`

## Missing Fields

`PPDA`, `attacking_verticality_score`, `attacking_width_score`, `average_possession`, `blocks`, `build_up_speed`, `counter_attacks`, `counterpress_actions`, `crosses`, `crosses_per_match`, `crossing_score`, `defensive_activity_score`, `defensive_aggression_score`, `defensive_line_height_proxy`, `directness_score`, `fast_break_frequency`, `high_line_score`, `high_press_events`, `interceptions`, `long_balls`, `long_pass_ratio`, `low_block_score`, `pass_completion_pct`, `passes_attempted`, `passes_completed`, `passes_per_sequence`, `possession`, `possession_score`, `press_intensity_score`, `press_success_rate`, `progression_score`, `progressive_carries`, `progressive_passes`, `tackles`, `through_balls`, `turnovers_forced`

## Feature Mapping Formulas

- `attacking_pressure_score = shots + 2 * shots_on_target`
- `possession_score = possession`
- `progression_score = progressive_passes + progressive_carries`
- `directness_score = long_balls / passes_attempted`
- `crossing_score = crosses`
- `defensive_activity_score = tackles + interceptions + blocks`

If a required input is unavailable, the mapped feature remains null.

## Missing Value Report

| field | non_null_rows | missing_rows | coverage_pct |
| --- | --- | --- | --- |
| attacking_pressure_score | 4560 | 0 | 1.0000 |
| shots | 4560 | 0 | 1.0000 |
| shots_on_target | 4560 | 0 | 1.0000 |
| venue | 4560 | 0 | 1.0000 |
| PPDA | 0 | 4560 | 0.0000 |
| attacking_verticality_score | 0 | 4560 | 0.0000 |
| attacking_width_score | 0 | 4560 | 0.0000 |
| average_possession | 0 | 4560 | 0.0000 |
| blocks | 0 | 4560 | 0.0000 |
| build_up_speed | 0 | 4560 | 0.0000 |
| counter_attacks | 0 | 4560 | 0.0000 |
| counterpress_actions | 0 | 4560 | 0.0000 |
| crosses | 0 | 4560 | 0.0000 |
| crosses_per_match | 0 | 4560 | 0.0000 |
| crossing_score | 0 | 4560 | 0.0000 |
| defensive_activity_score | 0 | 4560 | 0.0000 |
| defensive_aggression_score | 0 | 4560 | 0.0000 |
| defensive_line_height_proxy | 0 | 4560 | 0.0000 |
| directness_score | 0 | 4560 | 0.0000 |
| fast_break_frequency | 0 | 4560 | 0.0000 |
| high_line_score | 0 | 4560 | 0.0000 |
| high_press_events | 0 | 4560 | 0.0000 |
| interceptions | 0 | 4560 | 0.0000 |
| long_balls | 0 | 4560 | 0.0000 |
| long_pass_ratio | 0 | 4560 | 0.0000 |
| low_block_score | 0 | 4560 | 0.0000 |
| pass_completion_pct | 0 | 4560 | 0.0000 |
| passes_attempted | 0 | 4560 | 0.0000 |
| passes_completed | 0 | 4560 | 0.0000 |
| passes_per_sequence | 0 | 4560 | 0.0000 |
| possession | 0 | 4560 | 0.0000 |
| possession_score | 0 | 4560 | 0.0000 |
| press_intensity_score | 0 | 4560 | 0.0000 |
| press_success_rate | 0 | 4560 | 0.0000 |
| progression_score | 0 | 4560 | 0.0000 |
| progressive_carries | 0 | 4560 | 0.0000 |
| progressive_passes | 0 | 4560 | 0.0000 |
| tackles | 0 | 4560 | 0.0000 |
| through_balls | 0 | 4560 | 0.0000 |
| turnovers_forced | 0 | 4560 | 0.0000 |
