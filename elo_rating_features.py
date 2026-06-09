from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

import numpy as np
import pandas as pd


ELO_HISTORY_PATH = Path("data") / "elo_history.csv"


@dataclass(frozen=True)
class EloConfig:
    k_factor: float = 20.0
    home_advantage: float = 50.0
    margin_of_victory: bool = False
    initial_rating: float = 1500.0
    season_carryover: float = 1.0

    @property
    def name(self) -> str:
        mov = "mov" if self.margin_of_victory else "nomov"
        carry = int(round(self.season_carryover * 100))
        return f"k{int(self.k_factor)}_ha{int(self.home_advantage)}_{mov}_carry{carry}"


def expected_score(rating_a: float, rating_b: float) -> float:
    return float(1.0 / (1.0 + 10.0 ** ((rating_b - rating_a) / 400.0)))


def actual_home_score(result: str) -> float:
    if result == "H":
        return 1.0
    if result == "A":
        return 0.0
    return 0.5


def margin_multiplier(goal_diff: float, rating_diff: float, enabled: bool) -> float:
    if not enabled:
        return 1.0
    absolute_margin = abs(goal_diff)
    if absolute_margin <= 1:
        return 1.0
    return float(np.log(absolute_margin + 1.0) * (2.2 / ((abs(rating_diff) * 0.001) + 2.2)))


def gap_bucket(elo_difference: float) -> int:
    absolute = abs(elo_difference)
    if absolute < 50:
        return 0
    if absolute < 100:
        return 1 if elo_difference > 0 else -1
    if absolute < 200:
        return 2 if elo_difference > 0 else -2
    return 3 if elo_difference > 0 else -3


def _recent_change(values: list[float], current: float, window: int = 5) -> float:
    if len(values) < window:
        return 0.0
    return float(current - values[-window])


def build_elo_features(matches: pd.DataFrame, config: EloConfig) -> tuple[pd.DataFrame, pd.DataFrame]:
    ratings: dict[str, float] = {}
    rating_history: dict[str, list[float]] = {}
    feature_rows = []
    history_rows = []
    previous_season: str | None = None

    ordered = matches.sort_values("Date").reset_index(drop=True)
    for index, match in ordered.iterrows():
        current_season = str(match["Season"])
        if previous_season is not None and current_season != previous_season and config.season_carryover < 1.0:
            ratings = {
                team: config.initial_rating + config.season_carryover * (rating - config.initial_rating)
                for team, rating in ratings.items()
            }
            rating_history = {team: values + [float(ratings[team])] for team, values in rating_history.items()}
        previous_season = current_season

        home_team = match["HomeTeam"]
        away_team = match["AwayTeam"]
        for team in (home_team, away_team):
            ratings.setdefault(team, config.initial_rating)
            rating_history.setdefault(team, [])

        home_elo = float(ratings[home_team])
        away_elo = float(ratings[away_team])
        elo_difference = home_elo - away_elo
        home_change = _recent_change(rating_history[home_team], home_elo)
        away_change = _recent_change(rating_history[away_team], away_elo)
        rolling_elo_form = home_change - away_change

        feature_rows.append(
            {
                "home_elo": home_elo,
                "away_elo": away_elo,
                "elo_difference": elo_difference,
                "elo_ratio": home_elo / away_elo if away_elo else 1.0,
                "elo_gap_bucket": float(gap_bucket(elo_difference)),
                "elo_recent_change": rolling_elo_form,
                "home_elo_trend": home_change,
                "away_elo_trend": away_change,
                "rolling_elo_form": rolling_elo_form,
            }
        )
        history_rows.append(
            {
                "match_index": index,
                "Season": match["Season"],
                "Date": match["Date"],
                "HomeTeam": home_team,
                "AwayTeam": away_team,
                "home_elo_before_match": home_elo,
                "away_elo_before_match": away_elo,
                "elo_difference": elo_difference,
                "elo_config": config.name,
            }
        )

        adjusted_home = home_elo + config.home_advantage
        expected_home = expected_score(adjusted_home, away_elo)
        actual_home = actual_home_score(match["FTR"])
        goal_diff = float(match["FTHG"] - match["FTAG"])
        multiplier = margin_multiplier(goal_diff, adjusted_home - away_elo, config.margin_of_victory)
        change = config.k_factor * multiplier * (actual_home - expected_home)
        ratings[home_team] = home_elo + change
        ratings[away_team] = away_elo - change
        rating_history[home_team].append(float(ratings[home_team]))
        rating_history[away_team].append(float(ratings[away_team]))

    features = pd.DataFrame(feature_rows)
    history = pd.DataFrame(history_rows)
    ELO_HISTORY_PATH.parent.mkdir(exist_ok=True)
    history.to_csv(ELO_HISTORY_PATH, index=False)
    return features, history


def build_current_elo_state(matches: pd.DataFrame, config: EloConfig) -> dict[str, dict[str, object]]:
    ratings: dict[str, float] = {}
    rating_history: dict[str, list[float]] = {}
    previous_season: str | None = None

    ordered = matches.sort_values("Date").reset_index(drop=True)
    for _, match in ordered.iterrows():
        current_season = str(match["Season"])
        if previous_season is not None and current_season != previous_season and config.season_carryover < 1.0:
            ratings = {
                team: config.initial_rating + config.season_carryover * (rating - config.initial_rating)
                for team, rating in ratings.items()
            }
            rating_history = {team: values + [float(ratings[team])] for team, values in rating_history.items()}
        previous_season = current_season

        home_team = match["HomeTeam"]
        away_team = match["AwayTeam"]
        for team in (home_team, away_team):
            ratings.setdefault(team, config.initial_rating)
            rating_history.setdefault(team, [])

        home_elo = float(ratings[home_team])
        away_elo = float(ratings[away_team])
        adjusted_home = home_elo + config.home_advantage
        expected_home = expected_score(adjusted_home, away_elo)
        actual_home = actual_home_score(match["FTR"])
        goal_diff = float(match["FTHG"] - match["FTAG"])
        multiplier = margin_multiplier(goal_diff, adjusted_home - away_elo, config.margin_of_victory)
        change = config.k_factor * multiplier * (actual_home - expected_home)
        ratings[home_team] = home_elo + change
        ratings[away_team] = away_elo - change
        rating_history[home_team].append(float(ratings[home_team]))
        rating_history[away_team].append(float(ratings[away_team]))

    return {
        team: {
            "rating": float(rating),
            "history": rating_history.get(team, []).copy(),
        }
        for team, rating in ratings.items()
    }


def build_prediction_elo_row(home_team: str, away_team: str, elo_state: dict[str, dict[str, object]], initial_rating: float = 1500.0) -> dict[str, float]:
    home = elo_state.get(home_team, {"rating": initial_rating, "history": []})
    away = elo_state.get(away_team, {"rating": initial_rating, "history": []})
    home_elo = float(home.get("rating", initial_rating))
    away_elo = float(away.get("rating", initial_rating))
    home_history = [float(value) for value in home.get("history", [])]
    away_history = [float(value) for value in away.get("history", [])]
    home_change = _recent_change(home_history, home_elo)
    away_change = _recent_change(away_history, away_elo)
    rolling_elo_form = home_change - away_change
    elo_difference = home_elo - away_elo
    return {
        "home_elo": home_elo,
        "away_elo": away_elo,
        "elo_difference": elo_difference,
        "elo_ratio": home_elo / away_elo if away_elo else 1.0,
        "elo_gap_bucket": float(gap_bucket(elo_difference)),
        "elo_recent_change": rolling_elo_form,
        "home_elo_trend": home_change,
        "away_elo_trend": away_change,
        "rolling_elo_form": rolling_elo_form,
    }


def elo_feature_columns() -> list[str]:
    return [
        "home_elo",
        "away_elo",
        "elo_difference",
        "elo_ratio",
        "elo_gap_bucket",
        "elo_recent_change",
        "home_elo_trend",
        "away_elo_trend",
        "rolling_elo_form",
    ]
