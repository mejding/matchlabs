# Sprint 4A: Data Discovery & Feature Opportunity Assessment

Date: 2026-06-05

## Executive Summary

The highest-ROI next feature family is **bookmaker odds as a benchmark and potentially opening/pre-match market features**, but only if timing is controlled. The project already has complete football-data.co.uk odds coverage for 2019/20 to 2024/25, and market-only probabilities outperform the current model on the historical test set. However, the current audit found **0 verified SAFE_PREMATCH odds columns**, so odds should remain benchmark-only until opening/pre-match timing is proven.

The best production-safe engineering path is:

1. **Market odds timing hardening**: separate opening/listed, closing, average and max odds; use verified pre-match odds only.
2. **FBref tactical/team-match ingestion**: add possession, passing, carries, tackles, interceptions and blocks from reproducible historical match logs or user-provided exports.
3. **Lineup/substitution/formation ingestion**: use a reliable historical lineup source if licensing and coverage are acceptable.
4. **Injury/player availability intelligence**: defer until a reliable historical availability source exists.

Do not build injuries, suspensions or lineup stability as production features until the project has real historical rows and can prove no future leakage.

## Sources Reviewed

Local project sources:

- `data/premier_league_1920.csv` to `data/premier_league_2425.csv`
- `data/understat_epl_2019.json` to `data/understat_epl_2024.json`
- `data/team_match_tactics.csv`
- `data/injuries.csv`
- `data/match_lineups.csv`
- `data/player_appearances.csv`
- `data/match_substitutions.csv`
- `data/formation_history.csv`
- `odds_column_inventory.md`
- `market_timing_audit_report.md`
- `injury_data_quality_report.md`
- `lineup_data_quality_report.md`
- `tactical_data_quality_report.md`
- `sprint3a_tactical_data_report.md`
- `head_to_head_intelligence_report.md`

External sources reviewed:

- football-data.co.uk data notes: https://www.football-data.co.uk/data
- Understat player/league API documentation: https://understat.readthedocs.io/en/latest/classes/understat.html
- FBref Premier League possession stats: https://fbref.com/en/comps/9/possession/Premier-League-Stats
- FBref Premier League scores and fixtures: https://fbref.com/en/comps/9/schedule/Premier-League-Scores-and-Fixtures
- Transfermarkt injury/suspension pages: https://www.transfermarkt.co.uk/
- Kaggle Barclays Premier League dataset listing: https://www.kaggle.com/datasets/narekzamanyan/barclays-premier-league/data
- Premier League match stats pages: https://www.premierleague.com/

## Local Data Inventory

| Data Area | Local Status | Coverage |
| --- | --- | --- |
| Match results | Available | 6 EPL seasons, 2019/20 to 2024/25, 2,280 matches |
| xG/xGA | Available | Understat JSON, 2019 to 2024 seasons |
| Shots / shots on target | Available | 4,560 team-match rows in `team_match_tactics.csv` |
| Bookmaker odds | Available | 66 match-result odds columns; 39 benchmark-only, 27 unknown timing, 0 safe-prematch |
| Injuries | Template only | `data/injuries.csv`, 0 rows |
| Suspensions | Not separately available | No local historical suspension rows |
| Lineups | Template only | `match_lineups.csv`, `player_appearances.csv`, 0 rows |
| Substitutions | Template only | `match_substitutions.csv`, 0 rows |
| Formations | Template only | `formation_history.csv`, 0 rows |
| Possession/passes/carries | Missing locally | 0 non-null rows in tactical table |
| Tackles/interceptions/blocks | Missing locally | 0 non-null rows in tactical table |
| Pressing metrics | Missing locally | No PPDA, pressure events or coordinates |

## Data Source Discovery

### 1. Injuries

Potential sources:

- Transfermarkt injury history and current injury/suspension pages.
- Premier Injuries / injury table providers.
- Public media/news aggregation.

Historical reproducibility: **MEDIUM-LOW**.

Transfermarkt has public injury histories with injury type, dates and missed matches, and current club injury pages often include expected return and market value. The challenge is not whether injury information exists; the challenge is reconstructing what was known before each kickoff. Historical pages can reflect later corrections.

Useful features:

- injured_players_count
- injured_expected_starters
- long_term_injury_count
- missing_minutes
- missing_xG_contribution
- missing_market_value
- availability_score

Expected predictive value: **HIGH** for high-quality data, **LOW** with incomplete public data.

Implementation cost: **HIGH**.

Recommendation: defer production. Build only after a reliable historical injury snapshot source is found.

### 2. Suspensions

Potential sources:

- Transfermarkt suspension/injury pages.
- Match event data from football-data.co.uk cards.
- FA/league disciplinary records if obtainable.

Historical reproducibility: **MEDIUM** for suspensions inferred from cards, **LOW-MEDIUM** for public availability snapshots.

Card accumulation can be reconstructed from match events only if competition-specific suspension rules are modeled. Direct suspension lists are easier but must be timestamped before kickoff.

Useful features:

- suspended_players_count
- suspended_expected_starters
- missing_minutes_suspended
- defensive_suspension_count
- key_player_suspension_flag

Expected predictive value: **MEDIUM**.

Implementation cost: **HIGH**.

Recommendation: bundle with injuries/player availability, not a standalone Sprint 4 priority.

### 3. Starting Lineups

Potential sources:

- FBref match reports.
- Kaggle Barclays Premier League dataset with starting squads and bench through 2020/21.
- plstats.uk and other historical lineup sites.

Historical reproducibility: **HIGH** for actual post-match lineups; **MEDIUM** for pre-match expected lineups.

Actual starting XIs are known before kickoff only around one hour before match start. They are valid for “pre-kickoff” predictions but not for early-week predictions. For the current app concept, lineup stability should use previous-match lineups only, not current actual XI.

Useful features:

- starting_xi_repeat_pct
- lineup_changes
- same_back_four
- same_midfield
- same_attack
- starters_from_last_win

Expected predictive value: **HIGH**.

Implementation cost: **MEDIUM-HIGH**.

Recommendation: promising, but requires a stable lineup source and careful prediction-timing definition.

### 4. Substitutions

Potential sources:

- FBref match reports.
- Kaggle Barclays Premier League dataset.
- Event datasets.

Historical reproducibility: **HIGH** post-match, **LOW** pre-match for the current match.

Substitution history can inform manager rotation and player load, but current-match substitutions cannot be used pre-match.

Useful features:

- bench_usage_rate
- average_sub_minute
- key_player_minutes_managed
- recent_minutes_load
- rotation_depth_score

Expected predictive value: **MEDIUM**.

Implementation cost: **MEDIUM** if lineups are already ingested.

Recommendation: secondary to starting lineups.

### 5. Formations

Potential sources:

- FBref match reports.
- Kaggle formation datasets.
- Match reports / lineup providers.

Historical reproducibility: **MEDIUM-HIGH**.

Formation labels are often available but can be subjective and coarse. They are less powerful than player-based lineup continuity and tactical event profiles.

Useful features:

- formation_change_flag
- formation_stability_last_5
- formation_matchup
- back_three_vs_back_four

Expected predictive value: **LOW-MEDIUM**.

Implementation cost: **MEDIUM**.

Recommendation: include only if acquired with lineup data.

### 6. Squad Market Values

Potential sources:

- Transfermarkt club/squad market value pages.
- Kaggle/third-party Transfermarkt exports.

Historical reproducibility: **MEDIUM**.

Market values exist, but historical value timing and updates must be aligned to match dates. Values are not a pure measure of team strength; they include age, contract and market sentiment.

Useful features:

- squad_market_value
- market_value_ratio_home_away
- available_squad_market_value
- market_value_weighted_form

Expected predictive value: **MEDIUM-HIGH**.

Implementation cost: **MEDIUM-HIGH**.

Recommendation: useful as a team-strength proxy, but lower priority than odds and lineup/tactical data.

### 7. Player Market Values

Potential sources:

- Transfermarkt player profiles and market value history.
- Third-party Transfermarkt datasets.

Historical reproducibility: **MEDIUM**.

Useful if combined with lineups and injuries. Alone, player values risk duplicating team strength and wage/club size signals.

Useful features:

- starting_xi_market_value
- bench_market_value
- missing_market_value
- value_weighted_availability_score

Expected predictive value: **MEDIUM-HIGH** when joined to lineups/injuries; **LOW-MEDIUM** alone.

Implementation cost: **HIGH**.

Recommendation: not standalone. Use after lineup/player identity pipeline exists.

### 8. Possession

Potential sources:

- FBref squad possession and match reports.
- Premier League match stats pages.
- Event providers.

Historical reproducibility: **HIGH** if from FBref season/match logs; **MEDIUM** if scraped from dynamic PL pages.

Useful features:

- rolling_average_possession
- possession_dominance_score
- possession_delta_vs_opponent
- style_control_score

Expected predictive value: **MEDIUM**.

Implementation cost: **MEDIUM**.

Recommendation: good Sprint 4B candidate via FBref ingestion.

### 9. Progressive Passes

Potential sources:

- FBref passing/progression stats.
- Event data providers.

Historical reproducibility: **HIGH** for season/team logs, **MEDIUM** for match-level depending on availability.

Useful features:

- progressive_passes_last_5
- progression_score
- progression_allowed_proxy
- home_progression_vs_away_press_proxy

Expected predictive value: **MEDIUM-HIGH**.

Implementation cost: **MEDIUM-HIGH**.

Recommendation: strong tactical feature if FBref match-level extraction is reliable.

### 10. Progressive Carries

Potential sources:

- FBref possession stats.
- Event data providers.

Historical reproducibility: **HIGH** for season/team logs, **MEDIUM** for match-level.

Useful features:

- progressive_carries_last_5
- carry_progression_score
- transition_carry_score

Expected predictive value: **MEDIUM**.

Implementation cost: **MEDIUM-HIGH**.

Recommendation: build together with progressive passes.

### 11. Tackles

Potential sources:

- FBref defensive stats.
- Premier League match stats.
- Event data providers.

Historical reproducibility: **HIGH** if match logs are available.

Useful features:

- tackles_last_5
- possession_adjusted_tackles
- defensive_activity_score

Expected predictive value: **LOW-MEDIUM**.

Implementation cost: **MEDIUM**.

Recommendation: lower standalone priority; useful in tactical profiles.

### 12. Interceptions

Potential sources:

- FBref defensive stats.
- Premier League match stats.
- Event data providers.

Historical reproducibility: **HIGH** if match logs are available.

Useful features:

- interceptions_last_5
- possession_adjusted_interceptions
- defensive_disruption_score

Expected predictive value: **LOW-MEDIUM**.

Implementation cost: **MEDIUM**.

Recommendation: include as part of tactical/defensive profile, not standalone.

### 13. Blocks

Potential sources:

- FBref defensive stats.
- Event data providers.

Historical reproducibility: **HIGH** if match logs are available.

Useful features:

- blocks_last_5
- low_block_score
- shot_block_rate

Expected predictive value: **LOW-MEDIUM**.

Implementation cost: **MEDIUM**.

Recommendation: include as part of tactical/defensive profile, not standalone.

### 14. Pressing Metrics

Potential sources:

- Event data providers.
- FBref may support proxies, but full PPDA/high press/counterpress requires event locations and opponent pass zones.

Historical reproducibility: **LOW-MEDIUM** with free public data; **HIGH** with paid event data.

Useful features:

- PPDA
- high_press_events
- press_success_rate
- turnovers_forced
- counterpress_actions
- press_intensity_score

Expected predictive value: **HIGH** if true event data exists, **LOW** if approximated poorly.

Implementation cost: **HIGH**.

Recommendation: avoid until a reliable event data source exists.

### 15. Bookmaker Odds

Potential sources:

- football-data.co.uk.

Historical reproducibility: **HIGH** as historical benchmark; **MEDIUM** as production feature because timing must be verified.

football-data.co.uk documents historical odds and says since 2019/20 it collected two odds sets: first after market opening and second closing odds marked with `C` in headings. The local audit found 66 match-result odds columns, complete coverage for average odds across 2019/20 to 2024/25, but no columns currently classified as SAFE_PREMATCH.

Useful features:

- market_home_prob
- market_draw_prob
- market_away_prob
- market_margin
- market_favorite_class
- model_vs_market_edge

Expected predictive value: **VERY HIGH**.

Implementation cost: **LOW** for benchmark, **MEDIUM** for production-safe opening odds policy.

Recommendation: highest priority, but keep benchmark-only until timing is controlled.

## Prioritization Matrix

| Feature Family | Data Availability | Historical Reliability | Expected Predictive Value | Implementation Cost | Overall Priority |
| --- | --- | --- | --- | --- | --- |
| Bookmaker odds timing / market benchmark | HIGH | HIGH for benchmark, MEDIUM for production | VERY HIGH | LOW-MEDIUM | 1 |
| FBref tactical team-match stats | MEDIUM | HIGH if exported consistently | HIGH | MEDIUM | 2 |
| Starting lineup continuity | MEDIUM | HIGH post-match, MEDIUM pre-match | HIGH | MEDIUM-HIGH | 3 |
| Player availability / injuries / suspensions | MEDIUM | MEDIUM-LOW | HIGH if high quality | HIGH | 4 |
| Squad/player market values | MEDIUM | MEDIUM | MEDIUM-HIGH | MEDIUM-HIGH | 5 |
| Substitutions / minutes load | MEDIUM | HIGH historical, LOW current-match | MEDIUM | MEDIUM | 6 |
| Formations | MEDIUM | MEDIUM-HIGH | LOW-MEDIUM | MEDIUM | 7 |
| Head-to-head | HIGH | HIGH | LOW-MEDIUM | LOW | 8 |
| Possession-only features | MEDIUM | HIGH if from FBref | MEDIUM | MEDIUM | 9 |
| Tackles/interceptions/blocks | MEDIUM | HIGH if from FBref | LOW-MEDIUM | MEDIUM | 10 |
| True pressing metrics | LOW with free data | LOW-MEDIUM | HIGH | HIGH | 11 |

## Answers to Sprint 4A Questions

### 1. Which feature family should be built next?

Build **market odds timing hardening** next, not as blind production features but as a disciplined market layer:

- verified opening/listed odds if timing can be proven
- closing odds as benchmark only
- model-vs-market disagreement analysis
- market calibration and edge reporting

This has the strongest expected impact and lowest implementation cost because the data already exists locally.

### 2. Which data source is most trustworthy?

For current project ROI:

1. **football-data.co.uk** is most trustworthy for match results, shots, cards, corners and historical odds because it is already local, structured and complete.
2. **Understat** is trustworthy for xG/xGA and player xG contribution, already integrated locally.
3. **FBref** is the best next public candidate for tactical/team-match/player stats, but ingestion and scraping/export stability need care.

### 3. Which feature has highest expected impact on Log Loss?

**Market probabilities** have the highest expected impact on log loss. The existing market-only benchmark already beats the current model:

- Current production model log loss: `0.9946`
- Market-only benchmark log loss: `0.9467`

However, this does not mean market odds should be activated in production yet. Timing/leakage must be solved first.

### 4. Which feature is easiest to implement?

The easiest useful feature is **market benchmark probabilities** from existing football-data odds:

- market_home_prob
- market_draw_prob
- market_away_prob
- market_margin
- market_favorite_class

The easiest non-market football feature is **shots-based tactical pressure**, already populated from football-data `HS`, `AS`, `HST`, `AST`.

### 5. Which features should be avoided?

Avoid as production features for now:

- Injuries and suspensions without historical pre-kickoff snapshots.
- Current-match actual lineups if the app is meant to predict days before kickoff.
- Pressing metrics without real event data.
- Full tactical style embeddings built from mostly empty tactical vectors.
- Market odds as production features until opening/pre-match timing is verified.
- Transfermarkt market value features before player/team identity joins are stable.

### 6. Recommended Sprint 4 Roadmap

#### Sprint 4B: Market Timing & Opening Odds Policy

Goal: turn odds from benchmark-only into controlled pre-match candidates if possible.

Tasks:

- Split odds into opening/listed, closing, average, max and single-bookmaker groups.
- Verify football-data collection timing for listed odds per season.
- Train market-only, production, production+verified opening odds and calibrated blends.
- Keep closing odds benchmark-only.
- Update frontend with market benchmark comparison, not production influence.

Success criteria:

- Verified pre-match timing.
- Log loss or Brier improves out-of-sample.
- Calibration does not materially worsen.
- No closing-price leakage.

#### Sprint 4C: FBref Tactical Match Stats Ingestion

Goal: add possession/progression/defensive activity from a richer public stats source.

Tasks:

- Support user-provided FBref CSV exports first, avoiding brittle scraping.
- Populate possession, progressive passes, progressive carries, tackles, interceptions, blocks.
- Build rolling last 5, last 10 and season-to-date profiles.
- Compare against current production model and shots-pressure candidate.

Success criteria:

- At least one full season with high coverage.
- No future leakage.
- Improved log loss or Brier.
- SHAP shows meaningful non-zero tactical contribution.

#### Sprint 4D: Lineup Continuity Data Ingestion

Goal: build reliable historical player appearance tables.

Tasks:

- Evaluate Kaggle lineup dataset coverage and license.
- Add FBref/plstats lineup ingestion if reproducible.
- Populate starting XI, bench, substitutions and formations.
- Use only previous-match lineup continuity for early predictions.
- Treat current announced XI as optional matchday mode only.

Success criteria:

- Multiple seasons of lineup rows.
- Timing mode clearly defined.
- Lineup features improve out-of-sample metrics.

#### Sprint 4E: Injury / Availability Research

Goal: decide whether injury data is worth building.

Tasks:

- Test Transfermarkt injury history availability and player matching.
- Join unavailable players to Understat player xG and minutes.
- Build long-term injury features first, because they are easier to reconstruct historically.
- Compare only after coverage is audited.

Success criteria:

- Reliable historical injury/suspension rows.
- Clear `report_date <= match_date` rule.
- Missing xG/minutes/market value are not defaulted to zero silently.
- Out-of-sample improvement.

## Final Recommendation

The next build should be:

1. **Market timing hardening** because it is highest signal and lowest cost.
2. **FBref tactical ingestion** because it adds real football information that is not already captured by xG/form.
3. **Lineup continuity** if a reliable historical lineup source is accepted.
4. **Injury availability** only after a source proves historically reproducible.

Do not implement new injury, lineup or pressing features until data coverage is solved. The project should stay strict: features only move into production when they are historically reproducible, no-leakage, complete enough, and improve out-of-sample log loss or Brier score.
