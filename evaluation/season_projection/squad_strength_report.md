# Squad Strength / Market Value Report

## 1. Data Source and Coverage

The project uses a manually maintained CSV-first dataset:

- File: `data/squad_strength_2026_27.csv`
- Teams covered: `20` of `20`
- Sources: Transfermarkt Premier League and Championship competition start pages
- Historical validation: not available in this project, so this is classified as a Season Projection preseason prior / research feature.

## 2. Team Squad Strength Ranking

| team | squad_strength_rank | squad_strength_bucket | squad_market_value_eur | average_player_value_eur | squad_size | data_confidence | expected_points | expected_position | relegation_probability |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| Man City | 1.0000 | Elite | 1320000000 | 47142857 | 28 | High | 79.2288 | 1.9138 | 0.0000 |
| Arsenal | 2.0000 | Elite | 1250000000 | 52083333 | 24 | High | 80.9402 | 1.6311 | 0.0000 |
| Chelsea | 3.0000 | Elite | 1110000000 | 37000000 | 30 | High | 54.4925 | 8.6691 | 0.0063 |
| Liverpool | 4.0000 | Elite | 939500000 | 33553571 | 28 | High | 67.4957 | 4.1536 | 0.0001 |
| Man United | 5.0000 | Strong | 752100000 | 30084000 | 25 | High | 65.2483 | 4.8410 | 0.0000 |
| Tottenham | 6.0000 | Strong | 700000000 | 23333333 | 30 | High | 37.6104 | 16.7166 | 0.4793 |
| Newcastle | 7.0000 | Strong | 696350000 | 24012069 | 29 | High | 51.3534 | 10.3165 | 0.0253 |
| Nott'm Forest | 8.0000 | Strong | 577600000 | 19917241 | 29 | High | 53.0397 | 9.5644 | 0.0169 |
| Brighton | 9.0000 | Mid-table | 567000000 | 17181818 | 33 | High | 62.5021 | 5.5493 | 0.0008 |
| Bournemouth | 10.0000 | Mid-table | 565700000 | 21757692 | 26 | High | 57.7699 | 7.1790 | 0.0029 |
| Crystal Palace | 11.0000 | Mid-table | 553000000 | 18433333 | 30 | High | 38.0458 | 16.3131 | 0.4219 |
| Aston Villa | 12.0000 | Mid-table | 531500000 | 20442308 | 26 | High | 46.4148 | 12.3550 | 0.0834 |
| Brentford | 13.0000 | Mid-table | 490580000 | 15825161 | 31 | High | 49.2198 | 11.0797 | 0.0367 |
| Everton | 14.0000 | Mid-table | 443150000 | 17044231 | 26 | High | 49.8917 | 10.8769 | 0.0345 |
| Sunderland | 15.0000 | Lower-table | 386430000 | 13801071 | 28 | High | 48.9931 | 11.5358 | 0.0475 |
| Leeds | 16.0000 | Lower-table | 358800000 | 13800000 | 26 | High | 46.1686 | 12.7853 | 0.1033 |
| Fulham | 17.0000 | Lower-table | 356200000 | 14248000 | 25 | High | 40.7971 | 15.2234 | 0.2824 |
| Ipswich | 18.0000 | Promoted / uncertain | 212950000 | 7098333 | 30 | Medium | 29.2544 | 19.1232 | 0.8871 |
| Coventry | 19.0000 | Promoted / uncertain | 194250000 | 7471154 | 26 | Medium | 37.8913 | 16.3035 | 0.4169 |
| Hull | 20.0000 | Promoted / uncertain | 95900000 | 3551852 | 27 | Medium | 43.8594 | 13.8697 | 0.1547 |

## 3. Calculation

`squad_strength_score = min-max normalized log(squad_market_value_eur)` across the 20 projected Premier League teams.

The log transform prevents the richest squads from dominating the prior too aggressively. The score is converted into a mild pre-season probability prior, strongest in matchweeks 1-5, lower in matchweeks 6-12 and small after matchweek 12.

## 4. Effect on Season Projection

| team | expected_points_before_squad_strength | expected_points | expected_points_delta | relegation_probability_before_squad_strength | relegation_probability | relegation_probability_delta |
| --- | --- | --- | --- | --- | --- | --- |
| Ipswich | 28.6365 | 29.2544 | 0.6179 | 0.8999 | 0.8871 | -0.0128 |
| Tottenham | 37.1064 | 37.6104 | 0.5040 | 0.4988 | 0.4793 | -0.0195 |
| Crystal Palace | 37.6107 | 38.0458 | 0.4351 | 0.4363 | 0.4219 | -0.0144 |
| Chelsea | 54.2819 | 54.4925 | 0.2106 | 0.0071 | 0.0063 | -0.0008 |
| Newcastle | 51.2184 | 51.3534 | 0.1350 | 0.0246 | 0.0253 | 0.0007 |
| Leeds | 46.0399 | 46.1686 | 0.1287 | 0.1005 | 0.1033 | 0.0028 |
| Brentford | 49.1053 | 49.2198 | 0.1145 | 0.0369 | 0.0367 | -0.0002 |
| Fulham | 40.7415 | 40.7971 | 0.0556 | 0.2753 | 0.2824 | 0.0071 |
| Aston Villa | 46.4053 | 46.4148 | 0.0095 | 0.0813 | 0.0834 | 0.0021 |
| Everton | 49.8948 | 49.8917 | -0.0031 | 0.0329 | 0.0345 | 0.0016 |
| Coventry | 37.9431 | 37.8913 | -0.0518 | 0.4038 | 0.4169 | 0.0131 |
| Sunderland | 49.0492 | 48.9931 | -0.0561 | 0.0450 | 0.0475 | 0.0025 |
| Nott'm Forest | 53.1252 | 53.0397 | -0.0855 | 0.0150 | 0.0169 | 0.0019 |
| Hull | 44.0647 | 43.8594 | -0.2053 | 0.1396 | 0.1547 | 0.0151 |
| Brighton | 62.7884 | 62.5021 | -0.2863 | 0.0005 | 0.0008 | 0.0003 |
| Bournemouth | 58.0576 | 57.7699 | -0.2877 | 0.0025 | 0.0029 | 0.0004 |
| Liverpool | 67.8784 | 67.4957 | -0.3827 | 0.0000 | 0.0001 | 0.0001 |
| Man City | 79.7264 | 79.2288 | -0.4976 | 0.0000 | 0.0000 | 0.0000 |
| Man United | 65.7956 | 65.2483 | -0.5473 | 0.0000 | 0.0000 | 0.0000 |
| Arsenal | 81.5016 | 80.9402 | -0.5614 | 0.0000 | 0.0000 | 0.0000 |

## 5. Promoted Team Interaction

| team | promoted_team_flag | squad_strength_rank | squad_strength_score | promotion_adjustment_applied | fallback_used | expected_points | relegation_probability |
| --- | --- | --- | --- | --- | --- | --- | --- |
| Coventry | True | 19.0000 | 0.2692 | True | False | 37.8913 | 0.4169 |
| Hull | True | 20.0000 | 0.0000 | True | False | 43.8594 | 0.1547 |
| Ipswich | True | 18.0000 | 0.3042 | True | False | 29.2544 | 0.8871 |

## 6. Validation

Historical squad market value snapshots are not currently stored locally, so this sprint does not claim a proven model improvement. Validation remains required before using squad strength in the single-match production model.

## 7. Limitations

- Squad market values change during transfer windows and must be maintained manually.
- Transfermarkt values are estimates, not audited financial values.
- The prior does not include wages, injuries, suspensions or expected lineups.
- The effect is intentionally mild and should not override xG, Elo or actual performance.

## 8. Recommendation

`Research / Season Projection prior`

Use squad strength in Season Projection as a transparent preseason stabilizer. Do not add it to the single-match model until historical market-value snapshots are available for backtesting.
