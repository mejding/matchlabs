# Production Readiness Report

Date: 2026-06-08

## Current Production Model

The saved production artifact is `models/football_model.joblib`.

Active model inputs:

- Rolling form: points last 5 and goals scored average.
- xG strength: rolling xG, rolling xGA and xG differential.
- Schedule/fatigue: days rest, days since last match, matches last 14 days and midweek match flag.
- Home advantage.
- Elo team-strength features.

Model artifact status:

- Feature count: 28.
- Calibration layer: present in `models/calibrated_probability_layer.joblib`.
- Latest local model history: Premier League through 2025/26.
- Current deployment branch: `main`.

Latest saved production comparison:

| Model | Accuracy | Log Loss | Brier | Calibration Error |
| --- | ---: | ---: | ---: | ---: |
| Baseline | 0.4598 | 1.0696 | 0.6448 | 0.0347 |
| xG | 0.4897 | 1.0534 | 0.6335 | 0.0397 |
| xG + schedule | 0.4729 | 1.0592 | 0.6373 | 0.0431 |
| xG + schedule + Elo | 0.4710 | 1.0540 | 0.6332 | 0.0419 |

Interpretation:

- xG adds the clearest historical uplift over baseline.
- Elo improves log loss and Brier versus the schedule model, but not accuracy.
- Schedule/fatigue should remain monitored because it adds football context but did not improve every aggregate metric in the latest split.

## Production UI Status

The Streamlit app should show only production-active groups in the main prediction flow:

- Recent Form.
- xG Strength.
- Schedule & Fatigue.
- Elo Team Strength.
- Recent meetings as historical context only, marked Research / Not active.
- Market odds as benchmark only.

The frontend should not present injuries, player availability, lineup stability or full tactical intelligence as active unless real historical rows exist and the model artifact uses those features.

## Research / Not Production

| Feature Family | Current Status | Reason |
| --- | --- | --- |
| Market odds | Benchmark only | Historical timing is not verified as safe pre-match. |
| Head-to-head | Research only | H2H improved some draw diagnostics but did not improve overall log loss/Brier enough. |
| Injury/player availability | Missing/template only | `data/injuries.csv` has 0 rows. |
| Lineup stability | Missing/template only | `data/player_appearances.csv` has 0 rows. |
| Full tactical intelligence | Research only | Shots data exists, but possession, passing, pressing and defensive event data are incomplete. |

## Five-Step Roadmap

1. **Finish Streamlit Cloud deployment.**
   Confirm GitHub login, select `mejding/matchlabs`, branch `main`, main file `app.py`, then verify the live app loads.

2. **Public-release frontend cleanup.**
   Keep the main UI focused on active production inputs. Keep research-only signals behind context/status labels.

3. **Production model audit.**
   Maintain this report and `model_feature_policy.md` whenever a feature is promoted or rejected.

4. **Market odds timing sprint.**
   Highest potential model-value sprint, but only if opening/pre-match odds timing can be verified. Until then, keep odds as benchmark and fair-odds comparison only.

5. **FBref/tactical data ingestion sprint.**
   Next best non-market data path: populate real possession, passing, carries, tackles, interceptions and blocks. Only promote tactical features after time-based out-of-sample validation.

## Recommended Immediate Next Action

Complete the Streamlit deployment, then run a live smoke test:

- Open the deployed app.
- Predict Arsenal vs Brighton.
- Confirm probability bars, fair odds, feature groups, data status and season projection render.
- Confirm no inactive injury/lineup features are presented as production features.
