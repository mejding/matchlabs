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
| Man City | 1.0000 | Elite | 1320000000 | 47142857 | 28 | High | 77.1864 | 1.8746 | 0.0000 |
| Arsenal | 2.0000 | Elite | 1250000000 | 52083333 | 24 | High | 75.9748 | 1.9709 | 0.0000 |
| Chelsea | 3.0000 | Elite | 1110000000 | 37000000 | 30 | High | 59.7381 | 6.4684 | 0.0012 |
| Liverpool | 4.0000 | Elite | 939500000 | 33553571 | 28 | High | 64.6178 | 4.8612 | 0.0004 |
| Man United | 5.0000 | Strong | 752100000 | 30084000 | 25 | High | 46.0113 | 13.2097 | 0.1291 |
| Tottenham | 6.0000 | Strong | 700000000 | 23333333 | 30 | High | 52.8561 | 9.8375 | 0.0226 |
| Newcastle | 7.0000 | Strong | 696350000 | 24012069 | 29 | High | 48.9711 | 11.7105 | 0.0579 |
| Nott'm Forest | 8.0000 | Strong | 577600000 | 19917241 | 29 | High | 47.2062 | 12.6582 | 0.1002 |
| Brighton | 9.0000 | Mid-table | 567000000 | 17181818 | 33 | High | 66.4661 | 4.2038 | 0.0001 |
| Bournemouth | 10.0000 | Mid-table | 565700000 | 21757692 | 26 | High | 63.2125 | 5.1319 | 0.0001 |
| Crystal Palace | 11.0000 | Mid-table | 553000000 | 18433333 | 30 | High | 35.7900 | 17.6130 | 0.6333 |
| Aston Villa | 12.0000 | Mid-table | 531500000 | 20442308 | 26 | High | 54.0678 | 8.8118 | 0.0104 |
| Brentford | 13.0000 | Mid-table | 490580000 | 15825161 | 31 | High | 52.2265 | 9.7306 | 0.0149 |
| Everton | 14.0000 | Mid-table | 443150000 | 17044231 | 26 | High | 48.2239 | 11.8783 | 0.0679 |
| Sunderland | 15.0000 | Lower-table | 386430000 | 13801071 | 28 | High | 38.1846 | 16.9087 | 0.5234 |
| Leeds | 16.0000 | Lower-table | 358800000 | 13800000 | 26 | High | 44.4766 | 13.9627 | 0.1676 |
| Fulham | 17.0000 | Lower-table | 356200000 | 14248000 | 25 | High | 48.6817 | 11.6939 | 0.0518 |
| Ipswich | 18.0000 | Promoted / uncertain | 212950000 | 7098333 | 30 | Medium | 32.4235 | 18.7708 | 0.8311 |
| Coventry | 19.0000 | Promoted / uncertain | 194250000 | 7471154 | 26 | Medium | 43.3937 | 14.3051 | 0.1887 |
| Hull | 20.0000 | Promoted / uncertain | 95900000 | 3551852 | 27 | Medium | 43.4643 | 14.3984 | 0.1993 |

## 3. Calculation

`squad_strength_score = min-max normalized log(squad_market_value_eur)` across the 20 projected Premier League teams.

The log transform prevents the richest squads from dominating the prior too aggressively. The score is converted into a mild pre-season probability prior, strongest in matchweeks 1-5, lower in matchweeks 6-12 and small after matchweek 12.

## 4. Effect on Season Projection

| team | expected_points_before_squad_strength | expected_points | expected_points_delta | relegation_probability_before_squad_strength | relegation_probability | relegation_probability_delta |
| --- | --- | --- | --- | --- | --- | --- |
| Crystal Palace | 35.3121 | 35.7900 | 0.4779 | 0.6569 | 0.6333 | -0.0236 |
| Ipswich | 31.9525 | 32.4235 | 0.4710 | 0.8468 | 0.8311 | -0.0157 |
| Newcastle | 48.7590 | 48.9711 | 0.2121 | 0.0567 | 0.0579 | 0.0012 |
| Sunderland | 38.0322 | 38.1846 | 0.1524 | 0.5254 | 0.5234 | -0.0020 |
| Leeds | 44.3345 | 44.4766 | 0.1421 | 0.1689 | 0.1676 | -0.0013 |
| Man United | 45.9156 | 46.0113 | 0.0957 | 0.1262 | 0.1291 | 0.0029 |
| Everton | 48.1792 | 48.2239 | 0.0447 | 0.0679 | 0.0679 | 0.0000 |
| Tottenham | 52.8317 | 52.8561 | 0.0244 | 0.0214 | 0.0226 | 0.0012 |
| Brentford | 52.2127 | 52.2265 | 0.0138 | 0.0140 | 0.0149 | 0.0009 |
| Nott'm Forest | 47.2094 | 47.2062 | -0.0032 | 0.0993 | 0.1002 | 0.0009 |
| Chelsea | 59.7439 | 59.7381 | -0.0058 | 0.0010 | 0.0012 | 0.0002 |
| Aston Villa | 54.2136 | 54.0678 | -0.1458 | 0.0096 | 0.0104 | 0.0008 |
| Fulham | 48.8377 | 48.6817 | -0.1560 | 0.0477 | 0.0518 | 0.0041 |
| Coventry | 43.5834 | 43.3937 | -0.1897 | 0.1751 | 0.1887 | 0.0136 |
| Hull | 43.6842 | 43.4643 | -0.2199 | 0.1829 | 0.1993 | 0.0164 |
| Arsenal | 76.2212 | 75.9748 | -0.2464 | 0.0000 | 0.0000 | 0.0000 |
| Liverpool | 64.8934 | 64.6178 | -0.2756 | 0.0002 | 0.0004 | 0.0002 |
| Brighton | 66.7533 | 66.4661 | -0.2872 | 0.0000 | 0.0001 | 0.0001 |
| Man City | 77.5992 | 77.1864 | -0.4128 | 0.0000 | 0.0000 | 0.0000 |
| Bournemouth | 63.6711 | 63.2125 | -0.4586 | 0.0000 | 0.0001 | 0.0001 |

## 5. Promoted Team Interaction

| team | promoted_team_flag | squad_strength_rank | squad_strength_score | promotion_adjustment_applied | fallback_used | expected_points | relegation_probability |
| --- | --- | --- | --- | --- | --- | --- | --- |
| Coventry | True | 19.0000 | 0.2692 | False | False | 43.3937 | 0.1887 |
| Hull | True | 20.0000 | 0.0000 | False | False | 43.4643 | 0.1993 |
| Ipswich | True | 18.0000 | 0.3042 | False | False | 32.4235 | 0.8311 |

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
