# Sprint 4F: Rolling Validation for Opponent-Adjusted xG Candidate

## Goal

Validate whether the best Sprint 4E configuration holds across multiple season-based forward splits.

Tested seasons: 2021/22, 2022/23, 2023/24, 2024/25, 2025/26

## Models

- `production`: current production feature set.
- `production_minus_xg_diff`: production without xG differential.
- `candidate_minus_xg_diff_plus_ratings`: production without xG differential plus opponent-adjusted ratings.
- `production_plus_full_ratings`: production plus ratings.
- `ratings_replace_all_raw_xg`: raw xG/xGA/xG-diff removed, ratings used instead.

## Rolling Summary

| model_version | mean_log_loss_delta | mean_Brier_delta | mean_ECE_delta | seasons_log_loss_improved | seasons_Brier_improved | seasons_ECE_not_worse | seasons_tested |
| --- | --- | --- | --- | --- | --- | --- | --- |
| production_minus_xg_diff | 0.0005 | 0.0000 | -0.0016 | 3 | 3 | 5 | 5 |
| production_plus_full_ratings | 0.0034 | 0.0020 | -0.0042 | 3 | 3 | 4 | 5 |
| candidate_minus_xg_diff_plus_ratings | 0.0043 | 0.0023 | -0.0014 | 3 | 3 | 4 | 5 |
| ratings_replace_all_raw_xg | 0.0113 | 0.0072 | -0.0027 | 1 | 1 | 4 | 5 |

Negative deltas are better for Log Loss, Brier and ECE.

## Per-Season Results

| test_season_label | model_version | accuracy | log_loss | Brier_score | expected_calibration_error | draw_recall | draw_log_loss |
| --- | --- | --- | --- | --- | --- | --- | --- |
| 2021/22 | production | 0.5026 | 1.0312 | 0.6073 | 0.0674 | 0.0909 | 0.5625 |
| 2021/22 | production_minus_xg_diff | 0.5105 | 1.0370 | 0.6100 | 0.0632 | 0.1250 | 0.5626 |
| 2021/22 | candidate_minus_xg_diff_plus_ratings | 0.4737 | 1.0683 | 0.6296 | 0.0846 | 0.0682 | 0.5819 |
| 2021/22 | production_plus_full_ratings | 0.4868 | 1.0603 | 0.6248 | 0.0797 | 0.0682 | 0.5792 |
| 2021/22 | ratings_replace_all_raw_xg | 0.4789 | 1.0809 | 0.6373 | 0.0860 | 0.1023 | 0.5842 |
| 2022/23 | production | 0.5079 | 1.0102 | 0.6032 | 0.0762 | 0.0460 | 0.5591 |
| 2022/23 | production_minus_xg_diff | 0.5289 | 1.0053 | 0.6010 | 0.0777 | 0.0575 | 0.5566 |
| 2022/23 | candidate_minus_xg_diff_plus_ratings | 0.5132 | 1.0038 | 0.5996 | 0.0759 | 0.0460 | 0.5628 |
| 2022/23 | production_plus_full_ratings | 0.5211 | 1.0062 | 0.6010 | 0.0745 | 0.0345 | 0.5602 |
| 2022/23 | ratings_replace_all_raw_xg | 0.4947 | 1.0171 | 0.6066 | 0.0846 | 0.0345 | 0.5573 |
| 2023/24 | production | 0.5526 | 0.9674 | 0.5700 | 0.0494 | 0.0244 | 0.5215 |
| 2023/24 | production_minus_xg_diff | 0.5579 | 0.9672 | 0.5689 | 0.0464 | 0.0244 | 0.5225 |
| 2023/24 | candidate_minus_xg_diff_plus_ratings | 0.5711 | 0.9756 | 0.5738 | 0.0507 | 0.0000 | 0.5309 |
| 2023/24 | production_plus_full_ratings | 0.5553 | 0.9724 | 0.5720 | 0.0480 | 0.0000 | 0.5317 |
| 2023/24 | ratings_replace_all_raw_xg | 0.5553 | 0.9757 | 0.5763 | 0.0582 | 0.0122 | 0.5338 |
| 2024/25 | production | 0.5079 | 1.0341 | 0.6159 | 0.0695 | 0.0108 | 0.5801 |
| 2024/25 | production_minus_xg_diff | 0.5158 | 1.0404 | 0.6196 | 0.0714 | 0.0108 | 0.5824 |
| 2024/25 | candidate_minus_xg_diff_plus_ratings | 0.5079 | 1.0229 | 0.6101 | 0.0602 | 0.0108 | 0.5705 |
| 2024/25 | production_plus_full_ratings | 0.4974 | 1.0241 | 0.6116 | 0.0502 | 0.0000 | 0.5751 |
| 2024/25 | ratings_replace_all_raw_xg | 0.4974 | 1.0355 | 0.6182 | 0.0426 | 0.0000 | 0.5732 |
| 2025/26 | production | 0.4579 | 1.0660 | 0.6427 | 0.0678 | 0.0096 | 0.6042 |
| 2025/26 | production_minus_xg_diff | 0.4658 | 1.0616 | 0.6397 | 0.0637 | 0.0096 | 0.6028 |
| 2025/26 | candidate_minus_xg_diff_plus_ratings | 0.4553 | 1.0600 | 0.6378 | 0.0522 | 0.0096 | 0.6053 |
| 2025/26 | production_plus_full_ratings | 0.4632 | 1.0632 | 0.6397 | 0.0568 | 0.0288 | 0.6060 |
| 2025/26 | ratings_replace_all_raw_xg | 0.4553 | 1.0565 | 0.6366 | 0.0453 | 0.0385 | 0.6006 |

## Decision

Best average Log Loss delta model: `production_minus_xg_diff`.

Candidate `candidate_minus_xg_diff_plus_ratings` mean Log Loss delta: 0.0043.
Candidate mean Brier delta: 0.0023.
Candidate mean ECE delta: -0.0014.

Do not promote yet. Keep as Candidate/Research until the improvement is stable across more seasons or a simpler feature subset.

Production gate remains: improve Log Loss or Brier across most rolling splits without materially worsening calibration.