# Manager Bounce Analysis

## Method

For each detected in-season manager change, compare the team's previous 5 matches with the first 5 and first 10 matches after the new manager first appears in the FBref match data.

This is exploratory only. The current manager source covers 2024/25, so sample size is small and should not be treated as stable evidence.

## Results

| team | manager | start_date | before_5_ppg | after_5_ppg | after_10_ppg | before_5_xg_diff_per_match | after_5_xg_diff_per_match | after_10_xg_diff_per_match |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| Everton | David Moyes | 2025-01-15 | 0.6000 | 2.0000 | 1.7000 | -1.3916 | 0.8047 | 0.5529 |
| Leicester | Ben Dawson | 2024-11-30 | 0.8000 | 0.8000 | 0.4000 | -0.5936 | -1.0440 | -1.0023 |
| Leicester | Ruud van Nistelrooy | 2024-12-03 | 0.2000 | 0.8000 | 0.7000 | -0.9379 | -1.1174 | -0.8582 |
| Man United | Ruud van Nistelrooy | 2024-11-03 | 1.0000 | 1.6000 | 1.1000 | -0.7408 | -0.1329 | 0.0310 |
| Man United | Rúben Amorim | 2024-11-24 | 1.6000 | 1.4000 | 1.1000 | 0.4381 | -0.0414 | -0.0905 |
| Southampton | Simon Rusk | 2024-12-22 | 0.2000 | 0.2000 | 0.4000 | -2.2507 | -1.9103 | -1.9766 |
| Southampton | Ivan Jurić | 2024-12-26 | 0.4000 | 0.0000 | 0.3000 | -2.1155 | -1.9368 | -2.0930 |
| Southampton | Simon Rusk | 2025-04-12 | 0.2000 | 0.4000 | 0.2857 | -1.5985 | -1.2425 | -1.3785 |
| West Ham | Graham Potter | 2025-01-14 | 1.0000 | 0.8000 | 1.1000 | -0.7738 | -0.8055 | -0.3810 |
| Wolves | Vítor Pereira | 2024-12-22 | 0.6000 | 1.4000 | 1.3000 | -0.4922 | -0.4312 | -0.2694 |

## Interpretation

This analysis is useful for spotting possible new-manager-bounce patterns, but the model comparison remains the production gate. In the current run, manager features did not improve log loss or Brier score, so manager bounce should remain research-only.
