from __future__ import annotations

from datetime import date
import unittest

from predict import build_prediction_features


class PredictionPromotedFallbackTests(unittest.TestCase):
    def test_low_history_away_team_gets_adjusted_values_in_prediction_features(self) -> None:
        feature_columns = [
            "home_team_points_last_5",
            "away_team_points_last_5",
            "home_goals_scored_avg",
            "away_goals_scored_avg",
            "home_advantage",
            "home_xg_avg",
            "away_xg_avg",
            "home_xga_avg",
            "away_xga_avg",
            "home_xg_diff",
            "away_xg_diff",
            "home_days_rest",
            "away_days_rest",
            "home_matches_last_14_days",
            "away_matches_last_14_days",
            "home_had_midweek_match",
            "away_had_midweek_match",
            "home_days_since_last_match",
            "away_days_since_last_match",
            "home_shots_avg_last5",
            "away_shots_avg_last5",
            "home_shots_on_target_avg_last5",
            "away_shots_on_target_avg_last5",
            "home_shots_avg_season",
            "away_shots_avg_season",
        ]
        team_history = {
            "Arsenal": {
                "points": [3, 3, 3, 3, 3],
                "goals_scored": [2, 2, 1, 3, 2],
                "xg": [2.1, 2.4, 1.9, 2.2, 2.0],
                "xga": [0.8, 0.7, 0.9, 0.6, 0.8],
                "match_dates": [date(2026, 5, day) for day in [1, 8, 15, 22, 24]],
                "shots": [14, 15, 13, 16, 14],
                "shots_on_target": [5, 6, 4, 7, 5],
                "shot_seasons": ["2526"] * 5,
            }
        }
        features = build_prediction_features(
            "Arsenal",
            "Coventry",
            team_history,
            feature_columns,
            match_date=date(2026, 8, 21),
            elo_state={},
        )
        row = features.iloc[0]
        self.assertGreater(float(row["away_team_points_last_5"]), 0.0)
        self.assertGreater(float(row["away_xg_avg"]), 0.0)
        self.assertGreater(float(row["away_xga_avg"]), 0.0)
        self.assertGreater(float(row["away_shots_avg_last5"]), 0.0)


if __name__ == "__main__":
    unittest.main()
