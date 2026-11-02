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
| Man City | 1.0000 | Elite | 1320000000 | 47142857 | 28 | High | 77.1733 | 1.8740 | 0.0000 |
| Arsenal | 2.0000 | Elite | 1250000000 | 52083333 | 24 | High | 76.1751 | 1.9365 | 0.0000 |
| Chelsea | 3.0000 | Elite | 1110000000 | 37000000 | 30 | High | 59.6138 | 6.5007 | 0.0010 |
| Liverpool | 4.0000 | Elite | 939500000 | 33553571 | 28 | High | 64.6740 | 4.8172 | 0.0003 |
| Man United | 5.0000 | Strong | 752100000 | 30084000 | 25 | High | 45.8997 | 13.2578 | 0.1367 |
| Tottenham | 6.0000 | Strong | 700000000 | 23333333 | 30 | High | 52.6370 | 9.9196 | 0.0236 |
| Newcastle | 7.0000 | Strong | 696350000 | 24012069 | 29 | High | 48.8815 | 11.7644 | 0.0573 |
| Nott'm Forest | 8.0000 | Strong | 577600000 | 19917241 | 29 | High | 47.1838 | 12.6587 | 0.1024 |
| Brighton | 9.0000 | Mid-table | 567000000 | 17181818 | 33 | High | 66.2504 | 4.2415 | 0.0000 |
| Bournemouth | 10.0000 | Mid-table | 565700000 | 21757692 | 26 | High | 63.1680 | 5.1230 | 0.0000 |
| Crystal Palace | 11.0000 | Mid-table | 553000000 | 18433333 | 30 | High | 35.9206 | 17.5652 | 0.6303 |
| Aston Villa | 12.0000 | Mid-table | 531500000 | 20442308 | 26 | High | 54.0194 | 8.7924 | 0.0114 |
| Brentford | 13.0000 | Mid-table | 490580000 | 15825161 | 31 | High | 52.0037 | 9.8321 | 0.0142 |
| Everton | 14.0000 | Mid-table | 443150000 | 17044231 | 26 | High | 48.1413 | 11.9122 | 0.0688 |
| Sunderland | 15.0000 | Lower-table | 386430000 | 13801071 | 28 | High | 38.3958 | 16.8258 | 0.5133 |
| Leeds | 16.0000 | Lower-table | 358800000 | 13800000 | 26 | High | 44.5084 | 13.9274 | 0.1648 |
| Fulham | 17.0000 | Lower-table | 356200000 | 14248000 | 25 | High | 48.7792 | 11.6203 | 0.0535 |
| Ipswich | 18.0000 | Promoted / uncertain | 212950000 | 7098333 | 30 | Medium | 32.4743 | 18.7594 | 0.8297 |
| Coventry | 19.0000 | Promoted / uncertain | 194250000 | 7471154 | 26 | Medium | 43.4178 | 14.2901 | 0.1883 |
| Hull | 20.0000 | Promoted / uncertain | 95900000 | 3551852 | 27 | Medium | 43.5089 | 14.3817 | 0.2044 |

## 3. Calculation

`squad_strength_score = min-max normalized log(squad_market_value_eur)` across the 20 projected Premier League teams.

The log transform prevents the richest squads from dominating the prior too aggressively. The score is converted into a mild pre-season probability prior, strongest in matchweeks 1-5, lower in matchweeks 6-12 and small after matchweek 12.

## 4. Effect on Season Projection

| team | expected_points_before_squad_strength | expected_points | expected_points_delta | relegation_probability_before_squad_strength | relegation_probability | relegation_probability_delta |
| --- | --- | --- | --- | --- | --- | --- |
| Ipswich | 31.9992 | 32.4743 | 0.4751 | 0.8459 | 0.8297 | -0.0162 |
| Crystal Palace | 35.4568 | 35.9206 | 0.4638 | 0.6506 | 0.6303 | -0.0203 |
| Newcastle | 48.6742 | 48.8815 | 0.2073 | 0.0591 | 0.0573 | -0.0018 |
| Sunderland | 38.2518 | 38.3958 | 0.1440 | 0.5153 | 0.5133 | -0.0020 |
| Leeds | 44.3727 | 44.5084 | 0.1357 | 0.1641 | 0.1648 | 0.0007 |
| Man United | 45.7980 | 45.8997 | 0.1017 | 0.1374 | 0.1367 | -0.0007 |
| Everton | 48.0893 | 48.1413 | 0.0520 | 0.0678 | 0.0688 | 0.0010 |
| Tottenham | 52.5922 | 52.6370 | 0.0448 | 0.0230 | 0.0236 | 0.0006 |
| Brentford | 51.9798 | 52.0037 | 0.0239 | 0.0147 | 0.0142 | -0.0005 |
| Chelsea | 59.5996 | 59.6138 | 0.0142 | 0.0010 | 0.0010 | 0.0000 |
| Nott'm Forest | 47.1746 | 47.1838 | 0.0092 | 0.0988 | 0.1024 | 0.0036 |
| Aston Villa | 54.1652 | 54.0194 | -0.1458 | 0.0102 | 0.0114 | 0.0012 |
| Fulham | 48.9299 | 48.7792 | -0.1507 | 0.0477 | 0.0535 | 0.0058 |
| Coventry | 43.6198 | 43.4178 | -0.2020 | 0.1747 | 0.1883 | 0.0136 |
| Hull | 43.7225 | 43.5089 | -0.2136 | 0.1896 | 0.2044 | 0.0148 |
| Arsenal | 76.4350 | 76.1751 | -0.2599 | 0.0000 | 0.0000 | 0.0000 |
| Brighton | 66.5255 | 66.2504 | -0.2751 | 0.0000 | 0.0000 | 0.0000 |
| Liverpool | 64.9656 | 64.6740 | -0.2916 | 0.0001 | 0.0003 | 0.0002 |
| Man City | 77.5923 | 77.1733 | -0.4190 | 0.0000 | 0.0000 | 0.0000 |
| Bournemouth | 63.6320 | 63.1680 | -0.4640 | 0.0000 | 0.0000 | 0.0000 |

## 5. Promoted Team Interaction

| team | promoted_team_flag | squad_strength_rank | squad_strength_score | promotion_adjustment_applied | fallback_used | expected_points | relegation_probability |
| --- | --- | --- | --- | --- | --- | --- | --- |
| Coventry | True | 19.0000 | 0.2692 | False | False | 43.4178 | 0.1883 |
| Hull | True | 20.0000 | 0.0000 | False | False | 43.5089 | 0.2044 |
| Ipswich | True | 18.0000 | 0.3042 | False | False | 32.4743 | 0.8297 |

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
