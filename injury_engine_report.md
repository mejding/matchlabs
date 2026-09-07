# Injury Data Engine Report

## Model Comparison

| model_version | accuracy | log_loss | Brier_score | calibration_score | expected_calibration_error |
| --- | --- | --- | --- | --- | --- |
| model_a_current_production | 0.4740 | 1.0595 | 0.6338 | 0.0509 | 0.0509 |
| model_b_production_injury_features | 0.4758 | 1.0600 | 0.6349 | 0.0491 | 0.0491 |

## Injury Data Coverage

- Historical injury/suspension rows available: 16992

## Performance Impact

- Log loss change: 0.0005
- Brier score change: 0.0011
- Calibration change: -0.0018
- ECE change: -0.0018

## SHAP

Top injury/suspension features:

- `away_missing_minutes`: 0.0294
- `home_missing_minutes`: 0.0253
- `away_injured_starters_count`: 0.0207
- `home_injured_players_count`: 0.0107
- `away_injured_players_count`: 0.0048
- `home_injured_starters_count`: 0.0046
- `away_missing_market_value`: 0.0000
- `away_missing_xa`: 0.0000
- `away_missing_xg_contribution`: 0.0000
- `away_missing_xg`: 0.0000
- `away_missing_goals`: 0.0000
- `away_missing_minutes_played`: 0.0000

## Production Decision

Do not activate injury features. Historical availability rows exist, but they did not improve out-of-sample log loss and Brier score versus the current production feature set.

## Leakage Controls

Injury rows are included only when report_date and unavailable_from are on or before the match date, and expected_return_date is blank or on/after the match date.
