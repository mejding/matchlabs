from __future__ import annotations

import unittest

import pandas as pd

from squad_strength import apply_squad_strength_prior, normalize_squad_strength, squad_strength_lookup


class SquadStrengthTests(unittest.TestCase):
    def test_market_values_are_normalized_and_ranked(self) -> None:
        frame = pd.DataFrame(
            [
                {
                    "season": "2026/27",
                    "team": "Elite FC",
                    "squad_market_value_eur": 1_000_000_000,
                    "average_player_value_eur": 40_000_000,
                    "squad_size": 25,
                    "source": "Manual",
                    "source_url": "https://example.com",
                    "last_updated": "2026-06-21",
                    "data_confidence": "High",
                    "promoted_team_flag": False,
                },
                {
                    "season": "2026/27",
                    "team": "Promoted FC",
                    "squad_market_value_eur": 100_000_000,
                    "average_player_value_eur": 4_000_000,
                    "squad_size": 25,
                    "source": "Manual",
                    "source_url": "https://example.com",
                    "last_updated": "2026-06-21",
                    "data_confidence": "Medium",
                    "promoted_team_flag": True,
                },
            ]
        )
        normalized = normalize_squad_strength(frame, ["Elite FC", "Promoted FC"])
        elite = normalized[normalized["team"] == "Elite FC"].iloc[0]
        promoted = normalized[normalized["team"] == "Promoted FC"].iloc[0]
        self.assertEqual(float(elite["squad_strength_rank"]), 1.0)
        self.assertGreater(float(elite["squad_strength_score"]), float(promoted["squad_strength_score"]))
        self.assertTrue(bool(promoted["squad_strength_used"]))

    def test_missing_squad_value_is_not_treated_as_zero(self) -> None:
        frame = pd.DataFrame(
            [
                {
                    "season": "2026/27",
                    "team": "Known FC",
                    "squad_market_value_eur": 500_000_000,
                    "average_player_value_eur": 20_000_000,
                    "squad_size": 25,
                    "source": "Manual",
                    "source_url": "https://example.com",
                    "last_updated": "2026-06-21",
                    "data_confidence": "High",
                    "promoted_team_flag": False,
                }
            ]
        )
        normalized = normalize_squad_strength(frame, ["Known FC", "Missing FC"])
        missing = normalized[normalized["team"] == "Missing FC"].iloc[0]
        self.assertFalse(bool(missing["squad_strength_used"]))
        self.assertTrue(pd.isna(missing["squad_strength_score"]))
        self.assertEqual(missing["squad_strength_bucket"], "Missing")

    def test_squad_prior_is_mild_and_favors_stronger_squad(self) -> None:
        probabilities = pd.DataFrame(
            [
                {
                    "Date": pd.Timestamp("2026-08-22").date(),
                    "Season": "2627",
                    "HomeTeam": "Strong FC",
                    "AwayTeam": "Weak FC",
                    "home_win_probability": 0.40,
                    "draw_probability": 0.30,
                    "away_win_probability": 0.30,
                }
            ]
        )
        adjusted = apply_squad_strength_prior(probabilities, {"Strong FC": 1.0, "Weak FC": 0.0})
        self.assertGreater(float(adjusted.iloc[0]["home_win_probability"]), 0.40)
        self.assertLess(float(adjusted.iloc[0]["away_win_probability"]), 0.30)
        self.assertLess(float(adjusted.iloc[0]["home_win_probability"]), 0.45)

    def test_lookup_excludes_missing_scores(self) -> None:
        normalized = pd.DataFrame({"team": ["A", "B"], "squad_strength_score": [0.8, pd.NA]})
        self.assertEqual(squad_strength_lookup(normalized), {"A": 0.8})


if __name__ == "__main__":
    unittest.main()
