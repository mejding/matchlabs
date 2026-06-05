# Sprint 3A Tactical Data Report

## Executive Summary

Sprint 3A populated `data/team_match_tactics.csv` with real historical team-match rows from the existing `football-data.co.uk` Premier League CSV files.

No tactical data was invented or simulated.

The local data source contains:

- shots
- shots on target

It does not contain:

- possession
- passes
- pass completion
- progressive passes
- progressive carries
- crosses
- long balls
- tackles
- interceptions
- blocks
- PPDA or pressing events

The Tactical Intelligence Engine now has one reliable derived tactical feature family:

```text
attacking_pressure_score = shots + 2 * shots_on_target
```

## 1. Which Tactical Data Fields Are Now Available?

Available with 100% coverage:

| Field | Source | Coverage |
| --- | --- | --- |
| `shots` | football-data `HS` / `AS` | 4560 / 4560 team-match rows |
| `shots_on_target` | football-data `HST` / `AST` | 4560 / 4560 team-match rows |
| `attacking_pressure_score` | derived from shots and shots on target | 4560 / 4560 team-match rows |
| `venue` | home/away team row mapping | 4560 / 4560 team-match rows |

Mapped formula:

```text
attacking_pressure_score = shots + 2 * shots_on_target
```

This is not a full tactical style model. It is a lightweight attacking-volume proxy.

## 2. How Many Matches and Seasons Are Covered?

Coverage:

| Season | Team rows | Matches | Matches with two team rows |
| --- | ---: | ---: | ---: |
| 2019/20 | 760 | 380 | 380 |
| 2020/21 | 760 | 380 | 380 |
| 2021/22 | 760 | 380 | 380 |
| 2022/23 | 760 | 380 | 380 |
| 2023/24 | 760 | 380 | 380 |
| 2024/25 | 760 | 380 | 380 |

Total:

- team-match rows: `4560`
- unique matches: `2280`
- duplicate `(match_id, team)` rows: `0`
- matches without exactly two team rows: `0`

## 3. Which Fields Have Missing Values?

Missing because they are not present in the current local data sources:

- `possession`
- `passes_attempted`
- `passes_completed`
- `pass_completion_pct`
- `progressive_passes`
- `progressive_carries`
- `crosses`
- `long_balls`
- `tackles`
- `interceptions`
- `blocks`
- `PPDA`
- `high_press_events`
- `press_success_rate`
- `turnovers_forced`
- `counterpress_actions`
- `crosses_per_match`
- `through_balls`
- `counter_attacks`
- `fast_break_frequency`
- `attacking_width_score`
- `attacking_verticality_score`
- `defensive_line_height_proxy`
- `low_block_score`
- `high_line_score`
- `defensive_activity_score`
- `defensive_aggression_score`

The ingestion pipeline leaves these values null. They are not filled with zero and they are not estimated.

## 4. Do Tactical Features Improve Out-of-Sample Prediction Quality?

Validation setup:

- train period: `2019-08-09 to 2024-04-04`
- test period: `2024-04-06 to 2025-05-25`
- split type: time-based, no random split

Model comparison:

| Model | Accuracy | Log Loss | Brier Score | Calibration / ECE |
| --- | ---: | ---: | ---: | ---: |
| Model A: Sprint 2.5 baseline | 0.5164 | 1.0129 | 0.6053 | 0.0393 |
| Model B: baseline + available tactical profiles | 0.5186 | 0.9927 | 0.5938 | 0.0419 |
| Model C: profiles + matchup features | 0.5164 | 1.0043 | 0.6005 | 0.0580 |
| Model D: full tactical intelligence | 0.5055 | 1.0084 | 0.6024 | 0.0551 |

Model B improves:

- accuracy: `+0.0022`
- log loss: `-0.0202`
- Brier score: `-0.0115`

But calibration worsens slightly:

- calibration/ECE: `+0.0026`

Interpretation:

The shots-derived attacking pressure profile has useful predictive signal, but it is not yet a complete tactical model.

Matchup and style embedding features do not improve performance. They add complexity and reduce calibration/performance because the underlying style data is too thin.

## 5. Which Tactical Features Have Non-Zero SHAP Importance?

Non-zero tactical profile features:

| Feature | Mean absolute SHAP |
| --- | ---: |
| `home_attacking_pressure_score_last10` | 0.0599 |
| `home_attacking_pressure_score_season` | 0.0526 |
| `away_attacking_pressure_score_season` | 0.0427 |
| `home_attacking_pressure_score_last5` | 0.0256 |
| `away_attacking_pressure_score_last10` | 0.0225 |
| `away_attacking_pressure_score_last5` | 0.0207 |

SHAP by group:

| Feature group | Mean absolute SHAP |
| --- | ---: |
| `xG` | 0.3932 |
| `tactical_profile` | 0.2240 |
| `baseline` | 0.1517 |
| `fatigue` | 0.0843 |
| `style_embedding` | 0.0710 |
| `matchup` | 0.0620 |
| `lineup_stability` | 0.0000 |

Important limitation:

The apparent `style_embedding` and `matchup` signal is not reliable enough for production because style clusters are still based on very limited tactical data. Model C and Model D perform worse than Model B.

## 6. Should Tactical Features Move Into Production Yet?

Recommendation:

Do not move the full Tactical Intelligence Engine into production yet.

Reason:

- only shots and shots-on-target are currently available
- possession, passing, pressing, crossing, and defensive event data are missing
- matchup features reduce out-of-sample performance
- style embeddings are not yet based on rich tactical archetypes
- calibration worsens slightly even for the best tactical model

Candidate feature to keep for further testing:

```text
attacking_pressure_score rolling profiles
```

Specifically:

- `home_attacking_pressure_score_last5`
- `home_attacking_pressure_score_last10`
- `home_attacking_pressure_score_season`
- `away_attacking_pressure_score_last5`
- `away_attacking_pressure_score_last10`
- `away_attacking_pressure_score_season`

Production gate:

These features should only move forward after:

- calibration is improved or post-calibrated
- the improvement is stable in rolling backtests
- at least one richer event-data source is added
- SHAP remains non-zero on future seasons

## Data Source Notes

Local source discovery found these available fields:

| Requested field | Local source column |
| --- | --- |
| `shots` | `HS` / `AS` |
| `shots_on_target` | `HST` / `AST` |

FBref ingestion support was added through `fbref_ingestion.py`, but no FBref export files are currently present under:

```text
data/fbref/
```

If FBref team match stats are added there later, the pipeline can map additional fields such as possession, passes, progressive passes, carries, crosses, tackles, interceptions, and blocks.

## Output Files

- `data/team_match_tactics.csv`
- `tactical_data_quality_report.md`
- `experiments/tactical_intelligence_results.csv`
- `evaluation/tactical_intelligence/tactical_missing_values.csv`
- `evaluation/tactical_intelligence/tactical_season_coverage.csv`
- `evaluation/tactical_intelligence/shap_feature_rankings.csv`
- `evaluation/tactical_intelligence/shap_group_rankings.csv`
- `evaluation/tactical_intelligence/model_comparison.csv`
