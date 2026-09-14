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
| Man City | 1.0000 | Elite | 1320000000 | 47142857 | 28 | High | 79.2343 | 1.9128 | 0.0000 |
| Arsenal | 2.0000 | Elite | 1250000000 | 52083333 | 24 | High | 80.9951 | 1.6234 | 0.0000 |
| Chelsea | 3.0000 | Elite | 1110000000 | 37000000 | 30 | High | 54.4578 | 8.6501 | 0.0065 |
| Liverpool | 4.0000 | Elite | 939500000 | 33553571 | 28 | High | 67.4320 | 4.1626 | 0.0000 |
| Man United | 5.0000 | Strong | 752100000 | 30084000 | 25 | High | 65.2235 | 4.8325 | 0.0000 |
| Tottenham | 6.0000 | Strong | 700000000 | 23333333 | 30 | High | 37.3625 | 16.7922 | 0.4870 |
| Newcastle | 7.0000 | Strong | 696350000 | 24012069 | 29 | High | 51.1462 | 10.3986 | 0.0273 |
| Nott'm Forest | 8.0000 | Strong | 577600000 | 19917241 | 29 | High | 52.8624 | 9.6270 | 0.0173 |
| Brighton | 9.0000 | Mid-table | 567000000 | 17181818 | 33 | High | 62.3940 | 5.5688 | 0.0009 |
| Bournemouth | 10.0000 | Mid-table | 565700000 | 21757692 | 26 | High | 57.7141 | 7.1857 | 0.0027 |
| Crystal Palace | 11.0000 | Mid-table | 553000000 | 18433333 | 30 | High | 37.7377 | 16.4142 | 0.4348 |
| Aston Villa | 12.0000 | Mid-table | 531500000 | 20442308 | 26 | High | 45.9722 | 12.5596 | 0.0915 |
| Brentford | 13.0000 | Mid-table | 490580000 | 15825161 | 31 | High | 49.0383 | 11.1453 | 0.0379 |
| Everton | 14.0000 | Mid-table | 443150000 | 17044231 | 26 | High | 49.7201 | 10.9272 | 0.0339 |
| Sunderland | 15.0000 | Lower-table | 386430000 | 13801071 | 28 | High | 48.9328 | 11.5478 | 0.0469 |
| Leeds | 16.0000 | Lower-table | 358800000 | 13800000 | 26 | High | 45.9443 | 12.8722 | 0.1053 |
| Fulham | 17.0000 | Lower-table | 356200000 | 14248000 | 25 | High | 40.3689 | 15.3905 | 0.2970 |
| Ipswich | 18.0000 | Promoted / uncertain | 212950000 | 7098333 | 30 | Medium | 31.2248 | 18.6740 | 0.8096 |
| Coventry | 19.0000 | Promoted / uncertain | 194250000 | 7471154 | 26 | Medium | 36.1339 | 16.9582 | 0.5124 |
| Hull | 20.0000 | Promoted / uncertain | 95900000 | 3551852 | 27 | Medium | 46.0977 | 12.7573 | 0.0890 |

## 3. Calculation

`squad_strength_score = min-max normalized log(squad_market_value_eur)` across the 20 projected Premier League teams.

The log transform prevents the richest squads from dominating the prior too aggressively. The score is converted into a mild pre-season probability prior, strongest in matchweeks 1-5, lower in matchweeks 6-12 and small after matchweek 12.

## 4. Effect on Season Projection

| team | expected_points_before_squad_strength | expected_points | expected_points_delta | relegation_probability_before_squad_strength | relegation_probability | relegation_probability_delta |
| --- | --- | --- | --- | --- | --- | --- |
| Ipswich | 30.7015 | 31.2248 | 0.5233 | 0.8258 | 0.8096 | -0.0162 |
| Tottenham | 36.8460 | 37.3625 | 0.5165 | 0.5077 | 0.4870 | -0.0207 |
| Crystal Palace | 37.2905 | 37.7377 | 0.4472 | 0.4464 | 0.4348 | -0.0116 |
| Chelsea | 54.2449 | 54.4578 | 0.2129 | 0.0064 | 0.0065 | 0.0001 |
| Newcastle | 51.0097 | 51.1462 | 0.1365 | 0.0263 | 0.0273 | 0.0010 |
| Leeds | 45.8090 | 45.9443 | 0.1353 | 0.1017 | 0.1053 | 0.0036 |
| Brentford | 48.9170 | 49.0383 | 0.1213 | 0.0370 | 0.0379 | 0.0009 |
| Fulham | 40.2979 | 40.3689 | 0.0710 | 0.2904 | 0.2970 | 0.0066 |
| Coventry | 36.1140 | 36.1339 | 0.0199 | 0.4992 | 0.5124 | 0.0132 |
| Aston Villa | 45.9620 | 45.9722 | 0.0102 | 0.0858 | 0.0915 | 0.0057 |
| Everton | 49.7165 | 49.7201 | 0.0036 | 0.0318 | 0.0339 | 0.0021 |
| Nott'm Forest | 52.9263 | 52.8624 | -0.0639 | 0.0157 | 0.0173 | 0.0016 |
| Sunderland | 48.9979 | 48.9328 | -0.0651 | 0.0432 | 0.0469 | 0.0037 |
| Hull | 46.3732 | 46.0977 | -0.2755 | 0.0791 | 0.0890 | 0.0099 |
| Bournemouth | 57.9941 | 57.7141 | -0.2800 | 0.0027 | 0.0027 | 0.0000 |
| Brighton | 62.6811 | 62.3940 | -0.2871 | 0.0008 | 0.0009 | 0.0001 |
| Liverpool | 67.8123 | 67.4320 | -0.3803 | 0.0000 | 0.0000 | 0.0000 |
| Man City | 79.7342 | 79.2343 | -0.4999 | 0.0000 | 0.0000 | 0.0000 |
| Man United | 65.7660 | 65.2235 | -0.5425 | 0.0000 | 0.0000 | 0.0000 |
| Arsenal | 81.5574 | 80.9951 | -0.5623 | 0.0000 | 0.0000 | 0.0000 |

## 5. Promoted Team Interaction

| team | promoted_team_flag | squad_strength_rank | squad_strength_score | promotion_adjustment_applied | fallback_used | expected_points | relegation_probability |
| --- | --- | --- | --- | --- | --- | --- | --- |
| Coventry | True | 19.0000 | 0.2692 | True | False | 36.1339 | 0.5124 |
| Hull | True | 20.0000 | 0.0000 | True | False | 46.0977 | 0.0890 |
| Ipswich | True | 18.0000 | 0.3042 | True | False | 31.2248 | 0.8096 |

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
