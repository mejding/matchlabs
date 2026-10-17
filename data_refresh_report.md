# Data Refresh Report

## Run Configuration

- Force download: `True`
- Dry run: `False`
- Train model: `True`
- Calibrate probabilities: `True`
- Run full evaluation: `True`
- Log upcoming forecasts: `True`
- Refresh season projection: `True`
- Injury provider: `local`

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
| football-data | 2627 | downloaded | 60 | 2026-10-12 | `data/premier_league_2627.csv` |

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
| understat | 2026 | downloaded | 60 | 2026-10-12 | `data/understat_epl_2026.json` |

## Understat Result Import

| Source | Season | Status | Rows | Latest date | Path |
| --- | --- | --- | ---: | --- | --- |
| understat-results | 1920 | complete | 380 | 2020-07-26 | `data/premier_league_1920.csv` |
| understat-results | 2021 | complete | 380 | 2021-05-23 | `data/premier_league_2021.csv` |
| understat-results | 2122 | complete | 380 | 2022-05-22 | `data/premier_league_2122.csv` |
| understat-results | 2223 | complete | 380 | 2023-05-28 | `data/premier_league_2223.csv` |
| understat-results | 2324 | complete | 380 | 2024-05-19 | `data/premier_league_2324.csv` |
| understat-results | 2425 | complete | 380 | 2025-05-25 | `data/premier_league_2425.csv` |
| understat-results | 2526 | complete | 380 | 2026-05-24 | `data/premier_league_2526.csv` |
| understat-results | 2627 | complete | 60 | 2026-10-12 | `data/premier_league_2627.csv` |

## Understat Shot Backfill

| Source | Season | Status | Rows | Latest date | Path |
| --- | --- | --- | ---: | --- | --- |
| understat-shots | 1920 | complete | 380 | 2020-07-26 | `data/premier_league_1920.csv` |
| understat-shots | 2021 | complete | 380 | 2021-05-23 | `data/premier_league_2021.csv` |
| understat-shots | 2122 | complete | 380 | 2022-05-22 | `data/premier_league_2122.csv` |
| understat-shots | 2223 | complete | 380 | 2023-05-28 | `data/premier_league_2223.csv` |
| understat-shots | 2324 | complete | 380 | 2024-05-19 | `data/premier_league_2324.csv` |
| understat-shots | 2425 | complete | 380 | 2025-05-25 | `data/premier_league_2425.csv` |
| understat-shots | 2526 | complete | 380 | 2026-05-24 | `data/premier_league_2526.csv` |
| understat-shots | 2627 | complete | 60 | 2026-10-12 | `data/premier_league_2627.csv` |

## Validation

- Football-data rows: `2720`
- First local match date: `2019-08-09`
- Latest local match date: `2026-10-12`
- Local seasons: `1920, 2021, 2122, 2223, 2324, 2425, 2526, 2627`
- Rows missing shot data: `0`
- xG merge status: `checked_by_training`
- xG rows: ``
- xG missing rows: ``

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
| 2627 | 60 |

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
Rows used: 2720

Baseline model
Accuracy: 0.4554
Log loss: 1.0685

xG model
Accuracy: 0.4827
Log loss: 1.0520
Brier score: 0.6322
Calibration error: 0.0424

xG + schedule model
Accuracy: 0.4681
Log loss: 1.0659
Brier score: 0.6421
Calibration error: 0.0508

Production xG + schedule + Elo + shot volume model
Accuracy: 0.4627
Log loss: 1.0760
Brier score: 0.6475
Calibration error: 0.0627

xG + schedule + injuries model
Accuracy: 0.4663
Log loss: 1.0654
Brier score: 0.6415
Calibration error: 0.0555

Comparison
Accuracy change: +0.0273
Log loss change: -0.0165
Schedule log loss change vs xG: +0.0140
Schedule Brier change vs xG: +0.0099
Schedule calibration change vs xG: +0.0083
Injury log loss change vs schedule: -0.0006
Injury Brier change vs schedule: -0.0006
Injury calibration change vs schedule: +0.0047
Elo log loss change vs schedule: +0.0100
Elo Brier change vs schedule: +0.0054
Elo calibration change vs schedule: +0.0119
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
  "best_method": "temperature_1.12",
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
Train: 2019-08-09 to 2025-02-27
Test:  2025-03-08 to 2026-10-12
Rows evaluated: 549
Accuracy: 0.4627
Log loss: 1.0760
Brier score: 0.6475
Calibration error: 0.0627
Expected calibration error: 0.0627
Bootstrap models: 30
Mean bootstrap std: 0.0641
Mean stability score: 0.6439
Saved evaluation outputs to: evaluation
```
### `/Users/sunemejding/Documents/Codex/2026-05-19/build-a-minimal-football-prediction-prototype/.venv/bin/python forecast_log.py`

Exit code: `0`

```text
Logged 320 upcoming fixture forecasts to evaluation/fixtures_2026_27/forecast_log.csv
Wrote latest snapshot to evaluation/fixtures_2026_27/latest_forecast_snapshot.csv
```
### `/Users/sunemejding/Documents/Codex/2026-05-19/build-a-minimal-football-prediction-prototype/.venv/bin/python season_projection_robustness.py`

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
Using existing file: data/premier_league_1920.csv
Using existing file: data/premier_league_2021.csv
Using existing file: data/premier_league_2122.csv
Using existing file: data/premier_league_2223.csv
Using existing file: data/premier_league_2324.csv
Using existing file: data/premier_league_2425.csv
Using existing file: data/premier_league_2526.csv
Using existing file: data/premier_league_2627.csv
Wrote Season Projection robustness outputs to evaluation/season_projection
```

## Notes

- `football-data.co.uk` CSV files are cached locally unless `--force` is used.
- Understat JSON files are cached locally unless `--force` is used.
- The production model is only updated after `python train_model.py --mode production` succeeds.
- Streamlit Cloud only updates after the changed files are committed and pushed to GitHub.
