# Sprint 2 Report: Fatigue, Scheduling, Injuries, and Availability

## Validation

All models use the same time-based train/test split. No random train/test split is used.

- Train period: 2019-08-09 to 2024-04-04
- Test period: 2024-04-06 to 2025-05-25

## Model Comparison

| model_version | accuracy | log_loss | Brier_score | calibration_score | expected_calibration_error |
| --- | --- | --- | --- | --- | --- |
| model_a_current_baseline | 0.5230 | 1.0161 | 0.6075 | 0.0498 | 0.0498 |
| model_b_baseline_fatigue | 0.5164 | 1.0129 | 0.6053 | 0.0393 | 0.0393 |
| model_c_baseline_fatigue_europe | 0.5164 | 1.0129 | 0.6053 | 0.0393 | 0.0393 |
| model_d_baseline_fatigue_europe_injury | 0.5164 | 1.0129 | 0.6053 | 0.0393 | 0.0393 |

Best model by log loss: `model_b_baseline_fatigue`.

## 1. Which fatigue features improve prediction quality?

Fatigue impact is measured by Model B vs Model A:

- Log loss change: -0.0032
- Brier score change: -0.0022
- Calibration score change: -0.0105

Top fatigue SHAP features:

- `league_only_away_days_rest`: 0.0352
- `league_only_away_fixture_congestion_score`: 0.0319
- `league_only_home_fixture_congestion_score`: 0.0267
- `league_only_home_matches_last_30_days`: 0.0157
- `league_only_away_matches_last_14_days`: 0.0129
- `league_only_home_matches_last_14_days`: 0.0082
- `league_only_home_days_rest`: 0.0081
- `league_only_away_matches_last_30_days`: 0.0038

## 2. Which injury features improve prediction quality?

Injury impact is measured by Model D vs Model C:

- Log loss change: 0.0000
- Brier score change: 0.0000
- Calibration score change: 0.0000

Top injury/availability SHAP features:

- No injury or availability feature had measurable SHAP contribution. Current injury data may be empty.

## 3. Does fixture congestion matter?

Fixture congestion formula:

`fixture_congestion_score = max(0, 7 - days_rest) + 1.5 * matches_last_14_days + 0.5 * matches_last_30_days`

Congestion SHAP rows:

| feature | mean_abs_shap |
| --- | --- |
| league_only_away_fixture_congestion_score | 0.0319 |
| league_only_home_fixture_congestion_score | 0.0267 |

## 4. Do some teams consistently overperform after midweek matches?

Top teams by points-per-match delta after midweek matches:

- Bournemouth: 0.470 points per match delta over normal rest
- Leicester: 0.390 points per match delta over normal rest
- Nott'm Forest: 0.303 points per match delta over normal rest
- Fulham: 0.223 points per match delta over normal rest
- Man United: 0.188 points per match delta over normal rest

Teams with weakest short-rest deltas:

- Norwich: -0.474 points per match delta under short rest
- Arsenal: -0.358 points per match delta under short rest
- Brentford: -0.275 points per match delta under short rest
- Aston Villa: -0.245 points per match delta under short rest
- Chelsea: -0.225 points per match delta under short rest

Manager-level analysis is not included because the project does not yet contain historical manager tenure data.

## 5. Which new features should move forward into production?

Move features forward when they improve log loss and Brier score without worsening calibration, and when SHAP shows non-trivial contribution.

Current recommendation:

- Move the fatigue features forward because Model B improves log loss, Brier score, and calibration versus Model A.
- Keep European features once `data/european_fixtures.csv` is populated with historical European fixtures.
- Keep injury and availability features once `data/injuries.csv` contains real historical injury/player contribution rows.
- Treat zero-impact injury or Europe conclusions as data-availability findings, not proof that those football factors do not matter.

## Reproducibility and Leakage Controls

- Match features are generated in date order.
- Team histories are read before the current match is appended.
- Injury rows require report dates before the match.
- European fixture rows require fixture dates before the match.
- Random seed: 42

## Data Notes

Injury rows are included only when report_date and unavailable_from are on or before the match date, and expected_return_date is blank or on/after the match date.

availability_score = 100 - weighted injury severity. Severity weights starters, squad depth, missing minutes, missing xG/xA, and missing market value. Scores are clipped to 0-100.
