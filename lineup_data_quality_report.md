# Lineup Data Quality Report

## Source

No live fetch requested; only local raw FBref exports/cache were used.

## Normalized Table Coverage

- `data/match_lineups.csv`: 0 rows
- `data/player_appearances.csv`: 0 rows
- `data/formation_history.csv`: 0 rows
- `data/match_substitutions.csv`: 0 rows

## Match Coverage

No seasons covered.

## Ingestion Stats

- Raw rows: 0
- Matched team rows: 0
- Unmatched team rows: 0

## Validation

| check | status | details |
| --- | --- | --- |
| player_appearances | missing | No historical lineup rows available. |

## Leakage Controls

- Actual lineups are stored as post-match facts with `source_collected_at = date + 1 day`.
- Pre-match features only use appearance rows dated before the fixture being predicted.
- Current-match actual XI is not used for normal production predictions.
- Expected/projected lineups can be added later only if `source_collected_at` is before kickoff.

## Production Decision

Do not activate lineup stability features. No historical player appearance rows are available locally yet.
