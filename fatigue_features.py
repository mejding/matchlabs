from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

import pandas as pd


EUROPE_FIXTURE_PATH = Path("data") / "european_fixtures.csv"
EUROPE_FIXTURE_COLUMNS = ["date", "team", "competition", "opponent"]

FATIGUE_FEATURES = [
    "days_rest",
    "had_midweek_match",
    "matches_last_14_days",
    "matches_last_30_days",
    "days_since_last_match",
    "fixture_congestion_score",
]
EUROPE_FEATURES = [
    "played_europe_midweek",
    "days_since_europe_match",
    "european_fixture_load",
]


@dataclass(frozen=True)
class ScheduleState:
    match_dates: list[pd.Timestamp]
    europe_dates: list[pd.Timestamp]


def ensure_europe_fixture_template(path: Path = EUROPE_FIXTURE_PATH) -> None:
    path.parent.mkdir(exist_ok=True)
    if not path.exists():
        pd.DataFrame(columns=EUROPE_FIXTURE_COLUMNS).to_csv(path, index=False)


def load_european_fixtures(path: Path = EUROPE_FIXTURE_PATH) -> pd.DataFrame:
    ensure_europe_fixture_template(path)
    fixtures = pd.read_csv(path)
    if fixtures.empty:
        return pd.DataFrame(columns=EUROPE_FIXTURE_COLUMNS + ["Date"])

    missing = sorted(set(EUROPE_FIXTURE_COLUMNS) - set(fixtures.columns))
    if missing:
        raise ValueError(f"Missing required European fixture columns: {missing}")

    fixtures = fixtures.copy()
    fixtures["Date"] = pd.to_datetime(fixtures["date"], errors="coerce")
    fixtures = fixtures.dropna(subset=["Date", "team"])
    fixtures["team"] = fixtures["team"].astype(str)
    return fixtures.sort_values("Date").reset_index(drop=True)


def _days_since(dates: list[pd.Timestamp], current_date: pd.Timestamp, default: float = 14.0) -> float:
    previous = [date for date in dates if date < current_date]
    if not previous:
        return default
    return float((current_date - max(previous)).days)


def _matches_last_days(dates: list[pd.Timestamp], current_date: pd.Timestamp, days: int) -> int:
    return sum(1 for date in dates if 0 < (current_date - date).days <= days)


def _played_europe_midweek(europe_dates: list[pd.Timestamp], current_date: pd.Timestamp) -> int:
    return int(any(0 < (current_date - date).days <= 7 and date.weekday() in {1, 2, 3} for date in europe_dates))


def fixture_congestion_score(days_rest: float, matches_last_14_days: int, matches_last_30_days: int) -> float:
    """Composite schedule intensity score.

    Formula:
    short_rest_penalty + recent_load_penalty + monthly_load_penalty

    - short_rest_penalty = max(0, 7 - days_rest)
    - recent_load_penalty = 1.5 * matches_last_14_days
    - monthly_load_penalty = 0.5 * matches_last_30_days

    Higher values mean a more congested schedule. All inputs are historical.
    """
    short_rest_penalty = max(0.0, 7.0 - float(days_rest))
    return float(short_rest_penalty + 1.5 * matches_last_14_days + 0.5 * matches_last_30_days)


def _team_schedule_features(state: ScheduleState, current_date: pd.Timestamp, include_europe: bool) -> dict[str, float]:
    competitive_dates = state.match_dates + state.europe_dates if include_europe else state.match_dates
    days_since_last = _days_since(competitive_dates, current_date)
    matches_14 = _matches_last_days(competitive_dates, current_date, 14)
    matches_30 = _matches_last_days(competitive_dates, current_date, 30)
    european_load = _matches_last_days(state.europe_dates, current_date, 30)

    return {
        "days_rest": days_since_last,
        "had_midweek_match": int(days_since_last <= 4),
        "matches_last_14_days": float(matches_14),
        "matches_last_30_days": float(matches_30),
        "days_since_last_match": days_since_last,
        "fixture_congestion_score": fixture_congestion_score(days_since_last, matches_14, matches_30),
        "played_europe_midweek": _played_europe_midweek(state.europe_dates, current_date),
        "days_since_europe_match": _days_since(state.europe_dates, current_date, default=60.0),
        "european_fixture_load": float(european_load),
    }


def build_fatigue_and_europe_features(
    matches: pd.DataFrame,
    european_fixtures: pd.DataFrame | None = None,
    include_europe_in_rest: bool = True,
) -> pd.DataFrame:
    """Create home/away historical schedule features without future information."""
    fixtures = european_fixtures if european_fixtures is not None else load_european_fixtures()
    europe_by_date = fixtures.copy()
    if not europe_by_date.empty:
        europe_by_date["Date"] = pd.to_datetime(europe_by_date["Date"])

    states: dict[str, ScheduleState] = {}
    rows: list[dict[str, float]] = []

    for _, match in matches.sort_values("Date").iterrows():
        current_date = pd.to_datetime(match["Date"])

        if not europe_by_date.empty:
            past_europe = europe_by_date[europe_by_date["Date"] < current_date]
            for _, fixture in past_europe.iterrows():
                team = fixture["team"]
                states.setdefault(team, ScheduleState(match_dates=[], europe_dates=[]))
                if fixture["Date"] not in states[team].europe_dates:
                    states[team].europe_dates.append(fixture["Date"])

        home_team = match["HomeTeam"]
        away_team = match["AwayTeam"]
        for team in (home_team, away_team):
            states.setdefault(team, ScheduleState(match_dates=[], europe_dates=[]))

        home = _team_schedule_features(states[home_team], current_date, include_europe_in_rest)
        away = _team_schedule_features(states[away_team], current_date, include_europe_in_rest)

        row = {}
        for feature, value in home.items():
            row[f"home_{feature}"] = value
        for feature, value in away.items():
            row[f"away_{feature}"] = value
        rows.append(row)

        states[home_team].match_dates.append(current_date)
        states[away_team].match_dates.append(current_date)

    return pd.DataFrame(rows)


def fatigue_feature_columns() -> list[str]:
    return [f"{side}_{feature}" for side in ("home", "away") for feature in FATIGUE_FEATURES]


def europe_feature_columns() -> list[str]:
    return [f"{side}_{feature}" for side in ("home", "away") for feature in EUROPE_FEATURES]
