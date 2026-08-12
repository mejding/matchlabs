# Minimal Football Prediction Prototype

Football analytics and prediction platform powered by machine learning. Predicts match outcomes, calculates fair odds, explains predictions with SHAP, and simulates full league seasons using historical results, xG, form and advanced statistical modelling.

This is a deliberately simple Python prototype that predicts Premier League match outcomes:

- home win
- draw
- away win

It downloads historical Premier League CSV files from [football-data.co.uk](https://www.football-data.co.uk/) and expected goals data from [Understat](https://understat.com/), creates a few basic form and xG features with pandas, trains an XGBoost multiclass model, and saves a local model file for predictions.

## Files

- `requirements.txt` - Python dependencies.
- `train_model.py` - Downloads data, builds features, trains and evaluates the model.
- `predict.py` - Loads the saved model and predicts probabilities for one fixture.
- `app.py` - Simple Streamlit user interface for testing predictions.
- `refresh_data.py` - Refreshes local data, validates coverage, and optionally retrains/calibrates/evaluates the model.
- `evaluate_model.py` - Professional probabilistic evaluation runner.
- `bootstrap_confidence.py` - Bootstrap and ensemble prediction intervals.
- `prediction_confidence.py` - Match-level confidence labels and stability scoring.
- `calibration_analysis.py` - Calibration analysis wrapper with ECE and diagnosis.
- `ensemble_predictor.py` - Optional ensemble mode with varied seeds and training subsets.
- `uncertainty_visualizations.py` - Bootstrap and stability visualizations.
- `fatigue_features.py` - Historical rest, congestion, and European scheduling features.
- `injury_features.py` - Historical injury feature pipeline.
- `availability_scores.py` - Availability, lineup strength, and injury severity scores.
- `feature_experiments.py` - Sprint 2 model comparison runner.
- `fatigue_analysis.py` - Exploratory team-level congestion analysis.
- `lineup_data.py` - Normalized lineup table templates.
- `lineup_stability_features.py` - Lineup continuity, familiarity, and stability features.
- `lineup_stability_experiments.py` - Lineup Stability Engine model comparison runner.
- `tactical_data.py` - Tactical event/profile input templates.
- `tactical_data_ingestion.py` - Sprint 3A ingestion from local football-data tactical/stat fields.
- `fbref_ingestion.py` - Optional ingestion support for user-provided FBref CSV exports.
- `tactical_features.py` - Tactical profiles, matchups, clusters, and style embeddings.
- `tactical_analysis.py` - Tactical discovery and style matchup reports.
- `tactical_intelligence_experiments.py` - Tactical Intelligence Engine model comparison runner.
- `opponent_adjusted_xg_features.py` - Opponent-adjusted xG attack/defense ratings and Poisson baseline features.
- `opponent_adjusted_xg_experiments.py` - Sprint 4D model comparison, SHAP, permutation and redundancy analysis.
- `non_pl_context_features.py` - Pre-season, cup, European and Championship context feature builder.
- `non_pl_context_experiments.py` - Non-PL context model comparison and production-readiness report.
- `experiment_tracker.py` - CSV and JSON experiment tracking.
- `shap_analysis.py` - Convenience wrapper for SHAP helpers.
- `calibration/calibration.py` - Calibration metrics and plots.
- `evaluation/model_evaluation.py` - Time split, metrics, confidence tables, weak spot analysis.
- `explainability/shap_analysis.py` - SHAP global and local explanations.
- `visualizations/plots.py` - Matplotlib visualizations.
- `README.md` - Project notes and usage instructions.

## Setup

Create and activate a virtual environment:

```bash
python -m venv .venv
source .venv/bin/activate
```

Install dependencies:

```bash
pip install -r requirements.txt
```

## Train the model

Run:

```bash
python train_model.py
```

What happens:

1. The script downloads Premier League CSV files from `football-data.co.uk`.
2. It downloads Premier League xG data from Understat.
3. It keeps the core match columns:
   - `Date`
   - `HomeTeam`
   - `AwayTeam`
   - `FTHG` full-time home goals
   - `FTAG` full-time away goals
   - `FTR` full-time result
4. It merges football-data and Understat matches by season, date, home team, and away team.
5. It sorts matches by date so form features only use games that happened before the match being predicted.
6. It creates these baseline features:
   - `home_team_points_last_5`
   - `away_team_points_last_5`
   - `home_goals_scored_avg`
   - `away_goals_scored_avg`
   - `home_advantage`
7. It creates these xG features:
   - `home_xg_avg`
   - `away_xg_avg`
   - `home_xga_avg`
   - `away_xga_avg`
   - `home_xg_diff`
   - `away_xg_diff`
8. It creates these scheduling and fatigue features:
   - `home_days_rest`
   - `away_days_rest`
   - `home_matches_last_14_days`
   - `away_matches_last_14_days`
   - `home_had_midweek_match`
   - `away_had_midweek_match`
   - `home_days_since_last_match`
   - `away_days_since_last_match`
9. It creates these Elo team-strength features with the validated `k30_ha75_nomov_carry100` configuration:
   - `home_elo`
   - `away_elo`
   - `elo_difference`
   - `elo_ratio`
   - `elo_gap_bucket`
   - `elo_recent_change`
   - `home_elo_trend`
   - `away_elo_trend`
   - `rolling_elo_form`
10. It creates these shot-volume features from football-data.co.uk shots and shots-on-target columns:
   - `home_shots_avg_last5`
   - `away_shots_avg_last5`
   - `home_shots_on_target_avg_last5`
   - `away_shots_on_target_avg_last5`
   - `home_shots_avg_last10`
   - `away_shots_avg_last10`
   - `home_shots_on_target_avg_last10`
   - `away_shots_on_target_avg_last10`
   - `home_shots_avg_season`
   - `away_shots_avg_season`
   - `home_shots_on_target_avg_season`
   - `away_shots_on_target_avg_season`
11. It can create these research-only injury features from `data/injuries.csv` when real historical rows exist:
   - `home_number_of_injured_starters`
   - `away_number_of_injured_starters`
   - `home_missing_minutes_played`
   - `away_missing_minutes_played`
   - `home_missing_xg_contribution`
   - `away_missing_xg_contribution`
   - `home_missing_market_value`
   - `away_missing_market_value`
12. It trains five XGBoost multiclass classifiers:
   - a baseline model without xG
   - an xG model with the extra Understat features
   - an xG + schedule model with fatigue features
   - a production xG + schedule + Elo + shot volume model
   - an xG + schedule + injuries model
13. It evaluates the models with accuracy, log loss, Brier score, and calibration error.
14. It saves the xG + schedule + Elo + shot volume production model to `models/football_model.joblib`.
15. It saves the xG + schedule model to `models/football_model_xg_schedule.joblib`.
16. It saves the xG-only model to `models/football_model_xg.joblib`.
17. It saves the baseline model to `models/football_model_baseline.joblib`.
18. In research mode, it saves the injury model separately to `models/football_model_xg_schedule_injury_research.joblib`.

The script also writes evaluation metrics to:

```text
models/metrics.json
```

Latest local comparison:

```text
Baseline log loss: 1.0306
Baseline Brier score: 0.6204
Baseline calibration error: 0.0328

xG log loss: 1.0165
xG Brier score: 0.6080
xG calibration error: 0.0536

xG + schedule log loss: 1.0112
xG + schedule Brier score: 0.6047
xG + schedule calibration error: 0.0421

xG + schedule + Elo + shot volume log loss: 1.0453
xG + schedule + Elo + shot volume Brier score: 0.6273
xG + schedule + Elo + shot volume calibration error: 0.0475

xG + schedule + injuries log loss: 1.0592
xG + schedule + injuries Brier score: 0.6373
xG + schedule + injuries calibration error: 0.0431
```

Lower log loss, Brier score, and calibration error are better.

The current `data/injuries.csv` file is an empty reproducible template, so injury features are not part of the production model. They stay research-only until historical availability data exists and improves out-of-sample log loss or Brier score.

Required injury CSV columns:

- `report_date`
- `team`
- `player`
- `unavailable_from`
- `expected_return_date`
- `is_expected_starter`
- `minutes_played_last_365`
- `xg_contribution_last_365`
- `market_value_eur`

For each match, the injury pipeline only uses rows where:

- `report_date` is on or before match date
- `unavailable_from` is on or before match date
- `expected_return_date` is blank or on/after match date

That keeps the injury features historical and avoids using future information.

## Refresh Data And Model

Use the refresh pipeline when new matches have been played and the local data/model should be updated.

Quick validation without downloading or retraining:

```bash
python refresh_data.py --dry-run --skip-train --skip-calibration --skip-evaluation
```

Force-refresh cached data and run the full model update:

```bash
python refresh_data.py --force
```

When a new season starts, include the new football-data season code. For example, for 2026/27:

```bash
python refresh_data.py --seasons 1920 2021 2122 2223 2324 2425 2526 2627 --force
```

The script writes `data_refresh_report.md` with:

- which CSV/JSON files were kept, downloaded or failed
- latest local match date
- match count by season
- whether training, calibration and evaluation commands ran successfully

`refresh_data.py` passes the selected season list into `train_model.py`, `calibration_improvement.py` and `evaluate_model.py`, so a newly downloaded season is actually used in retraining. Streamlit Cloud still updates only after the resulting files are committed and pushed to GitHub.

## Make a prediction

After training, run:

```bash
python predict.py --home-team Arsenal --away-team Chelsea --match-date 2025-06-01
```

Or run it interactively:

```bash
python predict.py
```

The output looks like:

```text
Prediction: Arsenal vs Chelsea
Home win: 0.452
Draw:     0.241
Away win: 0.307
```

## Test with the UI

After training, start the Streamlit app:

```bash
streamlit run app.py
```

Then choose a home team and an away team from the dropdowns and click `Predict match`.

The UI shows:

- probability of home win
- probability of draw
- probability of away win
- the feature row used by the model

## Evaluate the model

Run:

```bash
python evaluate_model.py
```

This evaluates the current saved model with a strict time-based split. The split uses the earliest matches for training and the latest matches for testing, without shuffling. If the 80/20 cutoff lands in the middle of a matchday, the whole cutoff date is kept in the test set.

Current validation period:

```text
Train: 2019-08-09 to 2024-04-04
Test:  2024-04-06 to 2025-05-25
```

It creates:

- `evaluation/evaluation_report.json`
- `evaluation/evaluation_summary.md`
- `evaluation/model_comparison.csv`
- `evaluation/bootstrap_prediction_intervals.csv`
- `evaluation/prediction_stability.csv`
- `evaluation/calibration_table.csv`
- `evaluation/class_performance.csv`
- `evaluation/confidence_analysis.csv`
- `evaluation/gain_importance.csv`
- `evaluation/permutation_importance.csv`
- `evaluation/feature_importance.csv`
- `evaluation/shap_class_importance.csv`
- `evaluation/shap_importance.csv`
- `evaluation/worst_predictions.csv`
- `evaluation/model_comparison.png`
- `evaluation/prediction_intervals.png`
- `evaluation/calibration_curve.png`
- `evaluation/confidence_accuracy.png`
- `evaluation/confusion_matrix.png`
- `evaluation/reliability_diagram.png`
- `evaluation/rolling_backtest_log_loss.png`
- `evaluation/bootstrap_prediction_histograms.png`
- `evaluation/rolling_prediction_stability.png`
- `evaluation/probability_histogram.png`
- `evaluation/feature_importance.png`
- `evaluation/permutation_importance.png`
- `evaluation/shap_importance.png`
- `evaluation/shap_summary.png`
- `evaluation/shap_waterfall_home_win.png`

The evaluation includes:

- accuracy
- log loss
- multiclass Brier score
- per-class Brier score
- calibration curve
- confidence vs accuracy analysis
- model comparison for log loss, Brier score, and calibration error
- bootstrap confidence intervals
- ensemble uncertainty from multiple bootstrapped XGBoost models
- prediction stability scores
- Expected Calibration Error
- confusion matrix
- class-level performance analysis
- worst individual predictions
- XGBoost feature importance
- permutation importance
- SHAP mean absolute contribution
- SHAP summary and local waterfall plots

### Metrics

Accuracy is the share of matches where the most likely class is correct. It is useful, but it ignores probability quality.

Multiclass log loss rewards assigning high probability to the true result and strongly penalizes confident wrong predictions. Lower is better.

Brier score measures squared error between predicted probabilities and the actual one-hot result. Lower is better.

Calibration error compares predicted probabilities with observed frequencies. A calibrated model should have events predicted at 60% happen about 60% of the time.

Expected Calibration Error, or ECE, summarizes calibration gaps across probability bins. Lower is better. A high ECE means the probabilities are not matching observed outcomes well, even if accuracy looks acceptable.

### Calibration

The calibration curve plots predicted probability against observed frequency for home win, draw, and away win. The reliability diagram shows whether each class is overpredicted or underpredicted by probability bin.

The evaluation labels each class as:

- overconfident / overpredicted
- underconfident / underpredicted
- reasonably calibrated

Current local calibration diagnosis:

```text
Home win: overconfident / overpredicted
Draw: reasonably calibrated
Away win: underconfident / underpredicted
Expected Calibration Error: 0.0421
```

### Confidence intervals and ensemble uncertainty

`bootstrap_confidence.py` retrains multiple XGBoost models on bootstrap samples of the historical training period. It then predicts the same fixtures across all models and estimates:

- mean probability
- standard deviation
- 95% confidence interval

This is an uncertainty estimate around the model pipeline, not a guarantee about the real-world match outcome.

Example local output for one test fixture:

```text
Crystal Palace vs Man City

Home win mean probability: 32.8%
95% confidence interval: 21.0% to 46.0%

Draw mean probability: 17.0%
95% confidence interval: 11.0% to 24.0%

Away win mean probability: 50.2%
95% confidence interval: 38.6% to 62.1%

Model confidence: Medium confidence
```

`ensemble_predictor.py` also supports an ensemble mode. It trains multiple XGBoost models with different random seeds and sampled training subsets, then aggregates probabilities and variance. This helps reveal whether a prediction is stable or sensitive to small changes in the training data.

### Probability vs confidence vs uncertainty

Probability is the model's estimate for one outcome, such as `Arsenal home win = 54%`.

Confidence describes how stable that estimate is across bootstrap runs and ensemble models. A prediction can have the highest probability and still be low confidence if different model runs disagree a lot.

Uncertainty is the size of that disagreement. Wider confidence intervals and higher standard deviation mean more uncertainty.

The stability score in `prediction_confidence.py` converts bootstrap standard deviation into:

- `High confidence`
- `Medium confidence`
- `Low confidence`

Current local stability summary:

```text
Mean bootstrap probability standard deviation: 0.0668
Mean stability score: 0.6288
Low confidence predictions: 39
Medium confidence predictions: 387
High confidence predictions: 31
```

### SHAP explainability

SHAP is used for global and local explanations.

Global SHAP importance shows which features most influence predictions across the test set.

Local SHAP waterfall plots explain one specific prediction by showing which features push the probability up or down for a class.

### Experiment tracking

Each evaluation appends a row to:

- `experiments/experiments.csv`
- `experiments/experiments.json`

Tracked fields include:

- experiment id
- model version
- features included
- train/test period
- accuracy
- log loss
- Brier score
- calibration score
- Expected Calibration Error
- bootstrap runs
- prediction variance
- notes

The latest run is also saved to:

```text
evaluation/evaluation_report.json
```

This report contains the full validation period, metrics, calibration diagnosis, top features, confidence intervals, stability counts, and the example match-level uncertainty output.

## Sprint 2 contextual features

Run:

```bash
python feature_experiments.py
```

This trains and compares:

- Model A: current xG/form baseline
- Model B: baseline + fatigue features
- Model C: baseline + fatigue + European scheduling features
- Model D: baseline + fatigue + Europe + injury/availability features

It saves:

- `experiments/results.csv`
- `sprint2_report.md`
- `evaluation/sprint2/model_comparison.csv`
- `evaluation/sprint2/shap_feature_rankings.csv`
- `evaluation/sprint2/team_midweek_performance.csv`
- `evaluation/sprint2/team_short_rest_performance.csv`
- `evaluation/sprint2/*.png`

Latest local result:

```text
Model A log loss: 1.0161, Brier: 0.6075, calibration: 0.0498
Model B log loss: 1.0129, Brier: 0.6053, calibration: 0.0393
Model C log loss: 1.0129, Brier: 0.6053, calibration: 0.0393
Model D log loss: 1.0129, Brier: 0.6053, calibration: 0.0393
```

Fatigue features currently improve log loss, Brier score, and calibration. European and injury features are zero-impact until `data/european_fixtures.csv` and `data/injuries.csv` contain real historical rows.

## Lineup Stability Engine

Run:

```bash
python lineup_stability_experiments.py
```

This creates normalized lineup input tables:

- `data/match_lineups.csv`
- `data/player_appearances.csv`
- `data/formation_history.csv`
- `data/match_substitutions.csv`
- `data/manager_history.csv`

It compares:

- Model A: Sprint 2 baseline
- Model B: baseline + lineup continuity
- Model C: baseline + continuity + familiarity
- Model D: full stability engine

It saves:

- `experiments/lineup_stability_results.csv`
- `lineup_stability_report.md`
- `evaluation/lineup_stability/model_comparison.csv`
- `evaluation/lineup_stability/shap_feature_rankings.csv`
- `evaluation/lineup_stability/team_lineup_continuity_analysis.csv`
- `evaluation/lineup_stability/*.png`

Current local result: lineup stability features do not improve performance yet because the lineup tables are templates. The engine is ready for historical lineup data, but the features should not move into production until they improve out-of-sample log loss and Brier score.

## Tactical Intelligence Engine

Run:

```bash
python tactical_intelligence_experiments.py
```

This creates the tactical input table:

- `data/team_match_tactics.csv`

The tactical table is where event-provider metrics belong, including possession, progressive passes, PPDA, pressing actions, directness, crosses, counterattacks, defensive aggression, low-block/high-line proxies, and related style metrics.

It compares:

- Model A: Sprint 2.5 baseline
- Model B: baseline + tactical profiles
- Model C: baseline + tactical profiles + matchup features
- Model D: full tactical intelligence engine

It saves:

- `experiments/tactical_intelligence_results.csv`
- `tactical_intelligence_report.md`
- `evaluation/tactical_intelligence/model_comparison.csv`
- `evaluation/tactical_intelligence/shap_feature_rankings.csv`
- `evaluation/tactical_intelligence/style_performance.csv`
- `evaluation/tactical_intelligence/style_matchup_edges.csv`
- `evaluation/tactical_intelligence/team_style_embeddings.csv`
- `evaluation/tactical_intelligence/*.png`

Current local result:

```text
Model A log loss: 1.0129, Brier: 0.6053, calibration: 0.0393
Model B log loss: 1.0129, Brier: 0.6053, calibration: 0.0393
Model C log loss: 1.0129, Brier: 0.6053, calibration: 0.0393
Model D log loss: 1.0129, Brier: 0.6053, calibration: 0.0393
```

Tactical features currently do not improve performance because `data/team_match_tactics.csv` is a template. The engine is ready for event data, but tactical features should only move forward after they improve out-of-sample log loss and Brier score.

## Sprint 3A tactical ingestion

Run:

```bash
python tactical_data_ingestion.py
python tactical_intelligence_experiments.py
```

The ingestion populates `data/team_match_tactics.csv` from existing football-data CSV columns where real data exists.

Currently available:

- `shots`
- `shots_on_target`
- `attacking_pressure_score = shots + 2 * shots_on_target`

Still missing until a richer source such as FBref/event data is added:

- possession
- passes and pass completion
- progressive passes/carries
- crosses and long balls
- tackles, interceptions, blocks
- PPDA and pressing events

Latest Sprint 3A result:

```text
Baseline log loss: 1.0129, Brier: 0.6053, calibration: 0.0393
Tactical profiles log loss: 0.9927, Brier: 0.5938, calibration: 0.0419
```

The shots-derived tactical profile improves log loss and Brier score, but calibration worsens slightly. Treat it as a candidate feature, not a production feature yet.

Sprint 3A reports:

- `tactical_data_quality_report.md`
- `sprint3a_tactical_data_report.md`
- `experiments/tactical_intelligence_results.csv`

## Important notes

This is a learning prototype, not a production betting model.

The production model uses recent form, goals, xG, rest/fatigue, Elo team-strength ratings, and shot-volume trends. Odds are benchmark-only, while injuries, lineups, and advanced tactical event data remain research/template pipelines until reliable historical data exists and improves out-of-sample metrics.

Team names must match the names used in the CSV files. Examples include:

- `Arsenal`
- `Chelsea`
- `Liverpool`
- `Man City`
- `Man United`
- `Tottenham`

## Frontend dashboard

Run the Streamlit dashboard:

```bash
streamlit run app.py
```

The dashboard is designed for normal football users, not only model builders. It shows:

- A central match prediction card with team logo support, most likely result, confidence and data-quality badges.
- Calibrated probabilities when a saved calibration layer improves out-of-sample metrics.
- Probability cards for home win, draw and away win, with the highest probability highlighted.
- A compact "Most likely scorelines" section below the 1X2 probabilities. It highlights a small set of likely scorelines for the model's most likely outcome plus the highest individual exact scoreline. This is supporting context, not the primary model target.
- Model fair odds calculated from the displayed probabilities with `fair odds = 1 / probability`.
- A manual bookmaker odds comparison tool that converts entered decimal odds into market-implied probabilities, compares them with the model probabilities, and highlights whether an offered odd is above or below the model's fair odds.
- Compact home-vs-away feature groups for recent form, xG strength, schedule/fatigue, Elo team strength and shot volume. Recent form, xG strength and last-5 shot volume use each team's latest 5 matches in the saved dataset; schedule congestion uses recent 14-day match activity.
- Plain-English key-factor explanations.
- Recent meetings as historical head-to-head context.
- A model/data status panel explaining Active, Candidate, Benchmark only, Research mode and Missing statuses.
- A technical details tab with raw model feature values and raw/calibrated probabilities.
- A season projection tab with upcoming-season Monte Carlo projections plus previous seasons' forecast-vs-result validation. If `data/upcoming_fixtures_2026_27.csv` is missing or invalid, the app clearly marks the projection as a neutral fixture-skeleton estimate.
- A Season Projection audit section showing feature validation status, official fixture status, fallback teams, promoted-team adjustment status, squad-strength prior status and season-start feature values.

The app intentionally does not invent missing data. Feature groups for injuries, lineups or advanced tactical data are only shown when real local rows exist. Otherwise they are kept out of the main dashboard to avoid implying that unavailable data influenced the prediction.

Club logos are loaded only from local files in `assets/logos/`. If a logo file is missing, the app shows a clean initials placeholder. See `assets/logos/README.md` for the expected filenames.

Head-to-head meetings are shown as context under "Recent meetings". They are only used as trained model features if the H2H experiment improves out-of-sample log loss or Brier score; otherwise they remain research/not active.

Market odds are benchmark-only unless odds timing is verified as safe pre-match and out-of-sample performance improves without calibration deterioration.

The bookmaker comparison in the dashboard does not train the production model on odds. It is a safe display-only tool: enter current decimal odds manually, and the app compares them with the model's fair odds and normalized market-implied probabilities. A bookmaker odd above the model fair odd means the model sees that outcome as better value; a lower bookmaker odd means the market price is worse than the model's fair price.

### Official 2026/27 fixtures

The app supports official 2026/27 Premier League fixtures from `data/upcoming_fixtures_2026_27.csv`.

- The Prediction tab can select a 2026/27 match by matchweek and fixture.
- The Season Projection tab uses official fixtures when the file is present and valid.
- If official fixtures are missing or invalid, the app falls back to a neutral fixture skeleton and shows a warning.
- Fixtures are scheduled subject to change.
- Premier League fixtures alone do not include European, FA Cup or EFL Cup fixtures, so schedule/fatigue currently uses Premier League fixtures only unless additional fixture files are added.
- Season Projection uses the same active production feature groups as the Prediction tab: recent form, xG/xGA strength, schedule/fatigue, Elo and shot volume.
- Season Projection runs a feature validation audit before projecting. Active feature groups must be populated or explicitly marked with fallback metadata.
- Promoted or low-history teams with zero local Premier League matches are handled separately with `source_league`, `local_pl_match_count`, `promotion_adjustment_applied`, `fallback_used` and `fallback_reason`.
- If Championship data is available, recent form and shot volume are converted into Premier League-equivalent values before use. Championship points last 5 are multiplied by `0.55`, and Championship shot volume is multiplied by `0.75`.
- Championship xG/xGA are used only if a reliable source provides them. The current football-data Championship file does not include xG, so promoted-team xG/xGA use a conservative promoted-team baseline.
- If Championship data is missing, the app uses a transparent conservative promoted-team baseline instead of treating missing Premier League form as zero.
- Predictions for promoted teams carry higher uncertainty until enough Premier League matches are available in the local dataset.

### Squad Strength / Market Value

The single-match production model does not currently rely on market value. Squad strength is used only by Season Projection as a transparent preseason prior.

- Source file: `data/squad_strength_2026_27.csv`
- Required fields include team, squad market value, average player value, squad size, source URL, last updated date and data confidence.
- Squad strength is calculated as normalized `log(squad_market_value_eur)` across the 20 projected Premier League teams.
- Squad strength is complementary to Elo and recent form:
  - Elo represents historical performance strength.
  - Squad strength represents current roster quality / resource level.
- The prior is intentionally mild. It nudges early-season probabilities and should not dominate xG, Elo, form or shot volume.
- Its influence is strongest in matchweeks 1-5, lower in matchweeks 6-12 and small after matchweek 12.
- Missing squad values are not treated as zero. They are flagged as missing and excluded from the squad-strength prior.
- Historical squad value snapshots are not currently stored locally, so this is classified as a preseason projection aid / research feature rather than proven model improvement.

Validation and integration reports:

- `evaluation/fixtures_2026_27/fixture_import_validation_report.md`
- `evaluation/fixtures_2026_27/official_fixtures_integration_report.md`
- `evaluation/season_projection/feature_parity_audit_report.md`
- `evaluation/season_projection/promoted_team_baseline_report.md`
- `evaluation/season_projection/promoted_team_adjustment_audit.csv`
- `evaluation/season_projection/promoted_team_adjustment_report.md`
- `evaluation/season_projection/squad_strength_audit.csv`
- `evaluation/season_projection/squad_strength_report.md`
- `evaluation/season_projection/everton_squad_strength_audit.md`
- `evaluation/season_projection/season_projection_robustness_report.md`

### Scoreline prediction

The production model predicts 1X2 probabilities: home win, draw and away win. The scoreline layer is an additional interpretation layer that estimates likely scorelines from expected goals and aligns the scoreline totals with the displayed 1X2 probabilities.

The scoreline output is supporting context only:

- It shows grouped likely scorelines and "Highest individual scoreline", not "Predicted final score".
- Correct-score probabilities are naturally low.
- It does not replace the main home/draw/away prediction.
- It should not be treated as a correct-score betting edge.

Technical method details are documented in `evaluation/scoreline/expected_goals_method.md`.

Run the opponent-adjusted xG evaluation:

```bash
python opponent_adjusted_xg_experiments.py
```

This generates `opponent_adjusted_xg_report.md` and outputs in `evaluation/opponent_adjusted_xg/`. The latest run found a small probability-quality gain from opponent-adjusted attack/defense ratings:

- Best candidate: `model_c_production_plus_attack_defense_ratings`
- Log Loss delta vs production: `-0.0021`
- Brier delta vs production: `-0.0008`
- ECE delta vs production: `-0.0014`

The feature family was initially marked as a candidate, but broader rolling-split validation later failed to confirm the gain. Opponent-adjusted xG is now `Tested - Not adopted`.

Run the opponent-adjusted xG replacement test:

```bash
python opponent_adjusted_xg_replacement_experiments.py
```

This generates:

- `evaluation/opponent_adjusted_xg/current_xg_feature_inventory.md`
- `evaluation/opponent_adjusted_xg/correlation_analysis.csv`
- `evaluation/opponent_adjusted_xg/model_replacement_comparison.csv`
- `evaluation/opponent_adjusted_xg/remove_one_analysis.md`
- `evaluation/opponent_adjusted_xg/shap_replacement_report.md`
- `evaluation/opponent_adjusted_xg/replacement_decision_report.md`

Latest replacement finding: opponent-adjusted ratings should not replace all xG/xGA averages. The best tested configuration kept xG and xGA averages, removed xG differential, and added opponent-adjusted ratings. It improved Log Loss, Brier and ECE, but draw recall and accuracy fell, so it remains a candidate pending broader rolling-split validation.

Run the rolling validation for the replacement candidate:

```bash
python opponent_adjusted_xg_rolling_validation.py
```

This generates `evaluation/opponent_adjusted_xg/rolling_validation_report.md`. The rolling validation tested 2021/22 through 2025/26 as separate forward test seasons. The ratings candidate did not improve average rolling Log Loss or Brier versus production, so opponent-adjusted xG is now `Tested - Not adopted`. The strongest follow-up is to separately test removing the existing xG-differential columns, because `production_minus_xg_diff` was the best average rolling model.

Run the recency-weighted rolling feature evaluation:

```bash
python recency_weighting_experiments.py
```

This generates:

- `evaluation/recency_weighting/current_rolling_features.md`
- `evaluation/recency_weighting/model_comparison.csv`
- `evaluation/recency_weighting/correlation_analysis.csv`
- `evaluation/recency_weighting/remove_one_tests.csv`
- `evaluation/recency_weighting/regime_change_analysis.md`
- `evaluation/recency_weighting/recency_weighting_report.md`

The latest Sprint 4G run tested linear, exponential, half-life 3 and half-life 5 weighting for rolling form, goals, xG/xGA, shot volume and opponent-adjusted rating candidates. The current production model still had the best Log Loss and better ECE than the best recency model. Recency weighting is therefore `Tested - Not adopted`.

Run the non-PL match context evaluation:

```bash
python non_pl_context_experiments.py
```

This generates `evaluation/non_pl_context/non_pl_context_report.md` and outputs in `evaluation/non_pl_context/`. The feature layer can use pre-season friendlies, domestic cups, European qualifiers and Championship data when local historical rows are available. Non-PL competitions are down-weighted so they are not treated as Premier League-equivalent. The latest run found no out-of-sample change because the project does not yet contain reliable historical non-PL rows for Premier League teams; it remains `Tested - Not adopted`.

Run the historical betting validation backtest:

```bash
python historical_betting_validation.py --market-mode benchmark
```

This generates `market_validation_report.md` plus CSV summaries and equity curves in `evaluation/betting_validation/`. The validation is research-only unless odds timing is verified as pre-match.

Run the pre-closing market odds model test:

```bash
python market_intelligence_experiments.py --market-mode preclosing
```

This generates `market_preclosing_experiment_report.md`, `market_timing_audit_report.md`, and outputs in `evaluation/market_intelligence/`. The latest run found that market-only pre-closing probabilities beat the current model on Log Loss, Brier and ECE, but direct XGBoost integration and the calibrated blend both worsened performance. Market odds remain benchmark-only in the app.

Run the market overlay / stacking test:

```bash
python market_overlay_experiments.py
```

This generates `evaluation/market_overlay/market_overlay_report.md`. The latest run found that market-only pre-closing probabilities were still best. Logistic stacking improved Log Loss and Brier versus production, but worsened ECE, so it is not production-ready.

Run the scoreline layer evaluation:

```bash
python evaluate_scoreline_model.py
```

This generates `evaluation/scoreline/scoreline_evaluation_report.md`, `evaluation/scoreline/scoreline_metrics.csv`, and `evaluation/scoreline/scoreline_predictions.csv`. The scoreline layer is evaluated as interpretation context and is not promoted as a betting model.

Run the Elo layer evaluation:

```bash
python elo_evaluation.py
```

This generates `elo_evaluation_report.md`, `elo_parameter_search_report.md`, `data/elo_history.csv`, and detailed outputs in `evaluation/elo/`. Elo is now included in the production model because it improved out-of-sample log loss and Brier without materially hurting calibration in the Sprint 4B test. The current Elo layer has tested K-factor, home advantage and margin-of-victory settings; explicit season-weighted or decayed Elo has not been promoted and is documented in `evaluation/elo/weighted_elo_investigation_report.md`.

Run historical season simulation validation:

```bash
python season_simulation.py --historical-validation --simulations 10000
```

For a custom fixture list, provide a CSV with `Date`, `HomeTeam`, and `AwayTeam`:

```bash
python season_simulation.py --fixture-csv fixtures.csv --simulations 10000
```

This generates `season_simulation_report.md` and outputs in `evaluation/season_simulation/`.

Run the Season Projection robustness audit:

```bash
python season_projection_robustness.py
```

This generates:

- `evaluation/season_projection/feature_parity_audit_report.md`
- `evaluation/season_projection/promoted_team_baseline_report.md`
- `evaluation/season_projection/promoted_team_adjustment_audit.csv`
- `evaluation/season_projection/promoted_team_adjustment_report.md`
- `evaluation/season_projection/squad_strength_audit.csv`
- `evaluation/season_projection/squad_strength_report.md`
- `evaluation/season_projection/everton_squad_strength_audit.md`
- `evaluation/season_projection/team_feature_audit_tottenham_coventry_hull.csv`
- `evaluation/season_projection/season_projection_robustness_report.md`

Run the FBref lineup data ingestion:

```bash
python -m pip install -r requirements-ingestion.txt
python fbref_lineup_ingestion.py --fetch --seasons 2024
python lineup_stability_engine_experiments.py
```

The ingestion writes normalized lineup tables to `data/match_lineups.csv`, `data/player_appearances.csv`, `data/formation_history.csv`, and `data/match_substitutions.csv`. One full 2024/25 FBref season is currently available and validated, but lineup features remain research-only because they worsened out-of-sample log loss, Brier score, and calibration in the latest experiment. See `lineup_fbref_ingestion_report.md` and `lineup_data_quality_report.md`.

Run the manager consistency experiment:

```bash
python manager_intelligence_experiments.py
```

This extracts locally cached FBref match-level manager rows and writes `manager_consistency_report.md`, `manager_data_quality_report.md`, `manager_bounce_analysis.md`, and outputs in `evaluation/manager_intelligence/`. The current local manager coverage is 2023/24 and 2024/25. Manager features remain research-only because the latest run worsened out-of-sample log loss and Brier score versus the production baseline.

Run the shot efficiency evaluation:

```bash
python shot_efficiency_experiments.py
```

This generates `shot_efficiency_report.md` and outputs in `evaluation/shot_efficiency/`. The latest run found that simple shot volume features improved out-of-sample log loss, Brier score, and ECE, so rolling shots and shots-on-target averages are now active in the production model. Finishing-efficiency features such as `goals_minus_xg` remain research-only because they appear noisier and were not the best-performing feature family.

## Robustness upgrade

Useful commands:

```bash
python calibration_improvement.py
python worst_prediction_analysis.py
python data_quality.py
python market_intelligence_experiments.py
python head_to_head_intelligence_experiments.py
python train_model.py --mode production
python train_model.py --mode research
```

Generated reports:

- `evaluation/calibration_improvement_report.md`
- `evaluation/worst_prediction_analysis.md`
- `data_quality_report.md`
- `market_intelligence_report.md`
- `head_to_head_intelligence_report.md`
- `model_feature_policy.md`
- `robustness_upgrade_report.md`

Calibration means adjusting probability outputs so that, for example, predictions around 60% happen about 60% of the time. Confidence is not the same as probability: probability is the model's estimated chance of each outcome, while confidence reflects stability, calibration and data quality.

## Feature Status Source Of Truth

Feature status is maintained in `model_feature_status.py` and surfaced in the Streamlit help text through `help_text.py`. A feature should only be marked `Active` when it is actually present in `models/football_model.joblib` or is an active production post-processing layer such as calibrated probabilities.

Current feature status:

| Feature family | Status | Used in production | Evidence |
| --- | --- | --- | --- |
| Recent form | Active | yes | Present in models/football_model.joblib as team points last 5 and goals scored averages. |
| Home advantage | Active | yes | Present in models/football_model.joblib as home_advantage. |
| xG strength | Active | yes | Present in models/football_model.joblib as home/away xG, xGA and xG differential columns. |
| Schedule and fatigue | Active | yes | Present in models/football_model.joblib as rest and last-14-days scheduling columns. |
| Elo rating | Active | yes | Elo was promoted after Sprint 4B and is present in models/football_model.joblib. |
| Decayed Elo | Tested - Not adopted | no | decayed_elo_evaluation_report.md shows season carryover below 1.0 does not improve Log Loss or Brier versus current Elo. |
| Shot volume | Active | yes | Activated after shot_efficiency_report.md and production retrain improved Log Loss and Brier. |
| Calibrated probabilities | Active | yes | models/calibrated_probability_layer.joblib is loaded by app.py when its feature list matches the production model. |
| Market odds | Benchmark only | no | market_overlay_report.md shows market-only preclosing probabilities remain best; logistic stacking improves Log Loss/Brier but fails the calibration promotion rule. |
| Opponent-adjusted xG | Tested - Not adopted | no | rolling_validation_report.md shows the ratings candidate did not improve average rolling Log Loss/Brier versus production. |
| Recency weighting | Tested - Not adopted | no | recency_weighting_report.md shows weighted rolling features did not beat production Log Loss or calibration. |
| Non-PL match context | Tested - Not adopted | no | non_pl_context_report.md shows no out-of-sample improvement with the currently available local source coverage. |
| Head-to-head | Tested - Not adopted | no | head_to_head_intelligence_report.md keeps H2H research-only despite some draw-metric improvement. |
| Manager consistency | Tested - Not adopted | no | manager_consistency_report.md shows worse Log Loss, Brier and ECE than production. |
| Lineup stability | Research | no | lineup_stability_report.md shows worse out-of-sample Log Loss and Brier than production. |
| Injuries and suspensions | Missing | no | injury_data_quality_report.md and injury_engine_report.md say injury features should not be activated. |
| Tactical intelligence | Research | no | tactical_intelligence_report.md says only limited shots-derived tactical data is available; broader tactics stay research-only. |
| Venue-specific form | Tested - Not adopted | no | venue_specific_features_report.md says the venue-specific set did not improve both Log Loss and Brier robustly. |
| Shot efficiency | Tested - Not adopted | no | shot_efficiency_report.md keeps finishing-efficiency and goals-minus-xG research-only/noisy. |

Refresh model metrics:

```bash
python train_model.py --mode production
python calibration_improvement.py
python evaluate_model.py
python feature_status_checks.py
```

After future experiments, update `model_feature_status.py` only when the evidence comes from out-of-sample, time-based validation. Do not promote a feature based only on intuition, in-sample accuracy, or SHAP importance.

## Troubleshooting

On macOS, XGBoost may need the OpenMP runtime. If training fails with a `libomp.dylib` error, install it with:

```bash
brew install libomp
```

Then run training again:

```bash
python train_model.py
```
