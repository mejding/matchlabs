from __future__ import annotations

import pandas as pd

import app
from app import add_projection_position_movement, completed_matches_with_matchweeks


def test_completed_matchweeks_match_home_away_when_dates_move() -> None:
    completed = pd.DataFrame(
        {
            "Date": ["2026-08-28"],
            "HomeTeam": ["Crystal Palace"],
            "AwayTeam": ["Man City"],
            "FTHG": [1],
            "FTAG": [4],
            "FTR": ["A"],
            "Season": ["2627"],
        }
    )
    official = pd.DataFrame(
        {
            "date": ["2026-08-29"],
            "home_team": ["Crystal Palace"],
            "away_team": ["Man City"],
            "matchweek": [2],
        }
    )

    annotated = completed_matches_with_matchweeks(completed, official)

    assert int(annotated.loc[0, "matchweek"]) == 2


def test_projection_position_movement_uses_positive_numbers_for_moving_up() -> None:
    current = pd.DataFrame({"team": ["Team A", "Team B"], "projected_position": [2, 1]})
    preseason = pd.DataFrame({"team": ["Team A", "Team B"], "projected_position": [1, 2]})
    previous_round = pd.DataFrame({"team": ["Team A", "Team B"], "projected_position": [3, 1]})

    movement = add_projection_position_movement(current, preseason, previous_round)

    team_a = movement[movement["team"].eq("Team A")].iloc[0]
    team_b = movement[movement["team"].eq("Team B")].iloc[0]
    assert int(team_a["position_change_since_season_start"]) == -1
    assert int(team_a["position_change_since_previous_round"]) == 1
    assert int(team_b["position_change_since_season_start"]) == 1
    assert int(team_b["position_change_since_previous_round"]) == 0


def test_long_term_strength_ignores_partial_current_season(monkeypatch) -> None:
    rows = []
    for season in ["2425", "2526"]:
        for _ in range(300):
            rows.append(
                {
                    "Season": season,
                    "HomeTeam": "Established",
                    "AwayTeam": "Partial Star",
                    "FTHG": 2,
                    "FTAG": 0,
                    "FTR": "H",
                }
            )
    for _ in range(20):
        rows.append(
            {
                "Season": "2627",
                "HomeTeam": "Partial Star",
                "AwayTeam": "Established",
                "FTHG": 3,
                "FTAG": 0,
                "FTR": "H",
            }
        )
    matches = pd.DataFrame(rows)
    monkeypatch.setattr(app, "load_matches", lambda: matches)

    strength = app.build_long_term_team_strength(("Established", "Partial Star"), {})

    assert strength["Established"] > strength["Partial Star"]
