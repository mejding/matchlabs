# Worst Prediction Analysis

The analysis uses the saved model on the held-out chronological test period only.

## Main Failure Patterns

- Confident wrong predictions above 70%: 16
- Home favorites that lost or drew: 135
- Draws predicted as home wins: 67
- Matches involving recent promoted/relegation-context teams: 160
- Matches with suspicious rest gaps above 30 days: 10

## Interpretation

The model remains most vulnerable when a home favorite has strong historical/xG indicators but the match outcome is a draw. This is consistent with draws being the least separable class.
Large rest gaps are treated as data-quality warnings because they often mean the selected prediction date is beyond the latest saved fixture history for one team.

## Teams Repeatedly Involved In Confident Wrong Predictions

- Arsenal: 5
- Liverpool: 4
- Brighton: 4
- Bournemouth: 3
- Nott'm Forest: 2
- Man United: 2
- Crystal Palace: 2
- Fulham: 2
- Aston Villa: 2
- Chelsea: 1

## Production Recommendation

Do not hide these failures in the frontend. Surface low confidence and data-quality warnings when favorite probabilities are high but rest gaps, missing injuries, or missing lineup data are present.
