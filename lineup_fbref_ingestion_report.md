# FBref Lineup Data Engine Report

Date: 2026-06-08

## Goal

Build a reproducible path for ingesting historical Premier League lineup data through FBref/soccerdata and test whether lineup stability can improve the prediction model.

## What Was Added

- `fbref_lineup_ingestion.py`
- `requirements-ingestion.txt`
- Local soccerdata cache/log paths under `data/fbref/`
- Validation output:
  - `evaluation/lineup_stability_engine/lineup_data_validation.csv`
- Updated gitignore rules for scraper cache/lock files.

## Data Ingestion Status

The ingestion engine now supports:

1. Local raw FBref lineup exports in `data/fbref/lineup_exports/*.csv`
2. Cached raw soccerdata output in `data/fbref_lineups_raw.csv`
3. Optional live soccerdata fetch:

```bash
.venv/bin/python -m pip install -r requirements-ingestion.txt
.venv/bin/python fbref_lineup_ingestion.py --fetch --seasons 2024
```

## Current Result

No historical lineup rows were populated in this run.

Reason:

- `soccerdata` installed successfully.
- The FBref reader uses SeleniumBase/undetected Chrome mode.
- SeleniumBase downloaded ChromeDriver successfully after network approval.
- The current Mac runtime failed to launch UC mode because Rosetta 2 is missing:
  - `Missing a macOS dependency: Your Mac needs Rosetta 2 to use UC Mode`

Because no real FBref rows were obtained, the normalized lineup tables remain empty:

- `data/match_lineups.csv`: 0 rows
- `data/player_appearances.csv`: 0 rows
- `data/formation_history.csv`: 0 rows
- `data/match_substitutions.csv`: 0 rows

## Model Experiment

The lineup stability experiment was rerun after the ingestion work:

```bash
.venv/bin/python lineup_stability_engine_experiments.py
```

Output:

```json
{
  "appearance_rows": 0,
  "activate": false
}
```

Interpretation:

- The experiment pipeline works.
- No lineup features can be evaluated yet because there are no historical player appearance rows.
- Lineup features must remain research-only and inactive in production.

## Leakage Controls

The ingestion design prevents leakage by default:

- Actual lineups are stored as post-match facts with `source_collected_at = date + 1 day`.
- Pre-match features only use rows before the fixture date.
- Current-match actual XI is not used in normal production predictions.
- Expected/projected lineups can be used later only if timestamped before kickoff.

## Recommended Next Step

Use one of these routes:

1. Install Rosetta 2 locally and rerun the soccerdata fetch.
2. Provide FBref lineup CSV exports in `data/fbref/lineup_exports/`.
3. Run the ingestion on a Linux/CI environment where soccerdata/SeleniumBase can launch Chrome cleanly.

Only after at least one full season of real lineup rows is populated should we rerun the model comparison and consider production activation.
