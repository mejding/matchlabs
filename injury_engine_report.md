# Injury Data Engine Report

## Model Comparison

| model_version | accuracy | log_loss | Brier_score | calibration_score | expected_calibration_error |
| --- | --- | --- | --- | --- | --- |
| model_a_current_production | 0.4740 | 1.0595 | 0.6338 | 0.0509 | 0.0509 |
| model_b_injury_only_features | 0.4758 | 1.0598 | 0.6348 | 0.0495 | 0.0495 |
| model_c_suspension_only_features | 0.4740 | 1.0595 | 0.6338 | 0.0509 | 0.0509 |
| model_d_injury_suspension_features | 0.4758 | 1.0598 | 0.6348 | 0.0495 | 0.0495 |

## Injury Data Coverage

- Historical injury/suspension rows available: 16992

## Train/Test Signal Coverage

- injury: train matches with signal `2099` of `2152`; test matches with signal `505` of `538`
- suspension: train matches with signal `0` of `2152`; test matches with signal `71` of `538`

## Performance Impact

- Best availability model: `model_c_suspension_only_features`
- Log loss change: 0.0000
- Brier score change: 0.0000
- Calibration change: 0.0000
- ECE change: 0.0000

## SHAP

Top injury/suspension features:

- `away_suspended_missing_minutes`: 0.0000
- `home_suspended_missing_defensive_contribution`: 0.0000
- `away_suspended_players_count`: 0.0000
- `away_suspended_expected_starters`: 0.0000
- `away_suspended_missing_xg`: 0.0000
- `away_suspended_missing_goals`: 0.0000
- `home_suspended_missing_xa`: 0.0000
- `away_suspended_missing_xa`: 0.0000
- `away_suspended_missing_market_value`: 0.0000
- `home_suspended_missing_market_value`: 0.0000
- `home_suspended_expected_starters`: 0.0000
- `home_suspended_missing_xg`: 0.0000

## Production Decision

Do not activate injury features. Historical availability rows exist, but they did not improve out-of-sample log loss and Brier score versus the current production feature set.

## Leakage Controls

Injury rows are included only when report_date and unavailable_from are on or before the match date, and expected_return_date is blank or on/after the match date.
