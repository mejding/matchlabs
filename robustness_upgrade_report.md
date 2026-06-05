# Robustness Upgrade Report

## 1. Did Calibration Improve The Model?

Yes, but modestly. Temperature scaling was the only calibration method that improved out-of-sample metrics.

| Method | Accuracy | Log Loss | Brier | ECE |
| --- | ---: | ---: | ---: | ---: |
| Raw XGBoost | 0.5274 | 1.0094 | 0.6032 | 0.0410 |
| Sigmoid / Platt | 0.4989 | 1.0124 | 0.6058 | 0.0501 |
| Isotonic | 0.5011 | 1.2945 | 0.6107 | 0.0604 |
| Temperature scaling | 0.5274 | 1.0071 | 0.6023 | 0.0411 |

Decision: temperature scaling with `T=1.12` was saved as `models/calibrated_probability_layer.joblib` because it improved log loss and Brier score. The improvement is real but small, so the frontend still surfaces uncertainty and data-quality warnings.

## 2. Did Overconfident Favorite Errors Reduce?

Calibration softens the probability distribution slightly, but the structural issue remains. Worst-prediction analysis found:

- 16 wrong predictions above 70% confidence.
- 135 home favorites that lost or drew.
- 67 draws predicted as home wins.
- 10 matches with suspicious rest gaps above 30 days.

Conclusion: home favorites and draws remain the main failure area. The dashboard now warns users rather than presenting favorite predictions as certainty.

## 3. Is Tactical Pressure Still Useful After Calibration?

Sprint 3A showed that shots-based tactical pressure improved the model before calibration:

- Baseline log loss: 1.0129.
- Tactical pressure log loss: 0.9927.
- Baseline Brier: 0.6053.
- Tactical pressure Brier: 0.5938.

However, full tactical matchups/style embeddings did not beat the simpler tactical-pressure model. Tactical pressure should remain a candidate feature and move forward only after it is integrated into the main production training path and retested with calibration.

## 4. How Does The Model Compare With Market Odds?

Market odds are a stronger benchmark on the current historical test period:

| Model | Accuracy | Log Loss | Brier | ECE |
| --- | ---: | ---: | ---: | ---: |
| Current non-market model | 0.5142 | 1.0112 | 0.6047 | 0.0421 |
| Market odds only | 0.5733 | 0.9467 | 0.5603 | 0.0416 |
| Current model + market odds | 0.4902 | 1.1565 | 0.6723 | 0.1230 |
| Calibrated/blended model + market odds | 0.5405 | 0.9837 | 0.5856 | 0.0658 |

Conclusion: odds are useful as a benchmark, but should not be used as production features until the project controls whether odds are opening, closing, final historical, or otherwise unavailable at prediction time.

## 5. Which Features Are Production-Ready?

Production-ready:

- Rolling form.
- xG, xGA and xG differential.
- Schedule/fatigue.
- Home advantage.
- Temperature-scaled calibrated probabilities, because they improved out-of-sample log loss/Brier.

Production candidate:

- Shots-based tactical pressure.

Research-only:

- Injuries and availability, because the injury file is template-only.
- Lineup stability and player familiarity, because lineup tables are template-only.
- Full tactical matchups and style embeddings, because they did not improve out-of-sample performance enough.
- Market odds as model features until timing is controlled.

## 6. What Should Be Built Next?

Next work should focus on fewer, higher-quality signals:

- Integrate shots-based tactical pressure into `train_model.py --mode production` behind a feature flag and retest after calibration.
- Add real historical injury and lineup sources before using those features.
- Build a draw-specific analysis layer, because draw underprediction is the clearest recurring model weakness.
- Add odds only as a benchmark unless opening-odds timing is guaranteed.
