from __future__ import annotations

import argparse
import json
import gzip
import os
import urllib.request
from pathlib import Path

import joblib
import pandas as pd
from sklearn.metrics import accuracy_score, log_loss
from sklearn.preprocessing import label_binarize

from elo_rating_features import EloConfig, build_current_elo_state, build_elo_features, elo_feature_columns


DATA_DIR = Path("data")
MODEL_DIR = Path("models")
MODEL_PATH = MODEL_DIR / "football_model.joblib"
BASELINE_MODEL_PATH = MODEL_DIR / "football_model_baseline.joblib"
XG_MODEL_PATH = MODEL_DIR / "football_model_xg.joblib"
XG_SCHEDULE_MODEL_PATH = MODEL_DIR / "football_model_xg_schedule.joblib"
INJURY_DATA_PATH = DATA_DIR / "injuries.csv"

DEFAULT_SEASONS = ["1920", "2021", "2122", "2223", "2324", "2425", "2526", "2627"]
BASE_URL = "https://www.football-data.co.uk/mmz4281/{season}/E0.csv"
UNDERSTAT_URL = "https://understat.com/getLeagueData/EPL/{season}"


def season_code_to_understat_year(season: str) -> int:
    return 2000 + int(str(season)[:2])


def configured_seasons() -> list[str]:
    raw = os.environ.get("FOOTBALL_DATA_SEASONS")
    if not raw:
        return list(DEFAULT_SEASONS)
    return [season.strip() for season in raw.replace(",", " ").split() if season.strip()]


def configured_understat_seasons(seasons: list[str]) -> dict[str, int]:
    raw = os.environ.get("UNDERSTAT_SEASONS")
    if raw:
        years = [int(year.strip()) for year in raw.replace(",", " ").split() if year.strip()]
        if len(years) != len(seasons):
            raise ValueError("UNDERSTAT_SEASONS must have the same number of entries as FOOTBALL_DATA_SEASONS.")
        return dict(zip(seasons, years))
    return {season: season_code_to_understat_year(season) for season in seasons}


SEASONS = configured_seasons()
UNDERSTAT_SEASONS = configured_understat_seasons(SEASONS)

UNDERSTAT_TO_FOOTBALL_DATA_TEAMS = {
    "Manchester City": "Man City",
    "Manchester United": "Man United",
    "Newcastle United": "Newcastle",
    "Nottingham Forest": "Nott'm Forest",
    "Leeds United": "Leeds",
    "Tottenham Hotspur": "Tottenham",
    "West Ham United": "West Ham",
    "West Bromwich Albion": "West Brom",
    "Wolverhampton Wanderers": "Wolves",
}

FEATURE_COLUMNS = [
    "home_team_points_last_5",
    "away_team_points_last_5",
    "home_goals_scored_avg",
    "away_goals_scored_avg",
    "home_advantage",
]
XG_FEATURE_COLUMNS = FEATURE_COLUMNS + [
    "home_xg_avg",
    "away_xg_avg",
    "home_xga_avg",
    "away_xga_avg",
    "home_xg_diff",
    "away_xg_diff",
]
SCHEDULE_FEATURE_COLUMNS = XG_FEATURE_COLUMNS + [
    "home_days_rest",
    "away_days_rest",
    "home_matches_last_14_days",
    "away_matches_last_14_days",
    "home_had_midweek_match",
    "away_had_midweek_match",
    "home_days_since_last_match",
    "away_days_since_last_match",
]
ELO_CONFIG = EloConfig(k_factor=30.0, home_advantage=75.0, margin_of_victory=False)
ELO_FEATURE_COLUMNS = elo_feature_columns()
SHOT_VOLUME_FEATURE_COLUMNS = [
    "home_shots_avg_last5",
    "away_shots_avg_last5",
    "home_shots_on_target_avg_last5",
    "away_shots_on_target_avg_last5",
    "home_shots_avg_last10",
    "away_shots_avg_last10",
    "home_shots_on_target_avg_last10",
    "away_shots_on_target_avg_last10",
    "home_shots_avg_season",
    "away_shots_avg_season",
    "home_shots_on_target_avg_season",
    "away_shots_on_target_avg_season",
]
PRODUCTION_FEATURE_COLUMNS = SCHEDULE_FEATURE_COLUMNS + ELO_FEATURE_COLUMNS + SHOT_VOLUME_FEATURE_COLUMNS
INJURY_FEATURE_COLUMNS = SCHEDULE_FEATURE_COLUMNS + [
    "home_number_of_injured_starters",
    "away_number_of_injured_starters",
    "home_missing_minutes_played",
    "away_missing_minutes_played",
    "home_missing_xg_contribution",
    "away_missing_xg_contribution",
    "home_missing_market_value",
    "away_missing_market_value",
]
INJURY_DATA_COLUMNS = [
    "report_date",
    "team",
    "player",
    "unavailable_from",
    "expected_return_date",
    "is_expected_starter",
    "minutes_played_last_365",
    "xg_contribution_last_365",
    "market_value_eur",
]

RESULT_TO_LABEL = {"H": 0, "D": 1, "A": 2}
LABEL_TO_RESULT = {0: "home_win", 1: "draw", 2: "away_win"}


def get_xgb_classifier():
    try:
        from xgboost import XGBClassifier
    except Exception as exc:
        raise RuntimeError(
            "Could not import XGBoost. If you are on macOS and see a libomp.dylib "
            "error, install the OpenMP runtime with `brew install libomp`, then "
            "run `python train_model.py` again."
        ) from exc

    return XGBClassifier


def download_csv(season: str) -> Path:
    DATA_DIR.mkdir(exist_ok=True)
    output_path = DATA_DIR / f"premier_league_{season}.csv"

    if output_path.exists():
        print(f"Using existing file: {output_path}")
        return output_path

    url = BASE_URL.format(season=season)
    print(f"Downloading {url}")
    urllib.request.urlretrieve(url, output_path)
    return output_path


def download_understat_json(season: int) -> Path:
    DATA_DIR.mkdir(exist_ok=True)
    output_path = DATA_DIR / f"understat_epl_{season}.json"

    if output_path.exists():
        print(f"Using existing file: {output_path}")
        return output_path

    url = UNDERSTAT_URL.format(season=season)
    print(f"Downloading {url}")
    request = urllib.request.Request(
        url,
        headers={
            "User-Agent": "Mozilla/5.0",
            "Referer": f"https://understat.com/league/EPL/{season}",
            "X-Requested-With": "XMLHttpRequest",
        },
    )
    raw = urllib.request.urlopen(request, timeout=30).read()

    try:
        text = gzip.decompress(raw).decode("utf-8")
    except gzip.BadGzipFile:
        text = raw.decode("utf-8")

    output_path.write_text(text)
    return output_path


def normalize_understat_team(team: str) -> str:
    return UNDERSTAT_TO_FOOTBALL_DATA_TEAMS.get(team, team)


def load_understat_matches() -> pd.DataFrame:
    frames = []

    for football_data_season, understat_season in UNDERSTAT_SEASONS.items():
        path = download_understat_json(understat_season)
        data = json.loads(path.read_text())
        rows = []

        for match in data["dates"]:
            if not match.get("isResult"):
                continue

            rows.append(
                {
                    "Season": football_data_season,
                    "Date": pd.to_datetime(match["datetime"]).date(),
                    "HomeTeam": normalize_understat_team(match["h"]["title"]),
                    "AwayTeam": normalize_understat_team(match["a"]["title"]),
                    "home_xg": float(match["xG"]["h"]),
                    "away_xg": float(match["xG"]["a"]),
                }
            )

        frames.append(pd.DataFrame(rows))

    return pd.concat(frames, ignore_index=True)


def load_matches() -> pd.DataFrame:
    paths = [(season, download_csv(season)) for season in SEASONS]
    frames = []

    for season, path in paths:
        frame = pd.read_csv(path)
        base_columns = ["Date", "HomeTeam", "AwayTeam", "FTHG", "FTAG", "FTR"]
        shot_columns = [column for column in ["HS", "AS", "HST", "AST"] if column in frame.columns]
        frame = frame[base_columns + shot_columns]
        frame["Season"] = season
        frames.append(frame)

    matches = pd.concat(frames, ignore_index=True)
    matches = matches.dropna(subset=["Date", "HomeTeam", "AwayTeam", "FTHG", "FTAG", "FTR"])
    matches["Date"] = pd.to_datetime(matches["Date"], dayfirst=True, errors="coerce")
    matches = matches.dropna(subset=["Date"])
    matches = matches.sort_values("Date").reset_index(drop=True)
    matches["Date"] = matches["Date"].dt.date
    return matches


def load_matches_with_xg() -> pd.DataFrame:
    matches = load_matches()
    understat_matches = load_understat_matches()

    merged = matches.merge(
        understat_matches,
        on=["Season", "Date", "HomeTeam", "AwayTeam"],
        how="left",
        validate="one_to_one",
    )

    missing = merged[merged[["home_xg", "away_xg"]].isna().any(axis=1)]
    if not missing.empty:
        examples = missing[["Season", "Date", "HomeTeam", "AwayTeam"]].head(10).to_dict("records")
        raise ValueError(
            "Could not match every football-data.co.uk match to Understat xG data. "
            f"Missing rows: {len(missing)}. Examples: {examples}"
        )

    return merged


def ensure_injury_template() -> None:
    if INJURY_DATA_PATH.exists():
        return

    DATA_DIR.mkdir(exist_ok=True)
    pd.DataFrame(columns=INJURY_DATA_COLUMNS).to_csv(INJURY_DATA_PATH, index=False)


def load_injury_reports() -> pd.DataFrame:
    ensure_injury_template()
    injuries = pd.read_csv(INJURY_DATA_PATH)

    if injuries.empty:
        return pd.DataFrame(columns=INJURY_DATA_COLUMNS)

    missing_columns = sorted(set(INJURY_DATA_COLUMNS) - set(injuries.columns))
    if missing_columns:
        raise ValueError(f"Missing required injury columns: {missing_columns}")

    for column in ["report_date", "unavailable_from", "expected_return_date"]:
        injuries[column] = pd.to_datetime(injuries[column], errors="coerce").dt.date

    numeric_columns = [
        "is_expected_starter",
        "minutes_played_last_365",
        "xg_contribution_last_365",
        "market_value_eur",
    ]
    for column in numeric_columns:
        injuries[column] = pd.to_numeric(injuries[column], errors="coerce").fillna(0.0)

    injuries = injuries.dropna(subset=["report_date", "team", "player", "unavailable_from"])
    return injuries


def active_injuries_for_team(injuries: pd.DataFrame, team: str, match_date) -> pd.DataFrame:
    if injuries.empty:
        return injuries

    return injuries[
        (injuries["team"] == team)
        & (injuries["report_date"] <= match_date)
        & (injuries["unavailable_from"] <= match_date)
        & (injuries["expected_return_date"].isna() | (injuries["expected_return_date"] >= match_date))
    ]


def injury_totals(active_injuries: pd.DataFrame) -> dict[str, float]:
    if active_injuries.empty:
        return {
            "number_of_injured_starters": 0.0,
            "missing_minutes_played": 0.0,
            "missing_xg_contribution": 0.0,
            "missing_market_value": 0.0,
        }

    starters = active_injuries[active_injuries["is_expected_starter"] >= 1]
    return {
        "number_of_injured_starters": float(starters["player"].nunique()),
        "missing_minutes_played": float(active_injuries["minutes_played_last_365"].sum()),
        "missing_xg_contribution": float(active_injuries["xg_contribution_last_365"].sum()),
        "missing_market_value": float(active_injuries["market_value_eur"].sum()),
    }


def add_injury_features(matches: pd.DataFrame, injuries: pd.DataFrame) -> pd.DataFrame:
    rows = []

    for _, row in matches.iterrows():
        home_totals = injury_totals(active_injuries_for_team(injuries, row["HomeTeam"], row["Date"]))
        away_totals = injury_totals(active_injuries_for_team(injuries, row["AwayTeam"], row["Date"]))
        rows.append(
            {
                "home_number_of_injured_starters": home_totals["number_of_injured_starters"],
                "away_number_of_injured_starters": away_totals["number_of_injured_starters"],
                "home_missing_minutes_played": home_totals["missing_minutes_played"],
                "away_missing_minutes_played": away_totals["missing_minutes_played"],
                "home_missing_xg_contribution": home_totals["missing_xg_contribution"],
                "away_missing_xg_contribution": away_totals["missing_xg_contribution"],
                "home_missing_market_value": home_totals["missing_market_value"],
                "away_missing_market_value": away_totals["missing_market_value"],
            }
        )

    injury_features = pd.DataFrame(rows)
    return pd.concat([matches.reset_index(drop=True), injury_features], axis=1)


def points_for_team(row: pd.Series, team: str) -> int:
    if row["FTR"] == "D":
        return 1

    home_team_won = row["FTR"] == "H"
    if row["HomeTeam"] == team:
        return 3 if home_team_won else 0

    return 0 if home_team_won else 3


def average(values: list[float]) -> float:
    return sum(values) / len(values) if values else 0.0


def average_last(values: list[float], window: int) -> float:
    return average(values[-window:])


MIN_SEASON_AVERAGE_MATCHES = 5
SEASON_AVERAGE_FALLBACK_WINDOW = 10


def average_current_season(values: list[float], seasons: list[str], current_season: str) -> float:
    season_values = [value for value, season in zip(values, seasons) if str(season) == str(current_season)]
    if len(season_values) >= MIN_SEASON_AVERAGE_MATCHES:
        return average(season_values)
    return average_last(values, SEASON_AVERAGE_FALLBACK_WINDOW)


def days_between(current_date, previous_date) -> float:
    return float((current_date - previous_date).days)


def days_since_last_match(match_dates: list, current_date) -> float:
    if not match_dates:
        return 14.0
    return days_between(current_date, match_dates[-1])


def matches_in_last_days(match_dates: list, current_date, days: int) -> int:
    return sum(1 for match_date in match_dates if 0 < (current_date - match_date).days <= days)


def had_midweek_match(match_dates: list, current_date) -> int:
    recent_dates = [match_date for match_date in match_dates if 0 < (current_date - match_date).days <= 7]
    return int(any(match_date.weekday() in {1, 2, 3} for match_date in recent_dates))


def build_features(
    matches: pd.DataFrame,
    include_xg: bool = False,
    include_schedule: bool = False,
    include_injuries: bool = False,
    include_shot_volume: bool = False,
) -> tuple[pd.DataFrame, dict[str, dict[str, list[float]]]]:
    team_history: dict[str, dict[str, list[float]]] = {}
    feature_rows = []

    for _, row in matches.iterrows():
        home_team = row["HomeTeam"]
        away_team = row["AwayTeam"]

        for team in (home_team, away_team):
            team_history.setdefault(
                team,
                {
                    "points": [],
                    "goals_scored": [],
                    "xg": [],
                    "xga": [],
                    "match_dates": [],
                    "shots": [],
                    "shots_on_target": [],
                    "shot_seasons": [],
                },
            )

        home_points = team_history[home_team]["points"][-5:]
        away_points = team_history[away_team]["points"][-5:]
        home_goals = team_history[home_team]["goals_scored"][-5:]
        away_goals = team_history[away_team]["goals_scored"][-5:]
        home_xg = team_history[home_team]["xg"][-5:]
        away_xg = team_history[away_team]["xg"][-5:]
        home_xga = team_history[home_team]["xga"][-5:]
        away_xga = team_history[away_team]["xga"][-5:]
        current_date = row["Date"]
        home_match_dates = team_history[home_team]["match_dates"]
        away_match_dates = team_history[away_team]["match_dates"]

        feature_row = {
            "home_team_points_last_5": sum(home_points),
            "away_team_points_last_5": sum(away_points),
            "home_goals_scored_avg": average(home_goals),
            "away_goals_scored_avg": average(away_goals),
            "home_advantage": 1,
            "target": RESULT_TO_LABEL[row["FTR"]],
        }

        if include_xg:
            home_xg_avg = average(home_xg)
            away_xg_avg = average(away_xg)
            home_xga_avg = average(home_xga)
            away_xga_avg = average(away_xga)
            feature_row.update(
                {
                    "home_xg_avg": home_xg_avg,
                    "away_xg_avg": away_xg_avg,
                    "home_xga_avg": home_xga_avg,
                    "away_xga_avg": away_xga_avg,
                    "home_xg_diff": home_xg_avg - home_xga_avg,
                    "away_xg_diff": away_xg_avg - away_xga_avg,
                }
            )

        if include_schedule:
            home_days_since_last = days_since_last_match(home_match_dates, current_date)
            away_days_since_last = days_since_last_match(away_match_dates, current_date)
            feature_row.update(
                {
                    "home_days_rest": home_days_since_last,
                    "away_days_rest": away_days_since_last,
                    "home_matches_last_14_days": matches_in_last_days(home_match_dates, current_date, 14),
                    "away_matches_last_14_days": matches_in_last_days(away_match_dates, current_date, 14),
                    "home_had_midweek_match": had_midweek_match(home_match_dates, current_date),
                    "away_had_midweek_match": had_midweek_match(away_match_dates, current_date),
                    "home_days_since_last_match": home_days_since_last,
                    "away_days_since_last_match": away_days_since_last,
                }
            )

        if include_shot_volume:
            current_season = str(row["Season"])
            home_shots = team_history[home_team]["shots"]
            away_shots = team_history[away_team]["shots"]
            home_sot = team_history[home_team]["shots_on_target"]
            away_sot = team_history[away_team]["shots_on_target"]
            home_shot_seasons = team_history[home_team]["shot_seasons"]
            away_shot_seasons = team_history[away_team]["shot_seasons"]
            feature_row.update(
                {
                    "home_shots_avg_last5": average_last(home_shots, 5),
                    "away_shots_avg_last5": average_last(away_shots, 5),
                    "home_shots_on_target_avg_last5": average_last(home_sot, 5),
                    "away_shots_on_target_avg_last5": average_last(away_sot, 5),
                    "home_shots_avg_last10": average_last(home_shots, 10),
                    "away_shots_avg_last10": average_last(away_shots, 10),
                    "home_shots_on_target_avg_last10": average_last(home_sot, 10),
                    "away_shots_on_target_avg_last10": average_last(away_sot, 10),
                    "home_shots_avg_season": average_current_season(home_shots, home_shot_seasons, current_season),
                    "away_shots_avg_season": average_current_season(away_shots, away_shot_seasons, current_season),
                    "home_shots_on_target_avg_season": average_current_season(home_sot, home_shot_seasons, current_season),
                    "away_shots_on_target_avg_season": average_current_season(away_sot, away_shot_seasons, current_season),
                }
            )

        if include_injuries:
            feature_row.update(
                {
                    "home_number_of_injured_starters": float(row.get("home_number_of_injured_starters", 0.0)),
                    "away_number_of_injured_starters": float(row.get("away_number_of_injured_starters", 0.0)),
                    "home_missing_minutes_played": float(row.get("home_missing_minutes_played", 0.0)),
                    "away_missing_minutes_played": float(row.get("away_missing_minutes_played", 0.0)),
                    "home_missing_xg_contribution": float(row.get("home_missing_xg_contribution", 0.0)),
                    "away_missing_xg_contribution": float(row.get("away_missing_xg_contribution", 0.0)),
                    "home_missing_market_value": float(row.get("home_missing_market_value", 0.0)),
                    "away_missing_market_value": float(row.get("away_missing_market_value", 0.0)),
                }
            )

        feature_rows.append(feature_row)

        team_history[home_team]["points"].append(points_for_team(row, home_team))
        team_history[away_team]["points"].append(points_for_team(row, away_team))
        team_history[home_team]["goals_scored"].append(float(row["FTHG"]))
        team_history[away_team]["goals_scored"].append(float(row["FTAG"]))
        if include_xg:
            team_history[home_team]["xg"].append(float(row["home_xg"]))
            team_history[away_team]["xg"].append(float(row["away_xg"]))
            team_history[home_team]["xga"].append(float(row["away_xg"]))
            team_history[away_team]["xga"].append(float(row["home_xg"]))
        if include_schedule:
            team_history[home_team]["match_dates"].append(current_date)
            team_history[away_team]["match_dates"].append(current_date)
        if include_shot_volume:
            team_history[home_team]["shots"].append(float(row.get("HS", 0.0)))
            team_history[away_team]["shots"].append(float(row.get("AS", 0.0)))
            team_history[home_team]["shots_on_target"].append(float(row.get("HST", 0.0)))
            team_history[away_team]["shots_on_target"].append(float(row.get("AST", 0.0)))
            team_history[home_team]["shot_seasons"].append(str(row["Season"]))
            team_history[away_team]["shot_seasons"].append(str(row["Season"]))

    return pd.DataFrame(feature_rows), team_history


def multiclass_brier_score(y_true: pd.Series, probabilities) -> float:
    y_one_hot = label_binarize(y_true, classes=[0, 1, 2])
    return float(((probabilities - y_one_hot) ** 2).sum(axis=1).mean())


def mean_absolute_calibration_error(y_true: pd.Series, probabilities, bins: int = 10) -> float:
    y_one_hot = label_binarize(y_true, classes=[0, 1, 2])
    bin_edges = [index / bins for index in range(bins + 1)]
    total_weighted_error = 0.0
    total_count = 0

    for class_index in range(3):
        class_probabilities = probabilities[:, class_index]
        class_actuals = y_one_hot[:, class_index]

        for bin_index in range(bins):
            lower = bin_edges[bin_index]
            upper = bin_edges[bin_index + 1]
            if bin_index == bins - 1:
                mask = (class_probabilities >= lower) & (class_probabilities <= upper)
            else:
                mask = (class_probabilities >= lower) & (class_probabilities < upper)

            if not mask.any():
                continue

            total_weighted_error += abs(class_actuals[mask].mean() - class_probabilities[mask].mean()) * mask.sum()
            total_count += int(mask.sum())

    return float(total_weighted_error / total_count)


def train_and_evaluate_model(
    XGBClassifier,
    dataset: pd.DataFrame,
    feature_columns: list[str],
    dates: pd.Series,
) -> tuple[XGBClassifier, dict[str, float]]:
    X = dataset[feature_columns]
    y = dataset["target"]
    split_index = int(len(X) * 0.8)
    cutoff_date = dates.iloc[split_index]
    train_mask = dates < cutoff_date
    test_mask = dates >= cutoff_date

    X_train = X.loc[train_mask]
    X_test = X.loc[test_mask]
    y_train = y.loc[train_mask]
    y_test = y.loc[test_mask]

    model = XGBClassifier(
        objective="multi:softprob",
        num_class=3,
        n_estimators=150,
        max_depth=3,
        learning_rate=0.05,
        subsample=0.9,
        colsample_bytree=1.0,
        eval_metric="mlogloss",
        random_state=42,
    )
    model.fit(X_train, y_train)

    probabilities = model.predict_proba(X_test)
    predictions = model.predict(X_test)

    accuracy = accuracy_score(y_test, predictions)
    loss = log_loss(y_test, probabilities, labels=[0, 1, 2])
    return model, {
        "accuracy": accuracy,
        "log_loss": loss,
        "brier_score": multiclass_brier_score(y_test, probabilities),
        "mean_absolute_calibration_error": mean_absolute_calibration_error(y_test, probabilities),
        "train_rows": int(len(X_train)),
        "test_rows": int(len(X_test)),
        "test_start_date": str(cutoff_date),
    }


def save_model(
    path: Path,
    model,
    feature_columns: list[str],
    team_history: dict[str, dict[str, list[float]]],
    extra_metadata: dict[str, object] | None = None,
) -> None:
    artifact = {
        "model": model,
        "feature_columns": feature_columns,
        "team_history": team_history,
        "label_to_result": LABEL_TO_RESULT,
    }
    if extra_metadata:
        artifact.update(extra_metadata)
    joblib.dump(artifact, path)


def train(mode: str = "production") -> None:
    if mode not in {"production", "research"}:
        raise ValueError("mode must be 'production' or 'research'")

    XGBClassifier = get_xgb_classifier()

    matches = load_matches_with_xg()
    injuries = load_injury_reports()
    matches_with_injuries = add_injury_features(matches, injuries)

    if injuries.empty:
        print(f"No injury rows found. Created/used injury template at: {INJURY_DATA_PATH}")

    baseline_dataset, baseline_team_history = build_features(matches, include_xg=False)
    xg_dataset, xg_team_history = build_features(matches, include_xg=True)
    schedule_dataset, schedule_team_history = build_features(matches, include_xg=True, include_schedule=True)
    production_base_dataset, production_team_history = build_features(
        matches,
        include_xg=True,
        include_schedule=True,
        include_shot_volume=True,
    )
    elo_features, _ = build_elo_features(matches, ELO_CONFIG)
    production_dataset = pd.concat(
        [production_base_dataset.reset_index(drop=True), elo_features.reset_index(drop=True)],
        axis=1,
    )
    elo_state = build_current_elo_state(matches, ELO_CONFIG)
    injury_dataset, injury_team_history = build_features(
        matches_with_injuries,
        include_xg=True,
        include_schedule=True,
        include_injuries=True,
    )

    baseline_model, baseline_metrics = train_and_evaluate_model(
        XGBClassifier,
        baseline_dataset,
        FEATURE_COLUMNS,
        matches["Date"],
    )
    xg_model, xg_metrics = train_and_evaluate_model(
        XGBClassifier,
        xg_dataset,
        XG_FEATURE_COLUMNS,
        matches["Date"],
    )
    schedule_model, schedule_metrics = train_and_evaluate_model(
        XGBClassifier,
        schedule_dataset,
        SCHEDULE_FEATURE_COLUMNS,
        matches["Date"],
    )
    production_model, production_metrics = train_and_evaluate_model(
        XGBClassifier,
        production_dataset,
        PRODUCTION_FEATURE_COLUMNS,
        matches["Date"],
    )
    injury_model, injury_metrics = train_and_evaluate_model(
        XGBClassifier,
        injury_dataset,
        INJURY_FEATURE_COLUMNS,
        matches["Date"],
    )

    MODEL_DIR.mkdir(exist_ok=True)
    save_model(BASELINE_MODEL_PATH, baseline_model, FEATURE_COLUMNS, baseline_team_history)
    save_model(XG_MODEL_PATH, xg_model, XG_FEATURE_COLUMNS, xg_team_history)
    save_model(XG_SCHEDULE_MODEL_PATH, schedule_model, SCHEDULE_FEATURE_COLUMNS, schedule_team_history)
    if mode == "production":
        save_model(
            MODEL_PATH,
            production_model,
            PRODUCTION_FEATURE_COLUMNS,
            production_team_history,
            {
                "elo_state": elo_state,
                "elo_config": {
                    "k_factor": ELO_CONFIG.k_factor,
                    "home_advantage": ELO_CONFIG.home_advantage,
                    "margin_of_victory": ELO_CONFIG.margin_of_victory,
                    "initial_rating": ELO_CONFIG.initial_rating,
                    "season_carryover": ELO_CONFIG.season_carryover,
                    "name": ELO_CONFIG.name,
                },
                "production_model_version": "xg_schedule_elo_shot_volume",
            },
        )
    else:
        research_model_path = MODEL_DIR / "football_model_xg_schedule_injury_research.joblib"
        save_model(research_model_path, injury_model, INJURY_FEATURE_COLUMNS, injury_team_history)

    metrics = {
        "baseline": baseline_metrics,
        "xg_model": xg_metrics,
        "xg_schedule_model": schedule_metrics,
        "xg_schedule_elo_shot_volume_model": production_metrics,
        "xg_schedule_injury_model": injury_metrics,
        "comparison": {
            "accuracy_change": xg_metrics["accuracy"] - baseline_metrics["accuracy"],
            "log_loss_change": xg_metrics["log_loss"] - baseline_metrics["log_loss"],
            "brier_score_change": xg_metrics["brier_score"] - baseline_metrics["brier_score"],
            "calibration_error_change": (
                xg_metrics["mean_absolute_calibration_error"]
                - baseline_metrics["mean_absolute_calibration_error"]
            ),
        },
        "schedule_comparison": {
            "accuracy_change_vs_xg": schedule_metrics["accuracy"] - xg_metrics["accuracy"],
            "log_loss_change_vs_xg": schedule_metrics["log_loss"] - xg_metrics["log_loss"],
            "brier_score_change_vs_xg": schedule_metrics["brier_score"] - xg_metrics["brier_score"],
            "calibration_error_change_vs_xg": (
                schedule_metrics["mean_absolute_calibration_error"]
                - xg_metrics["mean_absolute_calibration_error"]
            ),
        },
        "injury_comparison": {
            "accuracy_change_vs_schedule": injury_metrics["accuracy"] - schedule_metrics["accuracy"],
            "log_loss_change_vs_schedule": injury_metrics["log_loss"] - schedule_metrics["log_loss"],
            "brier_score_change_vs_schedule": injury_metrics["brier_score"] - schedule_metrics["brier_score"],
            "calibration_error_change_vs_schedule": (
                injury_metrics["mean_absolute_calibration_error"]
                - schedule_metrics["mean_absolute_calibration_error"]
            ),
        },
        "elo_comparison": {
            "accuracy_change_vs_schedule": production_metrics["accuracy"] - schedule_metrics["accuracy"],
            "log_loss_change_vs_schedule": production_metrics["log_loss"] - schedule_metrics["log_loss"],
            "brier_score_change_vs_schedule": production_metrics["brier_score"] - schedule_metrics["brier_score"],
            "calibration_error_change_vs_schedule": (
                production_metrics["mean_absolute_calibration_error"]
                - schedule_metrics["mean_absolute_calibration_error"]
            ),
        },
    }
    (MODEL_DIR / "metrics.json").write_text(json.dumps(metrics, indent=2))

    print(f"Rows used: {len(xg_dataset)}")
    print("\nBaseline model")
    print(f"Accuracy: {baseline_metrics['accuracy']:.4f}")
    print(f"Log loss: {baseline_metrics['log_loss']:.4f}")
    print("\nxG model")
    print(f"Accuracy: {xg_metrics['accuracy']:.4f}")
    print(f"Log loss: {xg_metrics['log_loss']:.4f}")
    print(f"Brier score: {xg_metrics['brier_score']:.4f}")
    print(f"Calibration error: {xg_metrics['mean_absolute_calibration_error']:.4f}")
    print("\nxG + schedule model")
    print(f"Accuracy: {schedule_metrics['accuracy']:.4f}")
    print(f"Log loss: {schedule_metrics['log_loss']:.4f}")
    print(f"Brier score: {schedule_metrics['brier_score']:.4f}")
    print(f"Calibration error: {schedule_metrics['mean_absolute_calibration_error']:.4f}")
    print("\nProduction xG + schedule + Elo + shot volume model")
    print(f"Accuracy: {production_metrics['accuracy']:.4f}")
    print(f"Log loss: {production_metrics['log_loss']:.4f}")
    print(f"Brier score: {production_metrics['brier_score']:.4f}")
    print(f"Calibration error: {production_metrics['mean_absolute_calibration_error']:.4f}")
    print("\nxG + schedule + injuries model")
    print(f"Accuracy: {injury_metrics['accuracy']:.4f}")
    print(f"Log loss: {injury_metrics['log_loss']:.4f}")
    print(f"Brier score: {injury_metrics['brier_score']:.4f}")
    print(f"Calibration error: {injury_metrics['mean_absolute_calibration_error']:.4f}")
    print("\nComparison")
    print(f"Accuracy change: {metrics['comparison']['accuracy_change']:+.4f}")
    print(f"Log loss change: {metrics['comparison']['log_loss_change']:+.4f}")
    print(f"Schedule log loss change vs xG: {metrics['schedule_comparison']['log_loss_change_vs_xg']:+.4f}")
    print(f"Schedule Brier change vs xG: {metrics['schedule_comparison']['brier_score_change_vs_xg']:+.4f}")
    print(f"Schedule calibration change vs xG: {metrics['schedule_comparison']['calibration_error_change_vs_xg']:+.4f}")
    print(f"Injury log loss change vs schedule: {metrics['injury_comparison']['log_loss_change_vs_schedule']:+.4f}")
    print(f"Injury Brier change vs schedule: {metrics['injury_comparison']['brier_score_change_vs_schedule']:+.4f}")
    print(f"Injury calibration change vs schedule: {metrics['injury_comparison']['calibration_error_change_vs_schedule']:+.4f}")
    print(f"Elo log loss change vs schedule: {metrics['elo_comparison']['log_loss_change_vs_schedule']:+.4f}")
    print(f"Elo Brier change vs schedule: {metrics['elo_comparison']['brier_score_change_vs_schedule']:+.4f}")
    print(f"Elo calibration change vs schedule: {metrics['elo_comparison']['calibration_error_change_vs_schedule']:+.4f}")
    print(f"Training mode: {mode}")
    if mode == "production":
        print(f"Saved production xG + schedule + Elo + shot volume model to: {MODEL_PATH}")
    else:
        print(f"Saved research xG + schedule + injuries model to: {MODEL_DIR / 'football_model_xg_schedule_injury_research.joblib'}")
        print(f"Production model unchanged at: {MODEL_PATH}")
    print(f"Saved xG + schedule model to: {XG_SCHEDULE_MODEL_PATH}")
    print(f"Saved xG model to: {XG_MODEL_PATH}")
    print(f"Saved baseline model to: {BASELINE_MODEL_PATH}")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Train Premier League prediction models.")
    parser.add_argument(
        "--mode",
        choices=["production", "research"],
        default="production",
        help="production uses safe historical form/xG/fatigue features; research trains template injury features to a separate research artifact.",
    )
    return parser.parse_args()


if __name__ == "__main__":
    args = parse_args()
    train(mode=args.mode)
