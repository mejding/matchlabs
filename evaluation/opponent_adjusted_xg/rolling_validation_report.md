# Sprint 4F: Rolling Validation for Opponent-Adjusted xG Candidate

## Goal

Validate whether the best Sprint 4E configuration holds across multiple season-based forward splits.

Tested seasons: 2021/22, 2022/23, 2023/24, 2024/25, 2025/26

## Models

- `production`: current production feature set.
- `production_minus_xg_diff`: production without xG differential.
- `candidate_minus_xg_diff_plus_ratings`: production without xG differential plus opponent-adjusted ratings.
- `candidate_minus_xg_diff_plus_attack_ratings`: production without xG differential plus attack-only ratings.
- `candidate_minus_xg_diff_plus_defense_ratings`: production without xG differential plus defense-only ratings.
- `candidate_minus_xg_diff_plus_matchup_ratings`: production without xG differential plus matchup-only ratings.
- `production_plus_full_ratings`: production plus ratings.
- `ratings_replace_all_raw_xg`: raw xG/xGA/xG-diff removed, ratings used instead.

## Rolling Summary

| model_version | mean_log_loss_delta | mean_Brier_delta | mean_ECE_delta | seasons_log_loss_improved | seasons_Brier_improved | seasons_ECE_not_worse | seasons_tested |
| --- | --- | --- | --- | --- | --- | --- | --- |
| candidate_minus_xg_diff_plus_defense_ratings | -0.0027 | -0.0020 | -0.0032 | 2 | 2 | 4 | 5 |
| candidate_minus_xg_diff_plus_ratings | -0.0016 | 0.0001 | -0.0015 | 2 | 2 | 4 | 5 |
| candidate_minus_xg_diff_plus_matchup_ratings | -0.0003 | 0.0003 | -0.0071 | 4 | 3 | 5 | 5 |
| production_plus_full_ratings | 0.0001 | 0.0015 | -0.0008 | 2 | 2 | 4 | 5 |
| production_minus_xg_diff | 0.0003 | 0.0002 | -0.0047 | 2 | 2 | 5 | 5 |
| candidate_minus_xg_diff_plus_attack_ratings | 0.0028 | 0.0025 | -0.0036 | 1 | 1 | 5 | 5 |
| ratings_replace_all_raw_xg | 0.0042 | 0.0035 | -0.0040 | 1 | 1 | 5 | 5 |

Negative deltas are better for Log Loss, Brier and ECE.

## Per-Season Results

| test_season_label | model_version | accuracy | log_loss | Brier_score | expected_calibration_error | draw_recall | draw_log_loss |
| --- | --- | --- | --- | --- | --- | --- | --- |
| 2021/22 | production | 0.4842 | 1.0576 | 0.6257 | 0.0717 | 0.0795 | 0.5803 |
| 2021/22 | production_minus_xg_diff | 0.5000 | 1.0551 | 0.6242 | 0.0603 | 0.1023 | 0.5813 |
| 2021/22 | candidate_minus_xg_diff_plus_ratings | 0.4711 | 1.0666 | 0.6342 | 0.0659 | 0.0568 | 0.5889 |
| 2021/22 | candidate_minus_xg_diff_plus_attack_ratings | 0.4816 | 1.0699 | 0.6372 | 0.0755 | 0.0682 | 0.5849 |
| 2021/22 | candidate_minus_xg_diff_plus_defense_ratings | 0.5053 | 1.0611 | 0.6259 | 0.0679 | 0.1250 | 0.5877 |
| 2021/22 | candidate_minus_xg_diff_plus_matchup_ratings | 0.4789 | 1.0555 | 0.6263 | 0.0662 | 0.0682 | 0.5788 |
| 2021/22 | production_plus_full_ratings | 0.4632 | 1.0656 | 0.6343 | 0.0747 | 0.0682 | 0.5878 |
| 2021/22 | ratings_replace_all_raw_xg | 0.4684 | 1.0772 | 0.6376 | 0.0684 | 0.1023 | 0.5864 |
| 2022/23 | production | 0.5421 | 0.9902 | 0.5866 | 0.0632 | 0.0690 | 0.5484 |
| 2022/23 | production_minus_xg_diff | 0.5474 | 0.9956 | 0.5909 | 0.0676 | 0.0575 | 0.5508 |
| 2022/23 | candidate_minus_xg_diff_plus_ratings | 0.5579 | 0.9660 | 0.5727 | 0.0597 | 0.0805 | 0.5335 |
| 2022/23 | candidate_minus_xg_diff_plus_attack_ratings | 0.5316 | 0.9927 | 0.5890 | 0.0678 | 0.0575 | 0.5485 |
| 2022/23 | candidate_minus_xg_diff_plus_defense_ratings | 0.5553 | 0.9734 | 0.5771 | 0.0535 | 0.0920 | 0.5383 |
| 2022/23 | candidate_minus_xg_diff_plus_matchup_ratings | 0.5395 | 0.9836 | 0.5830 | 0.0652 | 0.0575 | 0.5499 |
| 2022/23 | production_plus_full_ratings | 0.5368 | 0.9730 | 0.5763 | 0.0561 | 0.0575 | 0.5385 |
| 2022/23 | ratings_replace_all_raw_xg | 0.5658 | 0.9692 | 0.5735 | 0.0599 | 0.1494 | 0.5300 |
| 2023/24 | production | 0.5579 | 0.9676 | 0.5705 | 0.0642 | 0.0366 | 0.5253 |
| 2023/24 | production_minus_xg_diff | 0.5579 | 0.9703 | 0.5715 | 0.0549 | 0.0366 | 0.5310 |
| 2023/24 | candidate_minus_xg_diff_plus_ratings | 0.5447 | 0.9821 | 0.5806 | 0.0520 | 0.0122 | 0.5331 |
| 2023/24 | candidate_minus_xg_diff_plus_attack_ratings | 0.5632 | 0.9765 | 0.5742 | 0.0412 | 0.0122 | 0.5350 |
| 2023/24 | candidate_minus_xg_diff_plus_defense_ratings | 0.5526 | 0.9704 | 0.5726 | 0.0503 | 0.0122 | 0.5247 |
| 2023/24 | candidate_minus_xg_diff_plus_matchup_ratings | 0.5447 | 0.9770 | 0.5771 | 0.0412 | 0.0366 | 0.5307 |
| 2023/24 | production_plus_full_ratings | 0.5395 | 0.9810 | 0.5803 | 0.0530 | 0.0000 | 0.5295 |
| 2023/24 | ratings_replace_all_raw_xg | 0.5105 | 0.9870 | 0.5866 | 0.0541 | 0.0000 | 0.5299 |
| 2024/25 | production | 0.5105 | 1.0371 | 0.6197 | 0.0574 | 0.0108 | 0.5826 |
| 2024/25 | production_minus_xg_diff | 0.5132 | 1.0312 | 0.6157 | 0.0491 | 0.0108 | 0.5783 |
| 2024/25 | candidate_minus_xg_diff_plus_ratings | 0.4947 | 1.0260 | 0.6133 | 0.0547 | 0.0108 | 0.5727 |
| 2024/25 | candidate_minus_xg_diff_plus_attack_ratings | 0.5053 | 1.0269 | 0.6140 | 0.0531 | 0.0108 | 0.5776 |
| 2024/25 | candidate_minus_xg_diff_plus_defense_ratings | 0.5079 | 1.0290 | 0.6151 | 0.0553 | 0.0108 | 0.5751 |
| 2024/25 | candidate_minus_xg_diff_plus_matchup_ratings | 0.5079 | 1.0358 | 0.6186 | 0.0497 | 0.0430 | 0.5800 |
| 2024/25 | production_plus_full_ratings | 0.4895 | 1.0315 | 0.6172 | 0.0533 | 0.0215 | 0.5759 |
| 2024/25 | ratings_replace_all_raw_xg | 0.4947 | 1.0397 | 0.6218 | 0.0450 | 0.0215 | 0.5768 |
| 2025/26 | production | 0.4763 | 1.0714 | 0.6443 | 0.0496 | 0.0481 | 0.6053 |
| 2025/26 | production_minus_xg_diff | 0.4737 | 1.0733 | 0.6456 | 0.0511 | 0.0288 | 0.6073 |
| 2025/26 | candidate_minus_xg_diff_plus_ratings | 0.4553 | 1.0750 | 0.6467 | 0.0662 | 0.0288 | 0.6113 |
| 2025/26 | candidate_minus_xg_diff_plus_attack_ratings | 0.4684 | 1.0717 | 0.6451 | 0.0507 | 0.0288 | 0.6086 |
| 2025/26 | candidate_minus_xg_diff_plus_defense_ratings | 0.4579 | 1.0767 | 0.6461 | 0.0635 | 0.0385 | 0.6131 |
| 2025/26 | candidate_minus_xg_diff_plus_matchup_ratings | 0.4737 | 1.0707 | 0.6435 | 0.0484 | 0.0385 | 0.6070 |
| 2025/26 | production_plus_full_ratings | 0.4553 | 1.0733 | 0.6460 | 0.0653 | 0.0288 | 0.6085 |
| 2025/26 | ratings_replace_all_raw_xg | 0.4579 | 1.0718 | 0.6446 | 0.0587 | 0.0385 | 0.6094 |

## Decision

Best average Log Loss delta model: `candidate_minus_xg_diff_plus_defense_ratings`.

Best model mean Log Loss delta: -0.0027.
Best model mean Brier delta: -0.0020.
Best model improved Log Loss in 2 of 5 seasons.
Best model improved Brier in 2 of 5 seasons.

Candidate `candidate_minus_xg_diff_plus_ratings` mean Log Loss delta: -0.0016.
Candidate mean Brier delta: 0.0001.
Candidate mean ECE delta: -0.0015.

Do not promote yet. The best focused variant improves average Log Loss/Brier, but the gain is not stable across enough seasons.

Production gate remains: improve Log Loss or Brier across most rolling splits without materially worsening calibration.