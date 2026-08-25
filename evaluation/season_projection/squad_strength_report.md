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
| Man City | 1.0000 | Elite | 1320000000 | 47142857 | 28 | High | 76.8969 | 1.9403 | 0.0000 |
| Arsenal | 2.0000 | Elite | 1250000000 | 52083333 | 24 | High | 75.3845 | 2.0916 | 0.0000 |
| Chelsea | 3.0000 | Elite | 1110000000 | 37000000 | 30 | High | 50.4090 | 10.7394 | 0.0533 |
| Liverpool | 4.0000 | Elite | 939500000 | 33553571 | 28 | High | 62.8644 | 5.3325 | 0.0016 |
| Man United | 5.0000 | Strong | 752100000 | 30084000 | 25 | High | 67.4792 | 3.9417 | 0.0002 |
| Tottenham | 6.0000 | Strong | 700000000 | 23333333 | 30 | High | 42.1480 | 15.3162 | 0.3481 |
| Newcastle | 7.0000 | Strong | 696350000 | 24012069 | 29 | High | 47.0802 | 12.7588 | 0.1468 |
| Nott'm Forest | 8.0000 | Strong | 577600000 | 19917241 | 29 | High | 43.0783 | 14.8453 | 0.2913 |
| Brighton | 9.0000 | Mid-table | 567000000 | 17181818 | 33 | High | 62.3687 | 5.3465 | 0.0011 |
| Bournemouth | 10.0000 | Mid-table | 565700000 | 21757692 | 26 | High | 50.1644 | 10.7709 | 0.0604 |
| Crystal Palace | 11.0000 | Mid-table | 553000000 | 18433333 | 30 | High | 39.8185 | 16.1182 | 0.4341 |
| Aston Villa | 12.0000 | Mid-table | 531500000 | 20442308 | 26 | High | 49.2288 | 11.2099 | 0.0772 |
| Brentford | 13.0000 | Mid-table | 490580000 | 15825161 | 31 | High | 49.7782 | 11.0008 | 0.0641 |
| Everton | 14.0000 | Mid-table | 443150000 | 17044231 | 26 | High | 50.1057 | 10.9663 | 0.0664 |
| Sunderland | 15.0000 | Lower-table | 386430000 | 13801071 | 28 | High | 47.5263 | 12.5956 | 0.1329 |
| Leeds | 16.0000 | Lower-table | 358800000 | 13800000 | 26 | High | 48.2868 | 12.0405 | 0.1054 |
| Fulham | 17.0000 | Lower-table | 356200000 | 14248000 | 25 | High | 42.0710 | 15.1406 | 0.3323 |
| Ipswich | 18.0000 | Promoted / uncertain | 212950000 | 7098333 | 30 | Medium | 52.4309 | 9.8611 | 0.0401 |
| Coventry | 19.0000 | Promoted / uncertain | 194250000 | 7471154 | 26 | Medium | 32.2454 | 18.7005 | 0.8158 |
| Hull | 20.0000 | Promoted / uncertain | 95900000 | 3551852 | 27 | Medium | 53.5360 | 9.2833 | 0.0289 |

## 3. Calculation

`squad_strength_score = min-max normalized log(squad_market_value_eur)` across the 20 projected Premier League teams.

The log transform prevents the richest squads from dominating the prior too aggressively. The score is converted into a mild pre-season probability prior, strongest in matchweeks 1-5, lower in matchweeks 6-12 and small after matchweek 12.

## 4. Effect on Season Projection

| team | expected_points_before_squad_strength | expected_points | expected_points_delta | relegation_probability_before_squad_strength | relegation_probability | relegation_probability_delta |
| --- | --- | --- | --- | --- | --- | --- |
| Crystal Palace | 39.3704 | 39.8185 | 0.4481 | 0.4486 | 0.4341 | -0.0145 |
| Chelsea | 50.0090 | 50.4090 | 0.4000 | 0.0570 | 0.0533 | -0.0037 |
| Tottenham | 41.7753 | 42.1480 | 0.3727 | 0.3574 | 0.3481 | -0.0093 |
| Coventry | 31.9059 | 32.2454 | 0.3395 | 0.8222 | 0.8158 | -0.0064 |
| Newcastle | 46.8310 | 47.0802 | 0.2492 | 0.1465 | 0.1468 | 0.0003 |
| Nott'm Forest | 42.8320 | 43.0783 | 0.2463 | 0.2922 | 0.2913 | -0.0009 |
| Fulham | 41.9158 | 42.0710 | 0.1552 | 0.3302 | 0.3323 | 0.0021 |
| Brentford | 49.6803 | 49.7782 | 0.0979 | 0.0639 | 0.0641 | 0.0002 |
| Everton | 50.0430 | 50.1057 | 0.0627 | 0.0643 | 0.0664 | 0.0021 |
| Aston Villa | 49.1867 | 49.2288 | 0.0421 | 0.0729 | 0.0772 | 0.0043 |
| Leeds | 48.2542 | 48.2868 | 0.0326 | 0.0999 | 0.1054 | 0.0055 |
| Bournemouth | 50.1572 | 50.1644 | 0.0072 | 0.0570 | 0.0604 | 0.0034 |
| Sunderland | 47.5304 | 47.5263 | -0.0041 | 0.1263 | 0.1329 | 0.0066 |
| Liverpool | 63.0739 | 62.8644 | -0.2095 | 0.0014 | 0.0016 | 0.0002 |
| Ipswich | 52.7575 | 52.4309 | -0.3266 | 0.0355 | 0.0401 | 0.0046 |
| Brighton | 62.7102 | 62.3687 | -0.3415 | 0.0008 | 0.0011 | 0.0003 |
| Man United | 68.0208 | 67.4792 | -0.5416 | 0.0001 | 0.0002 | 0.0001 |
| Man City | 77.4743 | 76.8969 | -0.5774 | 0.0000 | 0.0000 | 0.0000 |
| Arsenal | 75.9674 | 75.3845 | -0.5829 | 0.0000 | 0.0000 | 0.0000 |
| Hull | 54.1662 | 53.5360 | -0.6302 | 0.0238 | 0.0289 | 0.0051 |

## 5. Promoted Team Interaction

| team | promoted_team_flag | squad_strength_rank | squad_strength_score | promotion_adjustment_applied | fallback_used | expected_points | relegation_probability |
| --- | --- | --- | --- | --- | --- | --- | --- |
| Coventry | True | 19.0000 | 0.2692 | True | False | 32.2454 | 0.8158 |
| Hull | True | 20.0000 | 0.0000 | True | False | 53.5360 | 0.0289 |
| Ipswich | True | 18.0000 | 0.3042 | False | False | 52.4309 | 0.0401 |

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
