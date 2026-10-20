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
| Man City | 1.0000 | Elite | 1320000000 | 47142857 | 28 | High | 81.3332 | 1.5008 | 0.0000 |
| Arsenal | 2.0000 | Elite | 1250000000 | 52083333 | 24 | High | 71.0861 | 3.1499 | 0.0000 |
| Chelsea | 3.0000 | Elite | 1110000000 | 37000000 | 30 | High | 59.5838 | 6.6385 | 0.0009 |
| Liverpool | 4.0000 | Elite | 939500000 | 33553571 | 28 | High | 70.2616 | 3.4819 | 0.0000 |
| Man United | 5.0000 | Strong | 752100000 | 30084000 | 25 | High | 56.8385 | 7.8698 | 0.0043 |
| Tottenham | 6.0000 | Strong | 700000000 | 23333333 | 30 | High | 39.1859 | 16.2275 | 0.4156 |
| Newcastle | 7.0000 | Strong | 696350000 | 24012069 | 29 | High | 44.6367 | 13.5786 | 0.1454 |
| Nott'm Forest | 8.0000 | Strong | 577600000 | 19917241 | 29 | High | 47.9329 | 11.9637 | 0.0706 |
| Brighton | 9.0000 | Mid-table | 567000000 | 17181818 | 33 | High | 69.3770 | 3.6184 | 0.0000 |
| Bournemouth | 10.0000 | Mid-table | 565700000 | 21757692 | 26 | High | 60.2731 | 6.2982 | 0.0004 |
| Crystal Palace | 11.0000 | Mid-table | 553000000 | 18433333 | 30 | High | 39.9537 | 15.5817 | 0.3255 |
| Aston Villa | 12.0000 | Mid-table | 531500000 | 20442308 | 26 | High | 51.1670 | 10.0267 | 0.0200 |
| Brentford | 13.0000 | Mid-table | 490580000 | 15825161 | 31 | High | 50.4451 | 10.4332 | 0.0238 |
| Everton | 14.0000 | Mid-table | 443150000 | 17044231 | 26 | High | 55.0227 | 8.4926 | 0.0063 |
| Sunderland | 15.0000 | Lower-table | 386430000 | 13801071 | 28 | High | 39.0846 | 16.1746 | 0.4154 |
| Leeds | 16.0000 | Lower-table | 358800000 | 13800000 | 26 | High | 45.7947 | 12.9436 | 0.1066 |
| Fulham | 17.0000 | Lower-table | 356200000 | 14248000 | 25 | High | 44.3695 | 13.5115 | 0.1425 |
| Ipswich | 18.0000 | Promoted / uncertain | 212950000 | 7098333 | 30 | Medium | 32.0532 | 18.6610 | 0.8041 |
| Coventry | 19.0000 | Promoted / uncertain | 194250000 | 7471154 | 26 | Medium | 40.0979 | 15.4628 | 0.3146 |
| Hull | 20.0000 | Promoted / uncertain | 95900000 | 3551852 | 27 | Medium | 42.7535 | 14.3850 | 0.2040 |

## 3. Calculation

`squad_strength_score = min-max normalized log(squad_market_value_eur)` across the 20 projected Premier League teams.

The log transform prevents the richest squads from dominating the prior too aggressively. The score is converted into a mild pre-season probability prior, strongest in matchweeks 1-5, lower in matchweeks 6-12 and small after matchweek 12.

## 4. Effect on Season Projection

| team | expected_points_before_squad_strength | expected_points | expected_points_delta | relegation_probability_before_squad_strength | relegation_probability | relegation_probability_delta |
| --- | --- | --- | --- | --- | --- | --- |
| Ipswich | 31.5362 | 32.0532 | 0.5170 | 0.8185 | 0.8041 | -0.0144 |
| Tottenham | 38.7958 | 39.1859 | 0.3901 | 0.4284 | 0.4156 | -0.0128 |
| Crystal Palace | 39.5699 | 39.9537 | 0.3838 | 0.3369 | 0.3255 | -0.0114 |
| Newcastle | 44.3383 | 44.6367 | 0.2984 | 0.1487 | 0.1454 | -0.0033 |
| Sunderland | 38.8942 | 39.0846 | 0.1904 | 0.4146 | 0.4154 | 0.0008 |
| Leeds | 45.6715 | 45.7947 | 0.1232 | 0.1044 | 0.1066 | 0.0022 |
| Brentford | 50.3838 | 50.4451 | 0.0613 | 0.0231 | 0.0238 | 0.0007 |
| Chelsea | 59.5569 | 59.5838 | 0.0269 | 0.0012 | 0.0009 | -0.0003 |
| Nott'm Forest | 47.9501 | 47.9329 | -0.0172 | 0.0662 | 0.0706 | 0.0044 |
| Coventry | 40.1180 | 40.0979 | -0.0201 | 0.3036 | 0.3146 | 0.0110 |
| Fulham | 44.4042 | 44.3695 | -0.0347 | 0.1377 | 0.1425 | 0.0048 |
| Aston Villa | 51.2055 | 51.1670 | -0.0385 | 0.0187 | 0.0200 | 0.0013 |
| Arsenal | 71.2214 | 71.0861 | -0.1353 | 0.0000 | 0.0000 | 0.0000 |
| Everton | 55.2140 | 55.0227 | -0.1913 | 0.0054 | 0.0063 | 0.0009 |
| Man United | 57.0361 | 56.8385 | -0.1976 | 0.0040 | 0.0043 | 0.0003 |
| Hull | 42.9635 | 42.7535 | -0.2100 | 0.1883 | 0.2040 | 0.0157 |
| Brighton | 69.8023 | 69.3770 | -0.4253 | 0.0000 | 0.0000 | 0.0000 |
| Man City | 81.7903 | 81.3332 | -0.4571 | 0.0000 | 0.0000 | 0.0000 |
| Liverpool | 70.7317 | 70.2616 | -0.4701 | 0.0000 | 0.0000 | 0.0000 |
| Bournemouth | 60.7564 | 60.2731 | -0.4833 | 0.0003 | 0.0004 | 0.0001 |

## 5. Promoted Team Interaction

| team | promoted_team_flag | squad_strength_rank | squad_strength_score | promotion_adjustment_applied | fallback_used | expected_points | relegation_probability |
| --- | --- | --- | --- | --- | --- | --- | --- |
| Coventry | True | 19.0000 | 0.2692 | False | False | 40.0979 | 0.3146 |
| Hull | True | 20.0000 | 0.0000 | False | False | 42.7535 | 0.2040 |
| Ipswich | True | 18.0000 | 0.3042 | False | False | 32.0532 | 0.8041 |

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
