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
| Man City | 1.0000 | Elite | 1320000000 | 47142857 | 28 | High | 76.8663 | 1.9460 | 0.0000 |
| Arsenal | 2.0000 | Elite | 1250000000 | 52083333 | 24 | High | 74.8876 | 2.1746 | 0.0000 |
| Chelsea | 3.0000 | Elite | 1110000000 | 37000000 | 30 | High | 57.7964 | 7.6123 | 0.0042 |
| Liverpool | 4.0000 | Elite | 939500000 | 33553571 | 28 | High | 64.0669 | 5.1982 | 0.0003 |
| Man United | 5.0000 | Strong | 752100000 | 30084000 | 25 | High | 61.1931 | 6.3333 | 0.0012 |
| Tottenham | 6.0000 | Strong | 700000000 | 23333333 | 30 | High | 35.7973 | 17.7253 | 0.6370 |
| Newcastle | 7.0000 | Strong | 696350000 | 24012069 | 29 | High | 46.7188 | 13.1100 | 0.1107 |
| Nott'm Forest | 8.0000 | Strong | 577600000 | 19917241 | 29 | High | 53.7587 | 9.7327 | 0.0174 |
| Brighton | 9.0000 | Mid-table | 567000000 | 17181818 | 33 | High | 65.5718 | 4.5805 | 0.0000 |
| Bournemouth | 10.0000 | Mid-table | 565700000 | 21757692 | 26 | High | 53.0216 | 9.7071 | 0.0213 |
| Crystal Palace | 11.0000 | Mid-table | 553000000 | 18433333 | 30 | High | 38.2949 | 16.6295 | 0.4646 |
| Aston Villa | 12.0000 | Mid-table | 531500000 | 20442308 | 26 | High | 41.6831 | 15.0975 | 0.2652 |
| Brentford | 13.0000 | Mid-table | 490580000 | 15825161 | 31 | High | 58.8337 | 7.0944 | 0.0029 |
| Everton | 14.0000 | Mid-table | 443150000 | 17044231 | 26 | High | 54.6900 | 9.0603 | 0.0121 |
| Sunderland | 15.0000 | Lower-table | 386430000 | 13801071 | 28 | High | 51.0998 | 11.0574 | 0.0426 |
| Leeds | 16.0000 | Lower-table | 358800000 | 13800000 | 26 | High | 48.6454 | 12.1239 | 0.0720 |
| Fulham | 17.0000 | Lower-table | 356200000 | 14248000 | 25 | High | 43.8915 | 14.3091 | 0.1920 |
| Ipswich | 18.0000 | Promoted / uncertain | 212950000 | 7098333 | 30 | Medium | 34.5874 | 18.0137 | 0.6958 |
| Coventry | 19.0000 | Promoted / uncertain | 194250000 | 7471154 | 26 | Medium | 39.5028 | 16.0938 | 0.3850 |
| Hull | 20.0000 | Promoted / uncertain | 95900000 | 3551852 | 27 | Medium | 47.9743 | 12.4004 | 0.0757 |

## 3. Calculation

`squad_strength_score = min-max normalized log(squad_market_value_eur)` across the 20 projected Premier League teams.

The log transform prevents the richest squads from dominating the prior too aggressively. The score is converted into a mild pre-season probability prior, strongest in matchweeks 1-5, lower in matchweeks 6-12 and small after matchweek 12.

## 4. Effect on Season Projection

| team | expected_points_before_squad_strength | expected_points | expected_points_delta | relegation_probability_before_squad_strength | relegation_probability | relegation_probability_delta |
| --- | --- | --- | --- | --- | --- | --- |
| Tottenham | 35.3004 | 35.7973 | 0.4969 | 0.6590 | 0.6370 | -0.0220 |
| Crystal Palace | 37.8434 | 38.2949 | 0.4515 | 0.4793 | 0.4646 | -0.0147 |
| Ipswich | 34.2024 | 34.5874 | 0.3850 | 0.7053 | 0.6958 | -0.0095 |
| Newcastle | 46.4195 | 46.7188 | 0.2993 | 0.1122 | 0.1107 | -0.0015 |
| Aston Villa | 41.3894 | 41.6831 | 0.2937 | 0.2695 | 0.2652 | -0.0043 |
| Leeds | 48.6083 | 48.6454 | 0.0371 | 0.0690 | 0.0720 | 0.0030 |
| Chelsea | 57.8080 | 57.7964 | -0.0116 | 0.0036 | 0.0042 | 0.0006 |
| Coventry | 39.5540 | 39.5028 | -0.0512 | 0.3677 | 0.3850 | 0.0173 |
| Fulham | 43.9574 | 43.8915 | -0.0659 | 0.1813 | 0.1920 | 0.0107 |
| Nott'm Forest | 53.8656 | 53.7587 | -0.1069 | 0.0160 | 0.0174 | 0.0014 |
| Everton | 54.8135 | 54.6900 | -0.1235 | 0.0111 | 0.0121 | 0.0010 |
| Bournemouth | 53.2045 | 53.0216 | -0.1829 | 0.0185 | 0.0213 | 0.0028 |
| Liverpool | 64.2558 | 64.0669 | -0.1889 | 0.0003 | 0.0003 | 0.0000 |
| Brentford | 59.0245 | 58.8337 | -0.1908 | 0.0026 | 0.0029 | 0.0003 |
| Sunderland | 51.2974 | 51.0998 | -0.1976 | 0.0381 | 0.0426 | 0.0045 |
| Hull | 48.3467 | 47.9743 | -0.3724 | 0.0655 | 0.0757 | 0.0102 |
| Man City | 77.2393 | 76.8663 | -0.3730 | 0.0000 | 0.0000 | 0.0000 |
| Brighton | 65.9643 | 65.5718 | -0.3925 | 0.0000 | 0.0000 | 0.0000 |
| Man United | 61.5902 | 61.1931 | -0.3971 | 0.0010 | 0.0012 | 0.0002 |
| Arsenal | 75.3007 | 74.8876 | -0.4131 | 0.0000 | 0.0000 | 0.0000 |

## 5. Promoted Team Interaction

| team | promoted_team_flag | squad_strength_rank | squad_strength_score | promotion_adjustment_applied | fallback_used | expected_points | relegation_probability |
| --- | --- | --- | --- | --- | --- | --- | --- |
| Coventry | True | 19.0000 | 0.2692 | False | False | 39.5028 | 0.3850 |
| Hull | True | 20.0000 | 0.0000 | False | False | 47.9743 | 0.0757 |
| Ipswich | True | 18.0000 | 0.3042 | False | False | 34.5874 | 0.6958 |

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
