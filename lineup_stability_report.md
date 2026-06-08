# Lineup Stability Report

## Data Coverage

- Historical player appearance rows available: 15188

## Model Comparison

| model_version | accuracy | log_loss | Brier_score | calibration_score | expected_calibration_error |
| --- | --- | --- | --- | --- | --- |
| model_a_current_production | 0.4860 | 1.0633 | 0.6369 | 0.0592 | 0.0592 |
| model_b_lineup_continuity | 0.4729 | 1.0755 | 0.6438 | 0.0670 | 0.0670 |
| model_c_continuity_familiarity | 0.4748 | 1.0750 | 0.6425 | 0.0789 | 0.0789 |
| model_d_full_lineup_stability | 0.4710 | 1.0775 | 0.6447 | 0.0816 | 0.0816 |

## Does lineup continuity create genuine predictive signal?

Model D vs Model A:

- Log loss change: 0.0142
- Brier score change: 0.0078
- Calibration change: 0.0225

Top lineup SHAP features:

- `away_shared_starts_score` (familiarity): 0.0636
- `away_lineup_rotation_rate` (stability): 0.0354
- `home_squad_consistency_score` (stability): 0.0289
- `away_shared_minutes_score` (familiarity): 0.0270
- `away_squad_consistency_score` (stability): 0.0217
- `home_starting_xi_repeat_count` (continuity): 0.0212
- `home_lineup_rotation_rate` (stability): 0.0201
- `home_same_midfield` (continuity): 0.0163
- `home_shared_starts_score` (familiarity): 0.0132
- `home_shared_minutes_score` (familiarity): 0.0123
- `home_same_back_four` (continuity): 0.0121
- `away_lineup_familiarity_score` (familiarity): 0.0113

## Production Decision

Do not activate lineup stability features. Real 2024/25 lineup rows are available, but the full lineup model worsened out-of-sample log loss and Brier score versus the current production baseline. Keep the features research-only until additional seasons and a new validation run show measurable improvement.

## Leakage Controls

The stability engine never reads the actual current match XI as a pre-match feature. It uses only appearances and manager rows dated before the fixture. Lineup tables are normalized CSV inputs. For pre-match validation, features only use rows with source_collected_at strictly before the match date unless the row is marked as an expected lineup. Actual current-match starting XIs are not used as pre-match features.
