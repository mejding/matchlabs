# Data Refresh Report

## Run Configuration

- Force download: `False`
- Dry run: `True`
- Train model: `False`
- Calibrate probabilities: `False`
- Run full evaluation: `False`

## Football-Data Refresh

| Source | Season | Status | Rows | Latest date | Path |
| --- | --- | --- | ---: | --- | --- |
| football-data | 1920 | kept_existing | 380 | 2020-07-26 | `data/premier_league_1920.csv` |
| football-data | 2021 | kept_existing | 380 | 2021-05-23 | `data/premier_league_2021.csv` |
| football-data | 2122 | kept_existing | 380 | 2022-05-22 | `data/premier_league_2122.csv` |
| football-data | 2223 | kept_existing | 380 | 2023-05-28 | `data/premier_league_2223.csv` |
| football-data | 2324 | kept_existing | 380 | 2024-05-19 | `data/premier_league_2324.csv` |
| football-data | 2425 | kept_existing | 380 | 2025-05-25 | `data/premier_league_2425.csv` |
| football-data | 2526 | kept_existing | 380 | 2026-05-24 | `data/premier_league_2526.csv` |

## Understat Refresh

| Source | Season | Status | Rows | Latest date | Path |
| --- | --- | --- | ---: | --- | --- |
| understat | 2019 | kept_existing |  |  | `data/understat_epl_2019.json` |
| understat | 2020 | kept_existing |  |  | `data/understat_epl_2020.json` |
| understat | 2021 | kept_existing |  |  | `data/understat_epl_2021.json` |
| understat | 2022 | kept_existing |  |  | `data/understat_epl_2022.json` |
| understat | 2023 | kept_existing |  |  | `data/understat_epl_2023.json` |
| understat | 2024 | kept_existing |  |  | `data/understat_epl_2024.json` |
| understat | 2025 | kept_existing |  |  | `data/understat_epl_2025.json` |

## Validation

- Football-data rows: `2660`
- First local match date: `2019-08-09`
- Latest local match date: `2026-05-24`
- Local seasons: `1920, 2021, 2122, 2223, 2324, 2425, 2526`
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

## Commands

No training/evaluation commands were run.

## Notes

- `football-data.co.uk` CSV files are cached locally unless `--force` is used.
- Understat JSON files are cached locally unless `--force` is used.
- The production model is only updated after `python train_model.py --mode production` succeeds.
- Streamlit Cloud only updates after the changed files are committed and pushed to GitHub.
