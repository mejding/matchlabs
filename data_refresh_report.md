# Data Refresh Report

## Run Configuration

- Force download: `True`
- Dry run: `False`
- Train model: `True`
- Calibrate probabilities: `True`
- Run full evaluation: `True`

## Football-Data Refresh

| Source | Season | Status | Rows | Latest date | Path |
| --- | --- | --- | ---: | --- | --- |
| football-data | 1920 | downloaded | 380 | 2020-07-26 | `data/premier_league_1920.csv` |
| football-data | 2021 | downloaded | 380 | 2021-05-23 | `data/premier_league_2021.csv` |
| football-data | 2122 | downloaded | 380 | 2022-05-22 | `data/premier_league_2122.csv` |
| football-data | 2223 | downloaded | 380 | 2023-05-28 | `data/premier_league_2223.csv` |
| football-data | 2324 | downloaded | 380 | 2024-05-19 | `data/premier_league_2324.csv` |
| football-data | 2425 | downloaded | 380 | 2025-05-25 | `data/premier_league_2425.csv` |
| football-data | 2526 | downloaded | 380 | 2026-05-24 | `data/premier_league_2526.csv` |
| football-data | 2627 | downloaded | 10 | 2026-08-24 | `data/premier_league_2627.csv` |

## Understat Refresh

| Source | Season | Status | Rows | Latest date | Path |
| --- | --- | --- | ---: | --- | --- |
| understat | 2019 | downloaded | 380 | 2020-07-26 | `data/understat_epl_2019.json` |
| understat | 2020 | downloaded | 380 | 2021-05-23 | `data/understat_epl_2020.json` |
| understat | 2021 | downloaded | 380 | 2022-05-22 | `data/understat_epl_2021.json` |
| understat | 2022 | downloaded | 380 | 2023-05-28 | `data/understat_epl_2022.json` |
| understat | 2023 | downloaded | 380 | 2024-05-19 | `data/understat_epl_2023.json` |
| understat | 2024 | downloaded | 380 | 2025-05-25 | `data/understat_epl_2024.json` |
| understat | 2025 | downloaded | 380 | 2026-05-24 | `data/understat_epl_2025.json` |
| understat | 2026 | downloaded | 20 | 2026-08-31 | `data/understat_epl_2026.json` |

## Validation

- Football-data rows after Matchweek 2 supplement: `2680`
- First local match date: `2019-08-09`
- Latest local match date after Matchweek 2 supplement: `2026-08-31`
- Local seasons: `1920, 2021, 2122, 2223, 2324, 2425, 2526, 2627`
- xG merge status: `checked_by_training`
- xG rows: ``
- xG missing rows: ``

## Manual Matchweek 2 Supplement

The football-data.co.uk `2627` download available during this refresh contained only Matchweek 1, with 10 rows through `2026-08-24`. Understat had already published all 20 Premier League rows through `2026-08-31`, so Matchweek 2 was added to `data/premier_league_2627.csv` from current result/stat sources before the final model refresh.

Supplemented matches:

| Date | Match | Result |
| --- | --- | --- |
| 2026-08-28 | Crystal Palace v Man City | 1-4 |
| 2026-08-29 | Liverpool v Nott'm Forest | 2-2 |
| 2026-08-29 | Coventry v Hull | 0-1 |
| 2026-08-29 | Bournemouth v Everton | 1-1 |
| 2026-08-29 | Tottenham v Newcastle | 0-2 |
| 2026-08-30 | Sunderland v Fulham | 1-0 |
| 2026-08-30 | Chelsea v Brighton | 4-3 |
| 2026-08-30 | Leeds v Brentford | 1-1 |
| 2026-08-30 | Man United v Ipswich | 5-2 |
| 2026-08-31 | Aston Villa v Arsenal | 0-1 |

Final post-supplement commands:

- `.venv/bin/python train_model.py --mode production`
- `.venv/bin/python calibration_improvement.py`
- `.venv/bin/python evaluate_model.py`
- `.venv/bin/python season_simulation.py --fixture-csv /tmp/upcoming_fixtures_2026_27_model.csv --simulations 10000`
- `.venv/bin/python feature_status_checks.py`

### Matches By Season

| Season | Matches |
| --- | ---: |
| 1920 | 380 |
| 2021 | 380 |
| 2122 | 380 |
| 2223 | 380 |
| 2324 | 380 |
| 2425 | 380 |
| 2526 | 380 |
| 2627 | 20 |

## Commands

### `/Users/sunemejding/Documents/Codex/2026-05-19/build-a-minimal-football-prediction-prototype/.venv/bin/python train_model.py --mode production`

Exit code: `0`

```text
Using existing file: data/premier_league_1920.csv
Using existing file: data/premier_league_2021.csv
Using existing file: data/premier_league_2122.csv
Using existing file: data/premier_league_2223.csv
Using existing file: data/premier_league_2324.csv
Using existing file: data/premier_league_2425.csv
Using existing file: data/premier_league_2526.csv
Using existing file: data/premier_league_2627.csv
Using existing file: data/understat_epl_2019.json
Using existing file: data/understat_epl_2020.json
Using existing file: data/understat_epl_2021.json
Using existing file: data/understat_epl_2022.json
Using existing file: data/understat_epl_2023.json
Using existing file: data/understat_epl_2024.json
Using existing file: data/understat_epl_2025.json
Using existing file: data/understat_epl_2026.json
No injury rows found. Created/used injury template at: data/injuries.csv
Rows used: 2670

Baseline model
Accuracy: 0.4617
Log loss: 1.0684

xG model
Accuracy: 0.4841
Log loss: 1.0468
Brier score: 0.6286
Calibration error: 0.0394

xG + schedule model
Accuracy: 0.4785
Log loss: 1.0565
Brier score: 0.6351
Calibration error: 0.0411

Production xG + schedule + Elo + shot volume model
Accuracy: 0.4636
Log loss: 1.0534
Brier score: 0.6337
Calibration error: 0.0551

xG + schedule + injuries model
Accuracy: 0.4785
Log loss: 1.0565
Brier score: 0.6351
Calibration error: 0.0411

Comparison
Accuracy change: +0.0224
Log loss change: -0.0216
Schedule log loss change vs xG: +0.0098
Schedule Brier change vs xG: +0.0065
Schedule calibration change vs xG: +0.0017
Injury log loss change vs schedule: +0.0000
Injury Brier change vs schedule: +0.0000
Injury calibration change vs schedule: +0.0000
Elo log loss change vs schedule: -0.0031
Elo Brier change vs schedule: -0.0014
Elo calibration change vs schedule: +0.0140
Training mode: production
Saved production xG + schedule + Elo + shot volume model to: models/football_model.joblib
Saved xG + schedule model to: models/football_model_xg_schedule.joblib
Saved xG model to: models/football_model_xg.joblib
Saved baseline model to: models/football_model_baseline.joblib
```
### `/Users/sunemejding/Documents/Codex/2026-05-19/build-a-minimal-football-prediction-prototype/.venv/bin/python calibration_improvement.py`

Exit code: `0`

```text
Using existing file: data/premier_league_1920.csv
Using existing file: data/premier_league_2021.csv
Using existing file: data/premier_league_2122.csv
Using existing file: data/premier_league_2223.csv
Using existing file: data/premier_league_2324.csv
Using existing file: data/premier_league_2425.csv
Using existing file: data/premier_league_2526.csv
Using existing file: data/premier_league_2627.csv
Using existing file: data/understat_epl_2019.json
Using existing file: data/understat_epl_2020.json
Using existing file: data/understat_epl_2021.json
Using existing file: data/understat_epl_2022.json
Using existing file: data/understat_epl_2023.json
Using existing file: data/understat_epl_2024.json
Using existing file: data/understat_epl_2025.json
Using existing file: data/understat_epl_2026.json
{
  "best_method": "sigmoid",
  "deployed": true
}
```
### `/Users/sunemejding/Documents/Codex/2026-05-19/build-a-minimal-football-prediction-prototype/.venv/bin/python evaluate_model.py`

Exit code: `0`

```text
Using existing file: data/premier_league_1920.csv
Using existing file: data/premier_league_2021.csv
Using existing file: data/premier_league_2122.csv
Using existing file: data/premier_league_2223.csv
Using existing file: data/premier_league_2324.csv
Using existing file: data/premier_league_2425.csv
Using existing file: data/premier_league_2526.csv
Using existing file: data/premier_league_2627.csv
Using existing file: data/understat_epl_2019.json
Using existing file: data/understat_epl_2020.json
Using existing file: data/understat_epl_2021.json
Using existing file: data/understat_epl_2022.json
Using existing file: data/understat_epl_2023.json
Using existing file: data/understat_epl_2024.json
Using existing file: data/understat_epl_2025.json
Using existing file: data/understat_epl_2026.json
Validation: time-based split, no random train/test split
Train: 2019-08-09 to 2025-02-01
Test:  2025-02-02 to 2026-08-24
Rows evaluated: 535
Accuracy: 0.4636
Log loss: 1.0534
Brier score: 0.6337
Calibration error: 0.0551
Expected calibration error: 0.0551
Bootstrap models: 30
Mean bootstrap std: 0.0646
Mean stability score: 0.6414
Saved evaluation outputs to: evaluation
```

## Notes

- `football-data.co.uk` CSV files are cached locally unless `--force` is used.
- Understat JSON files are cached locally unless `--force` is used.
- The production model is only updated after `python train_model.py --mode production` succeeds.
- Streamlit Cloud only updates after the changed files are committed and pushed to GitHub.
