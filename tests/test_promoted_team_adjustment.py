from __future__ import annotations

from datetime import date, timedelta
import unittest

import pandas as pd

from season_simulation import season_start_feature_audit


def championship_matches(team: str = "Promoted FC") -> pd.DataFrame:
    rows = []
    start = date(2026, 4, 1)
    results = [
        (team, "A", 2, 0, 14, 8, 5, 3, 1.8, 0.7),
        ("B", team, 1, 1, 10, 13, 4, 5, 0.9, 1.6),
        (team, "C", 3, 1, 16, 9, 7, 2, 2.2, 0.8),
        ("D", team, 0, 2, 7, 15, 1, 6, 0.5, 1.9),
        (team, "E", 1, 0, 12, 10, 4, 3, 1.4, 0.9),
    ]
    for index, (home, away, fthg, ftag, hs, as_, hst, ast, hxg, axg) in enumerate(results):
        rows.append(
            {
                "Date": start + timedelta(days=index * 7),
                "HomeTeam": home,
                "AwayTeam": away,
                "FTHG": fthg,
                "FTAG": ftag,
                "FTR": "H" if fthg > ftag else "A" if ftag > fthg else "D",
                "HS": hs,
                "AS": as_,
                "HST": hst,
                "AST": ast,
                "home_xg": hxg,
                "away_xg": axg,
                "Season": "2526",
            }
        )
    return pd.DataFrame(rows)


class PromotedTeamAdjustmentTests(unittest.TestCase):
    def test_championship_form_is_adjusted_before_use(self) -> None:
        audit = season_start_feature_audit(
            ["Promoted FC"],
            team_history={},
            elo_state={},
            championship_matches=championship_matches(),
        )
        row = audit.iloc[0]
        self.assertEqual(row["local_pl_match_count"], 0)
        self.assertTrue(row["championship_data_available"])
        self.assertTrue(row["promotion_adjustment_applied"])
        self.assertFalse(row["fallback_used"])
        self.assertAlmostEqual(float(row["raw_recent_form"]), 13.0)
        self.assertAlmostEqual(float(row["adjusted_recent_form"]), 7.15)
        self.assertGreater(float(row["recent_form_points_last5"]), 0.0)

    def test_championship_xg_is_down_weighted_and_xga_up_adjusted(self) -> None:
        audit = season_start_feature_audit(
            ["Promoted FC"],
            team_history={},
            elo_state={},
            championship_matches=championship_matches(),
        )
        row = audit.iloc[0]
        self.assertAlmostEqual(float(row["adjusted_xg"]), float(row["raw_xg"]) * 0.75)
        self.assertAlmostEqual(float(row["adjusted_xga"]), float(row["raw_xga"]) * 1.35)

    def test_fallback_baseline_used_when_championship_data_missing(self) -> None:
        audit = season_start_feature_audit(
            ["Unknown FC"],
            team_history={},
            elo_state={},
            championship_matches=pd.DataFrame(),
        )
        row = audit.iloc[0]
        self.assertTrue(row["fallback_used"])
        self.assertTrue(row["promotion_adjustment_applied"])
        self.assertGreater(float(row["recent_form_points_last5"]), 0.0)
        self.assertGreater(float(row["xg_strength_last5"]), 0.0)
        self.assertGreater(float(row["shots_avg_last5"]), 0.0)

    def test_established_premier_league_team_is_not_adjusted(self) -> None:
        history = {
            "Established FC": {
                "points": [1, 3, 0, 3, 1],
                "goals_scored": [1, 2, 0, 3, 1],
                "xg": [1.1, 1.5, 0.8, 2.0, 1.2],
                "xga": [0.9, 1.0, 1.7, 0.7, 1.1],
                "match_dates": [date(2026, 4, day) for day in [1, 8, 15, 22, 29]],
                "shots": [10, 12, 9, 15, 11],
                "shots_on_target": [3, 4, 2, 6, 3],
                "shot_seasons": ["2526"] * 5,
            }
        }
        audit = season_start_feature_audit(
            ["Established FC"],
            team_history=history,
            elo_state={"Established FC": {"rating": 1550.0, "history": [1500.0, 1510.0, 1520.0, 1530.0, 1540.0]}},
            championship_matches=championship_matches("Established FC"),
        )
        row = audit.iloc[0]
        self.assertFalse(row["promotion_adjustment_applied"])
        self.assertFalse(row["fallback_used"])
        self.assertEqual(row["source_league"], "Premier League historical data")
        self.assertAlmostEqual(float(row["recent_form_points_last5"]), 8.0)


if __name__ == "__main__":
    unittest.main()
