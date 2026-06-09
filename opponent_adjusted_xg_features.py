from __future__ import annotations

from collections import defaultdict
from dataclasses import dataclass
from math import factorial

import numpy as np
import pandas as pd


RATING_WINDOWS = [5, 10]
PRIMARY_WINDOW = "ewm"

RATING_FEATURE_COLUMNS = [
    "home_xg_attack_rating",
    "away_xg_attack_rating",
    "home_xg_defense_rating",
    "away_xg_defense_rating",
    "home_attack_vs_away_defense",
    "away_attack_vs_home_defense",
    "attack_defense_matchup_score",
    "home_xg_attack_rating_last5",
    "away_xg_attack_rating_last5",
    "home_xg_defense_rating_last5",
    "away_xg_defense_rating_last5",
    "home_xg_attack_rating_last10",
    "away_xg_attack_rating_last10",
    "home_xg_defense_rating_last10",
    "away_xg_defense_rating_last10",
    "home_xg_attack_rating_season",
    "away_xg_attack_rating_season",
    "home_xg_defense_rating_season",
    "away_xg_defense_rating_season",
]
EXPECTED_GOALS_FEATURE_COLUMNS = [
    "expected_home_goals_model",
    "expected_away_goals_model",
    "expected_goal_diff_model",
]
POISSON_FEATURE_COLUMNS = [
    "poisson_home_win_prob",
    "poisson_draw_prob",
    "poisson_away_win_prob",
]
OPPONENT_ADJUSTED_XG_FEATURE_COLUMNS = RATING_FEATURE_COLUMNS + EXPECTED_GOALS_FEATURE_COLUMNS + POISSON_FEATURE_COLUMNS


@dataclass(frozen=True)
class XgRatingConfig:
    home_advantage_factor: float = 1.08
    away_factor: float = 0.96
    ewm_alpha: float = 0.35
    max_poisson_goals: int = 10


def _safe_mean(values: list[float], default: float = 1.0) -> float:
    return float(np.mean(values)) if values else default


def _ewm(values: list[float], alpha: float, default: float = 1.0) -> float:
    if not values:
        return default
    current = float(values[0])
    for value in values[1:]:
        current = alpha * float(value) + (1.0 - alpha) * current
    return float(current)


def _team_rating_block(history: list[dict[str, float]], season: str, league_avg_xg: float, config: XgRatingConfig) -> dict[str, float]:
    attack_values = [row["adjusted_attack_xg"] for row in history]
    defense_values = [row["adjusted_defense_xga"] for row in history]

    def relative(values: list[float], *, window: int | None = None, season_only: bool = False, ewm: bool = False) -> tuple[float, float]:
        selected_rows = history
        if season_only:
            selected_rows = [row for row in selected_rows if str(row["season"]) == str(season)]
        if window is not None:
            selected_rows = selected_rows[-window:]
        attacks = [row["adjusted_attack_xg"] for row in selected_rows]
        defenses = [row["adjusted_defense_xga"] for row in selected_rows]
        if ewm:
            attack = _ewm(attack_values, config.ewm_alpha, league_avg_xg)
            defense = _ewm(defense_values, config.ewm_alpha, league_avg_xg)
        else:
            attack = _safe_mean(attacks, league_avg_xg)
            defense = _safe_mean(defenses, league_avg_xg)
        return attack / league_avg_xg, defense / league_avg_xg

    attack_ewm, defense_ewm = relative([], ewm=True)
    attack_last5, defense_last5 = relative([], window=5)
    attack_last10, defense_last10 = relative([], window=10)
    attack_season, defense_season = relative([], season_only=True)
    return {
        "attack": attack_ewm,
        "defense": defense_ewm,
        "attack_last5": attack_last5,
        "defense_last5": defense_last5,
        "attack_last10": attack_last10,
        "defense_last10": defense_last10,
        "attack_season": attack_season,
        "defense_season": defense_season,
    }


def _poisson_pmf(lam: float, max_goals: int) -> np.ndarray:
    lam = max(float(lam), 0.05)
    values = [np.exp(-lam) * (lam**goals) / factorial(goals) for goals in range(max_goals + 1)]
    probs = np.asarray(values, dtype=float)
    return probs / probs.sum()


def poisson_outcome_probabilities(home_xg: float, away_xg: float, max_goals: int = 10) -> tuple[float, float, float]:
    home_probs = _poisson_pmf(home_xg, max_goals)
    away_probs = _poisson_pmf(away_xg, max_goals)
    matrix = np.outer(home_probs, away_probs)
    home_win = float(np.tril(matrix, -1).sum())
    draw = float(np.trace(matrix))
    away_win = float(np.triu(matrix, 1).sum())
    total = home_win + draw + away_win
    return home_win / total, draw / total, away_win / total


def build_opponent_adjusted_xg_features(
    matches: pd.DataFrame,
    config: XgRatingConfig | None = None,
) -> pd.DataFrame:
    """Build opponent-adjusted xG ratings using only pre-match history.

    Formula summary:
    - opponent attack strength before match = opponent adjusted attack xG / league average xG.
    - opponent defense weakness before match = opponent adjusted xGA conceded / league average xG.
    - adjusted attack xG for a completed match = team xG / opponent defense weakness before kickoff.
    - adjusted defense xGA for a completed match = xG conceded / opponent attack strength before kickoff.
    - ratings are relative to league average, so 1.10 attack means 10% above league average and 0.90 defense means
      10% better than league average at suppressing xG.
    """
    config = config or XgRatingConfig()
    ordered = matches.sort_values("Date").reset_index(drop=True)
    team_history: dict[str, list[dict[str, float]]] = defaultdict(list)
    league_xg_history: list[float] = []
    home_xg_history: list[float] = []
    away_xg_history: list[float] = []
    rows: list[dict[str, float]] = []

    for _, match in ordered.iterrows():
        home_team = match["HomeTeam"]
        away_team = match["AwayTeam"]
        season = str(match["Season"])
        league_avg_xg = _safe_mean(league_xg_history, default=1.35)
        league_home_xg = _safe_mean(home_xg_history, default=1.45)
        league_away_xg = _safe_mean(away_xg_history, default=1.20)

        home_block = _team_rating_block(team_history[home_team], season, league_avg_xg, config)
        away_block = _team_rating_block(team_history[away_team], season, league_avg_xg, config)

        expected_home = league_home_xg * home_block["attack"] * away_block["defense"] * config.home_advantage_factor
        expected_away = league_away_xg * away_block["attack"] * home_block["defense"] * config.away_factor
        expected_home = float(np.clip(expected_home, 0.15, 4.5))
        expected_away = float(np.clip(expected_away, 0.15, 4.5))
        poisson_home, poisson_draw, poisson_away = poisson_outcome_probabilities(
            expected_home,
            expected_away,
            max_goals=config.max_poisson_goals,
        )

        rows.append(
            {
                "home_xg_attack_rating": home_block["attack"],
                "away_xg_attack_rating": away_block["attack"],
                "home_xg_defense_rating": home_block["defense"],
                "away_xg_defense_rating": away_block["defense"],
                "home_attack_vs_away_defense": home_block["attack"] * away_block["defense"],
                "away_attack_vs_home_defense": away_block["attack"] * home_block["defense"],
                "attack_defense_matchup_score": (home_block["attack"] * away_block["defense"])
                - (away_block["attack"] * home_block["defense"]),
                "home_xg_attack_rating_last5": home_block["attack_last5"],
                "away_xg_attack_rating_last5": away_block["attack_last5"],
                "home_xg_defense_rating_last5": home_block["defense_last5"],
                "away_xg_defense_rating_last5": away_block["defense_last5"],
                "home_xg_attack_rating_last10": home_block["attack_last10"],
                "away_xg_attack_rating_last10": away_block["attack_last10"],
                "home_xg_defense_rating_last10": home_block["defense_last10"],
                "away_xg_defense_rating_last10": away_block["defense_last10"],
                "home_xg_attack_rating_season": home_block["attack_season"],
                "away_xg_attack_rating_season": away_block["attack_season"],
                "home_xg_defense_rating_season": home_block["defense_season"],
                "away_xg_defense_rating_season": away_block["defense_season"],
                "expected_home_goals_model": expected_home,
                "expected_away_goals_model": expected_away,
                "expected_goal_diff_model": expected_home - expected_away,
                "poisson_home_win_prob": poisson_home,
                "poisson_draw_prob": poisson_draw,
                "poisson_away_win_prob": poisson_away,
            }
        )

        home_attack_strength = home_block["attack"]
        away_attack_strength = away_block["attack"]
        home_defense_weakness = home_block["defense"]
        away_defense_weakness = away_block["defense"]
        home_xg = float(match["home_xg"])
        away_xg = float(match["away_xg"])
        team_history[home_team].append(
            {
                "season": season,
                "adjusted_attack_xg": home_xg / max(away_defense_weakness, 0.25),
                "adjusted_defense_xga": away_xg / max(away_attack_strength, 0.25),
            }
        )
        team_history[away_team].append(
            {
                "season": season,
                "adjusted_attack_xg": away_xg / max(home_defense_weakness, 0.25),
                "adjusted_defense_xga": home_xg / max(home_attack_strength, 0.25),
            }
        )
        league_xg_history.extend([home_xg, away_xg])
        home_xg_history.append(home_xg)
        away_xg_history.append(away_xg)

    return pd.DataFrame(rows)[OPPONENT_ADJUSTED_XG_FEATURE_COLUMNS].fillna(1.0)
