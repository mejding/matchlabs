# Injury Data Engine Report

## Model Comparison

| model_version | accuracy | log_loss | Brier_score | calibration_score | expected_calibration_error |
| --- | --- | --- | --- | --- | --- |
| model_a_current_production | 0.5142 | 0.9946 | 0.5946 | 0.0499 | 0.0499 |
| model_b_production_injury_features | 0.5142 | 0.9946 | 0.5946 | 0.0499 | 0.0499 |

## Injury Data Coverage

- Historical injury/suspension rows available: 0

## Performance Impact

- Log loss change: 0.0000
- Brier score change: 0.0000
- Calibration change: 0.0000
- ECE change: 0.0000

## SHAP

Top injury/suspension features:

- `away_injured_starters_count`: 0.0000
- `away_injured_expected_starters`: 0.0000
- `away_missing_minutes`: 0.0000
- `away_injured_players_count`: 0.0000
- `away_suspended_players_count`: 0.0000
- `away_suspended_expected_starters`: 0.0000
- `away_missing_xg_contribution`: 0.0000
- `away_missing_minutes_played`: 0.0000
- `away_missing_goals`: 0.0000
- `away_missing_xg`: 0.0000
- `home_missing_market_value`: 0.0000
- `away_missing_xa`: 0.0000

## Production Decision

Do not activate injury features. Keep them research-only until real historical rows exist and out-of-sample log loss/Brier improve.

## Leakage Controls

Injury rows are included only when report_date and unavailable_from are on or before the match date, and expected_return_date is blank or on/after the match date.
