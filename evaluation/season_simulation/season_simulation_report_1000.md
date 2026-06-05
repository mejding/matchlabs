# Season Simulation Report

This report validates preseason Premier League season simulations using only information available before each season starts.

Historical validation seasons:

- 2021/22
- 2022/23
- 2023/24
- 2024/25

Monte Carlo simulations per validation run: `1000`.

Important limitation: preseason forecasts freeze form, xG and Elo at season start. Fixture dates are used for rest/fatigue because fixture dates are known before the matches, but no in-season match results are fed back into the forecast.

## Aggregate Validation

| model_variant | average_position_error | average_points_error | rank_correlation | champion_prediction_accuracy | top_4_prediction_accuracy | relegation_prediction_accuracy |
| --- | --- | --- | --- | --- | --- | --- |
| current_plus_elo | 3.3104 | 10.9714 | 0.7237 | 0.2500 | 0.5625 | 0.3333 |
| current_plus_elo_calibrated | 3.3137 | 11.4395 | 0.7165 | 0.0000 | 0.6250 | 0.4167 |
| current_without_elo | 3.8021 | 11.9769 | 0.6312 | 0.2500 | 0.4375 | 0.4167 |

Best variant by position error: `current_plus_elo`.

## Season-by-Season Validation

| season_label | model_variant | average_position_error | average_points_error | rank_correlation | champion_prediction_accuracy | top_4_prediction_accuracy | relegation_prediction_accuracy |
| --- | --- | --- | --- | --- | --- | --- | --- |
| 2021/22 | current_plus_elo | 3.1559 | 9.7769 | 0.7278 | 0.0000 | 0.7500 | 0.3333 |
| 2021/22 | current_plus_elo_calibrated | 3.2513 | 11.0501 | 0.7654 | 0.0000 | 0.7500 | 0.6667 |
| 2021/22 | current_without_elo | 3.3491 | 9.6351 | 0.6827 | 0.0000 | 0.7500 | 0.3333 |
| 2022/23 | current_plus_elo | 4.1097 | 13.0115 | 0.6346 | 1.0000 | 0.2500 | 0.3333 |
| 2022/23 | current_plus_elo_calibrated | 4.0508 | 13.0680 | 0.6030 | 0.0000 | 0.2500 | 0.3333 |
| 2022/23 | current_without_elo | 4.5855 | 13.6267 | 0.5023 | 1.0000 | 0.2500 | 0.3333 |
| 2023/24 | current_plus_elo | 3.1089 | 10.4704 | 0.7654 | 0.0000 | 0.5000 | 0.3333 |
| 2023/24 | current_plus_elo_calibrated | 3.2800 | 11.8072 | 0.6902 | 0.0000 | 0.5000 | 0.3333 |
| 2023/24 | current_without_elo | 3.9510 | 13.4210 | 0.6662 | 0.0000 | 0.2500 | 0.6667 |
| 2024/25 | current_plus_elo | 2.8671 | 10.6267 | 0.7669 | 0.0000 | 0.7500 | 0.3333 |
| 2024/25 | current_plus_elo_calibrated | 2.6728 | 9.8326 | 0.8075 | 0.0000 | 1.0000 | 0.3333 |
| 2024/25 | current_without_elo | 3.3226 | 11.2249 | 0.6737 | 0.0000 | 0.5000 | 0.3333 |

## Consistently Mis-Ranked Teams

For the best variant:

| team | seasons | mean_position_error | mean_points_error | mean_expected_position | mean_actual_position |
| --- | --- | --- | --- | --- | --- |
| Watford | 1 | 8.3890 | 28.6100 | 10.6110 | 19.0000 |
| Tottenham | 4 | 5.2923 | 15.8400 | 6.7103 | 8.5000 |
| Leicester | 3 | 5.0980 | 14.5437 | 10.4520 | 14.6667 |
| Ipswich | 1 | 4.7820 | 20.9000 | 14.2180 | 19.0000 |
| Man United | 4 | 4.7652 | 11.9360 | 9.7862 | 8.0000 |
| Luton | 1 | 4.7120 | 18.8730 | 13.2880 | 18.0000 |
| Leeds | 2 | 4.6610 | 10.0375 | 13.3390 | 18.0000 |
| Burnley | 2 | 4.3615 | 13.6635 | 14.1385 | 18.5000 |
| Fulham | 3 | 3.7527 | 8.9803 | 14.4773 | 11.6667 |
| Chelsea | 4 | 3.6725 | 10.7107 | 6.4690 | 6.2500 |
| Aston Villa | 4 | 3.6225 | 10.7720 | 11.3725 | 7.7500 |
| Wolves | 4 | 3.5095 | 8.7085 | 17.0095 | 13.5000 |

## Answers

### 1. How accurately can the model forecast a season?

Best average position error: `3.31` places.  
Best average points error: `10.97` points.  
Best rank correlation: `0.724`.

### 2. Which teams are consistently mis-ranked?

The most mis-ranked teams are listed above. These are usually clubs whose season-level outcomes diverge from preseason rolling form/Elo, often due to transfers, manager changes, injuries, tactical changes or promoted-team uncertainty.

### 3. Does Elo improve season forecasting?

Without Elo average position error: `3.80`.  
With Elo average position error: `3.31`.

Answer: Yes, Elo improves average position error in this preseason simulation backtest.

### 4. Does calibration improve season forecasting?

With Elo raw average position error: `3.31`.  
With Elo calibrated average position error: `3.31`.

Answer: No, calibration does not improve average position error in this run.

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
