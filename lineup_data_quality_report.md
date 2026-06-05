# Lineup Data Quality Report

## Source Discovery

- existing match_lineups.csv: found at `data/match_lineups.csv`; rows=0; usable=False; File exists but lacks required team/player rows.
- existing player_appearances.csv: found at `data/player_appearances.csv`; rows=0; usable=False; File exists but lacks required team/player rows.
- FBref lineup export: missing at `data/fbref_lineups.csv`; rows=0; usable=False; No local source file found.
- Understat lineup export: missing at `data/understat_lineups.csv`; rows=0; usable=False; No local source file found.
- generic available lineup dataset: missing at `data/lineups.csv`; rows=0; usable=False; No local source file found.

## Normalized Table Coverage

- `data/match_lineups.csv`: 0 rows
- `data/player_appearances.csv`: 0 rows
- `data/formation_history.csv`: 0 rows
- `data/match_substitutions.csv`: 0 rows

## Production Decision

Do not activate lineup stability features. No historical player appearance rows are available locally.

## Leakage Controls

- Actual current-match XIs are not used as pre-match features.
- Historical actual appearances are used only before the fixture date.
- Expected/projected lineups require `source_collected_at` before kickoff.
- No lineup, captain, formation or substitution rows are simulated.
