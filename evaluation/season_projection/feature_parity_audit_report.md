# Season Projection Feature Parity Audit

## Summary

- Feature validation status: `Adjusted`
- Fixtures checked: `80`
- Production features checked: `40`
- Non-promoted fixture max raw difference: `0.00000000`

For fixtures where neither team uses a promoted-team fallback, the Prediction tab and Season Projection feature rows should match after the same official-fixture schedule override is applied. Differences on promoted fixtures are intentional and come from the transparent promoted-team adjustment.

## Non-Promoted Feature Group Parity

| feature_group | max_raw_abs_diff | features_checked | rows_checked |
| --- | --- | --- | --- |
| Elo | 0.0000 | 9 | 513 |
| Home advantage | 0.0000 | 1 | 57 |
| Recent form | 0.0000 | 4 | 228 |
| Schedule/fatigue | 0.0000 | 8 | 456 |
| Shot volume | 0.0000 | 12 | 684 |
| xG/xGA | 0.0000 | 6 | 342 |

## Adjusted Feature Group Differences

| feature_group | max_adjusted_abs_diff | adjusted_rows |
| --- | --- | --- |
| xG/xGA | 1.1060 | 480 |
| Elo | 0.0000 | 720 |
| Home advantage | 0.0000 | 80 |
| Recent form | 0.0000 | 320 |
| Schedule/fatigue | 0.0000 | 640 |
| Shot volume | 0.0000 | 960 |

## Feature Validation Rows

| team | feature_validation_status | fallback_used | fallback_reason | source_league | local_pl_match_count | championship_data_available | promotion_adjustment_applied | missing_or_fallback_groups |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| Arsenal | ok | False | none | Premier League historical data | 270 | False | False | none |
| Aston Villa | ok | False | none | Premier League historical data | 270 | False | False | none |
| Bournemouth | ok | False | none | Premier League historical data | 194 | False | False | none |
| Brentford | ok | False | none | Premier League historical data | 194 | False | False | none |
| Brighton | ok | False | none | Premier League historical data | 270 | False | False | none |
| Chelsea | ok | False | none | Premier League historical data | 270 | False | False | none |
| Coventry | adjusted | False | Championship recent form and shot volume converted to Premier League-equivalent values. Championship xG unavailable, so xG/xGA use conservative promoted-team baseline. | Championship adjusted to Premier League equivalent | 4 | True | True | promoted_adjustment |
| Crystal Palace | ok | False | none | Premier League historical data | 270 | False | False | none |
| Everton | ok | False | none | Premier League historical data | 270 | False | False | none |
| Fulham | ok | False | none | Premier League historical data | 194 | False | False | none |
| Hull | adjusted | False | Championship recent form and shot volume converted to Premier League-equivalent values. Championship xG unavailable, so xG/xGA use conservative promoted-team baseline. | Championship adjusted to Premier League equivalent | 4 | True | True | promoted_adjustment |
| Ipswich | adjusted | False | Championship recent form and shot volume converted to Premier League-equivalent values. Championship xG unavailable, so xG/xGA use conservative promoted-team baseline. | Championship adjusted to Premier League equivalent | 42 | True | True | promoted_adjustment |
| Leeds | ok | False | none | Premier League historical data | 155 | False | False | none |
| Liverpool | ok | False | none | Premier League historical data | 270 | False | False | none |
| Man City | ok | False | none | Premier League historical data | 270 | False | False | none |
| Man United | ok | False | none | Premier League historical data | 270 | False | False | none |
| Newcastle | ok | False | none | Premier League historical data | 269 | False | False | none |
| Nott'm Forest | ok | False | none | Premier League historical data | 156 | False | False | none |
| Sunderland | ok | False | none | Premier League historical data | 42 | False | False | none |
| Tottenham | ok | False | none | Premier League historical data | 270 | False | False | none |
