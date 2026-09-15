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
| Man City | 1.0000 | Elite | 1320000000 | 47142857 | 28 | High | 79.4964 | 1.8923 | 0.0000 |
| Arsenal | 2.0000 | Elite | 1250000000 | 52083333 | 24 | High | 81.0481 | 1.6250 | 0.0000 |
| Chelsea | 3.0000 | Elite | 1110000000 | 37000000 | 30 | High | 54.3746 | 8.6829 | 0.0090 |
| Liverpool | 4.0000 | Elite | 939500000 | 33553571 | 28 | High | 67.3533 | 4.1933 | 0.0000 |
| Man United | 5.0000 | Strong | 752100000 | 30084000 | 25 | High | 65.3182 | 4.7968 | 0.0001 |
| Tottenham | 6.0000 | Strong | 700000000 | 23333333 | 30 | High | 37.0876 | 16.9015 | 0.5027 |
| Newcastle | 7.0000 | Strong | 696350000 | 24012069 | 29 | High | 47.8171 | 12.0335 | 0.0631 |
| Nott'm Forest | 8.0000 | Strong | 577600000 | 19917241 | 29 | High | 53.1530 | 9.4710 | 0.0134 |
| Brighton | 9.0000 | Mid-table | 567000000 | 17181818 | 33 | High | 62.3847 | 5.5561 | 0.0002 |
| Bournemouth | 10.0000 | Mid-table | 565700000 | 21757692 | 26 | High | 57.6493 | 7.2094 | 0.0021 |
| Crystal Palace | 11.0000 | Mid-table | 553000000 | 18433333 | 30 | High | 37.4724 | 16.5261 | 0.4453 |
| Aston Villa | 12.0000 | Mid-table | 531500000 | 20442308 | 26 | High | 45.7633 | 12.6662 | 0.0920 |
| Brentford | 13.0000 | Mid-table | 490580000 | 15825161 | 31 | High | 48.8684 | 11.2035 | 0.0412 |
| Everton | 14.0000 | Mid-table | 443150000 | 17044231 | 26 | High | 50.0489 | 10.7619 | 0.0327 |
| Sunderland | 15.0000 | Lower-table | 386430000 | 13801071 | 28 | High | 49.0543 | 11.4845 | 0.0489 |
| Leeds | 16.0000 | Lower-table | 358800000 | 13800000 | 26 | High | 49.7679 | 11.0049 | 0.0361 |
| Fulham | 17.0000 | Lower-table | 356200000 | 14248000 | 25 | High | 40.4278 | 15.3227 | 0.2969 |
| Ipswich | 18.0000 | Promoted / uncertain | 212950000 | 7098333 | 30 | Medium | 31.5589 | 18.6138 | 0.7977 |
| Coventry | 19.0000 | Promoted / uncertain | 194250000 | 7471154 | 26 | Medium | 36.2792 | 16.9182 | 0.5110 |
| Hull | 20.0000 | Promoted / uncertain | 95900000 | 3551852 | 27 | Medium | 45.3235 | 13.1364 | 0.1076 |

## 3. Calculation

`squad_strength_score = min-max normalized log(squad_market_value_eur)` across the 20 projected Premier League teams.

The log transform prevents the richest squads from dominating the prior too aggressively. The score is converted into a mild pre-season probability prior, strongest in matchweeks 1-5, lower in matchweeks 6-12 and small after matchweek 12.

## 4. Effect on Season Projection

| team | expected_points_before_squad_strength | expected_points | expected_points_delta | relegation_probability_before_squad_strength | relegation_probability | relegation_probability_delta |
| --- | --- | --- | --- | --- | --- | --- |
| Tottenham | 36.5706 | 37.0876 | 0.5170 | 0.5187 | 0.5027 | -0.0160 |
| Ipswich | 31.0476 | 31.5589 | 0.5113 | 0.8111 | 0.7977 | -0.0134 |
| Crystal Palace | 37.0316 | 37.4724 | 0.4408 | 0.4617 | 0.4453 | -0.0164 |
| Newcastle | 47.6081 | 47.8171 | 0.2090 | 0.0634 | 0.0631 | -0.0003 |
| Chelsea | 54.1675 | 54.3746 | 0.2071 | 0.0086 | 0.0090 | 0.0004 |
| Brentford | 48.7485 | 48.8684 | 0.1199 | 0.0394 | 0.0412 | 0.0018 |
| Fulham | 40.3496 | 40.4278 | 0.0782 | 0.2882 | 0.2969 | 0.0087 |
| Leeds | 49.6998 | 49.7679 | 0.0681 | 0.0355 | 0.0361 | 0.0006 |
| Aston Villa | 45.7432 | 45.7633 | 0.0201 | 0.0870 | 0.0920 | 0.0050 |
| Coventry | 36.2652 | 36.2792 | 0.0140 | 0.4971 | 0.5110 | 0.0139 |
| Everton | 50.0472 | 50.0489 | 0.0017 | 0.0311 | 0.0327 | 0.0016 |
| Sunderland | 49.1107 | 49.0543 | -0.0564 | 0.0454 | 0.0489 | 0.0035 |
| Nott'm Forest | 53.2322 | 53.1530 | -0.0792 | 0.0125 | 0.0134 | 0.0009 |
| Hull | 45.5808 | 45.3235 | -0.2573 | 0.0986 | 0.1076 | 0.0090 |
| Bournemouth | 57.9088 | 57.6493 | -0.2595 | 0.0016 | 0.0021 | 0.0005 |
| Brighton | 62.6830 | 62.3847 | -0.2983 | 0.0001 | 0.0002 | 0.0001 |
| Liverpool | 67.7442 | 67.3533 | -0.3909 | 0.0000 | 0.0000 | 0.0000 |
| Man City | 79.9868 | 79.4964 | -0.4904 | 0.0000 | 0.0000 | 0.0000 |
| Man United | 65.8595 | 65.3182 | -0.5413 | 0.0000 | 0.0001 | 0.0001 |
| Arsenal | 81.6436 | 81.0481 | -0.5955 | 0.0000 | 0.0000 | 0.0000 |

## 5. Promoted Team Interaction

| team | promoted_team_flag | squad_strength_rank | squad_strength_score | promotion_adjustment_applied | fallback_used | expected_points | relegation_probability |
| --- | --- | --- | --- | --- | --- | --- | --- |
| Coventry | True | 19.0000 | 0.2692 | True | False | 36.2792 | 0.5110 |
| Hull | True | 20.0000 | 0.0000 | True | False | 45.3235 | 0.1076 |
| Ipswich | True | 18.0000 | 0.3042 | True | False | 31.5589 | 0.7977 |

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
