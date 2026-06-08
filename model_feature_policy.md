# Model Feature Policy

## Production Features

These features are historically reproducible and safe for the current production-style model:

- Rolling form: points last 5 and goals scored average.
- xG strength: rolling xG, xGA and xG differential from Understat historical files.
- Schedule and fatigue: days rest, days since last match, matches last 14 days and midweek indicator.
- Elo rating: chronological team-strength features (`home_elo`, `away_elo`, `elo_difference`, Elo trends and rolling Elo form).
- Shot volume: rolling shots and shots-on-target averages from football-data.co.uk over last 5, last 10 and current season.
- Home advantage.
- Calibrated probabilities when the calibration layer improves out-of-sample log loss or Brier score.

Shot volume is active because Sprint 4 shot-efficiency evaluation and the production retrain improved out-of-sample log loss and Brier score. Finishing-efficiency, goals-minus-xG, defensive shot-prevention, and broader tactical-pressure features remain research-only until they beat the simpler production model.

## Market Odds Policy

Safe production odds fields:

- None currently verified.

Benchmark-only odds fields:

- Closing odds columns such as `B365CH/B365CD/B365CA`, `BWCH/BWCD/BWCA`, `PSCH/PSCD/PSCA`, `WHCH/WHCD/WHCA`, `VCCH/VCCD/VCCA`, `MaxCH/MaxCD/MaxCA`, `AvgCH/AvgCD/AvgCA`.
- Average and maximum listed odds such as `AvgH/AvgD/AvgA` and `MaxH/MaxD/MaxA`.

Research-only / unknown timing odds fields:

- Single-bookmaker listed odds such as `B365H/B365D/B365A`, `BWH/BWD/BWA`, `IWH/IWD/IWA`, `PSH/PSD/PSA`, `WHH/WHD/WHA`, `VCH/VCD/VCA`, `BFH/BFD/BFA`, `1XBH/1XBD/1XBA` until the data collection time is verified.

Activation requirements:

- The source must guarantee the odds are known before kickoff.
- Odds features must improve out-of-sample log loss or Brier score.
- Calibration must not materially worsen.
- The live prediction path must avoid closing-price leakage.

Current decision: market odds remain benchmark-only. The market-only benchmark beats the model, but no odds fields are currently verified as safe pre-match production inputs.

OddsPortal opening odds status:

- OddsPortal explicitly distinguishes opening odds from closing odds, so opening odds are a promising `SAFE_PREMATCH_CANDIDATE`.
- They are not production-active until we have a reproducible and permitted data path with separate opening prices, bookmaker, market, kickoff date/time and source audit trail.
- Closing OddsPortal prices should remain benchmark-only for the same reason as football-data closing odds: they may contain late pre-match information that would leak into early predictions.

Latest market production decision:

- Benchmark and research-mode market-only probabilities beat the current production model on the time-based test.
- Directly adding benchmark/research odds to the XGBoost feature set worsened out-of-sample Log Loss, Brier Score and calibration.
- Keep market odds as benchmark/edge context only until a verified opening-odds dataset exists and direct integration or a calibrated blend improves out-of-sample metrics.

## Research / Inactive Features

These features should stay out of production unless real historical data is added and they improve out-of-sample metrics:

- Injuries and player availability: current CSV is template-only.
- Lineup stability and player familiarity: the Historical Lineup Data Engine found no local FBref, Understat or available lineup rows; normalized lineup tables are template-only, so lineup SHAP contribution is zero.
- Full tactical matchups and style embeddings: current experiments did not beat the simpler production model.
- Advanced tactical profiles such as possession, passing, pressing and defensive shape until FBref/event data is populated with real historical rows.
- Head-to-head features: Sprint 3.7 found measurable SHAP signal and better draw metrics, but worse overall log loss and Brier score than the current production baseline.
- Market odds as model features until the timing of opening/closing odds is controlled.

## Training Modes

Use:

```bash
python train_model.py --mode production
```

This trains the saved model with safe form, xG, schedule/fatigue, Elo and shot-volume features.

Use:

```bash
python train_model.py --mode research
```

This trains injury-template columns to a separate research artifact only. If the injury file is empty, these columns are zero-impact and must not be shown as active frontend features.

## Deployment Rule

A feature only moves into production when all of these are true:

- It is generated historically without future leakage.
- It has reliable real data coverage.
- It improves out-of-sample log loss or Brier score on a time-based split.
- SHAP or gain/permutation importance shows non-zero contribution.
- It does not make calibration materially worse.
