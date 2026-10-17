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
| Man City | 1.0000 | Elite | 1320000000 | 47142857 | 28 | High | 80.0355 | 1.6517 | 0.0000 |
| Arsenal | 2.0000 | Elite | 1250000000 | 52083333 | 24 | High | 77.5605 | 1.8768 | 0.0000 |
| Chelsea | 3.0000 | Elite | 1110000000 | 37000000 | 30 | High | 58.0036 | 7.3161 | 0.0020 |
| Liverpool | 4.0000 | Elite | 939500000 | 33553571 | 28 | High | 64.6478 | 4.9200 | 0.0002 |
| Man United | 5.0000 | Strong | 752100000 | 30084000 | 25 | High | 59.8010 | 6.7315 | 0.0022 |
| Tottenham | 6.0000 | Strong | 700000000 | 23333333 | 30 | High | 36.2948 | 17.4724 | 0.5933 |
| Newcastle | 7.0000 | Strong | 696350000 | 24012069 | 29 | High | 48.9562 | 11.7939 | 0.0563 |
| Nott'm Forest | 8.0000 | Strong | 577600000 | 19917241 | 29 | High | 53.5443 | 9.5908 | 0.0149 |
| Brighton | 9.0000 | Mid-table | 567000000 | 17181818 | 33 | High | 64.0911 | 4.9864 | 0.0001 |
| Bournemouth | 10.0000 | Mid-table | 565700000 | 21757692 | 26 | High | 54.1228 | 8.9507 | 0.0110 |
| Crystal Palace | 11.0000 | Mid-table | 553000000 | 18433333 | 30 | High | 38.4602 | 16.4126 | 0.4200 |
| Aston Villa | 12.0000 | Mid-table | 531500000 | 20442308 | 26 | High | 47.3249 | 12.2286 | 0.0731 |
| Brentford | 13.0000 | Mid-table | 490580000 | 15825161 | 31 | High | 54.4570 | 8.8294 | 0.0080 |
| Everton | 14.0000 | Mid-table | 443150000 | 17044231 | 26 | High | 57.7769 | 7.4820 | 0.0044 |
| Sunderland | 15.0000 | Lower-table | 386430000 | 13801071 | 28 | High | 44.8748 | 13.8179 | 0.1511 |
| Leeds | 16.0000 | Lower-table | 358800000 | 13800000 | 26 | High | 45.9834 | 13.1807 | 0.1093 |
| Fulham | 17.0000 | Lower-table | 356200000 | 14248000 | 25 | High | 38.8724 | 16.2509 | 0.4108 |
| Ipswich | 18.0000 | Promoted / uncertain | 212950000 | 7098333 | 30 | Medium | 33.0190 | 18.4458 | 0.7662 |
| Coventry | 19.0000 | Promoted / uncertain | 194250000 | 7471154 | 26 | Medium | 40.5439 | 15.5215 | 0.2979 |
| Hull | 20.0000 | Promoted / uncertain | 95900000 | 3551852 | 27 | Medium | 47.1880 | 12.5403 | 0.0792 |

## 3. Calculation

`squad_strength_score = min-max normalized log(squad_market_value_eur)` across the 20 projected Premier League teams.

The log transform prevents the richest squads from dominating the prior too aggressively. The score is converted into a mild pre-season probability prior, strongest in matchweeks 1-5, lower in matchweeks 6-12 and small after matchweek 12.

## 4. Effect on Season Projection

| team | expected_points_before_squad_strength | expected_points | expected_points_delta | relegation_probability_before_squad_strength | relegation_probability | relegation_probability_delta |
| --- | --- | --- | --- | --- | --- | --- |
| Ipswich | 32.5172 | 33.0190 | 0.5018 | 0.7780 | 0.7662 | -0.0118 |
| Crystal Palace | 37.9727 | 38.4602 | 0.4875 | 0.4373 | 0.4200 | -0.0173 |
| Tottenham | 35.8199 | 36.2948 | 0.4749 | 0.6116 | 0.5933 | -0.0183 |
| Newcastle | 48.7840 | 48.9562 | 0.1722 | 0.0557 | 0.0563 | 0.0006 |
| Fulham | 38.7416 | 38.8724 | 0.1308 | 0.4055 | 0.4108 | 0.0053 |
| Leeds | 45.8809 | 45.9834 | 0.1025 | 0.1081 | 0.1093 | 0.0012 |
| Aston Villa | 47.2715 | 47.3249 | 0.0534 | 0.0694 | 0.0731 | 0.0037 |
| Chelsea | 57.9779 | 58.0036 | 0.0257 | 0.0019 | 0.0020 | 0.0001 |
| Brentford | 54.4714 | 54.4570 | -0.0144 | 0.0069 | 0.0080 | 0.0011 |
| Coventry | 40.5702 | 40.5439 | -0.0263 | 0.2836 | 0.2979 | 0.0143 |
| Sunderland | 44.9064 | 44.8748 | -0.0316 | 0.1440 | 0.1511 | 0.0071 |
| Nott'm Forest | 53.7199 | 53.5443 | -0.1756 | 0.0130 | 0.0149 | 0.0019 |
| Everton | 58.0170 | 57.7769 | -0.2401 | 0.0039 | 0.0044 | 0.0005 |
| Bournemouth | 54.3823 | 54.1228 | -0.2595 | 0.0094 | 0.0110 | 0.0016 |
| Brighton | 64.3526 | 64.0911 | -0.2615 | 0.0002 | 0.0001 | -0.0001 |
| Liverpool | 64.9413 | 64.6478 | -0.2935 | 0.0000 | 0.0002 | 0.0002 |
| Man United | 60.1182 | 59.8010 | -0.3172 | 0.0017 | 0.0022 | 0.0005 |
| Hull | 47.5420 | 47.1880 | -0.3540 | 0.0698 | 0.0792 | 0.0094 |
| Man City | 80.4729 | 80.0355 | -0.4374 | 0.0000 | 0.0000 | 0.0000 |
| Arsenal | 78.0252 | 77.5605 | -0.4647 | 0.0000 | 0.0000 | 0.0000 |

## 5. Promoted Team Interaction

| team | promoted_team_flag | squad_strength_rank | squad_strength_score | promotion_adjustment_applied | fallback_used | expected_points | relegation_probability |
| --- | --- | --- | --- | --- | --- | --- | --- |
| Coventry | True | 19.0000 | 0.2692 | False | False | 40.5439 | 0.2979 |
| Hull | True | 20.0000 | 0.0000 | False | False | 47.1880 | 0.0792 |
| Ipswich | True | 18.0000 | 0.3042 | False | False | 33.0190 | 0.7662 |

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
