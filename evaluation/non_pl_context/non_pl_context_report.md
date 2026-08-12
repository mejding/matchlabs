# Non-PL Match Context Evaluation

## Goal

Test whether pre-season friendlies, European qualifiers and other competitive non-Premier-League matches should inform the match prediction model.

## Feature Design

These features are generated chronologically and use only matches before kickoff:

- recent non-PL match activity
- days since any known match
- pre-season match count
- competitive non-PL match count
- European qualifier flag
- weighted non-PL points, goals and shot volume

First-version weighting:

- Championship: `0.55`
- Champions League: `0.80`
- Europa League: `0.75`
- Conference League / European qualifier: `0.70`
- Domestic cups: `0.45`
- Friendlies / pre-season: `0.25`

The intent is to let non-PL matches help with match rhythm and early-season context without treating them as Premier League-equivalent.

## Local Source Coverage

| source_file | competition | team_rows | teams | first_date | last_date |
| --- | --- | --- | --- | --- | --- |
| championship_2526.csv | Championship | 1104 | 24 | 2025-08-08 | 2026-05-02 |

Premier League training/evaluation rows with actual non-PL context available: `0`.

## Model Comparison

| model_version | accuracy | log_loss | Brier_score | expected_calibration_error | draw_recall | draw_log_loss | test_period |
| --- | --- | --- | --- | --- | --- | --- | --- |
| model_a_current_production | 0.4879 | 1.0438 | 0.6264 | 0.0429 | 0.0365 | 0.5803 | 2025-01-26 to 2026-05-24 |
| model_b_production_plus_non_pl_context | 0.4879 | 1.0438 | 0.6264 | 0.0429 | 0.0365 | 0.5803 | 2025-01-26 to 2026-05-24 |

Candidate deltas versus production:

- Log Loss: `+0.000000`
- Brier Score: `+0.000000`
- ECE: `+0.000000`

## Answer

European qualifiers and cup matches are conceptually stronger than friendlies because they are competitive and affect fatigue. Pre-season friendlies are much noisier and should only be weak context.

However, the current local project does not yet contain reliable historical pre-season or European qualifier rows for Premier League teams. The available Championship file is useful for promoted-team season projection context, but it does not provide broad historical non-PL coverage for the Premier League match training set.

## Production Decision

Do not move into production yet. Local source coverage is too thin and the candidate must improve out-of-sample Log Loss or Brier before activation.

## Next Data Needed

To make this feature family genuinely testable, add historically reproducible rows for:

- European qualifiers and European group-stage matches before each Premier League fixture
- domestic cup matches
- selected pre-season friendlies with kickoff dates, teams, result and ideally shots/xG

Each source must include match date and competition so timing and weighting stay transparent.
