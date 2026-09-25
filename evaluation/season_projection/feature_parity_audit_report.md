# Season Projection Feature Parity Audit

## Summary

- Feature validation status: `Ready`
- Fixtures checked: `80`
- Production features checked: `40`
- Non-promoted fixture max raw difference: `0.00000000`

For fixtures where neither team uses a promoted-team fallback, the Prediction tab and Season Projection feature rows should match after the same official-fixture schedule override is applied. Differences on promoted fixtures are intentional and come from the transparent promoted-team adjustment.

## Non-Promoted Feature Group Parity

| feature_group | max_raw_abs_diff | features_checked | rows_checked |
| --- | --- | --- | --- |
| Elo | 0.0000 | 9 | 720 |
| Home advantage | 0.0000 | 1 | 80 |
| Recent form | 0.0000 | 4 | 320 |
| Schedule/fatigue | 0.0000 | 8 | 640 |
| Shot volume | 0.0000 | 12 | 960 |
| xG/xGA | 0.0000 | 6 | 480 |

## Adjusted Feature Group Differences

| feature_group | max_adjusted_abs_diff | adjusted_rows |
| --- | --- | --- |
| Elo | 0.0000 | 720 |
| Home advantage | 0.0000 | 80 |
| Recent form | 0.0000 | 320 |
| Schedule/fatigue | 0.0000 | 640 |
| Shot volume | 0.0000 | 960 |
| xG/xGA | 0.0000 | 480 |

## Feature Validation Rows

| team | feature_validation_status | fallback_used | fallback_reason | source_league | local_pl_match_count | championship_data_available | promotion_adjustment_applied | missing_or_fallback_groups |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| Arsenal | ok | False | none | Premier League historical data | 271 | False | False | none |
| Aston Villa | ok | False | none | Premier League historical data | 271 | False | False | none |
| Bournemouth | ok | False | none | Premier League historical data | 195 | False | False | none |
| Brentford | ok | False | none | Premier League historical data | 195 | False | False | none |
| Brighton | ok | False | none | Premier League historical data | 271 | False | False | none |
| Chelsea | ok | False | none | Premier League historical data | 271 | False | False | none |
| Coventry | ok | False | none | Premier League historical data | 5 | True | False | none |
| Crystal Palace | ok | False | none | Premier League historical data | 271 | False | False | none |
| Everton | ok | False | none | Premier League historical data | 271 | False | False | none |
| Fulham | ok | False | none | Premier League historical data | 195 | False | False | none |
| Hull | ok | False | none | Premier League historical data | 5 | True | False | none |
| Ipswich | ok | False | none | Premier League historical data | 43 | True | False | none |
| Leeds | ok | False | none | Premier League historical data | 157 | False | False | none |
| Liverpool | ok | False | none | Premier League historical data | 271 | False | False | none |
| Man City | ok | False | none | Premier League historical data | 271 | False | False | none |
| Man United | ok | False | none | Premier League historical data | 271 | False | False | none |
| Newcastle | ok | False | none | Premier League historical data | 271 | False | False | none |
| Nott'm Forest | ok | False | none | Premier League historical data | 157 | False | False | none |
| Sunderland | ok | False | none | Premier League historical data | 43 | False | False | none |
| Tottenham | ok | False | none | Premier League historical data | 271 | False | False | none |
