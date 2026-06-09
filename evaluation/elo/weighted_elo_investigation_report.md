# Weighted Elo Investigation Report

## Question

Has the project tested a weighted Elo setup where recent seasons count more than matches from several seasons ago?

## Short Answer

No. The current production Elo layer is chronological and dynamic, but it does not apply explicit season-level recency weighting, season decay, or regression to the league mean.

## What Has Been Tested

The Sprint 4B Elo evaluation tested:

- K-factor: `10`, `20`, `30`, `40`
- Fixed home Elo bonus: `0`, `50`, `75`, `100`
- Margin-of-victory adjustment: enabled / disabled

The selected production configuration is documented as `k30_ha75_nomov`.

## What The Current Elo Does

The current Elo engine:

- starts teams at an initial rating
- processes matches chronologically
- stores each team's Elo before kickoff
- updates ratings after each result
- uses only information available before each match

This means newer matches naturally move ratings more recently than older matches, but older seasons remain embedded in the rating unless later results move the team away from them.

The model also has Elo trend features:

- `elo_recent_change`
- `home_elo_trend`
- `away_elo_trend`
- `rolling_elo_form`

These measure recent movement in Elo, but they are not the same as a season-weighted Elo system.

## What Has Not Been Tested

The project has not yet tested:

- season-start regression to the league mean
- season carryover weighting
- explicit decay of older seasons
- separate promoted-team initialization
- multi-year weighted Elo where the latest season is stronger than matches from 3-5 seasons ago

## Recommended Next Elo Test

Run a dedicated decayed-Elo sprint with season carryover:

At each season boundary:

```text
new_rating = 1500 + carryover * (old_rating - 1500)
```

Candidate carryover values:

- `1.00`: current behavior, no season decay
- `0.85`: light regression
- `0.75`: medium regression
- `0.65`: stronger regression
- `0.50`: aggressive regression

The test should compare:

- current production model
- production + current Elo
- production + decayed Elo
- production + decayed Elo + Elo trend features

Primary metrics:

- Log Loss
- Brier Score
- ECE / calibration
- draw recall and draw log loss

## Recommendation

Weighted/decayed Elo is a reasonable next research sprint because it may improve future-match prediction by reducing the influence of very old seasons. It should not be assumed better than the current Elo. It should only replace or modify production Elo if it improves out-of-sample Log Loss or Brier Score without materially worsening calibration.
