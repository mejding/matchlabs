# FBref Lineup Data Engine Report

Date: 2026-06-08

## Goal

Build a reproducible path for ingesting historical Premier League lineup data through FBref/soccerdata and test whether lineup stability can improve the prediction model.

## What Was Added

- `fbref_lineup_ingestion.py`
- `requirements-ingestion.txt`
- Local soccerdata cache/log paths under `data/fbref/`
- Raw FBref/soccerdata exports:
  - `data/fbref_lineups_raw.csv`
  - `data/fbref_schedule_raw.csv`
- Normalized lineup tables:
  - `data/match_lineups.csv`
  - `data/player_appearances.csv`
  - `data/formation_history.csv`
  - `data/match_substitutions.csv`
- Validation output:
  - `evaluation/lineup_stability_engine/lineup_data_validation.csv`

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

The FBref/soccerdata ingestion successfully populated one full Premier League season:

- Season covered: 2024/25
- Matches covered: 380
- Team lineup rows: 760
- Player appearance rows: 15,188
- Formation rows: 760
- Substitution rows: 0
- Matched raw rows: 15,188
- Unmatched raw rows: 0

Validation passed:

- No duplicate team-lineup rows.
- No duplicate player appearances per match/team/player.
- Every match has two team lineups.
- Every team lineup has exactly 11 starters.

## Model Experiment

The lineup stability experiment was rerun after ingestion:

```bash
.venv/bin/python lineup_stability_engine_experiments.py
```

Output:

```json
{
  "appearance_rows": 15188,
  "activate": false
}
```

## Model Comparison

| model_version | accuracy | log_loss | Brier_score | calibration_score | expected_calibration_error |
| --- | --- | --- | --- | --- | --- |
| model_a_current_production | 0.4860 | 1.0633 | 0.6369 | 0.0592 | 0.0592 |
| model_b_lineup_continuity | 0.4729 | 1.0755 | 0.6438 | 0.0670 | 0.0670 |
| model_c_continuity_familiarity | 0.4748 | 1.0750 | 0.6425 | 0.0789 | 0.0789 |
| model_d_full_lineup_stability | 0.4710 | 1.0775 | 0.6447 | 0.0816 | 0.0816 |

## Interpretation

Lineup features have measurable SHAP contribution, especially shared starts, rotation rate, and squad consistency. However, they do not improve the validation metrics in this run.

Compared with the current production baseline, the full lineup model worsened:

- Log loss by 0.0142
- Brier score by 0.0078
- Calibration/ECE by 0.0225

Because the goal is stronger out-of-sample probability quality, these features should not be activated in production yet.

## Leakage Controls

The ingestion design prevents leakage by default:

- Actual lineups are stored as post-match facts with `source_collected_at = date + 1 day`.
- Pre-match features only use rows before the fixture date.
- Current-match actual XI is not used in normal production predictions.
- Expected/projected lineups can be used later only if timestamped before kickoff.

## Production Decision

Keep lineup stability research-only.

Reason:

- One full season of real lineup rows is now available.
- The data is historically reproducible and passes validation.
- Out-of-sample log loss, Brier score, and calibration all worsened after adding lineup features.

## Recommended Next Step

Do not add lineup features to the Streamlit production prediction model yet.

The next useful test is to ingest more historical seasons via FBref/soccerdata and rerun the same experiment. If multiple seasons improve log loss or Brier without hurting calibration, lineup stability can be reconsidered as a production candidate.
