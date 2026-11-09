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
| Man City | 1.0000 | Elite | 1320000000 | 47142857 | 28 | High | 76.3503 | 2.0878 | 0.0000 |
| Arsenal | 2.0000 | Elite | 1250000000 | 52083333 | 24 | High | 78.8300 | 1.6352 | 0.0000 |
| Chelsea | 3.0000 | Elite | 1110000000 | 37000000 | 30 | High | 59.4742 | 6.3558 | 0.0007 |
| Liverpool | 4.0000 | Elite | 939500000 | 33553571 | 28 | High | 64.5746 | 4.7913 | 0.0000 |
| Man United | 5.0000 | Strong | 752100000 | 30084000 | 25 | High | 46.6654 | 12.6817 | 0.1124 |
| Tottenham | 6.0000 | Strong | 700000000 | 23333333 | 30 | High | 47.6303 | 12.3191 | 0.0908 |
| Newcastle | 7.0000 | Strong | 696350000 | 24012069 | 29 | High | 46.9812 | 12.5384 | 0.0940 |
| Nott'm Forest | 8.0000 | Strong | 577600000 | 19917241 | 29 | High | 46.8423 | 12.6755 | 0.1067 |
| Brighton | 9.0000 | Mid-table | 567000000 | 17181818 | 33 | High | 68.5632 | 3.6166 | 0.0000 |
| Bournemouth | 10.0000 | Mid-table | 565700000 | 21757692 | 26 | High | 61.8115 | 5.4539 | 0.0005 |
| Crystal Palace | 11.0000 | Mid-table | 553000000 | 18433333 | 30 | High | 35.0290 | 17.9242 | 0.6976 |
| Aston Villa | 12.0000 | Mid-table | 531500000 | 20442308 | 26 | High | 53.5845 | 8.7315 | 0.0115 |
| Brentford | 13.0000 | Mid-table | 490580000 | 15825161 | 31 | High | 49.4794 | 10.8812 | 0.0361 |
| Everton | 14.0000 | Mid-table | 443150000 | 17044231 | 26 | High | 51.1017 | 10.1344 | 0.0258 |
| Sunderland | 15.0000 | Lower-table | 386430000 | 13801071 | 28 | High | 41.3803 | 15.5204 | 0.3418 |
| Leeds | 16.0000 | Lower-table | 358800000 | 13800000 | 26 | High | 46.5471 | 12.6989 | 0.0990 |
| Fulham | 17.0000 | Lower-table | 356200000 | 14248000 | 25 | High | 48.3471 | 11.5853 | 0.0512 |
| Ipswich | 18.0000 | Promoted / uncertain | 212950000 | 7098333 | 30 | Medium | 32.8044 | 18.7014 | 0.8192 |
| Coventry | 19.0000 | Promoted / uncertain | 194250000 | 7471154 | 26 | Medium | 42.5247 | 14.6181 | 0.2344 |
| Hull | 20.0000 | Promoted / uncertain | 95900000 | 3551852 | 27 | Medium | 41.9469 | 15.0493 | 0.2783 |

## 3. Calculation

`squad_strength_score = min-max normalized log(squad_market_value_eur)` across the 20 projected Premier League teams.

The log transform prevents the richest squads from dominating the prior too aggressively. The score is converted into a mild pre-season probability prior, strongest in matchweeks 1-5, lower in matchweeks 6-12 and small after matchweek 12.

## 4. Effect on Season Projection

| team | expected_points_before_squad_strength | expected_points | expected_points_delta | relegation_probability_before_squad_strength | relegation_probability | relegation_probability_delta |
| --- | --- | --- | --- | --- | --- | --- |
| Crystal Palace | 34.5888 | 35.0290 | 0.4402 | 0.7160 | 0.6976 | -0.0184 |
| Ipswich | 32.3975 | 32.8044 | 0.4069 | 0.8366 | 0.8192 | -0.0174 |
| Tottenham | 47.4392 | 47.6303 | 0.1911 | 0.0925 | 0.0908 | -0.0017 |
| Newcastle | 46.8045 | 46.9812 | 0.1767 | 0.0968 | 0.0940 | -0.0028 |
| Leeds | 46.4209 | 46.5471 | 0.1262 | 0.0980 | 0.0990 | 0.0010 |
| Brentford | 49.3618 | 49.4794 | 0.1176 | 0.0363 | 0.0361 | -0.0002 |
| Nott'm Forest | 46.7506 | 46.8423 | 0.0917 | 0.1060 | 0.1067 | 0.0007 |
| Sunderland | 41.3011 | 41.3803 | 0.0792 | 0.3409 | 0.3418 | 0.0009 |
| Everton | 51.0273 | 51.1017 | 0.0744 | 0.0252 | 0.0258 | 0.0006 |
| Man United | 46.6361 | 46.6654 | 0.0293 | 0.1124 | 0.1124 | 0.0000 |
| Chelsea | 59.5058 | 59.4742 | -0.0316 | 0.0009 | 0.0007 | -0.0002 |
| Aston Villa | 53.7000 | 53.5845 | -0.1155 | 0.0106 | 0.0115 | 0.0009 |
| Fulham | 48.5160 | 48.3471 | -0.1689 | 0.0459 | 0.0512 | 0.0053 |
| Coventry | 42.7119 | 42.5247 | -0.1872 | 0.2198 | 0.2344 | 0.0146 |
| Liverpool | 64.7746 | 64.5746 | -0.2000 | 0.0000 | 0.0000 | 0.0000 |
| Hull | 42.1697 | 41.9469 | -0.2228 | 0.2616 | 0.2783 | 0.0167 |
| Brighton | 68.8803 | 68.5632 | -0.3171 | 0.0000 | 0.0000 | 0.0000 |
| Bournemouth | 62.1472 | 61.8115 | -0.3357 | 0.0005 | 0.0005 | 0.0000 |
| Arsenal | 79.1878 | 78.8300 | -0.3578 | 0.0000 | 0.0000 | 0.0000 |
| Man City | 76.7813 | 76.3503 | -0.4310 | 0.0000 | 0.0000 | 0.0000 |

## 5. Promoted Team Interaction

| team | promoted_team_flag | squad_strength_rank | squad_strength_score | promotion_adjustment_applied | fallback_used | expected_points | relegation_probability |
| --- | --- | --- | --- | --- | --- | --- | --- |
| Coventry | True | 19.0000 | 0.2692 | False | False | 42.5247 | 0.2344 |
| Hull | True | 20.0000 | 0.0000 | False | False | 41.9469 | 0.2783 |
| Ipswich | True | 18.0000 | 0.3042 | False | False | 32.8044 | 0.8192 |

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
