# Feature Engineering Audit

This audit inspects the production feature engineering in `train_model.py`.

## Summary

The inspected form and xG features use all recent matches combined. They are not venue-specific. For a home team, the latest 5 matches can include both home and away matches. For an away team, the latest 5 matches can also include both home and away matches.

## Feature Details

| Feature | Exact calculation | Data window | Venue-specific? | Potential information loss |
| --- | --- | --- | --- | --- |
| `home_team_points_last_5` | Sum of `team_history[home_team]["points"][-5:]` before the fixture. Points are 3/1/0 from each previous match regardless of venue. | Latest 5 matches played by the home team before the fixture. | No. Uses all recent home-team matches combined. | Home form at the stadium is blended with away form. |
| `away_team_points_last_5` | Sum of `team_history[away_team]["points"][-5:]` before the fixture. | Latest 5 matches played by the away team before the fixture. | No. Uses all recent away-team matches combined. | Away-specific travel/performance signal is blended with home form. |
| `home_goals_scored_avg` | Average of `team_history[home_team]["goals_scored"][-5:]`. | Latest 5 matches played by the home team before the fixture. | No. | Home scoring strength may be diluted by away scoring context. |
| `away_goals_scored_avg` | Average of `team_history[away_team]["goals_scored"][-5:]`. | Latest 5 matches played by the away team before the fixture. | No. | Away scoring strength may be overstated if recent goals came mostly at home. |
| `home_xg_avg` | Average of `team_history[home_team]["xg"][-5:]`. | Latest 5 matches played by the home team before the fixture. | No. | Home chance creation is blended with away chance creation. |
| `away_xg_avg` | Average of `team_history[away_team]["xg"][-5:]`. | Latest 5 matches played by the away team before the fixture. | No. | Away attacking quality can be misrepresented if recent xG came at home. |
| `home_xga_avg` | Average of `team_history[home_team]["xga"][-5:]`. | Latest 5 matches played by the home team before the fixture. | No. | Home defensive strength can be blended with away defensive difficulty. |
| `away_xga_avg` | Average of `team_history[away_team]["xga"][-5:]`. | Latest 5 matches played by the away team before the fixture. | No. | Away defensive weakness/strength can be hidden by home matches. |
| `home_xg_diff` | `home_xg_avg - home_xga_avg`. | Same latest 5 all-venue matches. | No. | Venue-specific xG balance is not captured. |
| `away_xg_diff` | `away_xg_avg - away_xga_avg`. | Same latest 5 all-venue matches. | No. | Away-specific xG balance is not captured. |

## Leakage Assessment

The current features are historically safe: each feature is calculated before the current fixture, then the match result is appended to history afterward. The issue is not leakage; it is information loss from mixing home and away contexts.

## Experimental Venue-Specific Features

Because production venue-specific versions did not exist, this sprint adds research features in `venue_specific_feature_experiments.py`:

- `home_points_last_5_home_matches`
- `away_points_last_5_away_matches`
- `home_xg_last_5_home_matches`
- `away_xg_last_5_away_matches`
- `home_xga_last_5_home_matches`
- `away_xga_last_5_away_matches`
- `home_goal_diff_home_matches`
- `away_goal_diff_away_matches`
