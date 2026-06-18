# Scoreline Evaluation Report

## Purpose

Evaluate the scoreline interpretation layer on historical matches where final scores are known.

The scoreline layer is not a replacement for the 1X2 model. It estimates likely correct scores from expected goals and then aligns scoreline buckets with the production model's home/draw/away probabilities.

## Validation Period

- Train period: 2019-08-09 to 2025-01-25
- Test period: 2025-01-26 to 2026-05-24
- Test matches: 535

## Metrics

| Metric | Value |
| --- | ---: |
| Correct score accuracy | 0.114 |
| Top 3 scoreline hit rate | 0.320 |
| Top 5 scoreline hit rate | 0.445 |
| Mean probability assigned to actual scoreline | 0.065 |
| Scoreline log loss | 2.999 |
| Mean 1X2 alignment error | 0.000000 |
| Max 1X2 alignment error | 0.000000 |

## Examples Where It Worked

| Date | Match | Actual score | Most likely scoreline | Actual scoreline probability |
| --- | --- | --- | --- | --- |
| 2025-04-26 | Chelsea vs Everton | 1-0 | 1-0 | 0.2156 |
| 2025-11-30 | Chelsea vs Arsenal | 1-1 | 1-1 | 0.1830 |
| 2026-05-24 | Burnley vs Wolves | 1-1 | 1-1 | 0.1780 |
| 2025-09-20 | Burnley vs Nott'm Forest | 1-1 | 1-1 | 0.1708 |
| 2026-04-12 | Nott'm Forest vs Aston Villa | 1-1 | 1-1 | 0.1635 |
| 2025-04-02 | Man City vs Leicester | 2-0 | 1-0 | 0.1617 |
| 2025-04-19 | West Ham vs Southampton | 1-1 | 1-1 | 0.1486 |
| 2025-11-03 | Sunderland vs Everton | 1-1 | 1-1 | 0.1454 |

## Examples Where It Failed

| Date | Match | Actual score | Most likely scoreline | Actual scoreline probability |
| --- | --- | --- | --- | --- |
| 2025-02-01 | Nott'm Forest vs Brighton | 7-0 | 1-1 | 0.0000 |
| 2025-12-02 | Fulham vs Man City | 4-5 | 1-1 | 0.0009 |
| 2025-12-03 | Brighton vs Aston Villa | 3-4 | 1-1 | 0.0020 |
| 2026-04-24 | Sunderland vs Nott'm Forest | 0-5 | 1-1 | 0.0025 |
| 2025-12-15 | Man United vs Bournemouth | 4-4 | 2-1 | 0.0026 |
| 2025-05-04 | Brentford vs Man United | 4-3 | 1-1 | 0.0030 |
| 2025-04-12 | Man City vs Crystal Palace | 5-2 | 2-1 | 0.0037 |
| 2026-01-04 | Everton vs Brentford | 2-4 | 1-0 | 0.0048 |

## Interpretation

Correct-score prediction is inherently difficult. Even a useful scoreline layer will usually have low top-1 accuracy because many individual scorelines have small probabilities.

The useful validation check for this sprint is whether the layer provides plausible context and remains consistent with the main 1X2 probabilities. The alignment error should be effectively zero after scoreline bucket scaling.

## Production Guidance

Use the scoreline layer as supporting context only:

- show "Most likely scoreline"
- do not show "Predicted final score"
- do not claim a correct-score betting edge
- keep the main home/draw/away probabilities as the primary prediction
