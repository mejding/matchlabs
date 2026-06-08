# Lineup Data Quality Report

## Source

Local raw FBref/soccerdata rows were normalized. Run with `--fetch` to refresh the raw source file.

## Normalized Table Coverage

- `data/match_lineups.csv`: 760 rows
- `data/player_appearances.csv`: 15188 rows
- `data/formation_history.csv`: 760 rows
- `data/match_substitutions.csv`: 0 rows

## Match Coverage

| season | matches_with_lineups |
| --- | --- |
| 2425 | 380 |

## Ingestion Stats

- Raw rows: 15188
- Matched team rows: 15188
- Unmatched team rows: 0

## Validation

| check | status | details |
| --- | --- | --- |
| duplicate_player_appearances | pass | 0 duplicated match/team/player rows. |
| duplicate_team_lineups | pass | 0 duplicated match/team rows. |
| missing_dates | pass | 0 appearance rows without date. |
| starter_count | pass | {"count": 760.0, "mean": 11.0, "std": 0.0, "min": 11.0, "25%": 11.0, "50%": 11.0, "75%": 11.0, "max": 11.0} |
| two_team_lineups_per_match | pass | {"2": 380} |

## Leakage Controls

- Actual lineups are stored as post-match facts with `source_collected_at = date + 1 day`.
- Pre-match features only use appearance rows dated before the fixture being predicted.
- Current-match actual XI is not used for normal production predictions.
- Expected/projected lineups can be added later only if `source_collected_at` is before kickoff.

## Production Decision

Lineup rows are available. Run the lineup stability experiment before activation.
