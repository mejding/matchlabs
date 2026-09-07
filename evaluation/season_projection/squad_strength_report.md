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
| Man City | 1.0000 | Elite | 1320000000 | 47142857 | 28 | High | 78.4067 | 1.9500 | 0.0000 |
| Arsenal | 2.0000 | Elite | 1250000000 | 52083333 | 24 | High | 81.4810 | 1.5004 | 0.0000 |
| Chelsea | 3.0000 | Elite | 1110000000 | 37000000 | 30 | High | 55.2919 | 8.2850 | 0.0079 |
| Liverpool | 4.0000 | Elite | 939500000 | 33553571 | 28 | High | 66.3095 | 4.2564 | 0.0001 |
| Man United | 5.0000 | Strong | 752100000 | 30084000 | 25 | High | 63.5020 | 5.1415 | 0.0005 |
| Tottenham | 6.0000 | Strong | 700000000 | 23333333 | 30 | High | 37.3422 | 16.9655 | 0.5388 |
| Newcastle | 7.0000 | Strong | 696350000 | 24012069 | 29 | High | 51.6078 | 10.2544 | 0.0317 |
| Nott'm Forest | 8.0000 | Strong | 577600000 | 19917241 | 29 | High | 46.6626 | 12.7808 | 0.1146 |
| Brighton | 9.0000 | Mid-table | 567000000 | 17181818 | 33 | High | 57.8104 | 7.1353 | 0.0038 |
| Bournemouth | 10.0000 | Mid-table | 565700000 | 21757692 | 26 | High | 51.3195 | 10.0784 | 0.0292 |
| Crystal Palace | 11.0000 | Mid-table | 553000000 | 18433333 | 30 | High | 40.4197 | 15.5511 | 0.3310 |
| Aston Villa | 12.0000 | Mid-table | 531500000 | 20442308 | 26 | High | 52.3381 | 9.5293 | 0.0245 |
| Brentford | 13.0000 | Mid-table | 490580000 | 15825161 | 31 | High | 54.8402 | 8.3605 | 0.0077 |
| Everton | 14.0000 | Mid-table | 443150000 | 17044231 | 26 | High | 52.0162 | 9.9088 | 0.0244 |
| Sunderland | 15.0000 | Lower-table | 386430000 | 13801071 | 28 | High | 49.9349 | 11.1717 | 0.0495 |
| Leeds | 16.0000 | Lower-table | 358800000 | 13800000 | 26 | High | 46.2044 | 12.9541 | 0.1123 |
| Fulham | 17.0000 | Lower-table | 356200000 | 14248000 | 25 | High | 41.7779 | 15.0013 | 0.2696 |
| Ipswich | 18.0000 | Promoted / uncertain | 212950000 | 7098333 | 30 | Medium | 28.9044 | 19.2273 | 0.9015 |
| Coventry | 19.0000 | Promoted / uncertain | 194250000 | 7471154 | 26 | Medium | 39.5179 | 15.8345 | 0.3683 |
| Hull | 20.0000 | Promoted / uncertain | 95900000 | 3551852 | 27 | Medium | 43.7932 | 14.1137 | 0.1846 |

## 3. Calculation

`squad_strength_score = min-max normalized log(squad_market_value_eur)` across the 20 projected Premier League teams.

The log transform prevents the richest squads from dominating the prior too aggressively. The score is converted into a mild pre-season probability prior, strongest in matchweeks 1-5, lower in matchweeks 6-12 and small after matchweek 12.

## 4. Effect on Season Projection

| team | expected_points_before_squad_strength | expected_points | expected_points_delta | relegation_probability_before_squad_strength | relegation_probability | relegation_probability_delta |
| --- | --- | --- | --- | --- | --- | --- |
| Tottenham | 36.7794 | 37.3422 | 0.5628 | 0.5618 | 0.5388 | -0.0230 |
| Ipswich | 28.3748 | 28.9044 | 0.5296 | 0.9101 | 0.9015 | -0.0086 |
| Crystal Palace | 40.0510 | 40.4197 | 0.3687 | 0.3404 | 0.3310 | -0.0094 |
| Chelsea | 55.0990 | 55.2919 | 0.1929 | 0.0081 | 0.0079 | -0.0002 |
| Nott'm Forest | 46.5375 | 46.6626 | 0.1251 | 0.1134 | 0.1146 | 0.0012 |
| Newcastle | 51.4948 | 51.6078 | 0.1130 | 0.0328 | 0.0317 | -0.0011 |
| Leeds | 46.1059 | 46.2044 | 0.0985 | 0.1111 | 0.1123 | 0.0012 |
| Fulham | 41.7276 | 41.7779 | 0.0503 | 0.2664 | 0.2696 | 0.0032 |
| Bournemouth | 51.3134 | 51.3195 | 0.0061 | 0.0287 | 0.0292 | 0.0005 |
| Sunderland | 49.9470 | 49.9349 | -0.0121 | 0.0471 | 0.0495 | 0.0024 |
| Coventry | 39.5928 | 39.5179 | -0.0749 | 0.3552 | 0.3683 | 0.0131 |
| Everton | 52.0931 | 52.0162 | -0.0769 | 0.0221 | 0.0244 | 0.0023 |
| Brentford | 54.9312 | 54.8402 | -0.0910 | 0.0077 | 0.0077 | 0.0000 |
| Aston Villa | 52.5130 | 52.3381 | -0.1749 | 0.0202 | 0.0245 | 0.0043 |
| Brighton | 58.0052 | 57.8104 | -0.1948 | 0.0034 | 0.0038 | 0.0004 |
| Hull | 43.9889 | 43.7932 | -0.1957 | 0.1710 | 0.1846 | 0.0136 |
| Liverpool | 66.6266 | 66.3095 | -0.3171 | 0.0001 | 0.0001 | 0.0000 |
| Man United | 63.9113 | 63.5020 | -0.4093 | 0.0004 | 0.0005 | 0.0001 |
| Man City | 78.9148 | 78.4067 | -0.5081 | 0.0000 | 0.0000 | 0.0000 |
| Arsenal | 82.1880 | 81.4810 | -0.7070 | 0.0000 | 0.0000 | 0.0000 |

## 5. Promoted Team Interaction

| team | promoted_team_flag | squad_strength_rank | squad_strength_score | promotion_adjustment_applied | fallback_used | expected_points | relegation_probability |
| --- | --- | --- | --- | --- | --- | --- | --- |
| Coventry | True | 19.0000 | 0.2692 | True | False | 39.5179 | 0.3683 |
| Hull | True | 20.0000 | 0.0000 | True | False | 43.7932 | 0.1846 |
| Ipswich | True | 18.0000 | 0.3042 | False | False | 28.9044 | 0.9015 |

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
