from __future__ import annotations

from collections import defaultdict
from itertools import combinations

import numpy as np
import pandas as pd

from lineup_data import lineup_data_note
from train_model import points_for_team


LINEUP_CONTINUITY_FEATURES = [
    "starting_xi_repeat_count",
    "starting_xi_repeat_pct",
    "lineup_changes",
    "same_back_four",
    "same_midfield",
    "same_attack",
    "starters_from_last_win",
    "lineup_similarity_last_win",
    "days_since_last_win",
]
FAMILIARITY_FEATURES = [
    "shared_starts_score",
    "shared_minutes_score",
    "lineup_familiarity_score",
]
FULL_STABILITY_FEATURES = [
    "manager_stability_score",
    "lineup_rotation_rate",
    "squad_consistency_score",
]

POSITION_GROUPS = {
    "GK": "goalkeeper",
    "G": "goalkeeper",
    "D": "defender",
    "DF": "defender",
    "DEF": "defender",
    "CB": "defender",
    "LB": "defender",
    "RB": "defender",
    "WB": "defender",
    "LWB": "defender",
    "RWB": "defender",
    "M": "midfielder",
    "MF": "midfielder",
    "MID": "midfielder",
    "CM": "midfielder",
    "DM": "midfielder",
    "AM": "midfielder",
    "W": "attacker",
    "LW": "attacker",
    "RW": "attacker",
    "F": "attacker",
    "FW": "attacker",
    "ST": "attacker",
    "CF": "attacker",
}


def lineup_feature_columns() -> list[str]:
    return [f"{side}_{feature}" for side in ("home", "away") for feature in LINEUP_CONTINUITY_FEATURES]


def familiarity_feature_columns() -> list[str]:
    return [f"{side}_{feature}" for side in ("home", "away") for feature in FAMILIARITY_FEATURES]


def stability_feature_columns() -> list[str]:
    return [f"{side}_{feature}" for side in ("home", "away") for feature in FULL_STABILITY_FEATURES]


def all_lineup_stability_columns() -> list[str]:
    return lineup_feature_columns() + familiarity_feature_columns() + stability_feature_columns()


def _position_group(position: object, position_group: object) -> str:
    if isinstance(position_group, str) and position_group:
        return position_group.lower()
    if isinstance(position, str):
        return POSITION_GROUPS.get(position.upper(), "unknown")
    return "unknown"


def _historical_rows(appearances: pd.DataFrame, team: str, current_date: pd.Timestamp) -> pd.DataFrame:
    if appearances.empty:
        return appearances
    rows = appearances[(appearances["team"] == team) & (appearances["date"] < current_date)]
    if "source_collected_at" in rows.columns:
        rows = rows[rows["source_collected_at"].isna() | (rows["source_collected_at"] < current_date)]
    return rows


def _latest_known_starters_before(
    appearances: pd.DataFrame,
    team: str,
    current_date: pd.Timestamp,
) -> pd.DataFrame:
    rows = _historical_rows(appearances, team, current_date)
    if rows.empty:
        return rows
    last_date = rows["date"].max()
    return rows[(rows["date"] == last_date) & (rows["started"] >= 1)]


def _expected_or_latest_starters(
    appearances: pd.DataFrame,
    team: str,
    current_date: pd.Timestamp,
) -> tuple[pd.DataFrame, pd.Timestamp | None]:
    if appearances.empty:
        return appearances, None

    expected = appearances[
        (appearances["team"] == team)
        & (appearances["date"] == current_date)
        & (appearances["started"] >= 1)
        & (appearances["lineup_type"].fillna("").str.lower().isin(["expected", "projected"]))
        & (appearances["source_collected_at"].isna() | (appearances["source_collected_at"] < current_date))
    ]
    if not expected.empty:
        return expected, current_date

    latest = _latest_known_starters_before(appearances, team, current_date)
    if latest.empty:
        return latest, None
    return latest, latest["date"].max()


def _last_win_starters(appearances: pd.DataFrame, matches_before: pd.DataFrame, team: str) -> tuple[set[str], pd.Timestamp | None]:
    winning_matches = []
    for _, match in matches_before.iterrows():
        if team not in {match["HomeTeam"], match["AwayTeam"]}:
            continue
        if points_for_team(match, team) == 3:
            winning_matches.append(match)

    if not winning_matches:
        return set(), None

    last_win = winning_matches[-1]
    win_date = pd.to_datetime(last_win["Date"])
    starters = appearances[
        (appearances["team"] == team)
        & (appearances["date"] == win_date)
        & (appearances["started"] >= 1)
    ]
    return set(starters["player"].astype(str)), win_date


def _pair_key(player_a: str, player_b: str) -> tuple[str, str]:
    return tuple(sorted((player_a, player_b)))


def _familiarity_scores(historical_starts: pd.DataFrame, current_starters: list[str]) -> tuple[float, float]:
    if len(current_starters) < 2 or historical_starts.empty:
        return 0.0, 0.0

    starts_together: dict[tuple[str, str], int] = defaultdict(int)
    minutes_together: dict[tuple[str, str], float] = defaultdict(float)
    for _, group in historical_starts.groupby("date"):
        starters = group[group["started"] >= 1]
        players = starters["player"].astype(str).tolist()
        minutes = dict(zip(starters["player"].astype(str), starters["minutes"].astype(float)))
        for player_a, player_b in combinations(players, 2):
            key = _pair_key(player_a, player_b)
            starts_together[key] += 1
            minutes_together[key] += min(minutes.get(player_a, 0.0), minutes.get(player_b, 0.0))

    total_starts = 0.0
    total_minutes = 0.0
    for player_a, player_b in combinations(current_starters, 2):
        key = _pair_key(player_a, player_b)
        total_starts += starts_together.get(key, 0)
        total_minutes += minutes_together.get(key, 0.0)
    return total_starts, total_minutes


def _manager_stability(manager_history: pd.DataFrame, team: str, current_date: pd.Timestamp, matches_before: pd.DataFrame) -> float:
    if manager_history.empty:
        return 0.0

    rows = manager_history[
        (manager_history["team"] == team)
        & (manager_history["start_date"] <= current_date)
        & (manager_history["end_date"].isna() | (manager_history["end_date"] >= current_date))
    ]
    if rows.empty:
        return 0.0

    start_date = rows.sort_values("start_date").iloc[-1]["start_date"]
    team_matches = matches_before[
        ((matches_before["HomeTeam"] == team) | (matches_before["AwayTeam"] == team))
        & (pd.to_datetime(matches_before["Date"]) >= start_date)
    ]
    return float(len(team_matches))


def _team_lineup_features(
    matches_before: pd.DataFrame,
    appearances: pd.DataFrame,
    manager_history: pd.DataFrame,
    team: str,
    current_date: pd.Timestamp,
) -> dict[str, float]:
    current, current_lineup_date = _expected_or_latest_starters(appearances, team, current_date)
    historical = _historical_rows(appearances, team, current_date)

    if current.empty:
        return {feature: 0.0 for feature in LINEUP_CONTINUITY_FEATURES + FAMILIARITY_FEATURES + FULL_STABILITY_FEATURES}

    if current_lineup_date is None:
        previous = current.iloc[0:0]
    else:
        previous = _latest_known_starters_before(appearances, team, current_lineup_date)

    current_players = set(current["player"].astype(str))
    previous_players = set(previous["player"].astype(str))
    repeated = current_players & previous_players

    def repeated_group(group_name: str) -> float:
        if current.empty or "player" not in current.columns:
            return 0.0
        if previous.empty or "player" not in previous.columns:
            return 0.0
        current_group = set(
            current[current.apply(lambda row: _position_group(row.get("position"), row.get("position_group")) == group_name, axis=1)][
                "player"
            ].astype(str)
        )
        previous_group = set(
            previous[previous.apply(lambda row: _position_group(row.get("position"), row.get("position_group")) == group_name, axis=1)][
                "player"
            ].astype(str)
        )
        return float(len(current_group & previous_group))

    last_win_players, last_win_date = _last_win_starters(appearances, matches_before, team)
    starters_from_last_win = len(current_players & last_win_players)
    days_since_last_win = float((current_date - last_win_date).days) if last_win_date is not None else 365.0
    historical_starts = historical[historical["started"] >= 1]
    shared_starts, shared_minutes = _familiarity_scores(historical_starts, sorted(current_players))

    lineup_changes_history = []
    previous_lineup: set[str] | None = None
    for _, group in historical_starts.groupby("date"):
        lineup = set(group["player"].astype(str))
        if previous_lineup is not None:
            lineup_changes_history.append(max(0, 11 - len(lineup & previous_lineup)))
        previous_lineup = lineup
    rotation_rate = float(np.mean(lineup_changes_history[-10:])) if lineup_changes_history else 0.0
    repeat_pct = float(len(repeated) / 11.0)
    familiarity = float(np.log1p(shared_starts) + np.log1p(shared_minutes) / 10.0)
    squad_consistency = float(max(0.0, 100.0 - 7.0 * rotation_rate + 20.0 * repeat_pct))

    return {
        "starting_xi_repeat_count": float(len(repeated)),
        "starting_xi_repeat_pct": repeat_pct,
        "lineup_changes": float(max(0, 11 - len(repeated))),
        "same_back_four": repeated_group("defender"),
        "same_midfield": repeated_group("midfielder"),
        "same_attack": repeated_group("attacker"),
        "starters_from_last_win": float(starters_from_last_win),
        "lineup_similarity_last_win": float(starters_from_last_win / 11.0),
        "days_since_last_win": days_since_last_win,
        "shared_starts_score": float(shared_starts),
        "shared_minutes_score": float(shared_minutes),
        "lineup_familiarity_score": familiarity,
        "manager_stability_score": _manager_stability(manager_history, team, current_date, matches_before),
        "lineup_rotation_rate": rotation_rate,
        "squad_consistency_score": squad_consistency,
    }


def build_lineup_stability_features(
    matches: pd.DataFrame,
    appearances: pd.DataFrame,
    manager_history: pd.DataFrame,
) -> pd.DataFrame:
    """Build historical lineup features. Empty lineup tables produce neutral zero features."""
    rows = []
    ordered_matches = matches.sort_values("Date").reset_index(drop=True)
    appearances = appearances.copy()
    if not appearances.empty:
        appearances["date"] = pd.to_datetime(appearances["date"])
        appearances["source_collected_at"] = pd.to_datetime(appearances["source_collected_at"], errors="coerce")

    for index, match in ordered_matches.iterrows():
        current_date = pd.to_datetime(match["Date"])
        matches_before = ordered_matches.iloc[:index].copy()
        home = _team_lineup_features(matches_before, appearances, manager_history, match["HomeTeam"], current_date)
        away = _team_lineup_features(matches_before, appearances, manager_history, match["AwayTeam"], current_date)

        row = {}
        for feature, value in home.items():
            row[f"home_{feature}"] = value
        for feature, value in away.items():
            row[f"away_{feature}"] = value
        rows.append(row)

    return pd.DataFrame(rows)


def lineup_engine_note() -> str:
    return (
        "The stability engine never reads the actual current match XI as a pre-match feature. "
        "It uses only appearances and manager rows dated before the fixture. "
        + lineup_data_note()
    )
