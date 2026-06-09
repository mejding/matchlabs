# Weighted Elo Investigation Report

## Question

Has the project tested a weighted Elo setup where recent seasons count more than matches from several seasons ago?

## Short Answer

Yes. The project has now tested explicit season-level recency weighting through a decayed Elo sprint. The current production Elo remains best on Log Loss and Brier Score.

## What Was Already Tested

The Sprint 4B Elo evaluation tested:

- K-factor: `10`, `20`, `30`, `40`
- Fixed home Elo bonus: `0`, `50`, `75`, `100`
- Margin-of-victory adjustment: enabled / disabled

The selected production configuration is documented as `k30_ha75_nomov_carry100`.

## What The Current Elo Does

The current Elo engine:

- starts teams at an initial rating
- processes matches chronologically
- stores each team's Elo before kickoff
- updates ratings after each result
- uses only information available before each match
- carries ratings fully from one season into the next

This means newer matches naturally move ratings more recently than older matches, but old seasons remain embedded until later results move the team away from them.

The model also has Elo trend features:

- `elo_recent_change`
- `home_elo_trend`
- `away_elo_trend`
- `rolling_elo_form`

These measure recent movement in Elo, but they are not the same as season-boundary decay.

## Decayed Elo Sprint

The follow-up sprint tested this season-boundary formula:

```text
new_rating = 1500 + season_carryover * (old_rating - 1500)
```

Tested carryover values:

- `1.00`: current behavior, no season decay
- `0.90`
- `0.85`
- `0.75`
- `0.65`
- `0.50`

Result:

- Best Log Loss: current Elo with carryover `1.00`
- Best Brier Score: current Elo with carryover `1.00`
- Best ECE: decayed Elo with carryover `0.75`, but with worse Log Loss and Brier

Production decision: keep current Elo in production and keep decayed Elo research-only.

## What Still Has Not Been Tested

The project has not yet tested:

- separate promoted-team initialization
- club-level multi-season priors
- multi-year Elo weighting beyond simple season-boundary carryover

## Recommendation

Do not replace current Elo with simple season-decayed Elo. The best tested production setup remains carryover `1.00`, meaning no explicit season reset.

If Elo is revisited, focus on promoted-team priors or league-strength priors rather than simple decay.

## Artifacts

- `decayed_elo_evaluation_report.md`
- `evaluation/elo/decayed_elo_model_comparison.csv`
- `evaluation/elo/decayed_elo_draw_analysis.csv`
- `evaluation/elo/decayed_elo_model_comparison.png`
