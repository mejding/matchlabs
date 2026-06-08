from __future__ import annotations

import argparse
from datetime import date, datetime, timedelta
from pathlib import Path

import joblib
import pandas as pd

from elo_rating_features import build_prediction_elo_row


MODEL_PATH = Path("models") / "football_model.joblib"


def last_5_sum(values: list[float]) -> float:
    return float(sum(values[-5:]))


def last_5_average(values: list[float]) -> float:
    recent = values[-5:]
    return float(sum(recent) / len(recent)) if recent else 0.0


def last_n_average(values: list[float], window: int) -> float:
    recent = values[-window:]
    return float(sum(recent) / len(recent)) if recent else 0.0


def latest_season_average(values: list[float], seasons: list[str]) -> float:
    if not values or not seasons:
        return 0.0
    latest_season = str(seasons[-1])
    season_values = [value for value, season in zip(values, seasons) if str(season) == latest_season]
    return float(sum(season_values) / len(season_values)) if season_values else 0.0


def parse_match_date(value: str | date | None, team_history: dict[str, dict[str, list]]) -> date:
    if isinstance(value, date):
        return value
    if isinstance(value, str) and value:
        return datetime.strptime(value, "%Y-%m-%d").date()

    known_dates = [
        match_date
        for history in team_history.values()
        for match_date in history.get("match_dates", [])
    ]
    if not known_dates:
        return date.today()
    return max(known_dates) + timedelta(days=7)


def latest_history_date(team_history: dict[str, dict[str, list]]) -> date | None:
    known_dates = [
        match_date
        for history in team_history.values()
        for match_date in history.get("match_dates", [])
    ]
    return max(known_dates) if known_dates else None


def effective_feature_date(prediction_date: date, team_history: dict[str, dict[str, list]]) -> date:
    latest_date = latest_history_date(team_history)
    if latest_date is None:
        return prediction_date
    return min(prediction_date, latest_date + timedelta(days=7))


def days_since_last_match(match_dates: list[date], match_date: date) -> float:
    previous_dates = [previous_date for previous_date in match_dates if previous_date < match_date]
    if not previous_dates:
        return 14.0
    return float((match_date - max(previous_dates)).days)


def matches_in_last_days(match_dates: list[date], match_date: date, days: int) -> int:
    return sum(1 for previous_date in match_dates if 0 < (match_date - previous_date).days <= days)


def had_midweek_match(match_dates: list[date], match_date: date) -> int:
    recent_dates = [previous_date for previous_date in match_dates if 0 < (match_date - previous_date).days <= 7]
    return int(any(previous_date.weekday() in {1, 2, 3} for previous_date in recent_dates))


def build_prediction_features(
    home_team: str,
    away_team: str,
    team_history: dict[str, dict[str, list[float]]],
    feature_columns: list[str],
    match_date: str | date | None = None,
    elo_state: dict[str, dict[str, object]] | None = None,
) -> pd.DataFrame:
    empty_history = {"points": [], "goals_scored": [], "xg": [], "xga": [], "match_dates": []}
    home_history = team_history.get(home_team, empty_history)
    away_history = team_history.get(away_team, empty_history)
    prediction_date = parse_match_date(match_date, team_history)
    feature_date = effective_feature_date(prediction_date, team_history)

    home_xg_avg = last_5_average(home_history.get("xg", []))
    away_xg_avg = last_5_average(away_history.get("xg", []))
    home_xga_avg = last_5_average(home_history.get("xga", []))
    away_xga_avg = last_5_average(away_history.get("xga", []))
    home_dates = home_history.get("match_dates", [])
    away_dates = away_history.get("match_dates", [])
    home_days_since_last = days_since_last_match(home_dates, feature_date)
    away_days_since_last = days_since_last_match(away_dates, feature_date)

    row = {
        "home_team_points_last_5": last_5_sum(home_history["points"]),
        "away_team_points_last_5": last_5_sum(away_history["points"]),
        "home_goals_scored_avg": last_5_average(home_history["goals_scored"]),
        "away_goals_scored_avg": last_5_average(away_history["goals_scored"]),
        "home_advantage": 1,
        "home_xg_avg": home_xg_avg,
        "away_xg_avg": away_xg_avg,
        "home_xga_avg": home_xga_avg,
        "away_xga_avg": away_xga_avg,
        "home_xg_diff": home_xg_avg - home_xga_avg,
        "away_xg_diff": away_xg_avg - away_xga_avg,
        "home_days_rest": home_days_since_last,
        "away_days_rest": away_days_since_last,
        "home_matches_last_14_days": matches_in_last_days(home_dates, feature_date, 14),
        "away_matches_last_14_days": matches_in_last_days(away_dates, feature_date, 14),
        "home_had_midweek_match": had_midweek_match(home_dates, feature_date),
        "away_had_midweek_match": had_midweek_match(away_dates, feature_date),
        "home_days_since_last_match": home_days_since_last,
        "away_days_since_last_match": away_days_since_last,
        "home_number_of_injured_starters": 0.0,
        "away_number_of_injured_starters": 0.0,
        "home_missing_minutes_played": 0.0,
        "away_missing_minutes_played": 0.0,
        "home_missing_xg_contribution": 0.0,
        "away_missing_xg_contribution": 0.0,
        "home_missing_market_value": 0.0,
        "away_missing_market_value": 0.0,
    }
    if any("shots_avg" in column or "shots_on_target_avg" in column for column in feature_columns):
        home_shots = home_history.get("shots", [])
        away_shots = away_history.get("shots", [])
        home_sot = home_history.get("shots_on_target", [])
        away_sot = away_history.get("shots_on_target", [])
        home_shot_seasons = home_history.get("shot_seasons", [])
        away_shot_seasons = away_history.get("shot_seasons", [])
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
    if any(column.startswith("elo_") or column.endswith("_elo") or column.endswith("_elo_trend") for column in feature_columns):
        row.update(build_prediction_elo_row(home_team, away_team, elo_state or {}))
    return pd.DataFrame([row], columns=feature_columns)


def predict(home_team: str, away_team: str, match_date: str | None = None) -> None:
    if not MODEL_PATH.exists():
        raise FileNotFoundError("Model not found. Run `python train_model.py` first.")

    artifact = joblib.load(MODEL_PATH)
    model = artifact["model"]
    feature_columns = artifact["feature_columns"]
    team_history = artifact["team_history"]
    elo_state = artifact.get("elo_state", {})

    features = build_prediction_features(home_team, away_team, team_history, feature_columns, match_date=match_date, elo_state=elo_state)
    probabilities = model.predict_proba(features)[0]

    print(f"\nPrediction: {home_team} vs {away_team}")
    print(f"Home win: {probabilities[0]:.3f}")
    print(f"Draw:     {probabilities[1]:.3f}")
    print(f"Away win: {probabilities[2]:.3f}")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Predict a Premier League match result.")
    parser.add_argument("--home-team", help="Home team name, for example Arsenal")
    parser.add_argument("--away-team", help="Away team name, for example Chelsea")
    parser.add_argument("--match-date", help="Match date in YYYY-MM-DD format")
    return parser.parse_args()


if __name__ == "__main__":
    args = parse_args()

    home_team = args.home_team or input("Home team: ").strip()
    away_team = args.away_team or input("Away team: ").strip()

    predict(home_team, away_team, match_date=args.match_date)
