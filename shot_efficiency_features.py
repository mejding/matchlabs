from __future__ import annotations

from collections import defaultdict

import numpy as np
import pandas as pd

from train_model import SEASONS, download_csv, load_matches_with_xg


ROLLING_WINDOWS = [5, 10]

SHOT_VOLUME_BASE = [
    "shots_avg",
    "shots_on_target_avg",
]
SHOT_EFFICIENCY_BASE = [
    "shot_accuracy",
    "goals_per_shot",
    "goals_per_shot_on_target",
    "xg_per_shot",
    "goals_minus_xg",
]
SHOT_DEFENSIVE_BASE = [
    "shots_allowed_avg",
    "shots_on_target_allowed_avg",
    "opponent_shot_accuracy",
    "xga_per_shot_allowed",
]


def shot_volume_columns() -> list[str]:
    return _side_window_columns(SHOT_VOLUME_BASE)


def shot_efficiency_columns() -> list[str]:
    return _side_window_columns(SHOT_EFFICIENCY_BASE)


def shot_defensive_columns() -> list[str]:
    return _side_window_columns(SHOT_DEFENSIVE_BASE)


def all_shot_feature_columns() -> list[str]:
    return shot_volume_columns() + shot_efficiency_columns() + shot_defensive_columns()


def _side_window_columns(base_features: list[str]) -> list[str]:
    columns: list[str] = []
    for side in ("home", "away"):
        for feature in base_features:
            for window in ROLLING_WINDOWS:
                columns.append(f"{side}_{feature}_last{window}")
            columns.append(f"{side}_{feature}_season")
    return columns


def _safe_divide(numerator: float, denominator: float) -> float:
    return float(numerator / denominator) if denominator and denominator > 0 else 0.0


def _mean(values: list[float]) -> float:
    return float(np.mean(values)) if values else 0.0


def load_matches_with_xg_and_shots() -> pd.DataFrame:
    matches = load_matches_with_xg()
    frames = []
    for season in SEASONS:
        raw = pd.read_csv(download_csv(season))
        required = ["Date", "HomeTeam", "AwayTeam", "HS", "AS", "HST", "AST"]
        missing = [column for column in required if column not in raw.columns]
        if missing:
            raise ValueError(f"Missing shot columns in season {season}: {missing}")
        raw = raw[required].copy()
        raw["Season"] = season
        raw["Date"] = pd.to_datetime(raw["Date"], dayfirst=True, errors="coerce").dt.date
        frames.append(raw)
    shots = pd.concat(frames, ignore_index=True)
    merged = matches.merge(shots, on=["Season", "Date", "HomeTeam", "AwayTeam"], how="left", validate="one_to_one")
    missing_shots = merged[["HS", "AS", "HST", "AST"]].isna().any(axis=1)
    if missing_shots.any():
        examples = merged.loc[missing_shots, ["Season", "Date", "HomeTeam", "AwayTeam"]].head(10).to_dict("records")
        raise ValueError(f"Could not match shot data for {int(missing_shots.sum())} rows. Examples: {examples}")
    for column in ["HS", "AS", "HST", "AST"]:
        merged[column] = pd.to_numeric(merged[column], errors="coerce").fillna(0.0)
    return merged


def _team_summary(history: list[dict[str, float]], season: str, window: int | None) -> dict[str, float]:
    rows = [row for row in history if window is None or True]
    if window is None:
        rows = [row for row in rows if str(row["season"]) == str(season)]
    else:
        rows = rows[-window:]

    shots = sum(row["shots"] for row in rows)
    shots_on_target = sum(row["shots_on_target"] for row in rows)
    goals = sum(row["goals"] for row in rows)
    xg = sum(row["xg"] for row in rows)
    shots_allowed = sum(row["shots_allowed"] for row in rows)
    shots_on_target_allowed = sum(row["shots_on_target_allowed"] for row in rows)
    xga = sum(row["xga"] for row in rows)

    count = len(rows)
    return {
        "shots_avg": _safe_divide(shots, count),
        "shots_on_target_avg": _safe_divide(shots_on_target, count),
        "shot_accuracy": _safe_divide(shots_on_target, shots),
        "goals_per_shot": _safe_divide(goals, shots),
        "goals_per_shot_on_target": _safe_divide(goals, shots_on_target),
        "xg_per_shot": _safe_divide(xg, shots),
        "goals_minus_xg": _safe_divide(goals - xg, count),
        "shots_allowed_avg": _safe_divide(shots_allowed, count),
        "shots_on_target_allowed_avg": _safe_divide(shots_on_target_allowed, count),
        "opponent_shot_accuracy": _safe_divide(shots_on_target_allowed, shots_allowed),
        "xga_per_shot_allowed": _safe_divide(xga, shots_allowed),
    }


def _feature_block(history: list[dict[str, float]], season: str) -> dict[str, float]:
    block: dict[str, float] = {}
    for window in ROLLING_WINDOWS:
        summary = _team_summary(history, season, window)
        for feature, value in summary.items():
            block[f"{feature}_last{window}"] = value
    season_summary = _team_summary(history, season, None)
    for feature, value in season_summary.items():
        block[f"{feature}_season"] = value
    return block


def build_shot_efficiency_features(matches: pd.DataFrame) -> pd.DataFrame:
    """Build rolling shot features using only matches before each fixture."""
    rows: list[dict[str, float]] = []
    team_history: dict[str, list[dict[str, float]]] = defaultdict(list)
    ordered = matches.sort_values("Date").reset_index(drop=True)

    for _, match in ordered.iterrows():
        home_team = match["HomeTeam"]
        away_team = match["AwayTeam"]
        season = str(match["Season"])

        home_block = _feature_block(team_history[home_team], season)
        away_block = _feature_block(team_history[away_team], season)
        row: dict[str, float] = {}
        for feature, value in home_block.items():
            row[f"home_{feature}"] = value
        for feature, value in away_block.items():
            row[f"away_{feature}"] = value
        rows.append(row)

        home_record = {
            "season": season,
            "shots": float(match["HS"]),
            "shots_on_target": float(match["HST"]),
            "goals": float(match["FTHG"]),
            "xg": float(match["home_xg"]),
            "shots_allowed": float(match["AS"]),
            "shots_on_target_allowed": float(match["AST"]),
            "xga": float(match["away_xg"]),
        }
        away_record = {
            "season": season,
            "shots": float(match["AS"]),
            "shots_on_target": float(match["AST"]),
            "goals": float(match["FTAG"]),
            "xg": float(match["away_xg"]),
            "shots_allowed": float(match["HS"]),
            "shots_on_target_allowed": float(match["HST"]),
            "xga": float(match["home_xg"]),
        }
        team_history[home_team].append(home_record)
        team_history[away_team].append(away_record)

    features = pd.DataFrame(rows)
    for column in all_shot_feature_columns():
        if column not in features.columns:
            features[column] = 0.0
    return features[all_shot_feature_columns()].fillna(0.0)
