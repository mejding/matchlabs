from __future__ import annotations

from pathlib import Path

import pandas as pd


DATA_DIR = Path("data")
MATCH_LINEUPS_PATH = DATA_DIR / "match_lineups.csv"
PLAYER_APPEARANCES_PATH = DATA_DIR / "player_appearances.csv"
FORMATION_HISTORY_PATH = DATA_DIR / "formation_history.csv"
MATCH_SUBSTITUTIONS_PATH = DATA_DIR / "match_substitutions.csv"
MANAGER_HISTORY_PATH = DATA_DIR / "manager_history.csv"

MATCH_LINEUPS_COLUMNS = [
    "match_id",
    "season",
    "date",
    "team",
    "opponent",
    "is_home",
    "formation",
    "captain",
    "lineup_type",
    "source",
    "source_collected_at",
]
PLAYER_APPEARANCES_COLUMNS = [
    "match_id",
    "season",
    "date",
    "team",
    "opponent",
    "player",
    "position",
    "position_group",
    "started",
    "is_substitute",
    "minutes",
    "sub_on_minute",
    "sub_off_minute",
    "lineup_type",
    "source",
    "source_collected_at",
]
FORMATION_HISTORY_COLUMNS = [
    "match_id",
    "season",
    "date",
    "team",
    "formation",
    "manager",
    "source",
    "source_collected_at",
]
MATCH_SUBSTITUTIONS_COLUMNS = [
    "match_id",
    "season",
    "date",
    "team",
    "player_off",
    "player_on",
    "minute",
    "source",
    "source_collected_at",
]
MANAGER_HISTORY_COLUMNS = [
    "team",
    "manager",
    "start_date",
    "end_date",
    "source",
    "source_collected_at",
]


def ensure_lineup_tables() -> None:
    DATA_DIR.mkdir(exist_ok=True)
    templates = {
        MATCH_LINEUPS_PATH: MATCH_LINEUPS_COLUMNS,
        PLAYER_APPEARANCES_PATH: PLAYER_APPEARANCES_COLUMNS,
        FORMATION_HISTORY_PATH: FORMATION_HISTORY_COLUMNS,
        MATCH_SUBSTITUTIONS_PATH: MATCH_SUBSTITUTIONS_COLUMNS,
        MANAGER_HISTORY_PATH: MANAGER_HISTORY_COLUMNS,
    }
    for path, columns in templates.items():
        if not path.exists():
            pd.DataFrame(columns=columns).to_csv(path, index=False)


def _read_table(path: Path, columns: list[str], date_columns: list[str]) -> pd.DataFrame:
    ensure_lineup_tables()
    frame = pd.read_csv(path)
    if frame.empty:
        return pd.DataFrame(columns=columns)

    for column in columns:
        if column not in frame.columns:
            frame[column] = pd.NA
    for column in date_columns:
        frame[column] = pd.to_datetime(frame[column], errors="coerce")
    return frame[columns].copy()


def load_match_lineups() -> pd.DataFrame:
    return _read_table(MATCH_LINEUPS_PATH, MATCH_LINEUPS_COLUMNS, ["date", "source_collected_at"])


def load_player_appearances() -> pd.DataFrame:
    frame = _read_table(PLAYER_APPEARANCES_PATH, PLAYER_APPEARANCES_COLUMNS, ["date", "source_collected_at"])
    for column in ["started", "is_substitute", "minutes", "sub_on_minute", "sub_off_minute"]:
        if column in frame.columns:
            frame[column] = pd.to_numeric(frame[column], errors="coerce").fillna(0.0)
    return frame


def load_formation_history() -> pd.DataFrame:
    return _read_table(FORMATION_HISTORY_PATH, FORMATION_HISTORY_COLUMNS, ["date", "source_collected_at"])


def load_manager_history() -> pd.DataFrame:
    return _read_table(MANAGER_HISTORY_PATH, MANAGER_HISTORY_COLUMNS, ["start_date", "end_date", "source_collected_at"])


def make_match_id(season: str, date: object, home_team: str, away_team: str) -> str:
    date_text = pd.to_datetime(date).strftime("%Y%m%d")
    home_slug = str(home_team).lower().replace(" ", "_").replace("'", "")
    away_slug = str(away_team).lower().replace(" ", "_").replace("'", "")
    return f"{season}_{date_text}_{home_slug}_{away_slug}"


def lineup_data_note() -> str:
    return (
        "Lineup tables are normalized CSV inputs. For pre-match validation, features only use "
        "rows with source_collected_at strictly before the match date unless the row is marked "
        "as an expected lineup. Actual current-match starting XIs are not used as pre-match features."
    )
