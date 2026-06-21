# Season Projection Feature Parity Audit

## Summary

- Feature validation status: `Warning`
- Fixtures checked: `80`
- Production features checked: `40`
- Non-promoted fixture max raw difference: `0.00000000`

For fixtures where neither team uses a promoted-team fallback, the Prediction tab and Season Projection feature rows should match after the same official-fixture schedule override is applied. Differences on promoted fixtures are intentional and come from the transparent promoted-team adjustment.

## Non-Promoted Feature Group Parity

| feature_group | max_raw_abs_diff | features_checked | rows_checked |
| --- | --- | --- | --- |
| Elo | 0.0000 | 9 | 585 |
| Home advantage | 0.0000 | 1 | 65 |
| Recent form | 0.0000 | 4 | 260 |
| Schedule/fatigue | 0.0000 | 8 | 520 |
| Shot volume | 0.0000 | 12 | 780 |
| xG/xGA | 0.0000 | 6 | 390 |

## Adjusted Feature Group Differences

| feature_group | max_adjusted_abs_diff | adjusted_rows |
| --- | --- | --- |
| Shot volume | 10.7830 | 960 |
| Recent form | 3.4211 | 320 |
| xG/xGA | 1.7861 | 480 |
| Elo | 0.0000 | 720 |
| Home advantage | 0.0000 | 80 |
| Schedule/fatigue | 0.0000 | 640 |

## Feature Validation Rows

| team | feature_validation_status | fallback_used | fallback_reason | source_league | local_pl_match_count | missing_or_fallback_groups |
| --- | --- | --- | --- | --- | --- | --- |
| Arsenal | ok | False | none | Premier League historical data | 266 | none |
| Aston Villa | ok | False | none | Premier League historical data | 266 | none |
| Bournemouth | ok | False | none | Premier League historical data | 190 | none |
| Brentford | ok | False | none | Premier League historical data | 190 | none |
| Brighton | ok | False | none | Premier League historical data | 266 | none |
| Chelsea | ok | False | none | Premier League historical data | 266 | none |
| Coventry | warning | True | No local Premier League history; Championship data is not treated as Premier League-equivalent. | Promoted-team conservative Premier League baseline | 0 | explicit_fallback |
| Crystal Palace | ok | False | none | Premier League historical data | 266 | none |
| Everton | ok | False | none | Premier League historical data | 266 | none |
| Fulham | ok | False | none | Premier League historical data | 190 | none |
| Hull | warning | True | No local Premier League history; Championship data is not treated as Premier League-equivalent. | Promoted-team conservative Premier League baseline | 0 | explicit_fallback |
| Ipswich | ok | False | none | Premier League historical data | 38 | none |
| Leeds | ok | False | none | Premier League historical data | 152 | none |
| Liverpool | ok | False | none | Premier League historical data | 266 | none |
| Man City | ok | False | none | Premier League historical data | 266 | none |
| Man United | ok | False | none | Premier League historical data | 266 | none |
| Newcastle | ok | False | none | Premier League historical data | 266 | none |
| Nott'm Forest | ok | False | none | Premier League historical data | 152 | none |
| Sunderland | ok | False | none | Premier League historical data | 38 | none |
| Tottenham | ok | False | none | Premier League historical data | 266 | none |
