from __future__ import annotations

from collections import defaultdict
from dataclasses import dataclass

import numpy as np
import pandas as pd

from opponent_adjusted_xg_features import build_opponent_adjusted_xg_features
from train_model import RESULT_TO_LABEL, points_for_team


WEIGHTING_SCHEMES = ["linear", "exponential", "halflife3", "halflife5"]

WEIGHTED_BASE_FEATURES = [
    "points_weighted",
    "goals_scored_weighted",
    "xg_weighted",
    "xga_weighted",
    "xg_diff_weighted",
    "shots_weighted",
    "shots_on_target_weighted",
    "attack_rating_weighted",
    "defense_rating_weighted",
]


def weighted_feature_columns(scheme: str) -> list[str]:
    return [f"{side}_{feature}_{scheme}" for side in ("home", "away") for feature in WEIGHTED_BASE_FEATURES]


def all_weighted_feature_columns() -> list[str]:
    columns: list[str] = []
    for scheme in WEIGHTING_SCHEMES:
        columns.extend(weighted_feature_columns(scheme))
    return columns


@dataclass(frozen=True)
class WeightingConfig:
    window: int = 5
    exponential_decay: float = 0.75


def recency_weights(length: int, scheme: str, config: WeightingConfig | None = None) -> np.ndarray:
    config = config or WeightingConfig()
    if length <= 0:
        return np.asarray([], dtype=float)
    if scheme == "linear":
        weights = np.arange(1, length + 1, dtype=float)
    elif scheme == "exponential":
        ages = np.arange(length - 1, -1, -1, dtype=float)
        weights = np.power(config.exponential_decay, ages)
    elif scheme == "halflife3":
        ages = np.arange(length - 1, -1, -1, dtype=float)
        weights = np.power(0.5, ages / 3.0)
    elif scheme == "halflife5":
        ages = np.arange(length - 1, -1, -1, dtype=float)
        weights = np.power(0.5, ages / 5.0)
    else:
        raise ValueError(f"Unknown weighting scheme: {scheme}")
    return weights / weights.sum()


def _weighted_average(values: list[float], scheme: str, config: WeightingConfig) -> float:
    window_values = values[-config.window :]
    if not window_values:
        return 0.0
    weights = recency_weights(len(window_values), scheme, config)
    return float(np.dot(np.asarray(window_values, dtype=float), weights))


def _history_block(history: dict[str, list[float]], scheme: str, config: WeightingConfig) -> dict[str, float]:
    points = _weighted_average(history["points"], scheme, config)
    goals = _weighted_average(history["goals_scored"], scheme, config)
    xg = _weighted_average(history["xg"], scheme, config)
    xga = _weighted_average(history["xga"], scheme, config)
    shots = _weighted_average(history["shots"], scheme, config)
    shots_on_target = _weighted_average(history["shots_on_target"], scheme, config)
    attack_rating = _weighted_average(history["attack_rating"], scheme, config)
    defense_rating = _weighted_average(history["defense_rating"], scheme, config)
    return {
        "points_weighted": points,
        "goals_scored_weighted": goals,
        "xg_weighted": xg,
        "xga_weighted": xga,
        "xg_diff_weighted": xg - xga,
        "shots_weighted": shots,
        "shots_on_target_weighted": shots_on_target,
        "attack_rating_weighted": attack_rating,
        "defense_rating_weighted": defense_rating,
    }


def build_recency_weighted_features(matches: pd.DataFrame, config: WeightingConfig | None = None) -> pd.DataFrame:
    """Build weighted features using only matches before each fixture."""
    config = config or WeightingConfig()
    ordered = matches.sort_values("Date").reset_index(drop=True)
    ratings = build_opponent_adjusted_xg_features(ordered)
    history: dict[str, dict[str, list[float]]] = defaultdict(
        lambda: {
            "points": [],
            "goals_scored": [],
            "xg": [],
            "xga": [],
            "shots": [],
            "shots_on_target": [],
            "attack_rating": [],
            "defense_rating": [],
        }
    )
    rows: list[dict[str, float]] = []

    for idx, match in ordered.iterrows():
        home_team = match["HomeTeam"]
        away_team = match["AwayTeam"]
        row: dict[str, float] = {}
        for scheme in WEIGHTING_SCHEMES:
            home_block = _history_block(history[home_team], scheme, config)
            away_block = _history_block(history[away_team], scheme, config)
            for feature, value in home_block.items():
                row[f"home_{feature}_{scheme}"] = value
            for feature, value in away_block.items():
                row[f"away_{feature}_{scheme}"] = value
        rows.append(row)

        home_xg = float(match["home_xg"])
        away_xg = float(match["away_xg"])
        home_shots = float(match.get("HS", 0.0))
        away_shots = float(match.get("AS", 0.0))
        home_sot = float(match.get("HST", 0.0))
        away_sot = float(match.get("AST", 0.0))
        home_rating = ratings.iloc[idx]

        history[home_team]["points"].append(float(points_for_team(match, home_team)))
        history[away_team]["points"].append(float(points_for_team(match, away_team)))
        history[home_team]["goals_scored"].append(float(match["FTHG"]))
        history[away_team]["goals_scored"].append(float(match["FTAG"]))
        history[home_team]["xg"].append(home_xg)
        history[away_team]["xg"].append(away_xg)
        history[home_team]["xga"].append(away_xg)
        history[away_team]["xga"].append(home_xg)
        history[home_team]["shots"].append(home_shots)
        history[away_team]["shots"].append(away_shots)
        history[home_team]["shots_on_target"].append(home_sot)
        history[away_team]["shots_on_target"].append(away_sot)
        history[home_team]["attack_rating"].append(float(home_rating["home_xg_attack_rating"]))
        history[away_team]["attack_rating"].append(float(home_rating["away_xg_attack_rating"]))
        history[home_team]["defense_rating"].append(float(home_rating["home_xg_defense_rating"]))
        history[away_team]["defense_rating"].append(float(home_rating["away_xg_defense_rating"]))

    features = pd.DataFrame(rows)
    for column in all_weighted_feature_columns():
        if column not in features.columns:
            features[column] = 0.0
    features["target"] = ordered["FTR"].map(RESULT_TO_LABEL).astype(int)
    return features[all_weighted_feature_columns() + ["target"]].fillna(0.0)
