# Injury Data Quality Report

## Source Discovery

- existing injuries.csv: found at `data/injuries.csv`; rows=16992; usable=True; Found local source file.
- Transfermarkt injury history: missing at `data/transfermarkt_injuries.csv`; rows=0; usable=False; No local source file found.
- Premier Injuries history: missing at `data/premier_injuries.csv`; rows=0; usable=False; No local source file found.
- withqwerty availability-data: found at `/tmp/availability-data`; rows=220; usable=True; Found availability-data JSON files.

## Remote Provider Refresh

- No remote provider attempted.

## Coverage

Rows: 16992. Date range: 2019-08-09 to 2026-05-24. Teams covered: 22.

## Missing Values

- `report_date`: 0
- `team`: 0
- `player`: 0
- `unavailable_from`: 0
- `expected_return_date`: 0
- `status_type`: 0
- `injury_or_suspension`: 0
- `is_expected_starter`: 0
- `is_key_player`: 0
- `is_long_term_injury`: 0
- `is_suspended`: 0
- `minutes_played_last_365`: 0
- `goals_last_365`: 0
- `xg_contribution_last_365`: 0
- `xa_contribution_last_365`: 0
- `defensive_contribution_last_365`: 0
- `market_value_eur`: 0
- `source`: 0
- `source_url`: 0
- `source_collected_at`: 0

## Leakage Controls

- A player is unavailable for a fixture only when `report_date <= match_date` and `unavailable_from <= match_date`.
- `expected_return_date` must be blank or on/after the match date.
- Source rows with collection dates after kickoff should not be used in future ingestion.
- No missing injury values are inferred or simulated.

## Production Decision

Evaluate before activation; do not activate unless out-of-sample metrics improve.
