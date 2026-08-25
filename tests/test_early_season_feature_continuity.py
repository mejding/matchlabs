from __future__ import annotations

import unittest

from predict import latest_season_average as prediction_latest_season_average
from season_simulation import latest_season_average as projection_latest_season_average
from train_model import average_current_season


class EarlySeasonFeatureContinuityTests(unittest.TestCase):
    def test_prediction_season_average_uses_recent_history_when_new_season_is_short(self) -> None:
        values = [10, 12, 11, 13, 9, 20]
        seasons = ["2526", "2526", "2526", "2526", "2526", "2627"]

        self.assertAlmostEqual(prediction_latest_season_average(values, seasons), 12.5)

    def test_projection_season_average_uses_recent_history_when_new_season_is_short(self) -> None:
        values = [10, 12, 11, 13, 9, 20]
        seasons = ["2526", "2526", "2526", "2526", "2526", "2627"]

        self.assertAlmostEqual(projection_latest_season_average(values, seasons), 12.5)

    def test_training_season_average_uses_current_season_after_enough_matches(self) -> None:
        values = [10, 12, 11, 13, 9, 20, 21, 19, 18, 22]
        seasons = ["2526"] * 5 + ["2627"] * 5

        self.assertAlmostEqual(average_current_season(values, seasons, "2627"), 20.0)

    def test_training_season_average_falls_back_before_enough_current_season_matches(self) -> None:
        values = [10, 12, 11, 13, 9, 20]
        seasons = ["2526", "2526", "2526", "2526", "2526", "2627"]

        self.assertAlmostEqual(average_current_season(values, seasons, "2627"), 12.5)


if __name__ == "__main__":
    unittest.main()
