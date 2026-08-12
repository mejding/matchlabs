from __future__ import annotations

from datetime import date

import pandas as pd

from non_pl_context_features import build_non_pl_context_features


def test_non_pl_context_uses_only_matches_before_fixture() -> None:
    pl_matches = pd.DataFrame(
        [
            {
                "Date": date(2026, 8, 15),
                "HomeTeam": "Arsenal",
                "AwayTeam": "Chelsea",
            }
        ]
    )
    non_pl = pd.DataFrame(
        [
            {
                "Date": date(2026, 8, 10),
                "team": "Arsenal",
                "opponent": "Friendly XI",
                "competition": "Pre-season Friendly",
                "source_file": "test.csv",
                "points": 3.0,
                "goals_for": 4.0,
                "shots_for": 12.0,
                "weight": 0.25,
            },
            {
                "Date": date(2026, 8, 16),
                "team": "Arsenal",
                "opponent": "Future FC",
                "competition": "Pre-season Friendly",
                "source_file": "test.csv",
                "points": 3.0,
                "goals_for": 7.0,
                "shots_for": 30.0,
                "weight": 0.25,
            },
        ]
    )

    features = build_non_pl_context_features(pl_matches, non_pl).iloc[0]

    assert features["home_non_pl_context_available"] == 1.0
    assert features["home_preseason_matches_last_60_days"] == 1.0
    assert features["home_non_pl_points_equiv_last5"] == 0.75
    assert features["home_non_pl_goals_equiv_avg_last5"] == 1.0
    assert features["away_non_pl_context_available"] == 0.0


def test_championship_context_is_down_weighted() -> None:
    pl_matches = pd.DataFrame(
        [
            {
                "Date": date(2026, 8, 15),
                "HomeTeam": "Coventry",
                "AwayTeam": "Hull",
            }
        ]
    )
    championship = pd.DataFrame(
        [
            {
                "Date": date(2026, 8, 5),
                "team": "Coventry",
                "opponent": "Birmingham",
                "competition": "Championship",
                "source_file": "championship.csv",
                "points": 3.0,
                "goals_for": 2.0,
                "shots_for": 10.0,
                "weight": 0.55,
            },
            {
                "Date": date(2026, 8, 8),
                "team": "Coventry",
                "opponent": "Derby",
                "competition": "Championship",
                "source_file": "championship.csv",
                "points": 1.0,
                "goals_for": 1.0,
                "shots_for": 8.0,
                "weight": 0.55,
            },
        ]
    )

    features = build_non_pl_context_features(pl_matches, championship).iloc[0]

    assert round(features["home_non_pl_points_equiv_last5"], 2) == 2.20
    assert round(features["home_non_pl_goals_equiv_avg_last5"], 3) == 0.825
    assert round(features["home_non_pl_shots_equiv_avg_last5"], 2) == 4.95
    assert features["home_competitive_non_pl_matches_last_30_days"] == 2.0
