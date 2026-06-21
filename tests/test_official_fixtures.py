from __future__ import annotations

import unittest

from official_fixtures import (
    OFFICIAL_FIXTURE_PATH,
    fixtures_for_model,
    load_official_fixtures,
    normalize_team_name,
    schedule_context_for_fixture,
    validate_fixture_frame,
)
from season_simulation import read_default_upcoming_fixtures


class OfficialFixtureTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.fixtures = load_official_fixtures(OFFICIAL_FIXTURE_PATH)

    def test_team_name_mapping(self) -> None:
        self.assertEqual(normalize_team_name("Manchester City"), "Man City")
        self.assertEqual(normalize_team_name("Manchester United"), "Man United")
        self.assertEqual(normalize_team_name("Brighton and Hove Albion"), "Brighton")
        self.assertEqual(normalize_team_name("Nottingham Forest"), "Nott'm Forest")

    def test_fixture_file_validation(self) -> None:
        validation = validate_fixture_frame(self.fixtures)
        self.assertTrue(validation["valid"], validation["errors"])
        self.assertEqual(validation["fixture_count"], 380)
        self.assertEqual(validation["team_count"], 20)
        counts = validation["team_counts"]
        self.assertTrue((counts["matches"] == 38).all())
        self.assertTrue((counts["home"] == 19).all())
        self.assertTrue((counts["away"] == 19).all())

    def test_model_fixture_conversion(self) -> None:
        model_fixtures = fixtures_for_model(self.fixtures)
        self.assertEqual(len(model_fixtures), 380)
        self.assertIn("HomeTeam", model_fixtures.columns)
        self.assertIn("AwayTeam", model_fixtures.columns)

    def test_season_projection_uses_official_fixtures(self) -> None:
        model_fixtures, mode = read_default_upcoming_fixtures()
        self.assertEqual(mode, "Official fixtures loaded")
        self.assertIsNotNone(model_fixtures)
        self.assertEqual(len(model_fixtures), 380)

    def test_schedule_context_does_not_crash(self) -> None:
        first = self.fixtures.iloc[0]
        context = schedule_context_for_fixture(self.fixtures, first["home_team"], first["away_team"], first["date"])
        self.assertIn("home_days_rest", context)
        self.assertIn("away_matches_next_14_days", context)


if __name__ == "__main__":
    unittest.main()
