from __future__ import annotations

from pathlib import Path

import numpy as np
import pandas as pd
from sklearn.cluster import KMeans
from sklearn.preprocessing import StandardScaler

from tactical_data import STYLE_EMBEDDINGS_PATH, TACTICAL_METRICS, tactical_data_note


ARCHETYPE_NAMES = {
    0: "Balanced",
    1: "Possession Dominant",
    2: "High Press",
    3: "Direct Counterattack",
    4: "Low Block",
    5: "Cross Heavy",
}
ROLLING_WINDOWS = [5, 10]


def tactical_profile_columns() -> list[str]:
    columns = []
    for side in ("home", "away"):
        for metric in TACTICAL_METRICS:
            columns.extend([f"{side}_{metric}_last5", f"{side}_{metric}_last10", f"{side}_{metric}_season"])
    return columns


def matchup_feature_columns() -> list[str]:
    return [
        "home_press_vs_away_build_up",
        "away_press_vs_home_build_up",
        "possession_vs_counter",
        "high_line_vs_transition",
        "crossing_vs_low_block",
        "style_distance_score",
    ]


def embedding_feature_columns() -> list[str]:
    return [
        "home_team_style_cluster",
        "away_team_style_cluster",
        "style_cluster_matchup",
        "home_vs_away_style_history_points",
        "away_vs_home_style_history_points",
    ]


def all_tactical_feature_columns() -> list[str]:
    return tactical_profile_columns() + matchup_feature_columns() + embedding_feature_columns()


def _historical_team_rows(tactics: pd.DataFrame, team: str, current_date: pd.Timestamp) -> pd.DataFrame:
    if tactics.empty:
        return tactics
    rows = tactics[(tactics["team"] == team) & (tactics["date"] < current_date)]
    if "source_collected_at" in rows.columns:
        rows = rows[rows["source_collected_at"].isna() | (rows["source_collected_at"] < current_date)]
    return rows.sort_values("date")


def _team_profile(tactics: pd.DataFrame, team: str, current_date: pd.Timestamp, season: str) -> dict[str, float]:
    history = _historical_team_rows(tactics, team, current_date)
    profile: dict[str, float] = {}
    for metric in TACTICAL_METRICS:
        values = history[metric] if metric in history.columns else pd.Series(dtype=float)
        profile[f"{metric}_last5"] = float(values.tail(5).mean()) if len(values) and pd.notna(values.tail(5).mean()) else np.nan
        profile[f"{metric}_last10"] = float(values.tail(10).mean()) if len(values) and pd.notna(values.tail(10).mean()) else np.nan
        season_values = history[history["season"].astype(str) == str(season)][metric] if len(history) else pd.Series(dtype=float)
        profile[f"{metric}_season"] = (
            float(season_values.mean()) if len(season_values) and pd.notna(season_values.mean()) else np.nan
        )
    return profile


def _style_vector(profile: dict[str, float], suffix: str = "_last10") -> np.ndarray:
    raw_values = [profile.get(f"{metric}{suffix}", np.nan) for metric in TACTICAL_METRICS]
    values = np.array([np.nan if pd.isna(value) else float(value) for value in raw_values], dtype=float)
    return np.nan_to_num(values, nan=0.0)


def _value(profile: dict[str, float], key: str) -> float:
    value = profile.get(key, np.nan)
    return 0.0 if pd.isna(value) else float(value)


def _style_cluster(profile: dict[str, float]) -> int:
    possession = _value(profile, "average_possession_last10")
    press = _value(profile, "press_intensity_score_last10")
    direct = _value(profile, "directness_score_last10")
    low_block = _value(profile, "low_block_score_last10")
    crosses = _value(profile, "crosses_per_match_last10")
    if possession >= max(press, direct, low_block, crosses) and possession > 0:
        return 1
    if press >= max(direct, low_block, crosses) and press > 0:
        return 2
    if direct >= max(low_block, crosses) and direct > 0:
        return 3
    if low_block >= crosses and low_block > 0:
        return 4
    if crosses > 0:
        return 5
    return 0


def _matchups(home: dict[str, float], away: dict[str, float]) -> dict[str, float]:
    home_vector = _style_vector(home)
    away_vector = _style_vector(away)
    return {
        "home_press_vs_away_build_up": _value(home, "press_intensity_score_last10")
        - _value(away, "build_up_speed_last10"),
        "away_press_vs_home_build_up": _value(away, "press_intensity_score_last10")
        - _value(home, "build_up_speed_last10"),
        "possession_vs_counter": _value(home, "average_possession_last10")
        - _value(away, "counter_attacks_last10"),
        "high_line_vs_transition": _value(home, "high_line_score_last10")
        - _value(away, "fast_break_frequency_last10"),
        "crossing_vs_low_block": _value(home, "crosses_per_match_last10")
        - _value(away, "low_block_score_last10"),
        "style_distance_score": float(np.linalg.norm(home_vector - away_vector)),
    }


def _style_history_points(
    team: str,
    opponent_cluster: int,
    team_style_history: dict[str, list[tuple[int, float]]],
) -> float:
    rows = [points for cluster, points in team_style_history.get(team, []) if cluster == opponent_cluster]
    return float(np.mean(rows[-10:])) if rows else 0.0


def _fit_style_embeddings(profile_rows: list[dict[str, object]]) -> pd.DataFrame:
    if not profile_rows:
        return pd.DataFrame(columns=["season", "team", "team_style_cluster", "team_style_archetype"])
    profiles = pd.DataFrame(profile_rows)
    metric_columns = [column for column in profiles.columns if column.endswith("_season")]
    if not metric_columns or profiles[metric_columns].abs().sum().sum() == 0:
        profiles["team_style_cluster"] = 0
        profiles["team_style_archetype"] = ARCHETYPE_NAMES[0]
        return profiles

    n_clusters = min(6, max(1, len(profiles)))
    cluster_input = profiles[metric_columns].copy()
    cluster_input = cluster_input.fillna(cluster_input.median(numeric_only=True)).fillna(0.0)
    scaled = StandardScaler().fit_transform(cluster_input)
    labels = KMeans(n_clusters=n_clusters, n_init=10, random_state=42).fit_predict(scaled)
    profiles["team_style_cluster"] = labels.astype(int)
    profiles["team_style_archetype"] = profiles["team_style_cluster"].map(lambda value: ARCHETYPE_NAMES.get(value, "Balanced"))
    return profiles


def build_tactical_features(matches: pd.DataFrame, tactics: pd.DataFrame) -> tuple[pd.DataFrame, pd.DataFrame]:
    rows: list[dict[str, float]] = []
    profile_history: list[dict[str, object]] = []
    style_history: dict[str, list[tuple[int, float]]] = {}
    ordered_matches = matches.sort_values("Date").reset_index(drop=True)
    has_tactical_signal = (not tactics.empty) and float(tactics[TACTICAL_METRICS].abs().sum().sum()) > 0.0

    for index, match in ordered_matches.iterrows():
        current_date = pd.to_datetime(match["Date"])
        season = str(match["Season"])
        home_team = match["HomeTeam"]
        away_team = match["AwayTeam"]
        home = _team_profile(tactics, home_team, current_date, season)
        away = _team_profile(tactics, away_team, current_date, season)
        home_cluster = _style_cluster(home)
        away_cluster = _style_cluster(away)

        row: dict[str, float] = {}
        for metric, value in home.items():
            row[f"home_{metric}"] = value
        for metric, value in away.items():
            row[f"away_{metric}"] = value
        row.update(_matchups(home, away))
        row["home_team_style_cluster"] = float(home_cluster)
        row["away_team_style_cluster"] = float(away_cluster)
        row["style_cluster_matchup"] = float(home_cluster * 10 + away_cluster)
        row["home_vs_away_style_history_points"] = (
            _style_history_points(home_team, away_cluster, style_history) if has_tactical_signal else 0.0
        )
        row["away_vs_home_style_history_points"] = (
            _style_history_points(away_team, home_cluster, style_history) if has_tactical_signal else 0.0
        )
        rows.append(row)

        profile_history.append({"season": season, "team": home_team, **home, "team_style_cluster": home_cluster})
        profile_history.append({"season": season, "team": away_team, **away, "team_style_cluster": away_cluster})

        from train_model import points_for_team

        if has_tactical_signal:
            style_history.setdefault(home_team, []).append((away_cluster, float(points_for_team(match, home_team))))
            style_history.setdefault(away_team, []).append((home_cluster, float(points_for_team(match, away_team))))

    profiles = _fit_style_embeddings(profile_history)
    Path(STYLE_EMBEDDINGS_PATH).parent.mkdir(exist_ok=True)
    profiles.to_csv(STYLE_EMBEDDINGS_PATH, index=False)
    features = pd.DataFrame(rows)
    for column in features.columns:
        features[column] = pd.to_numeric(features[column], errors="coerce")
    return features, profiles


def tactical_engine_note() -> str:
    return (
        "Tactical profiles are rolling pre-match profiles over last 5, last 10, and current-season history. "
        "Matchup features compare home and away style profiles known before kickoff. "
        + tactical_data_note()
    )
