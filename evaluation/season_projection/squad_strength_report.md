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
| Man City | 1.0000 | Elite | 1320000000 | 47142857 | 28 | High | 77.2386 | 1.8758 | 0.0000 |
| Arsenal | 2.0000 | Elite | 1250000000 | 52083333 | 24 | High | 76.1955 | 1.9416 | 0.0000 |
| Chelsea | 3.0000 | Elite | 1110000000 | 37000000 | 30 | High | 59.4874 | 6.5657 | 0.0008 |
| Liverpool | 4.0000 | Elite | 939500000 | 33553571 | 28 | High | 64.5599 | 4.8672 | 0.0003 |
| Man United | 5.0000 | Strong | 752100000 | 30084000 | 25 | High | 46.0996 | 13.1545 | 0.1308 |
| Tottenham | 6.0000 | Strong | 700000000 | 23333333 | 30 | High | 52.7268 | 9.8782 | 0.0240 |
| Newcastle | 7.0000 | Strong | 696350000 | 24012069 | 29 | High | 48.9193 | 11.7437 | 0.0575 |
| Nott'm Forest | 8.0000 | Strong | 577600000 | 19917241 | 29 | High | 47.1782 | 12.6639 | 0.1044 |
| Brighton | 9.0000 | Mid-table | 567000000 | 17181818 | 33 | High | 66.6721 | 4.1344 | 0.0000 |
| Bournemouth | 10.0000 | Mid-table | 565700000 | 21757692 | 26 | High | 63.2780 | 5.1074 | 0.0000 |
| Crystal Palace | 11.0000 | Mid-table | 553000000 | 18433333 | 30 | High | 35.9867 | 17.5401 | 0.6240 |
| Aston Villa | 12.0000 | Mid-table | 531500000 | 20442308 | 26 | High | 54.2822 | 8.6873 | 0.0100 |
| Brentford | 13.0000 | Mid-table | 490580000 | 15825161 | 31 | High | 51.9113 | 9.8842 | 0.0158 |
| Everton | 14.0000 | Mid-table | 443150000 | 17044231 | 26 | High | 48.0155 | 11.9808 | 0.0712 |
| Sunderland | 15.0000 | Lower-table | 386430000 | 13801071 | 28 | High | 38.6945 | 16.7033 | 0.4941 |
| Leeds | 16.0000 | Lower-table | 358800000 | 13800000 | 26 | High | 44.4437 | 13.9634 | 0.1680 |
| Fulham | 17.0000 | Lower-table | 356200000 | 14248000 | 25 | High | 48.6467 | 11.6931 | 0.0539 |
| Ipswich | 18.0000 | Promoted / uncertain | 212950000 | 7098333 | 30 | Medium | 32.2535 | 18.8188 | 0.8402 |
| Coventry | 19.0000 | Promoted / uncertain | 194250000 | 7471154 | 26 | Medium | 43.3436 | 14.3206 | 0.1918 |
| Hull | 20.0000 | Promoted / uncertain | 95900000 | 3551852 | 27 | Medium | 43.3139 | 14.4760 | 0.2132 |

## 3. Calculation

`squad_strength_score = min-max normalized log(squad_market_value_eur)` across the 20 projected Premier League teams.

The log transform prevents the richest squads from dominating the prior too aggressively. The score is converted into a mild pre-season probability prior, strongest in matchweeks 1-5, lower in matchweeks 6-12 and small after matchweek 12.

## 4. Effect on Season Projection

| team | expected_points_before_squad_strength | expected_points | expected_points_delta | relegation_probability_before_squad_strength | relegation_probability | relegation_probability_delta |
| --- | --- | --- | --- | --- | --- | --- |
| Ipswich | 31.7791 | 32.2535 | 0.4744 | 0.8549 | 0.8402 | -0.0147 |
| Crystal Palace | 35.5296 | 35.9867 | 0.4571 | 0.6460 | 0.6240 | -0.0220 |
| Newcastle | 48.7096 | 48.9193 | 0.2097 | 0.0593 | 0.0575 | -0.0018 |
| Leeds | 44.3089 | 44.4437 | 0.1348 | 0.1660 | 0.1680 | 0.0020 |
| Sunderland | 38.5758 | 38.6945 | 0.1187 | 0.4931 | 0.4941 | 0.0010 |
| Man United | 46.0129 | 46.0996 | 0.0867 | 0.1324 | 0.1308 | -0.0016 |
| Everton | 47.9519 | 48.0155 | 0.0636 | 0.0711 | 0.0712 | 0.0001 |
| Brentford | 51.8786 | 51.9113 | 0.0327 | 0.0148 | 0.0158 | 0.0010 |
| Tottenham | 52.6963 | 52.7268 | 0.0305 | 0.0230 | 0.0240 | 0.0010 |
| Chelsea | 59.4660 | 59.4874 | 0.0214 | 0.0007 | 0.0008 | 0.0001 |
| Nott'm Forest | 47.1682 | 47.1782 | 0.0100 | 0.1002 | 0.1044 | 0.0042 |
| Fulham | 48.7874 | 48.6467 | -0.1407 | 0.0500 | 0.0539 | 0.0039 |
| Aston Villa | 54.4480 | 54.2822 | -0.1658 | 0.0085 | 0.0100 | 0.0015 |
| Coventry | 43.5319 | 43.3436 | -0.1883 | 0.1792 | 0.1918 | 0.0126 |
| Hull | 43.5105 | 43.3139 | -0.1966 | 0.2007 | 0.2132 | 0.0125 |
| Arsenal | 76.4546 | 76.1955 | -0.2591 | 0.0000 | 0.0000 | 0.0000 |
| Liverpool | 64.8491 | 64.5599 | -0.2892 | 0.0001 | 0.0003 | 0.0002 |
| Brighton | 66.9763 | 66.6721 | -0.3042 | 0.0000 | 0.0000 | 0.0000 |
| Man City | 77.6577 | 77.2386 | -0.4191 | 0.0000 | 0.0000 | 0.0000 |
| Bournemouth | 63.7261 | 63.2780 | -0.4481 | 0.0000 | 0.0000 | 0.0000 |

## 5. Promoted Team Interaction

| team | promoted_team_flag | squad_strength_rank | squad_strength_score | promotion_adjustment_applied | fallback_used | expected_points | relegation_probability |
| --- | --- | --- | --- | --- | --- | --- | --- |
| Coventry | True | 19.0000 | 0.2692 | False | False | 43.3436 | 0.1918 |
| Hull | True | 20.0000 | 0.0000 | False | False | 43.3139 | 0.2132 |
| Ipswich | True | 18.0000 | 0.3042 | False | False | 32.2535 | 0.8402 |

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
