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
| Man City | 1.0000 | Elite | 1320000000 | 47142857 | 28 | High | 80.7283 | 1.5195 | 0.0000 |
| Arsenal | 2.0000 | Elite | 1250000000 | 52083333 | 24 | High | 72.7702 | 2.7012 | 0.0000 |
| Chelsea | 3.0000 | Elite | 1110000000 | 37000000 | 30 | High | 57.8078 | 7.1603 | 0.0018 |
| Liverpool | 4.0000 | Elite | 939500000 | 33553571 | 28 | High | 67.0030 | 4.1865 | 0.0001 |
| Man United | 5.0000 | Strong | 752100000 | 30084000 | 25 | High | 54.2516 | 8.8759 | 0.0106 |
| Tottenham | 6.0000 | Strong | 700000000 | 23333333 | 30 | High | 43.3993 | 14.4498 | 0.2023 |
| Newcastle | 7.0000 | Strong | 696350000 | 24012069 | 29 | High | 47.6154 | 12.1823 | 0.0703 |
| Nott'm Forest | 8.0000 | Strong | 577600000 | 19917241 | 29 | High | 48.3899 | 11.8144 | 0.0654 |
| Brighton | 9.0000 | Mid-table | 567000000 | 17181818 | 33 | High | 70.7889 | 3.1823 | 0.0000 |
| Bournemouth | 10.0000 | Mid-table | 565700000 | 21757692 | 26 | High | 60.9112 | 5.8880 | 0.0006 |
| Crystal Palace | 11.0000 | Mid-table | 553000000 | 18433333 | 30 | High | 37.3945 | 16.8456 | 0.5074 |
| Aston Villa | 12.0000 | Mid-table | 531500000 | 20442308 | 26 | High | 50.3677 | 10.4046 | 0.0249 |
| Brentford | 13.0000 | Mid-table | 490580000 | 15825161 | 31 | High | 52.4695 | 9.4662 | 0.0122 |
| Everton | 14.0000 | Mid-table | 443150000 | 17044231 | 26 | High | 48.7574 | 11.3947 | 0.0487 |
| Sunderland | 15.0000 | Lower-table | 386430000 | 13801071 | 28 | High | 38.5442 | 16.6036 | 0.4752 |
| Leeds | 16.0000 | Lower-table | 358800000 | 13800000 | 26 | High | 48.2394 | 11.7848 | 0.0613 |
| Fulham | 17.0000 | Lower-table | 356200000 | 14248000 | 25 | High | 48.1451 | 11.7364 | 0.0549 |
| Ipswich | 18.0000 | Promoted / uncertain | 212950000 | 7098333 | 30 | Medium | 32.4971 | 18.6591 | 0.8058 |
| Coventry | 19.0000 | Promoted / uncertain | 194250000 | 7471154 | 26 | Medium | 38.6505 | 16.2731 | 0.4093 |
| Hull | 20.0000 | Promoted / uncertain | 95900000 | 3551852 | 27 | Medium | 42.0969 | 14.8717 | 0.2492 |

## 3. Calculation

`squad_strength_score = min-max normalized log(squad_market_value_eur)` across the 20 projected Premier League teams.

The log transform prevents the richest squads from dominating the prior too aggressively. The score is converted into a mild pre-season probability prior, strongest in matchweeks 1-5, lower in matchweeks 6-12 and small after matchweek 12.

## 4. Effect on Season Projection

| team | expected_points_before_squad_strength | expected_points | expected_points_delta | relegation_probability_before_squad_strength | relegation_probability | relegation_probability_delta |
| --- | --- | --- | --- | --- | --- | --- |
| Ipswich | 32.0185 | 32.4971 | 0.4786 | 0.8208 | 0.8058 | -0.0150 |
| Crystal Palace | 36.9584 | 37.3945 | 0.4361 | 0.5260 | 0.5074 | -0.0186 |
| Tottenham | 43.0730 | 43.3993 | 0.3263 | 0.2105 | 0.2023 | -0.0082 |
| Newcastle | 47.3522 | 47.6154 | 0.2632 | 0.0717 | 0.0703 | -0.0014 |
| Sunderland | 38.3754 | 38.5442 | 0.1688 | 0.4749 | 0.4752 | 0.0003 |
| Aston Villa | 50.3009 | 50.3677 | 0.0668 | 0.0250 | 0.0249 | -0.0001 |
| Leeds | 48.2005 | 48.2394 | 0.0389 | 0.0580 | 0.0613 | 0.0033 |
| Chelsea | 57.7835 | 57.8078 | 0.0243 | 0.0018 | 0.0018 | 0.0000 |
| Everton | 48.7389 | 48.7574 | 0.0185 | 0.0472 | 0.0487 | 0.0015 |
| Nott'm Forest | 48.3898 | 48.3899 | 0.0001 | 0.0629 | 0.0654 | 0.0025 |
| Brentford | 52.5148 | 52.4695 | -0.0453 | 0.0114 | 0.0122 | 0.0008 |
| Coventry | 38.7140 | 38.6505 | -0.0635 | 0.3974 | 0.4093 | 0.0119 |
| Fulham | 48.2699 | 48.1451 | -0.1248 | 0.0502 | 0.0549 | 0.0047 |
| Arsenal | 72.9376 | 72.7702 | -0.1674 | 0.0000 | 0.0000 | 0.0000 |
| Hull | 42.2777 | 42.0969 | -0.1808 | 0.2327 | 0.2492 | 0.0165 |
| Man United | 54.4604 | 54.2516 | -0.2088 | 0.0090 | 0.0106 | 0.0016 |
| Liverpool | 67.3351 | 67.0030 | -0.3321 | 0.0001 | 0.0001 | 0.0000 |
| Bournemouth | 61.3147 | 60.9112 | -0.4035 | 0.0004 | 0.0006 | 0.0002 |
| Man City | 81.2220 | 80.7283 | -0.4937 | 0.0000 | 0.0000 | 0.0000 |
| Brighton | 71.3032 | 70.7889 | -0.5143 | 0.0000 | 0.0000 | 0.0000 |

## 5. Promoted Team Interaction

| team | promoted_team_flag | squad_strength_rank | squad_strength_score | promotion_adjustment_applied | fallback_used | expected_points | relegation_probability |
| --- | --- | --- | --- | --- | --- | --- | --- |
| Coventry | True | 19.0000 | 0.2692 | False | False | 38.6505 | 0.4093 |
| Hull | True | 20.0000 | 0.0000 | False | False | 42.0969 | 0.2492 |
| Ipswich | True | 18.0000 | 0.3042 | False | False | 32.4971 | 0.8058 |

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
