from __future__ import annotations

from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd


DATA_DIR = Path("data")
NON_PL_MATCHES_PATH = DATA_DIR / "non_pl_matches.csv"
EUROPEAN_FIXTURES_PATH = DATA_DIR / "european_fixtures.csv"
CHAMPIONSHIP_2526_PATH = DATA_DIR / "championship_2526.csv"

COMPETITION_WEIGHTS = {
    "Premier League": 1.0,
    "Championship": 0.55,
    "Championship Playoff": 0.55,
    "Champions League": 0.80,
    "Europa League": 0.75,
    "Conference League": 0.70,
    "European Qualifier": 0.70,
    "Domestic Cup": 0.45,
    "Friendly": 0.25,
    "Pre-season Friendly": 0.25,
}

NON_PL_CONTEXT_COLUMNS = [
    "home_any_matches_last_14_days",
    "away_any_matches_last_14_days",
    "home_days_since_any_match",
    "away_days_since_any_match",
    "home_preseason_matches_last_60_days",
    "away_preseason_matches_last_60_days",
    "home_competitive_non_pl_matches_last_30_days",
    "away_competitive_non_pl_matches_last_30_days",
    "home_europe_qualifier_last_7_days",
    "away_europe_qualifier_last_7_days",
    "home_non_pl_points_equiv_last5",
    "away_non_pl_points_equiv_last5",
    "home_non_pl_goals_equiv_avg_last5",
    "away_non_pl_goals_equiv_avg_last5",
    "home_non_pl_shots_equiv_avg_last5",
    "away_non_pl_shots_equiv_avg_last5",
    "home_non_pl_context_available",
    "away_non_pl_context_available",
]


def _parse_date_series(values: pd.Series) -> pd.Series:
    return pd.to_datetime(values, dayfirst=True, errors="coerce").dt.date


def _competition_weight(competition: Any) -> float:
    name = str(competition or "").strip()
    return float(COMPETITION_WEIGHTS.get(name, 0.50))


def _points(result: str, is_home: bool) -> float:
    if result == "D":
        return 1.0
    if result == "H":
        return 3.0 if is_home else 0.0
    if result == "A":
        return 0.0 if is_home else 3.0
    return 0.0


def _looks_like_preseason(competition: Any) -> bool:
    text = str(competition or "").lower()
    return "friendly" in text or "pre-season" in text or "preseason" in text


def _looks_like_europe(competition: Any) -> bool:
    text = str(competition or "").lower()
    return any(token in text for token in ["champions league", "europa", "conference", "europe"])


def _is_competitive_non_pl(competition: Any) -> bool:
    return not _looks_like_preseason(competition)


def _empty_team_match_frame() -> pd.DataFrame:
    return pd.DataFrame(
        columns=[
            "Date",
            "team",
            "opponent",
            "competition",
            "source_file",
            "points",
            "goals_for",
            "shots_for",
            "weight",
        ]
    )


def _normalise_match_columns(frame: pd.DataFrame) -> pd.DataFrame:
    rename_map = {"date": "Date", "home_team": "HomeTeam", "away_team": "AwayTeam", "competition_name": "competition"}
    frame = frame.rename(columns={key: value for key, value in rename_map.items() if key in frame.columns}).copy()
    if "Date" not in frame.columns:
        raise ValueError("Non-PL match data must contain a Date/date column.")
    frame["Date"] = _parse_date_series(frame["Date"])
    return frame.dropna(subset=["Date"])


def _match_frame_to_team_rows(frame: pd.DataFrame, source_file: str, default_competition: str) -> pd.DataFrame:
    frame = _normalise_match_columns(frame)
    if {"HomeTeam", "AwayTeam"}.issubset(frame.columns):
        competition = frame["competition"] if "competition" in frame.columns else default_competition
        rows: list[dict[str, object]] = []
        for _, match in frame.iterrows():
            result = str(match.get("FTR", "") or "")
            weight = _competition_weight(match.get("competition", default_competition))
            home_shots = float(pd.to_numeric(pd.Series([match.get("HS", np.nan)]), errors="coerce").fillna(0.0).iloc[0])
            away_shots = float(pd.to_numeric(pd.Series([match.get("AS", np.nan)]), errors="coerce").fillna(0.0).iloc[0])
            rows.append(
                {
                    "Date": match["Date"],
                    "team": match["HomeTeam"],
                    "opponent": match["AwayTeam"],
                    "competition": match.get("competition", default_competition),
                    "source_file": source_file,
                    "points": _points(result, is_home=True),
                    "goals_for": float(match.get("FTHG", 0.0) or 0.0),
                    "shots_for": home_shots,
                    "weight": weight,
                }
            )
            rows.append(
                {
                    "Date": match["Date"],
                    "team": match["AwayTeam"],
                    "opponent": match["HomeTeam"],
                    "competition": match.get("competition", default_competition),
                    "source_file": source_file,
                    "points": _points(result, is_home=False),
                    "goals_for": float(match.get("FTAG", 0.0) or 0.0),
                    "shots_for": away_shots,
                    "weight": weight,
                }
            )
        return pd.DataFrame(rows)

    required_team_columns = {"team", "opponent", "competition"}
    if required_team_columns.issubset(frame.columns):
        output = frame.copy()
        output["source_file"] = source_file
        output["points"] = pd.to_numeric(output.get("points", 0.0), errors="coerce").fillna(0.0)
        output["goals_for"] = pd.to_numeric(output.get("goals_for", 0.0), errors="coerce").fillna(0.0)
        output["shots_for"] = pd.to_numeric(output.get("shots_for", 0.0), errors="coerce").fillna(0.0)
        output["weight"] = output["competition"].map(_competition_weight)
        return output[["Date", "team", "opponent", "competition", "source_file", "points", "goals_for", "shots_for", "weight"]]

    raise ValueError("Non-PL data must either be fixture-level or team-match-level rows.")


def load_non_pl_team_matches(include_championship: bool = True) -> pd.DataFrame:
    """Load optional non-Premier-League context rows.

    This function never invents matches. It only uses local files that already exist.
    Missing sources simply return an empty frame so experiments can document coverage.
    """
    frames: list[pd.DataFrame] = []

    if NON_PL_MATCHES_PATH.exists():
        raw = pd.read_csv(NON_PL_MATCHES_PATH)
        if not raw.empty:
            frames.append(_match_frame_to_team_rows(raw, NON_PL_MATCHES_PATH.name, "Non-PL"))

    if EUROPEAN_FIXTURES_PATH.exists():
        raw = pd.read_csv(EUROPEAN_FIXTURES_PATH)
        if not raw.empty:
            frames.append(_match_frame_to_team_rows(raw, EUROPEAN_FIXTURES_PATH.name, "European Qualifier"))

    if include_championship and CHAMPIONSHIP_2526_PATH.exists():
        raw = pd.read_csv(CHAMPIONSHIP_2526_PATH)
        if not raw.empty:
            raw = raw.copy()
            raw["competition"] = "Championship"
            frames.append(_match_frame_to_team_rows(raw, CHAMPIONSHIP_2526_PATH.name, "Championship"))

    if not frames:
        return _empty_team_match_frame()

    output = pd.concat(frames, ignore_index=True)
    output = output.dropna(subset=["Date", "team"])
    output = output[output["team"].astype(str).str.len() > 0]
    output = output.sort_values(["Date", "team"]).reset_index(drop=True)
    return output


def _side_context(history: pd.DataFrame, current_date) -> dict[str, float]:
    if history.empty:
        return {
            "any_matches_last_14_days": 0.0,
            "days_since_any_match": 14.0,
            "preseason_matches_last_60_days": 0.0,
            "competitive_non_pl_matches_last_30_days": 0.0,
            "europe_qualifier_last_7_days": 0.0,
            "non_pl_points_equiv_last5": 0.0,
            "non_pl_goals_equiv_avg_last5": 0.0,
            "non_pl_shots_equiv_avg_last5": 0.0,
            "non_pl_context_available": 0.0,
        }

    dated = history.copy()
    dated["days_ago"] = dated["Date"].map(lambda value: (current_date - value).days)
    positive = dated[dated["days_ago"] > 0]
    if positive.empty:
        return _side_context(pd.DataFrame(columns=history.columns), current_date)

    last5 = positive.tail(5)
    weighted_points = (last5["points"].astype(float) * last5["weight"].astype(float)).sum()
    weighted_goals = (last5["goals_for"].astype(float) * last5["weight"].astype(float)).mean()
    weighted_shots = (last5["shots_for"].astype(float) * last5["weight"].astype(float)).mean()

    return {
        "any_matches_last_14_days": float((positive["days_ago"] <= 14).sum()),
        "days_since_any_match": float(positive["days_ago"].min()),
        "preseason_matches_last_60_days": float(
            positive[(positive["days_ago"] <= 60) & positive["competition"].map(_looks_like_preseason)].shape[0]
        ),
        "competitive_non_pl_matches_last_30_days": float(
            positive[(positive["days_ago"] <= 30) & positive["competition"].map(_is_competitive_non_pl)].shape[0]
        ),
        "europe_qualifier_last_7_days": float(
            positive[(positive["days_ago"] <= 7) & positive["competition"].map(_looks_like_europe)].shape[0] > 0
        ),
        "non_pl_points_equiv_last5": float(weighted_points),
        "non_pl_goals_equiv_avg_last5": float(weighted_goals) if not np.isnan(weighted_goals) else 0.0,
        "non_pl_shots_equiv_avg_last5": float(weighted_shots) if not np.isnan(weighted_shots) else 0.0,
        "non_pl_context_available": 1.0,
    }


def build_non_pl_context_features(matches: pd.DataFrame, non_pl_team_matches: pd.DataFrame | None = None) -> pd.DataFrame:
    """Build pre-match non-PL context features without future leakage."""
    if non_pl_team_matches is None:
        non_pl_team_matches = load_non_pl_team_matches()

    if non_pl_team_matches.empty:
        return pd.DataFrame([{column: 0.0 for column in NON_PL_CONTEXT_COLUMNS} for _ in range(len(matches))])

    team_rows = {
        team: rows.sort_values("Date").reset_index(drop=True)
        for team, rows in non_pl_team_matches.groupby("team", sort=False)
    }

    feature_rows: list[dict[str, float]] = []
    ordered = matches.sort_values("Date").reset_index(drop=True)
    for _, match in ordered.iterrows():
        current_date = match["Date"]
        row: dict[str, float] = {}
        for side, team_column in [("home", "HomeTeam"), ("away", "AwayTeam")]:
            team = match[team_column]
            history = team_rows.get(team, _empty_team_match_frame())
            historical = history[history["Date"] < current_date]
            context = _side_context(historical, current_date)
            for key, value in context.items():
                row[f"{side}_{key}"] = value
        feature_rows.append(row)

    features = pd.DataFrame(feature_rows)
    for column in NON_PL_CONTEXT_COLUMNS:
        if column not in features.columns:
            features[column] = 0.0
    return features[NON_PL_CONTEXT_COLUMNS].fillna(0.0)


def non_pl_context_feature_columns() -> list[str]:
    return list(NON_PL_CONTEXT_COLUMNS)


def non_pl_source_coverage(non_pl_team_matches: pd.DataFrame) -> pd.DataFrame:
    if non_pl_team_matches.empty:
        return pd.DataFrame(
            columns=["source_file", "competition", "team_rows", "teams", "first_date", "last_date"]
        )
    grouped = (
        non_pl_team_matches.groupby(["source_file", "competition"], dropna=False)
        .agg(
            team_rows=("team", "size"),
            teams=("team", "nunique"),
            first_date=("Date", "min"),
            last_date=("Date", "max"),
        )
        .reset_index()
    )
    return grouped.sort_values(["source_file", "competition"]).reset_index(drop=True)
