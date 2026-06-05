# Injury Data Quality Report

## Source Discovery

- existing injuries.csv: found at `data/injuries.csv`; rows=0; usable=False; File is empty.
- Transfermarkt injury history: missing at `data/transfermarkt_injuries.csv`; rows=0; usable=False; No local source file found.
- Premier Injuries history: missing at `data/premier_injuries.csv`; rows=0; usable=False; No local source file found.

## Coverage

No historical injury/suspension rows are currently available locally.

## Missing Values

- n/a

## Leakage Controls

- A player is unavailable for a fixture only when `report_date <= match_date` and `unavailable_from <= match_date`.
- `expected_return_date` must be blank or on/after the match date.
- Source rows with collection dates after kickoff should not be used in future ingestion.
- No missing injury values are inferred or simulated.

## Production Decision

Do not activate injury features.
