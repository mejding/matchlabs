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
| Man City | 1.0000 | Elite | 1320000000 | 47142857 | 28 | High | 79.9862 | 1.4881 | 0.0000 |
| Arsenal | 2.0000 | Elite | 1250000000 | 52083333 | 24 | High | 72.1026 | 2.6296 | 0.0000 |
| Chelsea | 3.0000 | Elite | 1110000000 | 37000000 | 30 | High | 55.6921 | 7.8690 | 0.0060 |
| Liverpool | 4.0000 | Elite | 939500000 | 33553571 | 28 | High | 64.9468 | 4.5008 | 0.0003 |
| Man United | 5.0000 | Strong | 752100000 | 30084000 | 25 | High | 48.6729 | 11.6614 | 0.0758 |
| Tottenham | 6.0000 | Strong | 700000000 | 23333333 | 30 | High | 44.0112 | 14.3492 | 0.2247 |
| Newcastle | 7.0000 | Strong | 696350000 | 24012069 | 29 | High | 48.5141 | 11.7943 | 0.0752 |
| Nott'm Forest | 8.0000 | Strong | 577600000 | 19917241 | 29 | High | 50.5818 | 10.7037 | 0.0465 |
| Brighton | 9.0000 | Mid-table | 567000000 | 17181818 | 33 | High | 69.3242 | 3.2670 | 0.0000 |
| Bournemouth | 10.0000 | Mid-table | 565700000 | 21757692 | 26 | High | 60.3920 | 5.8437 | 0.0016 |
| Crystal Palace | 11.0000 | Mid-table | 553000000 | 18433333 | 30 | High | 39.3550 | 16.2796 | 0.4445 |
| Aston Villa | 12.0000 | Mid-table | 531500000 | 20442308 | 26 | High | 52.7967 | 9.1461 | 0.0187 |
| Brentford | 13.0000 | Mid-table | 490580000 | 15825161 | 31 | High | 51.3461 | 9.9624 | 0.0276 |
| Everton | 14.0000 | Mid-table | 443150000 | 17044231 | 26 | High | 47.9336 | 11.8928 | 0.0805 |
| Sunderland | 15.0000 | Lower-table | 386430000 | 13801071 | 28 | High | 39.3514 | 16.5246 | 0.4847 |
| Leeds | 16.0000 | Lower-table | 358800000 | 13800000 | 26 | High | 48.7219 | 11.5764 | 0.0734 |
| Fulham | 17.0000 | Lower-table | 356200000 | 14248000 | 25 | High | 47.7320 | 12.0299 | 0.0849 |
| Ipswich | 18.0000 | Promoted / uncertain | 212950000 | 7098333 | 30 | Medium | 33.9920 | 18.4744 | 0.7768 |
| Coventry | 19.0000 | Promoted / uncertain | 194250000 | 7471154 | 26 | Medium | 40.5203 | 15.6934 | 0.3577 |
| Hull | 20.0000 | Promoted / uncertain | 95900000 | 3551852 | 27 | Medium | 43.6375 | 14.3136 | 0.2211 |

## 3. Calculation

`squad_strength_score = min-max normalized log(squad_market_value_eur)` across the 20 projected Premier League teams.

The log transform prevents the richest squads from dominating the prior too aggressively. The score is converted into a mild pre-season probability prior, strongest in matchweeks 1-5, lower in matchweeks 6-12 and small after matchweek 12.

## 4. Effect on Season Projection

| team | expected_points_before_squad_strength | expected_points | expected_points_delta | relegation_probability_before_squad_strength | relegation_probability | relegation_probability_delta |
| --- | --- | --- | --- | --- | --- | --- |
| Ipswich | 33.5640 | 33.9920 | 0.4280 | 0.7896 | 0.7768 | -0.0128 |
| Crystal Palace | 38.9976 | 39.3550 | 0.3574 | 0.4610 | 0.4445 | -0.0165 |
| Tottenham | 43.7187 | 44.0112 | 0.2925 | 0.2334 | 0.2247 | -0.0087 |
| Newcastle | 48.2945 | 48.5141 | 0.2196 | 0.0789 | 0.0752 | -0.0037 |
| Sunderland | 39.2092 | 39.3514 | 0.1422 | 0.4875 | 0.4847 | -0.0028 |
| Chelsea | 55.5871 | 55.6921 | 0.1050 | 0.0058 | 0.0060 | 0.0002 |
| Everton | 47.8786 | 47.9336 | 0.0550 | 0.0783 | 0.0805 | 0.0022 |
| Man United | 48.6394 | 48.6729 | 0.0335 | 0.0733 | 0.0758 | 0.0025 |
| Leeds | 48.7002 | 48.7219 | 0.0217 | 0.0705 | 0.0734 | 0.0029 |
| Brentford | 51.3541 | 51.3461 | -0.0080 | 0.0261 | 0.0276 | 0.0015 |
| Aston Villa | 52.8371 | 52.7967 | -0.0404 | 0.0177 | 0.0187 | 0.0010 |
| Nott'm Forest | 50.6718 | 50.5818 | -0.0900 | 0.0442 | 0.0465 | 0.0023 |
| Fulham | 47.8500 | 47.7320 | -0.1180 | 0.0798 | 0.0849 | 0.0051 |
| Coventry | 40.6516 | 40.5203 | -0.1313 | 0.3463 | 0.3577 | 0.0114 |
| Arsenal | 72.2655 | 72.1026 | -0.1629 | 0.0000 | 0.0000 | 0.0000 |
| Liverpool | 65.1840 | 64.9468 | -0.2372 | 0.0002 | 0.0003 | 0.0001 |
| Hull | 43.8811 | 43.6375 | -0.2436 | 0.2063 | 0.2211 | 0.0148 |
| Bournemouth | 60.7894 | 60.3920 | -0.3974 | 0.0011 | 0.0016 | 0.0005 |
| Brighton | 69.7597 | 69.3242 | -0.4355 | 0.0000 | 0.0000 | 0.0000 |
| Man City | 80.4443 | 79.9862 | -0.4581 | 0.0000 | 0.0000 | 0.0000 |

## 5. Promoted Team Interaction

| team | promoted_team_flag | squad_strength_rank | squad_strength_score | promotion_adjustment_applied | fallback_used | expected_points | relegation_probability |
| --- | --- | --- | --- | --- | --- | --- | --- |
| Coventry | True | 19.0000 | 0.2692 | False | False | 40.5203 | 0.3577 |
| Hull | True | 20.0000 | 0.0000 | False | False | 43.6375 | 0.2211 |
| Ipswich | True | 18.0000 | 0.3042 | False | False | 33.9920 | 0.7768 |

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
