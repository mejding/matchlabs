from __future__ import annotations

from pathlib import Path

import pandas as pd


INJURY_PATH = Path("data") / "injuries.csv"
INJURY_COLUMNS = [
    "report_date",
    "team",
    "player",
    "unavailable_from",
    "expected_return_date",
    "status_type",
    "injury_or_suspension",
    "is_expected_starter",
    "is_key_player",
    "is_long_term_injury",
    "is_suspended",
    "minutes_played_last_365",
    "goals_last_365",
    "xg_contribution_last_365",
    "xa_contribution_last_365",
    "defensive_contribution_last_365",
    "market_value_eur",
    "source",
    "source_url",
    "source_collected_at",
]

INJURY_FEATURES = [
    "injured_players_count",
    "injured_starters_count",
    "injured_expected_starters",
    "suspended_players_count",
    "suspended_expected_starters",
    "missing_minutes",
    "missing_minutes_played",
    "missing_goals",
    "missing_xg",
    "missing_xg_contribution",
    "missing_xa",
    "missing_market_value",
    "missing_defensive_contribution",
]


def ensure_injury_template(path: Path = INJURY_PATH) -> None:
    path.parent.mkdir(exist_ok=True)
    if not path.exists():
        pd.DataFrame(columns=INJURY_COLUMNS).to_csv(path, index=False)


def load_historical_injuries(path: Path = INJURY_PATH) -> pd.DataFrame:
    ensure_injury_template(path)
    injuries = pd.read_csv(path)
    if injuries.empty:
        return pd.DataFrame(columns=INJURY_COLUMNS)

    injuries = injuries.copy()
    for column in INJURY_COLUMNS:
        if column not in injuries.columns:
            injuries[column] = (
                0.0
                if column
                not in {
                    "report_date",
                    "team",
                    "player",
                    "unavailable_from",
                    "expected_return_date",
                    "status_type",
                    "injury_or_suspension",
                    "source",
                    "source_url",
                    "source_collected_at",
                }
                else pd.NA
            )

    date_columns = ["report_date", "unavailable_from", "expected_return_date"]
    for column in date_columns:
        injuries[column] = pd.to_datetime(injuries[column], errors="coerce")

    numeric_columns = [
        "is_expected_starter",
        "is_key_player",
        "is_long_term_injury",
        "is_suspended",
        "minutes_played_last_365",
        "goals_last_365",
        "xg_contribution_last_365",
        "xa_contribution_last_365",
        "defensive_contribution_last_365",
        "market_value_eur",
    ]
    for column in numeric_columns:
        injuries[column] = pd.to_numeric(injuries[column], errors="coerce").fillna(0.0)

    return injuries.dropna(subset=["report_date", "team", "player", "unavailable_from"]).reset_index(drop=True)


def active_injuries(injuries: pd.DataFrame, team: str, match_date: pd.Timestamp) -> pd.DataFrame:
    if injuries.empty:
        return injuries

    current_date = pd.to_datetime(match_date)
    return injuries[
        (injuries["team"] == team)
        & (injuries["report_date"] <= current_date)
        & (injuries["unavailable_from"] <= current_date)
        & (injuries["expected_return_date"].isna() | (injuries["expected_return_date"] >= current_date))
    ]


def injury_feature_totals(active: pd.DataFrame) -> dict[str, float]:
    if active.empty:
        return {feature: 0.0 for feature in INJURY_FEATURES}

    suspended = active[(active["is_suspended"] >= 1) | (active["status_type"].astype(str).str.lower() == "suspension")]
    injured = active.drop(suspended.index)
    injured_starters = injured[injured["is_expected_starter"] >= 1]
    suspended_starters = suspended[suspended["is_expected_starter"] >= 1]
    return {
        "injured_players_count": float(injured["player"].nunique()),
        "injured_starters_count": float(injured_starters["player"].nunique()),
        "injured_expected_starters": float(injured_starters["player"].nunique()),
        "suspended_players_count": float(suspended["player"].nunique()),
        "suspended_expected_starters": float(suspended_starters["player"].nunique()),
        "missing_minutes": float(active["minutes_played_last_365"].sum()),
        "missing_minutes_played": float(active["minutes_played_last_365"].sum()),
        "missing_goals": float(active["goals_last_365"].sum()),
        "missing_xg": float(active["xg_contribution_last_365"].sum()),
        "missing_xg_contribution": float(active["xg_contribution_last_365"].sum()),
        "missing_xa": float(active["xa_contribution_last_365"].sum()),
        "missing_market_value": float(active["market_value_eur"].sum()),
        "missing_defensive_contribution": float(active["defensive_contribution_last_365"].sum()),
    }


def build_injury_features(matches: pd.DataFrame, injuries: pd.DataFrame | None = None) -> pd.DataFrame:
    injury_rows = []
    injury_data = injuries if injuries is not None else load_historical_injuries()

    for _, match in matches.sort_values("Date").iterrows():
        current_date = pd.to_datetime(match["Date"])
        home = injury_feature_totals(active_injuries(injury_data, match["HomeTeam"], current_date))
        away = injury_feature_totals(active_injuries(injury_data, match["AwayTeam"], current_date))

        row = {}
        for feature, value in home.items():
            row[f"home_{feature}"] = value
        for feature, value in away.items():
            row[f"away_{feature}"] = value
        injury_rows.append(row)

    return pd.DataFrame(injury_rows)


def injury_feature_columns() -> list[str]:
    return [f"{side}_{feature}" for side in ("home", "away") for feature in INJURY_FEATURES]


def historical_injury_pipeline_note() -> str:
    return (
        "Injury rows are included only when report_date and unavailable_from are on or before "
        "the match date, and expected_return_date is blank or on/after the match date."
    )
