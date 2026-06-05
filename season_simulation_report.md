# Season Simulation Report

This report validates preseason Premier League season simulations using only information available before each season starts.

Historical validation seasons:

- 2021/22
- 2022/23
- 2023/24
- 2024/25

Monte Carlo simulations per validation run: `10000`.

Important limitation: preseason forecasts freeze form, xG and Elo at season start. Fixture dates are used for rest/fatigue because fixture dates are known before the matches, but no in-season match results are fed back into the forecast.

## Aggregate Validation

| model_variant | average_position_error | average_points_error | rank_correlation | champion_prediction_accuracy | top_4_prediction_accuracy | relegation_prediction_accuracy |
| --- | --- | --- | --- | --- | --- | --- |
| current_plus_elo_calibrated | 3.2990 | 11.4043 | 0.7135 | 0.0000 | 0.6250 | 0.3333 |
| current_plus_elo | 3.3090 | 10.9689 | 0.7248 | 0.2500 | 0.5625 | 0.3333 |
| current_without_elo | 3.8069 | 11.9544 | 0.6301 | 0.2500 | 0.4375 | 0.3333 |

Best variant by position error: `current_plus_elo_calibrated`.

## 1,000 vs 10,000 Simulations

The engine was run with both requested Monte Carlo sizes. The 1,000-run outputs are archived in `evaluation/season_simulation/1000/`; the main report uses the 10,000-run outputs.

| simulations | best_variant | best_average_position_error | best_average_points_error | best_rank_correlation |
| --- | --- | ---: | ---: | ---: |
| 1,000 | current_plus_elo | 3.3104 | 10.9714 | 0.7237 |
| 10,000 | current_plus_elo_calibrated | 3.2990 | 11.4043 | 0.7135 |

The difference between 1,000 and 10,000 simulations is small. That suggests most forecast error comes from model inputs and preseason uncertainty, not Monte Carlo noise.

## Season-by-Season Validation

| season_label | model_variant | average_position_error | average_points_error | rank_correlation | champion_prediction_accuracy | top_4_prediction_accuracy | relegation_prediction_accuracy |
| --- | --- | --- | --- | --- | --- | --- | --- |
| 2021/22 | current_plus_elo | 3.1369 | 9.7922 | 0.7278 | 0.0000 | 0.7500 | 0.3333 |
| 2021/22 | current_plus_elo_calibrated | 3.2178 | 11.0409 | 0.7459 | 0.0000 | 0.7500 | 0.3333 |
| 2021/22 | current_without_elo | 3.3411 | 9.6069 | 0.6992 | 0.0000 | 0.7500 | 0.3333 |
| 2022/23 | current_plus_elo | 4.1165 | 13.0287 | 0.6391 | 1.0000 | 0.2500 | 0.3333 |
| 2022/23 | current_plus_elo_calibrated | 4.0285 | 12.9669 | 0.6180 | 0.0000 | 0.2500 | 0.3333 |
| 2022/23 | current_without_elo | 4.5868 | 13.5806 | 0.5023 | 1.0000 | 0.2500 | 0.3333 |
| 2023/24 | current_plus_elo | 3.0882 | 10.3906 | 0.7654 | 0.0000 | 0.5000 | 0.3333 |
| 2023/24 | current_plus_elo_calibrated | 3.2447 | 11.7131 | 0.6917 | 0.0000 | 0.5000 | 0.3333 |
| 2023/24 | current_without_elo | 3.9688 | 13.3830 | 0.6451 | 0.0000 | 0.2500 | 0.3333 |
| 2024/25 | current_plus_elo | 2.8943 | 10.6639 | 0.7669 | 0.0000 | 0.7500 | 0.3333 |
| 2024/25 | current_plus_elo_calibrated | 2.7048 | 9.8964 | 0.7985 | 0.0000 | 1.0000 | 0.3333 |
| 2024/25 | current_without_elo | 3.3307 | 11.2471 | 0.6737 | 0.0000 | 0.5000 | 0.3333 |

## Consistently Mis-Ranked Teams

For the best variant:

| team | seasons | mean_position_error | mean_points_error | mean_expected_position | mean_actual_position |
| --- | --- | --- | --- | --- | --- |
| Watford | 1 | 6.3315 | 26.7998 | 12.6685 | 19.0000 |
| Ipswich | 1 | 5.9145 | 23.9775 | 13.0855 | 19.0000 |
| Burnley | 2 | 5.7743 | 18.6983 | 12.7257 | 18.5000 |
| Leeds | 2 | 5.5579 | 14.5900 | 12.4421 | 18.0000 |
| Tottenham | 4 | 5.3581 | 13.1679 | 7.3009 | 8.5000 |
| Leicester | 3 | 5.2059 | 14.3942 | 10.9043 | 14.6667 |
| Luton | 1 | 4.2767 | 19.3964 | 13.7233 | 18.0000 |
| Man United | 4 | 4.2426 | 9.7050 | 9.5455 | 8.0000 |
| Chelsea | 4 | 3.8689 | 11.4718 | 7.3452 | 6.2500 |
| Fulham | 3 | 3.5097 | 7.7912 | 14.7462 | 11.6667 |
| Brentford | 4 | 3.3609 | 8.5567 | 11.7324 | 12.0000 |
| Aston Villa | 4 | 3.3489 | 9.4188 | 10.6783 | 7.7500 |

## Answers

### 1. How accurately can the model forecast a season?

Best average position error: `3.30` places.  
Best average points error: `11.40` points.  
Best rank correlation: `0.714`.

### 2. Which teams are consistently mis-ranked?

The most mis-ranked teams are listed above. These are usually clubs whose season-level outcomes diverge from preseason rolling form/Elo, often due to transfers, manager changes, injuries, tactical changes or promoted-team uncertainty.

### 3. Does Elo improve season forecasting?

Without Elo average position error: `3.81`.  
With Elo average position error: `3.31`.

Answer: Yes, Elo improves average position error in this preseason simulation backtest.

### 4. Does calibration improve season forecasting?

With Elo raw average position error: `3.31`.  
With Elo calibrated average position error: `3.30`.

Answer: Yes, calibration improves average position error.

### 5. Is the model good enough for public season projections?

Answer: Not yet. It is useful as an internal research projection, but not strong enough for confident public season projections.

The biggest concern is that the model has no transfer-window, manager-change, lineup, injury or squad-depth intelligence at preseason time.

## Artifacts

- `evaluation/season_simulation/historical_season_comparison.csv`
- `evaluation/season_simulation/historical_fixture_probabilities.csv`
- `evaluation/season_simulation/historical_validation_by_season.csv`
- `evaluation/season_simulation/historical_validation_summary.csv`
- `evaluation/season_simulation/misranked_teams.csv`
- `evaluation/season_simulation/historical_validation_summary.png`
