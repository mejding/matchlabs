# Decayed Elo Evaluation Report

## Goal

Test whether season-weighted Elo improves the football prediction model by reducing the influence of older seasons.

The test uses the active production feature family:

- form
- xG / xGA / xG differential
- schedule and fatigue
- shot volume
- Elo

No future information is used. Elo is calculated chronologically before each match, then updated after the match result.

## Method

At each new season boundary, ratings are optionally regressed toward the league mean:

```text
new_rating = 1500 + season_carryover * (old_rating - 1500)
```

Tested carryover values:

1.0, 0.9, 0.85, 0.75, 0.65, 0.5

`1.0` equals the current production behavior: no explicit season decay.

## Model Comparison

| model_name | model_type | season_carryover | accuracy | log_loss | brier_score | calibration_score | ece | train_period | test_period |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| production_without_elo | production_without_elo | nan | 0.4692 | 1.0493 | 0.6304 | 0.0513 | 0.0513 | 2019-08-09 to 2025-01-25 | 2025-01-26 to 2026-05-24 |
| production_plus_current_elo | production_plus_elo | 1.0000 | 0.4879 | 1.0438 | 0.6264 | 0.0429 | 0.0429 | 2019-08-09 to 2025-01-25 | 2025-01-26 to 2026-05-24 |
| production_plus_current_elo_calibrated | calibrated_current_elo | 1.0000 | 0.4879 | 1.1179 | 0.6655 | 0.1133 | 0.1133 | 2019-08-09 to 2025-01-25 | 2025-01-26 to 2026-05-24 |
| production_plus_decayed_elo_carry90 | production_plus_elo | 0.9000 | 0.4841 | 1.0443 | 0.6270 | 0.0522 | 0.0522 | 2019-08-09 to 2025-01-25 | 2025-01-26 to 2026-05-24 |
| production_plus_decayed_elo_carry85 | production_plus_elo | 0.8500 | 0.4822 | 1.0465 | 0.6287 | 0.0528 | 0.0528 | 2019-08-09 to 2025-01-25 | 2025-01-26 to 2026-05-24 |
| production_plus_decayed_elo_carry75 | production_plus_elo | 0.7500 | 0.4785 | 1.0467 | 0.6290 | 0.0412 | 0.0412 | 2019-08-09 to 2025-01-25 | 2025-01-26 to 2026-05-24 |
| production_plus_decayed_elo_carry65 | production_plus_elo | 0.6500 | 0.4748 | 1.0453 | 0.6283 | 0.0429 | 0.0429 | 2019-08-09 to 2025-01-25 | 2025-01-26 to 2026-05-24 |
| production_plus_decayed_elo_carry50 | production_plus_elo | 0.5000 | 0.4729 | 1.0520 | 0.6332 | 0.0534 | 0.0534 | 2019-08-09 to 2025-01-25 | 2025-01-26 to 2026-05-24 |

## Draw Analysis

| model_name | season_carryover | draw_recall | draw_precision | draw_log_loss | draw_calibration_error |
| --- | --- | --- | --- | --- | --- |
| production_without_elo | nan | 0.0219 | 0.2727 | 1.4843 | 0.0499 |
| production_plus_current_elo | 1.0000 | 0.0365 | 0.6250 | 1.4901 | 0.0318 |
| production_plus_current_elo_calibrated | 1.0000 | 0.0365 | 0.6250 | 1.8606 | 0.1115 |
| production_plus_decayed_elo_carry90 | 0.9000 | 0.0292 | 0.5000 | 1.5085 | 0.0517 |
| production_plus_decayed_elo_carry85 | 0.8500 | 0.0073 | 0.3333 | 1.5167 | 0.0588 |
| production_plus_decayed_elo_carry75 | 0.7500 | 0.0292 | 0.3636 | 1.5112 | 0.0351 |
| production_plus_decayed_elo_carry65 | 0.6500 | 0.0219 | 0.3750 | 1.4943 | 0.0449 |
| production_plus_decayed_elo_carry50 | 0.5000 | 0.0146 | 0.2857 | 1.5004 | 0.0534 |

## Key Findings

Current production Elo:

- Log Loss: 1.0438
- Brier Score: 0.6264
- ECE: 0.0429

Best carryover setting by Log Loss:

- Configuration: `production_plus_current_elo`
- Season carryover: 1.00
- Log Loss delta vs current Elo: +0.0000
- Brier delta vs current Elo: +0.0000
- ECE delta vs current Elo: +0.0000

Best actual decayed setting by Log Loss:

- Configuration: `production_plus_decayed_elo_carry90`
- Season carryover: 0.90
- Log Loss delta vs current Elo: +0.0005
- Brier delta vs current Elo: +0.0006
- ECE delta vs current Elo: +0.0093

Best decayed Elo by Brier Score:

- Configuration: `production_plus_current_elo`
- Season carryover: 1.00
- Brier Score: 0.6264

Best decayed Elo by ECE:

- Configuration: `production_plus_decayed_elo_carry75`
- Season carryover: 0.75
- ECE: 0.0412

## Production Decision

Recommended decision: Keep current Elo in production and keep decayed Elo as research-only.

Reason: The decayed Elo configurations do not beat current production Elo on the primary promotion rule.

## Practical Interpretation

Season decay is useful only if teams' old strength ratings are carrying too much stale information. If current Elo already adapts quickly enough through K-factor and recent results, season decay may add little or make ratings too reactive.

## Artifacts

- `evaluation/elo/decayed_elo_model_comparison.csv`
- `evaluation/elo/decayed_elo_draw_analysis.csv`
- `evaluation/elo/decayed_elo_model_comparison.png`
