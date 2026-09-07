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
| football-data | 1920 | failed | 380 | 2020-07-26 | `data/premier_league_1920.csv` |
| football-data | 2021 | failed | 380 | 2021-05-23 | `data/premier_league_2021.csv` |
| football-data | 2122 | failed | 380 | 2022-05-22 | `data/premier_league_2122.csv` |
| football-data | 2223 | failed | 380 | 2023-05-28 | `data/premier_league_2223.csv` |
| football-data | 2324 | failed | 380 | 2024-05-19 | `data/premier_league_2324.csv` |
| football-data | 2425 | failed | 380 | 2025-05-25 | `data/premier_league_2425.csv` |
| football-data | 2526 | failed | 380 | 2026-05-24 | `data/premier_league_2526.csv` |
| football-data | 2627 | failed | 20 | 2026-08-31 | `data/premier_league_2627.csv` |

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
| understat | 2026 | downloaded | 30 | 2026-09-06 | `data/understat_epl_2026.json` |

## Current Season Supplement

Football-data.co.uk still served the 2026/27 CSV through `2026-08-31` at refresh time, while Understat had 30 completed Premier League results through `2026-09-06`. Matchweek 3 was therefore supplemented locally from Understat result/xG rows before retraining.

The supplemental rows include final score and xG. Football-data-only fields such as referee, cards, odds and shot counts are left blank; missing shot counts are ignored by the shot-volume history rather than treated as zero.

## Validation

- Football-data rows: `2690`
- First local match date: `2019-08-09`
- Latest local match date: `2026-09-06`
- Local seasons: `1920, 2021, 2122, 2223, 2324, 2425, 2526, 2627`
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
| 2627 | 30 |

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
Rows used: 2680

Baseline model
Accuracy: 0.4601
Log loss: 1.0644

xG model
Accuracy: 0.4842
Log loss: 1.0433
Brier score: 0.6265
Calibration error: 0.0407

xG + schedule model
Accuracy: 0.4731
Log loss: 1.0540
Brier score: 0.6335
Calibration error: 0.0465

Production xG + schedule + Elo + shot volume model
Accuracy: 0.4861
Log loss: 1.0470
Brier score: 0.6269
Calibration error: 0.0598

xG + schedule + injuries model
Accuracy: 0.4731
Log loss: 1.0540
Brier score: 0.6335
Calibration error: 0.0465

Comparison
Accuracy change: +0.0241
Log loss change: -0.0211
Schedule log loss change vs xG: +0.0107
Schedule Brier change vs xG: +0.0070
Schedule calibration change vs xG: +0.0058
Injury log loss change vs schedule: +0.0000
Injury Brier change vs schedule: +0.0000
Injury calibration change vs schedule: +0.0000
Elo log loss change vs schedule: -0.0070
Elo Brier change vs schedule: -0.0066
Elo calibration change vs schedule: +0.0133
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
Train: 2019-08-09 to 2025-02-14
Test:  2025-02-15 to 2026-08-31
Rows evaluated: 539
Accuracy: 0.4861
Log loss: 1.0470
Brier score: 0.6269
Calibration error: 0.0598
Expected calibration error: 0.0598
Bootstrap models: 30
Mean bootstrap std: 0.0638
Mean stability score: 0.6457
Saved evaluation outputs to: evaluation
```

## Notes

- Post-supplement retraining was run after adding Matchweek 3 rows from Understat:
  - `python train_model.py --mode production`
    - Rows used: `2690`
    - Production accuracy: `0.4796`
    - Production log loss: `1.0598`
    - Production Brier score: `0.6344`
    - Production calibration error: `0.0481`
  - `python calibration_improvement.py`
    - Best method: `sigmoid`
    - Deployed: `true`
  - `python evaluate_model.py`
    - Train: `2019-08-09` to `2025-02-21`
    - Test: `2025-02-22` to `2026-09-06`
    - Rows evaluated: `538`
    - Accuracy: `0.4796`
    - Log loss: `1.0598`
    - Brier score: `0.6344`
    - Expected calibration error: `0.0481`
- `football-data.co.uk` CSV files are cached locally unless `--force` is used.
- Understat JSON files are cached locally unless `--force` is used.
- The production model is only updated after `python train_model.py --mode production` succeeds.
- Streamlit Cloud only updates after the changed files are committed and pushed to GitHub.
