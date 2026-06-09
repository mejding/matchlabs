# Remove-One Analysis: Raw xG vs Opponent-Adjusted Ratings

Lower Log Loss, Brier Score and ECE are better.

| test | feature_count | log_loss | Brier_score | expected_calibration_error | draw_recall | draw_log_loss |
| --- | --- | --- | --- | --- | --- | --- |
| production_reference | 40 | 1.0438 | 0.6264 | 0.0429 | 0.0365 | 0.5803 |
| remove_all_raw_xg | 34 | 1.0411 | 0.6255 | 0.0468 | 0.0365 | 0.5783 |
| remove_xg_avgs | 38 | 1.0460 | 0.6279 | 0.0452 | 0.0292 | 0.5801 |
| remove_xga_avgs | 38 | 1.0447 | 0.6272 | 0.0409 | 0.0219 | 0.5806 |
| remove_xg_diff | 38 | 1.0407 | 0.6250 | 0.0439 | 0.0219 | 0.5772 |
| ratings_reference | 53 | 1.0442 | 0.6280 | 0.0467 | 0.0219 | 0.5805 |
| ratings_reference_remove_attack | 42 | 1.0416 | 0.6261 | 0.0478 | 0.0365 | 0.5776 |
| ratings_reference_remove_defense | 42 | 1.0369 | 0.6232 | 0.0344 | 0.0438 | 0.5766 |
| production_plus_ratings_remove_raw_xg | 53 | 1.0442 | 0.6280 | 0.0467 | 0.0219 | 0.5805 |
| production_plus_ratings_remove_ratings | 40 | 1.0438 | 0.6264 | 0.0429 | 0.0365 | 0.5803 |

## Interpretation

- Removing all raw xG from production changes Log Loss by -0.0026.
- Replacing raw xG with ratings changes Log Loss by 0.0005.
- If raw xG removal hurts more than rating removal, raw xG still contains more unique signal.