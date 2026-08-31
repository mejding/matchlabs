from __future__ import annotations

import pandas as pd

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
