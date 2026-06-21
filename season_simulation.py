from __future__ import annotations

import argparse
import json
import os
from copy import deepcopy
from pathlib import Path

Path("evaluation", ".matplotlib-cache").mkdir(parents=True, exist_ok=True)
os.environ.setdefault("MPLCONFIGDIR", str(Path("evaluation") / ".matplotlib-cache"))

import joblib
import matplotlib
import numpy as np
import pandas as pd
from matplotlib import pyplot as plt
from sklearn.base import clone
from sklearn.calibration import CalibratedClassifierCV
from sklearn.frozen import FrozenEstimator

from elo_rating_features import EloConfig, build_current_elo_state, build_elo_features, build_prediction_elo_row, elo_feature_columns
from feature_experiments import _markdown_table, train_xgb
from official_fixtures import OFFICIAL_FIXTURE_PATH, fixtures_for_model, load_official_fixtures
from train_model import ELO_CONFIG, MODEL_PATH, PRODUCTION_FEATURE_COLUMNS, SCHEDULE_FEATURE_COLUMNS, build_features, load_matches_with_xg

matplotlib.use("Agg")

OUTPUT_DIR = Path("evaluation") / "season_simulation"
VALIDATION_SEASONS = ["2122", "2223", "2324", "2425"]
SEASON_LABELS = {
    "2122": "2021/22",
    "2223": "2022/23",
    "2324": "2023/24",
    "2425": "2024/25",
    "2526": "2025/26",
}
OUTCOME_LABELS = ["home", "draw", "away"]
RANDOM_SEED = 42


def average(values: list[float]) -> float:
    return float(sum(values) / len(values)) if values else 0.0


def last_5_sum(values: list[float]) -> float:
    return float(sum(values[-5:]))


def last_5_average(values: list[float]) -> float:
    return average(values[-5:])


def last_n_average(values: list[float], window: int) -> float:
    return average(values[-window:])


def latest_season_average(values: list[float], seasons: list[str]) -> float:
    if not values or not seasons:
        return 0.0
    latest_season = str(seasons[-1])
    season_values = [value for value, season in zip(values, seasons) if str(season) == latest_season]
    return average(season_values)


def days_since_last_match(match_dates: list, match_date) -> float:
    previous = [date for date in match_dates if date < match_date]
    return float((match_date - max(previous)).days) if previous else 14.0


def matches_in_last_days(match_dates: list, match_date, days: int) -> int:
    return sum(1 for previous in match_dates if 0 < (match_date - previous).days <= days)


def had_midweek_match(match_dates: list, match_date) -> int:
    recent = [previous for previous in match_dates if 0 < (match_date - previous).days <= 7]
    return int(any(previous.weekday() in {1, 2, 3} for previous in recent))


def feature_row_for_fixture(
    fixture: pd.Series,
    team_history: dict[str, dict[str, list[float]]],
    elo_state: dict[str, dict[str, object]],
    feature_columns: list[str],
) -> dict[str, float]:
    home_team = fixture["HomeTeam"]
    away_team = fixture["AwayTeam"]
    match_date = fixture["Date"]
    empty = {"points": [], "goals_scored": [], "xg": [], "xga": [], "match_dates": [], "shots": [], "shots_on_target": [], "shot_seasons": []}
    home = team_history.get(home_team, empty)
    away = team_history.get(away_team, empty)
    home_xg = last_5_average(home.get("xg", []))
    away_xg = last_5_average(away.get("xg", []))
    home_xga = last_5_average(home.get("xga", []))
    away_xga = last_5_average(away.get("xga", []))
    home_dates = home.get("match_dates", [])
    away_dates = away.get("match_dates", [])
    home_rest = days_since_last_match(home_dates, match_date)
    away_rest = days_since_last_match(away_dates, match_date)
    row = {
        "home_team_points_last_5": last_5_sum(home.get("points", [])),
        "away_team_points_last_5": last_5_sum(away.get("points", [])),
        "home_goals_scored_avg": last_5_average(home.get("goals_scored", [])),
        "away_goals_scored_avg": last_5_average(away.get("goals_scored", [])),
        "home_advantage": 1.0,
        "home_xg_avg": home_xg,
        "away_xg_avg": away_xg,
        "home_xga_avg": home_xga,
        "away_xga_avg": away_xga,
        "home_xg_diff": home_xg - home_xga,
        "away_xg_diff": away_xg - away_xga,
        "home_days_rest": home_rest,
        "away_days_rest": away_rest,
        "home_matches_last_14_days": matches_in_last_days(home_dates, match_date, 14),
        "away_matches_last_14_days": matches_in_last_days(away_dates, match_date, 14),
        "home_had_midweek_match": had_midweek_match(home_dates, match_date),
        "away_had_midweek_match": had_midweek_match(away_dates, match_date),
        "home_days_since_last_match": home_rest,
        "away_days_since_last_match": away_rest,
    }
    if any("shots_avg" in column or "shots_on_target_avg" in column for column in feature_columns):
        home_shots = home.get("shots", [])
        away_shots = away.get("shots", [])
        home_sot = home.get("shots_on_target", [])
        away_sot = away.get("shots_on_target", [])
        home_shot_seasons = home.get("shot_seasons", [])
        away_shot_seasons = away.get("shot_seasons", [])
        row.update(
            {
                "home_shots_avg_last5": last_n_average(home_shots, 5),
                "away_shots_avg_last5": last_n_average(away_shots, 5),
                "home_shots_on_target_avg_last5": last_n_average(home_sot, 5),
                "away_shots_on_target_avg_last5": last_n_average(away_sot, 5),
                "home_shots_avg_last10": last_n_average(home_shots, 10),
                "away_shots_avg_last10": last_n_average(away_shots, 10),
                "home_shots_on_target_avg_last10": last_n_average(home_sot, 10),
                "away_shots_on_target_avg_last10": last_n_average(away_sot, 10),
                "home_shots_avg_season": latest_season_average(home_shots, home_shot_seasons),
                "away_shots_avg_season": latest_season_average(away_shots, away_shot_seasons),
                "home_shots_on_target_avg_season": latest_season_average(home_sot, home_shot_seasons),
                "away_shots_on_target_avg_season": latest_season_average(away_sot, away_shot_seasons),
            }
        )
    if any("elo" in column for column in feature_columns):
        row.update(build_prediction_elo_row(home_team, away_team, elo_state))
    return {column: float(row.get(column, 0.0)) for column in feature_columns}


def season_start_feature_audit(
    teams: tuple[str, ...] | list[str],
    team_history: dict[str, dict[str, list[float]]],
    elo_state: dict[str, dict[str, object]],
) -> pd.DataFrame:
    rows = []
    for team in sorted(teams):
        history = team_history.get(
            team,
            {"points": [], "goals_scored": [], "xg": [], "xga": [], "match_dates": [], "shots": [], "shots_on_target": [], "shot_seasons": []},
        )
        points = history.get("points", [])
        goals = history.get("goals_scored", [])
        xg = history.get("xg", [])
        xga = history.get("xga", [])
        shots = history.get("shots", [])
        shots_on_target = history.get("shots_on_target", [])
        shot_seasons = history.get("shot_seasons", [])
        match_dates = history.get("match_dates", [])
        elo = elo_state.get(team, {})
        elo_history = [float(value) for value in elo.get("history", [])]
        elo_rating = float(elo.get("rating", 1500.0))
        premier_league_matches = len(points)
        xg_avg = last_5_average(xg)
        xga_avg = last_5_average(xga)
        flags = {
            "no_premier_league_history": premier_league_matches == 0,
            "limited_recent_form": 0 < premier_league_matches < 5,
            "xg_fallback": len(xg) < 5,
            "shot_volume_fallback": len(shots) < 5,
            "elo_fallback": team not in elo_state,
        }
        rows.append(
            {
                "team": team,
                "data_source_league": "Premier League historical data" if premier_league_matches else "No local Premier League history",
                "premier_league_matches_available": premier_league_matches,
                "latest_premier_league_match": max(match_dates).isoformat() if match_dates else "",
                "recent_form_points_last5": last_5_sum(points),
                "recent_goals_scored_avg_last5": last_5_average(goals),
                "xg_strength_last5": xg_avg,
                "xga_strength_last5": xga_avg,
                "xg_diff_last5": xg_avg - xga_avg,
                "shots_avg_last5": last_n_average(shots, 5),
                "shots_on_target_avg_last5": last_n_average(shots_on_target, 5),
                "shots_avg_last10": last_n_average(shots, 10),
                "shots_on_target_avg_last10": last_n_average(shots_on_target, 10),
                "shots_avg_latest_season": latest_season_average(shots, shot_seasons),
                "shots_on_target_avg_latest_season": latest_season_average(shots_on_target, shot_seasons),
                "elo_rating": elo_rating,
                "elo_recent_change": float(elo_rating - elo_history[-5]) if len(elo_history) >= 5 else 0.0,
                "fallback_flags": ", ".join(flag for flag, active in flags.items() if active) or "none",
            }
        )
    return pd.DataFrame(rows)


def predict_fixture_probabilities(
    fixtures: pd.DataFrame,
    model,
    feature_columns: list[str],
    preseason_team_history: dict[str, dict[str, list[float]]],
    preseason_elo_state: dict[str, dict[str, object]],
    calibrator=None,
) -> pd.DataFrame:
    rolling_history = deepcopy(preseason_team_history)
    rows = []
    for _, fixture in fixtures.sort_values("Date").iterrows():
        home_team = fixture["HomeTeam"]
        away_team = fixture["AwayTeam"]
        for team in (home_team, away_team):
            rolling_history.setdefault(
                team,
                {"points": [], "goals_scored": [], "xg": [], "xga": [], "match_dates": [], "shots": [], "shots_on_target": [], "shot_seasons": []},
            )
        row = feature_row_for_fixture(fixture, rolling_history, preseason_elo_state, feature_columns)
        X = pd.DataFrame([row], columns=feature_columns)
        probabilities = calibrator.predict_proba(X)[0] if calibrator is not None else model.predict_proba(X)[0]
        probabilities = np.clip(probabilities, 1e-15, 1.0)
        probabilities = probabilities / probabilities.sum()
        rows.append(
            {
                "Date": fixture["Date"],
                "Season": fixture["Season"],
                "HomeTeam": home_team,
                "AwayTeam": away_team,
                "home_win_probability": float(probabilities[0]),
                "draw_probability": float(probabilities[1]),
                "away_win_probability": float(probabilities[2]),
            }
        )
        rolling_history[home_team]["match_dates"].append(fixture["Date"])
        rolling_history[away_team]["match_dates"].append(fixture["Date"])
    return pd.DataFrame(rows)


def season_table_from_results(fixtures: pd.DataFrame) -> pd.DataFrame:
    teams = sorted(set(fixtures["HomeTeam"]).union(fixtures["AwayTeam"]))
    table = {team: {"team": team, "points": 0, "gf": 0, "ga": 0, "gd": 0} for team in teams}
    for _, match in fixtures.iterrows():
        home = match["HomeTeam"]
        away = match["AwayTeam"]
        home_goals = int(match["FTHG"])
        away_goals = int(match["FTAG"])
        table[home]["gf"] += home_goals
        table[home]["ga"] += away_goals
        table[away]["gf"] += away_goals
        table[away]["ga"] += home_goals
        if match["FTR"] == "H":
            table[home]["points"] += 3
        elif match["FTR"] == "A":
            table[away]["points"] += 3
        else:
            table[home]["points"] += 1
            table[away]["points"] += 1
    frame = pd.DataFrame(table.values())
    frame["gd"] = frame["gf"] - frame["ga"]
    frame = frame.sort_values(["points", "gd", "gf", "team"], ascending=[False, False, False, True]).reset_index(drop=True)
    frame["actual_position"] = frame.index + 1
    return frame


def expected_points_from_probabilities(probabilities: pd.DataFrame) -> pd.DataFrame:
    teams = sorted(set(probabilities["HomeTeam"]).union(probabilities["AwayTeam"]))
    points = {team: 0.0 for team in teams}
    for _, match in probabilities.iterrows():
        points[match["HomeTeam"]] += 3.0 * match["home_win_probability"] + match["draw_probability"]
        points[match["AwayTeam"]] += 3.0 * match["away_win_probability"] + match["draw_probability"]
    frame = pd.DataFrame({"team": list(points.keys()), "expected_points_deterministic": list(points.values())})
    return frame.sort_values(["expected_points_deterministic", "team"], ascending=[False, True]).reset_index(drop=True)


def monte_carlo_season(probabilities: pd.DataFrame, n_simulations: int, seed: int = RANDOM_SEED) -> pd.DataFrame:
    rng = np.random.default_rng(seed)
    teams = sorted(set(probabilities["HomeTeam"]).union(probabilities["AwayTeam"]))
    team_to_index = {team: index for index, team in enumerate(teams)}
    points = np.zeros((n_simulations, len(teams)), dtype=float)
    probs = probabilities[["home_win_probability", "draw_probability", "away_win_probability"]].to_numpy()
    probs = np.clip(probs, 1e-15, 1.0)
    probs = probs / probs.sum(axis=1, keepdims=True)
    outcomes = np.array([0, 1, 2])
    for fixture_index, match in probabilities.reset_index(drop=True).iterrows():
        draws = rng.choice(outcomes, size=n_simulations, p=probs[fixture_index])
        home_idx = team_to_index[match["HomeTeam"]]
        away_idx = team_to_index[match["AwayTeam"]]
        points[:, home_idx] += np.where(draws == 0, 3.0, np.where(draws == 1, 1.0, 0.0))
        points[:, away_idx] += np.where(draws == 2, 3.0, np.where(draws == 1, 1.0, 0.0))

    positions = np.zeros_like(points)
    for sim in range(n_simulations):
        order = np.lexsort((np.array(teams), -points[sim]))
        positions[sim, order] = np.arange(1, len(teams) + 1)

    rows = []
    for team, index in team_to_index.items():
        team_positions = positions[:, index]
        rows.append(
            {
                "team": team,
                "expected_points": float(points[:, index].mean()),
                "expected_position": float(team_positions.mean()),
                "title_probability": float((team_positions == 1).mean()),
                "top_4_probability": float((team_positions <= 4).mean()),
                "top_6_probability": float((team_positions <= 6).mean()),
                "relegation_probability": float((team_positions >= len(teams) - 2).mean()),
            }
        )
    return pd.DataFrame(rows).sort_values("expected_position").reset_index(drop=True)


def train_preseason_model(matches_before_season: pd.DataFrame, include_elo: bool) -> tuple[object, list[str], dict, dict, pd.DataFrame]:
    base_dataset, team_history = build_features(matches_before_season, include_xg=True, include_schedule=True)
    feature_columns = list(SCHEDULE_FEATURE_COLUMNS)
    dataset = base_dataset
    elo_state = {}
    if include_elo:
        elo_features, _ = build_elo_features(matches_before_season, ELO_CONFIG)
        dataset = pd.concat([base_dataset.reset_index(drop=True), elo_features.reset_index(drop=True)], axis=1)
        feature_columns = list(PRODUCTION_FEATURE_COLUMNS)
        elo_state = build_current_elo_state(matches_before_season, ELO_CONFIG)
    model = train_xgb(dataset[feature_columns], dataset["target"])
    return model, feature_columns, team_history, elo_state, dataset


def fit_preseason_calibrator(model, dataset: pd.DataFrame, feature_columns: list[str]):
    if len(dataset) < 500:
        return None
    split_index = int(len(dataset) * 0.8)
    X_fit = dataset[feature_columns].iloc[:split_index]
    y_fit = dataset["target"].iloc[:split_index]
    X_cal = dataset[feature_columns].iloc[split_index:]
    y_cal = dataset["target"].iloc[split_index:]
    fit_model = clone(model)
    fit_model.fit(X_fit, y_fit)
    calibrator = CalibratedClassifierCV(FrozenEstimator(fit_model), method="sigmoid")
    calibrator.fit(X_cal, y_cal)
    return calibrator


def forecast_historical_season(matches: pd.DataFrame, season: str, include_elo: bool, use_calibration: bool, n_simulations: int) -> tuple[pd.DataFrame, pd.DataFrame]:
    fixtures = matches[matches["Season"] == season].sort_values("Date").reset_index(drop=True)
    season_start = fixtures["Date"].min()
    training_matches = matches[matches["Date"] < season_start].sort_values("Date").reset_index(drop=True)
    model, feature_columns, team_history, elo_state, dataset = train_preseason_model(training_matches, include_elo=include_elo)
    calibrator = fit_preseason_calibrator(model, dataset, feature_columns) if use_calibration else None
    probabilities = predict_fixture_probabilities(fixtures, model, feature_columns, team_history, elo_state, calibrator=calibrator)
    deterministic = expected_points_from_probabilities(probabilities)
    simulation = monte_carlo_season(probabilities, n_simulations=n_simulations, seed=RANDOM_SEED)
    forecast = simulation.merge(deterministic, on="team", how="left")
    actual = season_table_from_results(fixtures)
    comparison = forecast.merge(actual[["team", "points", "actual_position"]], on="team", how="left")
    comparison["season"] = season
    comparison["model_variant"] = model_variant_name(include_elo, use_calibration)
    comparison["position_error"] = (comparison["expected_position"] - comparison["actual_position"]).abs()
    comparison["points_error"] = (comparison["expected_points"] - comparison["points"]).abs()
    return comparison, probabilities


def model_variant_name(include_elo: bool, use_calibration: bool) -> str:
    if include_elo and use_calibration:
        return "current_plus_elo_calibrated"
    if include_elo:
        return "current_plus_elo"
    if use_calibration:
        return "current_calibrated"
    return "current_without_elo"


def top_n_set(frame: pd.DataFrame, position_column: str, n: int) -> set[str]:
    return set(frame.sort_values(position_column).head(n)["team"])


def relegation_set(frame: pd.DataFrame, position_column: str) -> set[str]:
    return set(frame.sort_values(position_column).tail(3)["team"])


def validation_metrics(comparison: pd.DataFrame) -> pd.DataFrame:
    rows = []
    for (season, variant), frame in comparison.groupby(["season", "model_variant"]):
        predicted_order = frame.sort_values("expected_position").reset_index(drop=True)
        actual_order = frame.sort_values("actual_position").reset_index(drop=True)
        predicted_champion = predicted_order.iloc[0]["team"]
        actual_champion = actual_order.iloc[0]["team"]
        predicted_top4 = top_n_set(predicted_order, "expected_position", 4)
        actual_top4 = top_n_set(actual_order, "actual_position", 4)
        predicted_relegated = relegation_set(predicted_order, "expected_position")
        actual_relegated = relegation_set(actual_order, "actual_position")
        rows.append(
            {
                "season": season,
                "season_label": SEASON_LABELS.get(season, season),
                "model_variant": variant,
                "average_position_error": float(frame["position_error"].mean()),
                "average_points_error": float(frame["points_error"].mean()),
                "rank_correlation": float(frame["expected_position"].corr(frame["actual_position"], method="spearman")),
                "champion_prediction_accuracy": float(predicted_champion == actual_champion),
                "top_4_prediction_accuracy": float(len(predicted_top4 & actual_top4) / 4.0),
                "relegation_prediction_accuracy": float(len(predicted_relegated & actual_relegated) / 3.0),
            }
        )
    return pd.DataFrame(rows)


def aggregate_validation(metrics: pd.DataFrame) -> pd.DataFrame:
    return (
        metrics.groupby("model_variant", as_index=False)[
            [
                "average_position_error",
                "average_points_error",
                "rank_correlation",
                "champion_prediction_accuracy",
                "top_4_prediction_accuracy",
                "relegation_prediction_accuracy",
            ]
        ]
        .mean()
        .sort_values(["average_position_error", "average_points_error"])
    )


def misranked_teams(comparison: pd.DataFrame) -> pd.DataFrame:
    return (
        comparison.groupby(["model_variant", "team"], as_index=False)
        .agg(
            seasons=("season", "nunique"),
            mean_position_error=("position_error", "mean"),
            mean_points_error=("points_error", "mean"),
            mean_expected_position=("expected_position", "mean"),
            mean_actual_position=("actual_position", "mean"),
        )
        .sort_values(["model_variant", "mean_position_error"], ascending=[True, False])
    )


def plot_validation_summary(summary: pd.DataFrame, output_path: Path) -> None:
    fig, axes = plt.subplots(1, 3, figsize=(15, 4))
    for ax, metric in zip(axes, ["average_position_error", "average_points_error", "rank_correlation"]):
        ax.bar(summary["model_variant"], summary[metric])
        ax.set_title(metric)
        ax.tick_params(axis="x", rotation=25)
        ax.grid(axis="y", alpha=0.25)
    fig.suptitle("Season Simulation Historical Validation")
    fig.tight_layout()
    fig.savefig(output_path, dpi=160)
    plt.close(fig)


def plot_projection_table(projection: pd.DataFrame, output_path: Path) -> None:
    fig, ax = plt.subplots(figsize=(10, 7))
    data = projection.sort_values("expected_position", ascending=False)
    ax.barh(data["team"], data["expected_points"])
    ax.set_title("Season Projection Expected Points")
    ax.set_xlabel("Expected points")
    fig.tight_layout()
    fig.savefig(output_path, dpi=160)
    plt.close(fig)


def read_fixture_list(path: Path) -> pd.DataFrame:
    frame = pd.read_csv(path)
    required = {"Date", "HomeTeam", "AwayTeam"}
    missing = required - set(frame.columns)
    if missing:
        raise ValueError(f"Fixture list is missing columns: {sorted(missing)}")
    frame["Date"] = pd.to_datetime(frame["Date"], dayfirst=True, errors="coerce").dt.date
    frame = frame.dropna(subset=["Date", "HomeTeam", "AwayTeam"]).copy()
    if "Season" not in frame.columns:
        frame["Season"] = "custom"
    return frame.sort_values("Date").reset_index(drop=True)


def project_fixture_list(fixture_path: Path, n_simulations: int) -> pd.DataFrame:
    fixtures = read_fixture_list(fixture_path)
    artifact = joblib.load(MODEL_PATH)
    model = artifact["model"]
    feature_columns = artifact["feature_columns"]
    probabilities = predict_fixture_probabilities(
        fixtures,
        model,
        feature_columns,
        artifact["team_history"],
        artifact.get("elo_state", {}),
    )
    projection = monte_carlo_season(probabilities, n_simulations=n_simulations, seed=RANDOM_SEED)
    expected = expected_points_from_probabilities(probabilities)
    projection = projection.merge(expected, on="team", how="left")
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    probabilities.to_csv(OUTPUT_DIR / "custom_fixture_probabilities.csv", index=False)
    projection.to_csv(OUTPUT_DIR / f"custom_projection_{n_simulations}.csv", index=False)
    plot_projection_table(projection, OUTPUT_DIR / f"custom_projection_{n_simulations}.png")
    return projection


def read_default_upcoming_fixtures() -> tuple[pd.DataFrame | None, str]:
    if OFFICIAL_FIXTURE_PATH.exists():
        try:
            official = load_official_fixtures(OFFICIAL_FIXTURE_PATH)
            return fixtures_for_model(official), "Official fixtures loaded"
        except Exception as exc:
            return None, f"Fixture data outdated: {exc}"
    return None, "Missing fixtures"


def run_historical_validation(n_simulations: int = 1000) -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    matches = load_matches_with_xg().sort_values("Date").reset_index(drop=True)
    comparisons = []
    probability_rows = []
    for season in VALIDATION_SEASONS:
        for include_elo, use_calibration in [(False, False), (True, False), (True, True)]:
            comparison, probabilities = forecast_historical_season(
                matches,
                season,
                include_elo=include_elo,
                use_calibration=use_calibration,
                n_simulations=n_simulations,
            )
            comparisons.append(comparison)
            probabilities["model_variant"] = model_variant_name(include_elo, use_calibration)
            probability_rows.append(probabilities)
    comparison = pd.concat(comparisons, ignore_index=True)
    probabilities = pd.concat(probability_rows, ignore_index=True)
    metrics = validation_metrics(comparison)
    summary = aggregate_validation(metrics)
    misranked = misranked_teams(comparison)
    comparison.to_csv(OUTPUT_DIR / "historical_season_comparison.csv", index=False)
    probabilities.to_csv(OUTPUT_DIR / "historical_fixture_probabilities.csv", index=False)
    metrics.to_csv(OUTPUT_DIR / "historical_validation_by_season.csv", index=False)
    summary.to_csv(OUTPUT_DIR / "historical_validation_summary.csv", index=False)
    misranked.to_csv(OUTPUT_DIR / "misranked_teams.csv", index=False)
    plot_validation_summary(summary, OUTPUT_DIR / "historical_validation_summary.png")
    write_report(summary, metrics, misranked, comparison, n_simulations)
    return summary, metrics, comparison


def write_report(summary: pd.DataFrame, metrics: pd.DataFrame, misranked: pd.DataFrame, comparison: pd.DataFrame, n_simulations: int) -> None:
    best = summary.iloc[0]
    no_elo = summary[summary["model_variant"] == "current_without_elo"].iloc[0]
    elo = summary[summary["model_variant"] == "current_plus_elo"].iloc[0]
    elo_cal = summary[summary["model_variant"] == "current_plus_elo_calibrated"].iloc[0]
    improves_elo = float(elo["average_position_error"]) < float(no_elo["average_position_error"])
    improves_cal = float(elo_cal["average_position_error"]) < float(elo["average_position_error"])
    public_ready = float(best["average_position_error"]) <= 3.0 and float(best["rank_correlation"]) >= 0.75
    top_misranked = misranked[misranked["model_variant"] == str(best["model_variant"])].head(12)

    Path("season_simulation_report.md").write_text(
        f"""# Season Simulation Report

This report validates preseason Premier League season simulations using only information available before each season starts.

Historical validation seasons:

- 2021/22
- 2022/23
- 2023/24
- 2024/25

Monte Carlo simulations per validation run: `{n_simulations}`.

Important limitation: preseason forecasts freeze form, xG and Elo at season start. Fixture dates are used for rest/fatigue because fixture dates are known before the matches, but no in-season match results are fed back into the forecast.

## Aggregate Validation

{_markdown_table(summary, ['model_variant', 'average_position_error', 'average_points_error', 'rank_correlation', 'champion_prediction_accuracy', 'top_4_prediction_accuracy', 'relegation_prediction_accuracy'])}

Best variant by position error: `{best['model_variant']}`.

## Season-by-Season Validation

{_markdown_table(metrics, ['season_label', 'model_variant', 'average_position_error', 'average_points_error', 'rank_correlation', 'champion_prediction_accuracy', 'top_4_prediction_accuracy', 'relegation_prediction_accuracy'])}

## Consistently Mis-Ranked Teams

For the best variant:

{_markdown_table(top_misranked, ['team', 'seasons', 'mean_position_error', 'mean_points_error', 'mean_expected_position', 'mean_actual_position'])}

## Answers

### 1. How accurately can the model forecast a season?

Best average position error: `{float(best['average_position_error']):.2f}` places.  
Best average points error: `{float(best['average_points_error']):.2f}` points.  
Best rank correlation: `{float(best['rank_correlation']):.3f}`.

### 2. Which teams are consistently mis-ranked?

The most mis-ranked teams are listed above. These are usually clubs whose season-level outcomes diverge from preseason rolling form/Elo, often due to transfers, manager changes, injuries, tactical changes or promoted-team uncertainty.

### 3. Does Elo improve season forecasting?

Without Elo average position error: `{float(no_elo['average_position_error']):.2f}`.  
With Elo average position error: `{float(elo['average_position_error']):.2f}`.

Answer: {'Yes, Elo improves average position error in this preseason simulation backtest.' if improves_elo else 'No, Elo does not improve average position error in this preseason simulation backtest.'}

### 4. Does calibration improve season forecasting?

With Elo raw average position error: `{float(elo['average_position_error']):.2f}`.  
With Elo calibrated average position error: `{float(elo_cal['average_position_error']):.2f}`.

Answer: {'Yes, calibration improves average position error.' if improves_cal else 'No, calibration does not improve average position error in this run.'}

### 5. Is the model good enough for public season projections?

Answer: {'Yes, cautiously. It meets the rough projection-quality threshold used in this report.' if public_ready else 'Not yet. It is useful as an internal research projection, but not strong enough for confident public season projections.'}

The biggest concern is that the model has no transfer-window, manager-change, lineup, injury or squad-depth intelligence at preseason time.

## Artifacts

- `evaluation/season_simulation/historical_season_comparison.csv`
- `evaluation/season_simulation/historical_fixture_probabilities.csv`
- `evaluation/season_simulation/historical_validation_by_season.csv`
- `evaluation/season_simulation/historical_validation_summary.csv`
- `evaluation/season_simulation/misranked_teams.csv`
- `evaluation/season_simulation/historical_validation_summary.png`
"""
    )


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Simulate Premier League seasons from model probabilities.")
    parser.add_argument("--fixture-csv", type=Path, help="CSV fixture list with Date, HomeTeam and AwayTeam columns.")
    parser.add_argument("--simulations", type=int, default=1000, help="Monte Carlo simulations to run.")
    parser.add_argument("--historical-validation", action="store_true", help="Run historical preseason validation.")
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    if args.fixture_csv:
        projection = project_fixture_list(args.fixture_csv, n_simulations=args.simulations)
        print(json.dumps({"teams": len(projection), "simulations": args.simulations}, indent=2))
        return
    summary, _, _ = run_historical_validation(n_simulations=args.simulations)
    print(json.dumps({"best_variant": str(summary.iloc[0]["model_variant"]), "simulations": args.simulations}, indent=2))


if __name__ == "__main__":
    main()
