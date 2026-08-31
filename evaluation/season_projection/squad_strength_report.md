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
| Man City | 1.0000 | Elite | 1320000000 | 47142857 | 28 | High | 79.1412 | 1.7253 | 0.0000 |
| Arsenal | 2.0000 | Elite | 1250000000 | 52083333 | 24 | High | 76.1163 | 2.0750 | 0.0000 |
| Chelsea | 3.0000 | Elite | 1110000000 | 37000000 | 30 | High | 56.7343 | 7.7738 | 0.0069 |
| Liverpool | 4.0000 | Elite | 939500000 | 33553571 | 28 | High | 66.5701 | 4.3017 | 0.0001 |
| Man United | 5.0000 | Strong | 752100000 | 30084000 | 25 | High | 63.3313 | 5.3538 | 0.0011 |
| Tottenham | 6.0000 | Strong | 700000000 | 23333333 | 30 | High | 36.5473 | 17.4319 | 0.6227 |
| Newcastle | 7.0000 | Strong | 696350000 | 24012069 | 29 | High | 51.3602 | 10.5882 | 0.0417 |
| Nott'm Forest | 8.0000 | Strong | 577600000 | 19917241 | 29 | High | 48.0624 | 12.3562 | 0.0976 |
| Brighton | 9.0000 | Mid-table | 567000000 | 17181818 | 33 | High | 62.8339 | 5.3393 | 0.0014 |
| Bournemouth | 10.0000 | Mid-table | 565700000 | 21757692 | 26 | High | 51.9036 | 9.9836 | 0.0301 |
| Crystal Palace | 11.0000 | Mid-table | 553000000 | 18433333 | 30 | High | 40.5880 | 15.6762 | 0.3572 |
| Aston Villa | 12.0000 | Mid-table | 531500000 | 20442308 | 26 | High | 49.9198 | 10.9617 | 0.0543 |
| Brentford | 13.0000 | Mid-table | 490580000 | 15825161 | 31 | High | 50.2740 | 10.8324 | 0.0458 |
| Everton | 14.0000 | Mid-table | 443150000 | 17044231 | 26 | High | 50.9857 | 10.6139 | 0.0425 |
| Sunderland | 15.0000 | Lower-table | 386430000 | 13801071 | 28 | High | 50.7895 | 10.9321 | 0.0543 |
| Leeds | 16.0000 | Lower-table | 358800000 | 13800000 | 26 | High | 46.1604 | 13.1969 | 0.1409 |
| Fulham | 17.0000 | Lower-table | 356200000 | 14248000 | 25 | High | 47.1094 | 12.6239 | 0.1104 |
| Ipswich | 18.0000 | Promoted / uncertain | 212950000 | 7098333 | 30 | Medium | 28.7260 | 19.3101 | 0.9180 |
| Coventry | 19.0000 | Promoted / uncertain | 194250000 | 7471154 | 26 | Medium | 41.2028 | 15.3582 | 0.3107 |
| Hull | 20.0000 | Promoted / uncertain | 95900000 | 3551852 | 27 | Medium | 45.3488 | 13.5658 | 0.1643 |

## 3. Calculation

`squad_strength_score = min-max normalized log(squad_market_value_eur)` across the 20 projected Premier League teams.

The log transform prevents the richest squads from dominating the prior too aggressively. The score is converted into a mild pre-season probability prior, strongest in matchweeks 1-5, lower in matchweeks 6-12 and small after matchweek 12.

## 4. Effect on Season Projection

| team | expected_points_before_squad_strength | expected_points | expected_points_delta | relegation_probability_before_squad_strength | relegation_probability | relegation_probability_delta |
| --- | --- | --- | --- | --- | --- | --- |
| Ipswich | 28.1287 | 28.7260 | 0.5973 | 0.9281 | 0.9180 | -0.0101 |
| Tottenham | 35.9721 | 36.5473 | 0.5752 | 0.6482 | 0.6227 | -0.0255 |
| Crystal Palace | 40.2777 | 40.5880 | 0.3103 | 0.3675 | 0.3572 | -0.0103 |
| Chelsea | 56.5403 | 56.7343 | 0.1940 | 0.0072 | 0.0069 | -0.0003 |
| Newcastle | 51.1807 | 51.3602 | 0.1795 | 0.0424 | 0.0417 | -0.0007 |
| Brentford | 50.1419 | 50.2740 | 0.1321 | 0.0453 | 0.0458 | 0.0005 |
| Leeds | 46.0562 | 46.1604 | 0.1042 | 0.1378 | 0.1409 | 0.0031 |
| Nott'm Forest | 47.9782 | 48.0624 | 0.0842 | 0.0950 | 0.0976 | 0.0026 |
| Everton | 51.0196 | 50.9857 | -0.0339 | 0.0398 | 0.0425 | 0.0027 |
| Bournemouth | 51.9472 | 51.9036 | -0.0436 | 0.0276 | 0.0301 | 0.0025 |
| Sunderland | 50.8406 | 50.7895 | -0.0511 | 0.0515 | 0.0543 | 0.0028 |
| Aston Villa | 49.9795 | 49.9198 | -0.0597 | 0.0516 | 0.0543 | 0.0027 |
| Coventry | 41.3019 | 41.2028 | -0.0991 | 0.2999 | 0.3107 | 0.0108 |
| Fulham | 47.2139 | 47.1094 | -0.1045 | 0.1058 | 0.1104 | 0.0046 |
| Hull | 45.6118 | 45.3488 | -0.2630 | 0.1503 | 0.1643 | 0.0140 |
| Man United | 63.6910 | 63.3313 | -0.3597 | 0.0009 | 0.0011 | 0.0002 |
| Brighton | 63.2005 | 62.8339 | -0.3666 | 0.0010 | 0.0014 | 0.0004 |
| Liverpool | 66.9762 | 66.5701 | -0.4061 | 0.0001 | 0.0001 | 0.0000 |
| Arsenal | 76.6591 | 76.1163 | -0.5428 | 0.0000 | 0.0000 | 0.0000 |
| Man City | 79.7091 | 79.1412 | -0.5679 | 0.0000 | 0.0000 | 0.0000 |

## 5. Promoted Team Interaction

| team | promoted_team_flag | squad_strength_rank | squad_strength_score | promotion_adjustment_applied | fallback_used | expected_points | relegation_probability |
| --- | --- | --- | --- | --- | --- | --- | --- |
| Coventry | True | 19.0000 | 0.2692 | True | False | 41.2028 | 0.3107 |
| Hull | True | 20.0000 | 0.0000 | True | False | 45.3488 | 0.1643 |
| Ipswich | True | 18.0000 | 0.3042 | False | False | 28.7260 | 0.9180 |

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
