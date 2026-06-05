from __future__ import annotations

from collections import defaultdict
from dataclasses import dataclass

import pandas as pd


CORE_H2H_COLUMNS = [
    "h2h_matches_count",
    "h2h_home_wins",
    "h2h_draws",
    "h2h_away_wins",
    "h2h_points_home_team",
    "h2h_points_away_team",
    "h2h_data_strength_score",
]
RECENT_H2H_COLUMNS = [
    "h2h_last_3_points_home",
    "h2h_last_5_points_home_team",
    "h2h_last_3_goal_diff",
    "h2h_last_5_goal_diff",
    "h2h_last_3_xg_diff",
    "h2h_last_5_xg_diff",
]
VENUE_H2H_COLUMNS = [
    "h2h_home_venue_points",
    "h2h_home_venue_goal_diff",
    "h2h_home_venue_xg_diff",
]
ALL_H2H_COLUMNS = CORE_H2H_COLUMNS + RECENT_H2H_COLUMNS + VENUE_H2H_COLUMNS


@dataclass(frozen=True)
class HistoricalMeeting:
    date: object
    home_team: str
    away_team: str
    home_goals: float
    away_goals: float
    home_xg: float
    away_xg: float
    result: str


def pair_key(team_a: str, team_b: str) -> tuple[str, str]:
    return tuple(sorted([team_a, team_b]))


def points_for_current_home(meeting: HistoricalMeeting, current_home_team: str) -> float:
    if meeting.result == "D":
        return 1.0
    winner = meeting.home_team if meeting.result == "H" else meeting.away_team
    return 3.0 if winner == current_home_team else 0.0


def goal_diff_for_current_home(meeting: HistoricalMeeting, current_home_team: str) -> float:
    if meeting.home_team == current_home_team:
        return meeting.home_goals - meeting.away_goals
    return meeting.away_goals - meeting.home_goals


def xg_diff_for_current_home(meeting: HistoricalMeeting, current_home_team: str) -> float:
    if meeting.home_team == current_home_team:
        return meeting.home_xg - meeting.away_xg
    return meeting.away_xg - meeting.home_xg


def data_strength_score(meetings_count: int) -> float:
    if meetings_count <= 0:
        return 0.0
    if meetings_count <= 2:
        return 0.25
    if meetings_count <= 5:
        return 0.60
    return 1.0


def _sum_recent(values: list[float], window: int) -> float:
    return float(sum(values[-window:])) if values else 0.0


def _features_for_fixture(home_team: str, away_team: str, history: list[HistoricalMeeting]) -> dict[str, float]:
    meetings_count = len(history)
    home_points = [points_for_current_home(meeting, home_team) for meeting in history]
    away_points = [3.0 - value if value != 1.0 else 1.0 for value in home_points]
    goal_diffs = [goal_diff_for_current_home(meeting, home_team) for meeting in history]
    xg_diffs = [xg_diff_for_current_home(meeting, home_team) for meeting in history]
    venue_history = [
        meeting for meeting in history if meeting.home_team == home_team and meeting.away_team == away_team
    ]

    return {
        "h2h_matches_count": float(meetings_count),
        "h2h_home_wins": float(sum(1 for value in home_points if value == 3.0)),
        "h2h_draws": float(sum(1 for meeting in history if meeting.result == "D")),
        "h2h_away_wins": float(sum(1 for value in away_points if value == 3.0)),
        "h2h_points_home_team": float(sum(home_points)),
        "h2h_points_away_team": float(sum(away_points)),
        "h2h_data_strength_score": data_strength_score(meetings_count),
        "h2h_last_3_points_home": _sum_recent(home_points, 3),
        "h2h_last_5_points_home_team": _sum_recent(home_points, 5),
        "h2h_last_3_goal_diff": _sum_recent(goal_diffs, 3),
        "h2h_last_5_goal_diff": _sum_recent(goal_diffs, 5),
        "h2h_last_3_xg_diff": _sum_recent(xg_diffs, 3),
        "h2h_last_5_xg_diff": _sum_recent(xg_diffs, 5),
        "h2h_home_venue_points": float(sum(points_for_current_home(meeting, home_team) for meeting in venue_history)),
        "h2h_home_venue_goal_diff": float(sum(goal_diff_for_current_home(meeting, home_team) for meeting in venue_history)),
        "h2h_home_venue_xg_diff": float(sum(xg_diff_for_current_home(meeting, home_team) for meeting in venue_history)),
    }


def build_head_to_head_features(matches: pd.DataFrame) -> pd.DataFrame:
    """Build pre-match H2H features with strict historical ordering.

    Each row is calculated before the current match is added to the pair history,
    so later meetings never leak into earlier fixtures.
    """

    pair_history: dict[tuple[str, str], list[HistoricalMeeting]] = defaultdict(list)
    rows: list[dict[str, float]] = []
    ordered = matches.sort_values("Date").reset_index(drop=True)

    for _, match in ordered.iterrows():
        home_team = str(match["HomeTeam"])
        away_team = str(match["AwayTeam"])
        history = pair_history[pair_key(home_team, away_team)]
        rows.append(_features_for_fixture(home_team, away_team, history))

        pair_history[pair_key(home_team, away_team)].append(
            HistoricalMeeting(
                date=match["Date"],
                home_team=home_team,
                away_team=away_team,
                home_goals=float(match["FTHG"]),
                away_goals=float(match["FTAG"]),
                home_xg=float(match.get("home_xg", 0.0)),
                away_xg=float(match.get("away_xg", 0.0)),
                result=str(match["FTR"]),
            )
        )

    return pd.DataFrame(rows, columns=ALL_H2H_COLUMNS).fillna(0.0)


def h2h_methodology_note() -> str:
    return (
        "Head-to-head features are generated chronologically. For every fixture, only previous meetings between "
        "the two teams are visible. Recent windows use the last 3 and last 5 historical meetings. Venue features "
        "use only prior meetings where the current home team was also at home. `h2h_data_strength_score` is 0.0 "
        "for no meetings, 0.25 for 1-2 meetings, 0.60 for 3-5 meetings and 1.0 for 6+ meetings."
    )
