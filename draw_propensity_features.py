from __future__ import annotations

from collections import defaultdict

import numpy as np
import pandas as pd


DRAW_PROPENSITY_FEATURE_COLUMNS = [
    "home_draw_rate_last10",
    "away_draw_rate_last10",
    "combined_draw_rate_last10",
    "home_draw_rate_season",
    "away_draw_rate_season",
    "combined_draw_rate_season",
    "team_strength_similarity",
    "xg_diff_similarity",
    "form_points_similarity",
    "low_total_xg_profile",
    "low_total_goals_profile",
    "low_total_shots_on_target_profile",
    "draw_propensity_score",
]


def draw_propensity_feature_columns() -> list[str]:
    return DRAW_PROPENSITY_FEATURE_COLUMNS.copy()


def _mean(values: list[float]) -> float:
    return float(np.mean(values)) if values else 0.0


def _rate(values: list[float], window: int | None = None) -> float:
    subset = values if window is None else values[-window:]
    return _mean(subset)


def _similarity_gap(home_value: float, away_value: float, scale: float) -> float:
    return float(1.0 / (1.0 + abs(home_value - away_value) / scale))


def _low_total_profile(total_value: float, scale: float) -> float:
    return float(1.0 / (1.0 + total_value / scale))


def _season_values(history: list[dict[str, float]], season: str, key: str) -> list[float]:
    return [float(row[key]) for row in history if str(row["season"]) == str(season)]


def _last_values(history: list[dict[str, float]], key: str, window: int = 5) -> list[float]:
    return [float(row[key]) for row in history[-window:]]


def _team_record(match: pd.Series, is_home: bool) -> dict[str, float | str]:
    if is_home:
        goals_for = float(match["FTHG"])
        goals_against = float(match["FTAG"])
        xg_for = float(match["home_xg"])
        xg_against = float(match["away_xg"])
        shots_on_target = float(match.get("HST", 0.0))
    else:
        goals_for = float(match["FTAG"])
        goals_against = float(match["FTHG"])
        xg_for = float(match["away_xg"])
        xg_against = float(match["home_xg"])
        shots_on_target = float(match.get("AST", 0.0))
    return {
        "season": str(match["Season"]),
        "draw": float(match["FTR"] == "D"),
        "points": 3.0 if goals_for > goals_against else 1.0 if goals_for == goals_against else 0.0,
        "goals_for": goals_for,
        "goals_against": goals_against,
        "xg_for": xg_for,
        "xg_against": xg_against,
        "shots_on_target": shots_on_target,
    }


def build_draw_propensity_features(matches: pd.DataFrame) -> pd.DataFrame:
    rows: list[dict[str, float]] = []
    history: dict[str, list[dict[str, float | str]]] = defaultdict(list)
    ordered = matches.sort_values("Date").reset_index(drop=True)

    for _, match in ordered.iterrows():
        home_team = str(match["HomeTeam"])
        away_team = str(match["AwayTeam"])
        season = str(match["Season"])
        home = history[home_team]
        away = history[away_team]

        home_draws = [float(row["draw"]) for row in home]
        away_draws = [float(row["draw"]) for row in away]
        home_season_draws = _season_values(home, season, "draw")
        away_season_draws = _season_values(away, season, "draw")

        home_xg_diff = _mean(_last_values(home, "xg_for")) - _mean(_last_values(home, "xg_against"))
        away_xg_diff = _mean(_last_values(away, "xg_for")) - _mean(_last_values(away, "xg_against"))
        home_points = _mean(_last_values(home, "points"))
        away_points = _mean(_last_values(away, "points"))
        total_xg = _mean(_last_values(home, "xg_for")) + _mean(_last_values(away, "xg_for"))
        total_goals = _mean(_last_values(home, "goals_for")) + _mean(_last_values(away, "goals_for"))
        total_sot = _mean(_last_values(home, "shots_on_target")) + _mean(_last_values(away, "shots_on_target"))

        row = {
            "home_draw_rate_last10": _rate(home_draws, 10),
            "away_draw_rate_last10": _rate(away_draws, 10),
            "combined_draw_rate_last10": (_rate(home_draws, 10) + _rate(away_draws, 10)) / 2.0,
            "home_draw_rate_season": _rate(home_season_draws),
            "away_draw_rate_season": _rate(away_season_draws),
            "combined_draw_rate_season": (_rate(home_season_draws) + _rate(away_season_draws)) / 2.0,
            "team_strength_similarity": _similarity_gap(home_xg_diff, away_xg_diff, 1.0),
            "xg_diff_similarity": _similarity_gap(home_xg_diff, away_xg_diff, 0.75),
            "form_points_similarity": _similarity_gap(home_points, away_points, 1.25),
            "low_total_xg_profile": _low_total_profile(total_xg, 2.5),
            "low_total_goals_profile": _low_total_profile(total_goals, 2.5),
            "low_total_shots_on_target_profile": _low_total_profile(total_sot, 8.0),
        }
        row["draw_propensity_score"] = float(
            np.mean(
                [
                    row["combined_draw_rate_last10"],
                    row["combined_draw_rate_season"],
                    row["team_strength_similarity"],
                    row["low_total_xg_profile"],
                    row["low_total_goals_profile"],
                ]
            )
        )
        rows.append(row)

        history[home_team].append(_team_record(match, is_home=True))
        history[away_team].append(_team_record(match, is_home=False))

    return pd.DataFrame(rows, columns=DRAW_PROPENSITY_FEATURE_COLUMNS).fillna(0.0)
