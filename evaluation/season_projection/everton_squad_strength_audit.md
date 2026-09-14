# Everton Squad Strength Audit

## Before / After

| Metric | Before squad strength | After squad strength |
| --- | ---: | ---: |
| Expected points | 49.89 | 49.89 |
| Expected position | 10.87 | 10.88 |
| Relegation probability | 3.3% | 3.5% |

## Everton Feature Ranks

| team | squad_strength_rank | squad_strength_bucket | elo_rank | recent_form_rank | xg_rank | shot_volume_rank | recent_form_points_last5 | xg_diff_last5 | shots_avg_last5 | elo_rating |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| Everton | 14.0000 | Mid-table | 13.0000 | 12.0000 | 12.0000 | 13.0000 | 6.0000 | -0.2929 | 13.4000 | 1552.7823 |

## Diagnosis

1. Recent form is poor: Everton has low last-5 points in the local 2025/26 data.
2. xG/shot profile is weak: Everton's recent xG differential is negative.
3. Elo is not relegation-level, but the recent Elo movement is negative.
4. Fixture difficulty contributes through the official fixture list, but it is not the only reason.
5. Squad strength was previously missing from the Season Projection prior. Adding it gives Everton a mild resource-quality stabilizer, but it does not fully override recent form and xG.

## Recommendation

Keep the squad strength effect mild. It is useful as a preseason stabilizer, but not yet historically validated enough to dominate the forecast.
