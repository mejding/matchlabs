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
| Man City | 1.0000 | Elite | 1320000000 | 47142857 | 28 | High | 78.4549 | 1.9079 | 0.0000 |
| Arsenal | 2.0000 | Elite | 1250000000 | 52083333 | 24 | High | 78.1512 | 1.8805 | 0.0000 |
| Chelsea | 3.0000 | Elite | 1110000000 | 37000000 | 30 | High | 50.5189 | 10.5097 | 0.0430 |
| Liverpool | 4.0000 | Elite | 939500000 | 33553571 | 28 | High | 64.1255 | 5.0276 | 0.0007 |
| Man United | 5.0000 | Strong | 752100000 | 30084000 | 25 | High | 69.4633 | 3.6226 | 0.0000 |
| Tottenham | 6.0000 | Strong | 700000000 | 23333333 | 30 | High | 45.9564 | 13.1642 | 0.1610 |
| Newcastle | 7.0000 | Strong | 696350000 | 24012069 | 29 | High | 55.2122 | 8.4939 | 0.0149 |
| Nott'm Forest | 8.0000 | Strong | 577600000 | 19917241 | 29 | High | 47.1372 | 12.5059 | 0.1213 |
| Brighton | 9.0000 | Mid-table | 567000000 | 17181818 | 33 | High | 55.6764 | 8.0416 | 0.0100 |
| Bournemouth | 10.0000 | Mid-table | 565700000 | 21757692 | 26 | High | 57.2207 | 7.3489 | 0.0064 |
| Crystal Palace | 11.0000 | Mid-table | 553000000 | 18433333 | 30 | High | 42.2736 | 14.6860 | 0.2648 |
| Aston Villa | 12.0000 | Mid-table | 531500000 | 20442308 | 26 | High | 56.8833 | 7.4352 | 0.0070 |
| Brentford | 13.0000 | Mid-table | 490580000 | 15825161 | 31 | High | 44.7830 | 13.3571 | 0.1634 |
| Everton | 14.0000 | Mid-table | 443150000 | 17044231 | 26 | High | 41.9728 | 14.8777 | 0.2883 |
| Sunderland | 15.0000 | Lower-table | 386430000 | 13801071 | 28 | High | 46.7234 | 12.7574 | 0.1290 |
| Leeds | 16.0000 | Lower-table | 358800000 | 13800000 | 26 | High | 44.9918 | 13.5273 | 0.1846 |
| Fulham | 17.0000 | Lower-table | 356200000 | 14248000 | 25 | High | 47.6949 | 12.0791 | 0.0972 |
| Ipswich | 18.0000 | Promoted / uncertain | 212950000 | 7098333 | 30 | Medium | 27.0691 | 19.5240 | 0.9438 |
| Coventry | 19.0000 | Promoted / uncertain | 194250000 | 7471154 | 26 | Medium | 44.5006 | 13.5983 | 0.1824 |
| Hull | 20.0000 | Promoted / uncertain | 95900000 | 3551852 | 27 | Medium | 40.3834 | 15.6551 | 0.3822 |

## 3. Calculation

`squad_strength_score = min-max normalized log(squad_market_value_eur)` across the 20 projected Premier League teams.

The log transform prevents the richest squads from dominating the prior too aggressively. The score is converted into a mild pre-season probability prior, strongest in matchweeks 1-5, lower in matchweeks 6-12 and small after matchweek 12.

## 4. Effect on Season Projection

| team | expected_points_before_squad_strength | expected_points | expected_points_delta | relegation_probability_before_squad_strength | relegation_probability | relegation_probability_delta |
| --- | --- | --- | --- | --- | --- | --- |
| Ipswich | 26.4704 | 27.0691 | 0.5987 | 0.9506 | 0.9438 | -0.0068 |
| Crystal Palace | 41.9307 | 42.2736 | 0.3429 | 0.2740 | 0.2648 | -0.0092 |
| Chelsea | 50.1787 | 50.5189 | 0.3402 | 0.0463 | 0.0430 | -0.0033 |
| Tottenham | 45.6564 | 45.9564 | 0.3000 | 0.1684 | 0.1610 | -0.0074 |
| Everton | 41.7011 | 41.9728 | 0.2717 | 0.2936 | 0.2883 | -0.0053 |
| Brentford | 44.5780 | 44.7830 | 0.2050 | 0.1634 | 0.1634 | 0.0000 |
| Nott'm Forest | 46.9599 | 47.1372 | 0.1773 | 0.1229 | 0.1213 | -0.0016 |
| Sunderland | 46.6565 | 46.7234 | 0.0669 | 0.1262 | 0.1290 | 0.0028 |
| Leeds | 44.9300 | 44.9918 | 0.0618 | 0.1831 | 0.1846 | 0.0015 |
| Fulham | 47.6968 | 47.6949 | -0.0019 | 0.0958 | 0.0972 | 0.0014 |
| Newcastle | 55.2474 | 55.2122 | -0.0352 | 0.0142 | 0.0149 | 0.0007 |
| Coventry | 44.5669 | 44.5006 | -0.0663 | 0.1759 | 0.1824 | 0.0065 |
| Brighton | 55.7744 | 55.6764 | -0.0980 | 0.0092 | 0.0100 | 0.0008 |
| Hull | 40.5604 | 40.3834 | -0.1770 | 0.3648 | 0.3822 | 0.0174 |
| Bournemouth | 57.4173 | 57.2207 | -0.1966 | 0.0052 | 0.0064 | 0.0012 |
| Aston Villa | 57.0902 | 56.8833 | -0.2069 | 0.0060 | 0.0070 | 0.0010 |
| Liverpool | 64.4208 | 64.1255 | -0.2953 | 0.0004 | 0.0007 | 0.0003 |
| Man United | 70.0221 | 69.4633 | -0.5588 | 0.0000 | 0.0000 | 0.0000 |
| Man City | 79.1306 | 78.4549 | -0.6757 | 0.0000 | 0.0000 | 0.0000 |
| Arsenal | 78.8670 | 78.1512 | -0.7158 | 0.0000 | 0.0000 | 0.0000 |

## 5. Promoted Team Interaction

| team | promoted_team_flag | squad_strength_rank | squad_strength_score | promotion_adjustment_applied | fallback_used | expected_points | relegation_probability |
| --- | --- | --- | --- | --- | --- | --- | --- |
| Coventry | True | 19.0000 | 0.2692 | True | False | 44.5006 | 0.1824 |
| Hull | True | 20.0000 | 0.0000 | True | False | 40.3834 | 0.3822 |
| Ipswich | True | 18.0000 | 0.3042 | False | False | 27.0691 | 0.9438 |

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
