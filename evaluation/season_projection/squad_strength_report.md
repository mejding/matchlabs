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
| Man City | 1.0000 | Elite | 1320000000 | 47142857 | 28 | High | 72.9283 | 2.7232 | 0.0000 |
| Arsenal | 2.0000 | Elite | 1250000000 | 52083333 | 24 | High | 79.3542 | 1.5571 | 0.0000 |
| Chelsea | 3.0000 | Elite | 1110000000 | 37000000 | 30 | High | 58.5251 | 7.1106 | 0.0046 |
| Liverpool | 4.0000 | Elite | 939500000 | 33553571 | 28 | High | 59.6854 | 6.8334 | 0.0037 |
| Man United | 5.0000 | Strong | 752100000 | 30084000 | 25 | High | 66.9836 | 4.2686 | 0.0002 |
| Tottenham | 6.0000 | Strong | 700000000 | 23333333 | 30 | High | 38.4466 | 16.7140 | 0.5013 |
| Newcastle | 7.0000 | Strong | 696350000 | 24012069 | 29 | High | 46.3282 | 13.1660 | 0.1381 |
| Nott'm Forest | 8.0000 | Strong | 577600000 | 19917241 | 29 | High | 41.1726 | 15.6018 | 0.3434 |
| Brighton | 9.0000 | Mid-table | 567000000 | 17181818 | 33 | High | 63.0181 | 5.3497 | 0.0004 |
| Bournemouth | 10.0000 | Mid-table | 565700000 | 21757692 | 26 | High | 46.5703 | 12.7216 | 0.1159 |
| Crystal Palace | 11.0000 | Mid-table | 553000000 | 18433333 | 30 | High | 39.6840 | 15.9779 | 0.3975 |
| Aston Villa | 12.0000 | Mid-table | 531500000 | 20442308 | 26 | High | 44.5811 | 13.6523 | 0.1715 |
| Brentford | 13.0000 | Mid-table | 490580000 | 15825161 | 31 | High | 57.5076 | 7.4959 | 0.0063 |
| Everton | 14.0000 | Mid-table | 443150000 | 17044231 | 26 | High | 54.9097 | 8.7835 | 0.0145 |
| Sunderland | 15.0000 | Lower-table | 386430000 | 13801071 | 28 | High | 46.2919 | 13.2591 | 0.1415 |
| Leeds | 16.0000 | Lower-table | 358800000 | 13800000 | 26 | High | 46.0825 | 13.2263 | 0.1393 |
| Fulham | 17.0000 | Lower-table | 356200000 | 14248000 | 25 | High | 47.1052 | 12.6384 | 0.1142 |
| Ipswich | 18.0000 | Promoted / uncertain | 212950000 | 7098333 | 30 | Medium | 52.0543 | 10.2413 | 0.0351 |
| Coventry | 19.0000 | Promoted / uncertain | 194250000 | 7471154 | 26 | Medium | 30.6765 | 18.8865 | 0.8431 |
| Hull | 20.0000 | Promoted / uncertain | 95900000 | 3551852 | 27 | Medium | 52.9424 | 9.7928 | 0.0294 |

## 3. Calculation

`squad_strength_score = min-max normalized log(squad_market_value_eur)` across the 20 projected Premier League teams.

The log transform prevents the richest squads from dominating the prior too aggressively. The score is converted into a mild pre-season probability prior, strongest in matchweeks 1-5, lower in matchweeks 6-12 and small after matchweek 12.

## 4. Effect on Season Projection

| team | expected_points_before_squad_strength | expected_points | expected_points_delta | relegation_probability_before_squad_strength | relegation_probability | relegation_probability_delta |
| --- | --- | --- | --- | --- | --- | --- |
| Tottenham | 37.9169 | 38.4466 | 0.5297 | 0.5200 | 0.5013 | -0.0187 |
| Crystal Palace | 39.2473 | 39.6840 | 0.4367 | 0.4055 | 0.3975 | -0.0080 |
| Coventry | 30.2734 | 30.6765 | 0.4031 | 0.8493 | 0.8431 | -0.0062 |
| Nott'm Forest | 40.8785 | 41.1726 | 0.2941 | 0.3432 | 0.3434 | 0.0002 |
| Aston Villa | 44.3184 | 44.5811 | 0.2627 | 0.1716 | 0.1715 | -0.0001 |
| Newcastle | 46.0811 | 46.3282 | 0.2471 | 0.1389 | 0.1381 | -0.0008 |
| Bournemouth | 46.3872 | 46.5703 | 0.1831 | 0.1132 | 0.1159 | 0.0027 |
| Leeds | 45.9719 | 46.0825 | 0.1106 | 0.1346 | 0.1393 | 0.0047 |
| Chelsea | 58.4200 | 58.5251 | 0.1051 | 0.0037 | 0.0046 | 0.0009 |
| Sunderland | 46.2236 | 46.2919 | 0.0683 | 0.1369 | 0.1415 | 0.0046 |
| Fulham | 47.1765 | 47.1052 | -0.0713 | 0.1061 | 0.1142 | 0.0081 |
| Liverpool | 59.7754 | 59.6854 | -0.0900 | 0.0032 | 0.0037 | 0.0005 |
| Everton | 55.0452 | 54.9097 | -0.1355 | 0.0131 | 0.0145 | 0.0014 |
| Brentford | 57.7036 | 57.5076 | -0.1960 | 0.0057 | 0.0063 | 0.0006 |
| Ipswich | 52.3528 | 52.0543 | -0.2985 | 0.0306 | 0.0351 | 0.0045 |
| Brighton | 63.4064 | 63.0181 | -0.3883 | 0.0002 | 0.0004 | 0.0002 |
| Man City | 73.3525 | 72.9283 | -0.4242 | 0.0000 | 0.0000 | 0.0000 |
| Man United | 67.5224 | 66.9836 | -0.5388 | 0.0002 | 0.0002 | 0.0000 |
| Hull | 53.5373 | 52.9424 | -0.5949 | 0.0240 | 0.0294 | 0.0054 |
| Arsenal | 80.0739 | 79.3542 | -0.7197 | 0.0000 | 0.0000 | 0.0000 |

## 5. Promoted Team Interaction

| team | promoted_team_flag | squad_strength_rank | squad_strength_score | promotion_adjustment_applied | fallback_used | expected_points | relegation_probability |
| --- | --- | --- | --- | --- | --- | --- | --- |
| Coventry | True | 19.0000 | 0.2692 | True | False | 30.6765 | 0.8431 |
| Hull | True | 20.0000 | 0.0000 | True | False | 52.9424 | 0.0294 |
| Ipswich | True | 18.0000 | 0.3042 | False | False | 52.0543 | 0.0351 |

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
