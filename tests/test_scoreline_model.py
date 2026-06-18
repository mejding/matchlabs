from __future__ import annotations

import unittest

import numpy as np

from scoreline_model import (
    align_scorelines_to_1x2,
    bucket_probabilities,
    calculate_scoreline_probabilities,
    estimate_scorelines,
)


class ScorelineModelTests(unittest.TestCase):
    def test_scoreline_probabilities_sum_to_one(self) -> None:
        matrix = calculate_scoreline_probabilities(1.6, 1.1)
        self.assertAlmostEqual(float(matrix.sum()), 1.0, places=8)

    def test_aligned_buckets_match_model_probabilities(self) -> None:
        matrix = calculate_scoreline_probabilities(1.4, 1.2)
        aligned = align_scorelines_to_1x2(matrix, 0.52, 0.25, 0.23)
        home, draw, away = bucket_probabilities(aligned)
        self.assertAlmostEqual(home, 0.52, places=8)
        self.assertAlmostEqual(draw, 0.25, places=8)
        self.assertAlmostEqual(away, 0.23, places=8)
        self.assertAlmostEqual(float(aligned.sum()), 1.0, places=8)

    def test_missing_xg_inputs_fall_back_gracefully(self) -> None:
        result = estimate_scorelines({}, np.array([0.45, 0.27, 0.28]))
        self.assertGreater(result["expected_home_goals"], 0)
        self.assertGreater(result["expected_away_goals"], 0)
        self.assertAlmostEqual(float(result["scoreline_matrix"].sum()), 1.0, places=8)

    def test_predicted_outcome_scoreline_follows_top_1x2_bucket(self) -> None:
        result = estimate_scorelines(
            {"home_xg_avg": 2.0, "away_xg_avg": 1.1, "home_xga_avg": 1.0, "away_xga_avg": 1.8},
            np.array([0.58, 0.30, 0.12]),
        )
        scoreline = result["most_likely_predicted_outcome"]
        self.assertGreater(scoreline.home_goals, scoreline.away_goals)


if __name__ == "__main__":
    unittest.main()
