# Lineup Stability Report

## Data Coverage

- Historical player appearance rows available: 0

## Model Comparison

| model_version | accuracy | log_loss | Brier_score | calibration_score | expected_calibration_error |
| --- | --- | --- | --- | --- | --- |
| model_a_current_production | 0.5142 | 0.9946 | 0.5946 | 0.0499 | 0.0499 |
| model_b_lineup_continuity | 0.5142 | 0.9946 | 0.5946 | 0.0499 | 0.0499 |
| model_c_continuity_familiarity | 0.5142 | 0.9946 | 0.5946 | 0.0499 | 0.0499 |
| model_d_full_lineup_stability | 0.5142 | 0.9946 | 0.5946 | 0.0499 | 0.0499 |

## Does lineup continuity create genuine predictive signal?

Model D vs Model A:

- Log loss change: 0.0000
- Brier score change: 0.0000
- Calibration change: 0.0000

Top lineup SHAP features:

- `away_shared_starts_score` (familiarity): 0.0000
- `away_lineup_similarity_last_win` (continuity): 0.0000
- `home_shared_starts_score` (familiarity): 0.0000
- `home_shared_minutes_score` (familiarity): 0.0000
- `home_lineup_familiarity_score` (familiarity): 0.0000
- `home_lineup_rotation_rate` (stability): 0.0000
- `away_shared_minutes_score` (familiarity): 0.0000
- `away_lineup_familiarity_score` (familiarity): 0.0000
- `home_manager_stability_score` (stability): 0.0000
- `away_lineup_rotation_rate` (stability): 0.0000
- `away_same_midfield` (continuity): 0.0000
- `home_squad_consistency_score` (stability): 0.0000

## Production Decision

Do not activate lineup stability features. Keep them research-only until real historical lineup rows exist and improve out-of-sample log loss/Brier.

## Leakage Controls

The stability engine never reads the actual current match XI as a pre-match feature. It uses only appearances and manager rows dated before the fixture. Lineup tables are normalized CSV inputs. For pre-match validation, features only use rows with source_collected_at strictly before the match date unless the row is marked as an expected lineup. Actual current-match starting XIs are not used as pre-match features.
