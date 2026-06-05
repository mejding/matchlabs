# Tactical Intelligence Report

## Validation

All models use the same time-based split. No random train/test split is used.

- Train period: 2019-08-09 to 2024-04-04
- Test period: 2024-04-06 to 2025-05-25

## Model Comparison

| model_version | accuracy | log_loss | Brier_score | calibration_score | expected_calibration_error |
| --- | --- | --- | --- | --- | --- |
| model_a_sprint25_baseline | 0.5164 | 1.0129 | 0.6053 | 0.0393 | 0.0393 |
| model_b_baseline_tactical_profiles | 0.5186 | 0.9927 | 0.5938 | 0.0419 | 0.0419 |
| model_c_baseline_profiles_matchups | 0.5164 | 1.0043 | 0.6005 | 0.0580 | 0.0580 |
| model_d_full_tactical_intelligence | 0.5055 | 1.0084 | 0.6024 | 0.0551 | 0.0551 |

## 1. Do tactical profiles improve prediction quality?

Model B vs Model A:

- Log loss change: -0.0202
- Brier score change: -0.0115
- Calibration change: 0.0026

Strongest tactical profile SHAP signals:

- `home_attacking_pressure_score_last10`: 0.0599
- `home_attacking_pressure_score_season`: 0.0526
- `away_attacking_pressure_score_season`: 0.0427
- `home_attacking_pressure_score_last5`: 0.0256
- `away_attacking_pressure_score_last10`: 0.0225
- `away_attacking_pressure_score_last5`: 0.0207

## 2. Do matchup features improve prediction quality?

Model C vs Model B:

- Log loss change: 0.0116
- Brier score change: 0.0067
- Calibration change: 0.0161

Strongest matchup SHAP signals:

- `style_distance_score`: 0.0620

## 3. Which tactical styles are most predictive?

Style embedding SHAP signals:

- `away_vs_home_style_history_points`: 0.0544
- `home_vs_away_style_history_points`: 0.0166

Style clusters:

| style_cluster | style_archetype | matches | points_per_match |
| --- | --- | --- | --- |
| 0 | Balanced | 4560 | 1.3849 |

## 4. Which tactical relationships create measurable edge?

Top style matchup edges:

| style_archetype | opponent_style_archetype | matches | points_per_match |
| --- | --- | --- | --- |
| Balanced | Balanced | 4560 | 1.3849 |

## Production Decision

Only keep tactical features that improve out-of-sample log loss and Brier score without materially worsening calibration. Current local data supports only shots-derived attacking pressure features. Tactical profiles improve log loss and Brier score, but calibration worsens slightly. Matchup and style embedding features should not move forward yet because they add complexity and reduce performance.

## Reproducibility and Leakage Controls

- Profiles use only matches before the fixture.
- Rolling windows are last 5, last 10, and season-to-date.
- Tactical provider rows require `source_collected_at` before the fixture.
- Style history versus archetypes is updated only after each historical match.
- Formations alone are not used as a proxy for playing style.

## Data Notes

Tactical profiles are rolling pre-match profiles over last 5, last 10, and current-season history. Matchup features compare home and away style profiles known before kickoff. Tactical features require event-provider rows in data/team_match_tactics.csv. Rows are used only when date and source_collected_at are before the predicted fixture, so profiles are historically reproducible and leakage-safe.
