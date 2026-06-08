from __future__ import annotations

import argparse
import json
import os
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import pandas as pd

from lineup_data import (
    FORMATION_HISTORY_COLUMNS,
    FORMATION_HISTORY_PATH,
    MATCH_LINEUPS_COLUMNS,
    MATCH_LINEUPS_PATH,
    MATCH_SUBSTITUTIONS_COLUMNS,
    MATCH_SUBSTITUTIONS_PATH,
    PLAYER_APPEARANCES_COLUMNS,
    PLAYER_APPEARANCES_PATH,
    make_match_id,
)
from train_model import UNDERSTAT_TO_FOOTBALL_DATA_TEAMS, load_matches


DEFAULT_SEASONS = [2019, 2020, 2021, 2022, 2023, 2024, 2025]
FBREF_CACHE_DIR = Path("data") / "fbref" / "soccerdata_cache"
RAW_EXPORT_DIR = Path("data") / "fbref" / "lineup_exports"
LINEUP_RAW_PATH = Path("data") / "fbref_lineups_raw.csv"
SCHEDULE_RAW_PATH = Path("data") / "fbref_schedule_raw.csv"


TEAM_ALIASES = {
    **UNDERSTAT_TO_FOOTBALL_DATA_TEAMS,
    "Manchester Utd": "Man United",
    "Manchester United": "Man United",
    "Manchester City": "Man City",
    "Brighton & Hove Albion": "Brighton",
    "Ipswich Town": "Ipswich",
    "Leicester City": "Leicester",
    "Newcastle Utd": "Newcastle",
    "Newcastle United": "Newcastle",
    "Nott'ham Forest": "Nott'm Forest",
    "Nottingham Forest": "Nott'm Forest",
    "Tottenham Hotspur": "Tottenham",
    "West Ham United": "West Ham",
    "Wolverhampton Wanderers": "Wolves",
    "Wolves": "Wolves",
}

POSITION_GROUPS = {
    "GK": "goalkeeper",
    "G": "goalkeeper",
    "CB": "defender",
    "LB": "defender",
    "RB": "defender",
    "WB": "defender",
    "LWB": "defender",
    "RWB": "defender",
    "DF": "defender",
    "CM": "midfielder",
    "DM": "midfielder",
    "AM": "midfielder",
    "LM": "midfielder",
    "RM": "midfielder",
    "MF": "midfielder",
    "LW": "attacker",
    "RW": "attacker",
    "ST": "attacker",
    "CF": "attacker",
    "FW": "attacker",
}


@dataclass(frozen=True)
class FbrefLineupIngestionResult:
    raw_rows: int
    match_lineup_rows: int
    player_appearance_rows: int
    formation_rows: int
    substitution_rows: int
    matched_team_rows: int
    unmatched_team_rows: int
    output_files: dict[str, str]


def normalize_team_name(team: object) -> str:
    text = str(team).strip()
    return TEAM_ALIASES.get(text, text)


def normalize_position_group(position: object) -> str:
    if pd.isna(position):
        return "unknown"
    tokens = str(position).replace(",", " ").replace("/", " ").split()
    for token in tokens:
        group = POSITION_GROUPS.get(token.upper())
        if group:
            return group
    return "unknown"


def _flatten_columns(frame: pd.DataFrame) -> pd.DataFrame:
    frame = frame.copy()
    if isinstance(frame.columns, pd.MultiIndex):
        frame.columns = [
            "_".join(str(part) for part in column if str(part) and str(part) != "nan").strip("_")
            for column in frame.columns
        ]
    else:
        frame.columns = [str(column) for column in frame.columns]
    return frame.reset_index()


def _first_column(frame: pd.DataFrame, names: list[str]) -> str | None:
    normalized = {column.lower().replace(" ", "_"): column for column in frame.columns}
    for name in names:
        key = name.lower().replace(" ", "_")
        if key in normalized:
            return normalized[key]
    for column in frame.columns:
        column_key = column.lower().replace(" ", "_")
        if any(column_key.endswith("_" + name.lower().replace(" ", "_")) for name in names):
            return column
    return None


def _series(frame: pd.DataFrame, names: list[str], default: object = pd.NA) -> pd.Series:
    column = _first_column(frame, names)
    if column is None:
        return pd.Series([default] * len(frame))
    return frame[column]


def _markdown_table(frame: pd.DataFrame) -> str:
    if frame.empty:
        return "No validation rows."
    columns = list(frame.columns)
    header = "| " + " | ".join(columns) + " |"
    separator = "| " + " | ".join(["---"] * len(columns)) + " |"
    rows = []
    for _, row in frame.iterrows():
        rows.append("| " + " | ".join(str(row[column]) for column in columns) + " |")
    return "\n".join([header, separator] + rows)


def _to_bool_numeric(series: pd.Series) -> pd.Series:
    if pd.api.types.is_bool_dtype(series):
        return series.astype(float)
    text = series.astype(str).str.lower().str.strip()
    return text.isin({"1", "true", "yes", "y", "starter", "start", "starting"}).astype(float)


def _read_local_exports(directory: Path = RAW_EXPORT_DIR) -> pd.DataFrame:
    if not directory.exists():
        return pd.DataFrame()
    frames = []
    for path in sorted(directory.glob("*.csv")):
        frame = pd.read_csv(path)
        if not frame.empty:
            frame["source_file"] = path.name
            frames.append(frame)
    if not frames:
        return pd.DataFrame()
    return pd.concat(frames, ignore_index=True)


def fetch_fbref_lineups(seasons: list[int], force_cache: bool = False) -> pd.DataFrame:
    """Fetch FBref lineups through soccerdata.

    The function intentionally keeps the raw output. Normalization happens in a
    separate step so downloaded evidence can be inspected and reproduced.
    """
    soccerdata_home = Path("data") / "fbref" / "soccerdata_home"
    soccerdata_home.mkdir(parents=True, exist_ok=True)
    os.environ.setdefault("SOCCERDATA_DIR", str(soccerdata_home.resolve()))

    try:
        import soccerdata as sd
    except ImportError as exc:
        raise RuntimeError("soccerdata is not installed. Install it with `pip install soccerdata`.") from exc

    FBREF_CACHE_DIR.mkdir(parents=True, exist_ok=True)
    fbref = sd.FBref(
        leagues="ENG-Premier League",
        seasons=seasons,
        data_dir=FBREF_CACHE_DIR,
        no_cache=not force_cache,
    )
    lineups = fbref.read_lineup(force_cache=force_cache)
    schedule = fbref.read_schedule(force_cache=force_cache)
    lineups = _flatten_columns(lineups)
    schedule = _flatten_columns(schedule)
    lineups["source"] = "fbref_soccerdata"
    schedule.to_csv(SCHEDULE_RAW_PATH, index=False)
    lineups.to_csv(LINEUP_RAW_PATH, index=False)
    return lineups


def _enrich_raw_lineups_with_schedule(raw: pd.DataFrame) -> pd.DataFrame:
    if raw.empty or not SCHEDULE_RAW_PATH.exists():
        return raw

    frame = _flatten_columns(raw)
    schedule = _flatten_columns(pd.read_csv(SCHEDULE_RAW_PATH))
    raw_match_col = _first_column(frame, ["match_id", "game_id", "game"])
    if raw_match_col and raw_match_col.lower().replace(" ", "_") == "game":
        schedule_match_col = _first_column(schedule, ["game"])
    else:
        schedule_match_col = _first_column(schedule, ["match_id", "game_id", "game"])
    if raw_match_col is None or schedule_match_col is None:
        return frame

    keep_columns = [
        column
        for column in schedule.columns
        if column == schedule_match_col
        or column.lower().replace(" ", "_")
        in {"date", "home_team", "away_team", "home", "away", "season", "league", "game"}
    ]
    schedule_small = schedule[keep_columns].drop_duplicates(subset=[schedule_match_col])
    enriched = frame.merge(schedule_small, left_on=raw_match_col, right_on=schedule_match_col, how="left", suffixes=("", "_schedule"))

    team_col = _first_column(enriched, ["team", "squad"])
    home_col = _first_column(enriched, ["home_team", "home"])
    away_col = _first_column(enriched, ["away_team", "away"])
    opponent_col = _first_column(enriched, ["opponent", "opp"])
    if team_col and home_col and away_col and opponent_col is None:
        normalized_team = enriched[team_col].map(normalize_team_name)
        normalized_home = enriched[home_col].map(normalize_team_name)
        normalized_away = enriched[away_col].map(normalize_team_name)
        enriched["opponent"] = normalized_away.where(normalized_team == normalized_home, normalized_home)
    return enriched


def load_or_fetch_raw_lineups(seasons: list[int], fetch: bool = False, force_cache: bool = False) -> pd.DataFrame:
    if LINEUP_RAW_PATH.exists() and LINEUP_RAW_PATH.stat().st_size > 0:
        return pd.read_csv(LINEUP_RAW_PATH)

    local_exports = _read_local_exports()
    if not local_exports.empty:
        local_exports.to_csv(LINEUP_RAW_PATH, index=False)
        return local_exports

    if fetch:
        return fetch_fbref_lineups(seasons, force_cache=force_cache)

    return pd.DataFrame()


def _match_lookup(matches: pd.DataFrame) -> dict[tuple[pd.Timestamp, str, str], dict[str, Any]]:
    lookup = {}
    for _, row in matches.iterrows():
        date = pd.to_datetime(row["Date"]).normalize()
        home = normalize_team_name(row["HomeTeam"])
        away = normalize_team_name(row["AwayTeam"])
        match_id = make_match_id(str(row["Season"]), date, home, away)
        lookup[(date, home, away)] = {"match_id": match_id, "season": row["Season"], "is_home": 1, "opponent": away}
        lookup[(date, away, home)] = {"match_id": match_id, "season": row["Season"], "is_home": 0, "opponent": home}
    return lookup


def normalize_fbref_lineups(raw: pd.DataFrame, matches: pd.DataFrame) -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame, pd.DataFrame, dict[str, int]]:
    if raw.empty:
        return (
            pd.DataFrame(columns=MATCH_LINEUPS_COLUMNS),
            pd.DataFrame(columns=PLAYER_APPEARANCES_COLUMNS),
            pd.DataFrame(columns=FORMATION_HISTORY_COLUMNS),
            pd.DataFrame(columns=MATCH_SUBSTITUTIONS_COLUMNS),
            {"raw_rows": 0, "matched_team_rows": 0, "unmatched_team_rows": 0},
        )

    frame = _enrich_raw_lineups_with_schedule(raw)
    date = pd.to_datetime(_series(frame, ["date", "Date", "match_date"]), errors="coerce").dt.normalize()
    team = _series(frame, ["team", "squad", "Team", "Squad"]).map(normalize_team_name)
    opponent = _series(frame, ["opponent", "opp", "Opponent", "Opp"]).map(normalize_team_name)
    player = _series(frame, ["player", "Player", "name", "Name"])
    position = _series(frame, ["position", "pos", "Position", "Pos"])
    minutes = pd.to_numeric(_series(frame, ["minutes", "minutes_played", "Min"], 0), errors="coerce").fillna(0.0)
    formation = _series(frame, ["formation", "Formation"])
    captain_raw = _series(frame, ["captain", "is_captain"], "")
    starter_source = _series(frame, ["is_starter", "started", "starter", "Start"], pd.NA)
    started = _to_bool_numeric(starter_source)
    if starter_source.isna().all() and "minutes" in frame.columns:
        started = (minutes > 0).astype(float)
    substitute = _to_bool_numeric(_series(frame, ["is_substitute", "substitute", "bench"], 0))
    source = _series(frame, ["source"], "fbref_soccerdata").fillna("fbref_soccerdata")

    lookup = _match_lookup(matches)
    appearance_rows = []
    lineup_rows = {}
    formation_rows = {}
    matched = 0
    unmatched = 0

    for index in range(len(frame)):
        current_date = date.iloc[index]
        current_team = team.iloc[index]
        current_opponent = opponent.iloc[index]
        if pd.isna(current_date) or pd.isna(current_team) or pd.isna(current_opponent):
            unmatched += 1
            continue

        match_meta = lookup.get((current_date, current_team, current_opponent))
        if match_meta is None:
            unmatched += 1
            continue

        matched += 1
        match_id = match_meta["match_id"]
        season = match_meta["season"]
        source_collected_at = current_date + pd.Timedelta(days=1)
        position_value = position.iloc[index]
        base = {
            "match_id": match_id,
            "season": season,
            "date": current_date.date().isoformat(),
            "team": current_team,
            "opponent": match_meta["opponent"],
            "source": str(source.iloc[index]),
            "source_collected_at": source_collected_at.date().isoformat(),
        }
        lineup_rows[(match_id, current_team)] = {
            **base,
            "is_home": match_meta["is_home"],
            "formation": None if pd.isna(formation.iloc[index]) else formation.iloc[index],
            "captain": None if pd.isna(captain_raw.iloc[index]) else captain_raw.iloc[index],
            "lineup_type": "actual",
        }
        formation_rows[(match_id, current_team)] = {
            **base,
            "formation": None if pd.isna(formation.iloc[index]) else formation.iloc[index],
            "manager": pd.NA,
        }
        appearance_rows.append(
            {
                **base,
                "player": player.iloc[index],
                "position": position_value,
                "position_group": normalize_position_group(position_value),
                "started": float(started.iloc[index]),
                "is_substitute": float(substitute.iloc[index]),
                "minutes": float(minutes.iloc[index]),
                "sub_on_minute": 0.0,
                "sub_off_minute": 0.0,
                "lineup_type": "actual",
            }
        )

    appearances = pd.DataFrame(appearance_rows, columns=PLAYER_APPEARANCES_COLUMNS).dropna(subset=["player"])
    lineups = pd.DataFrame(lineup_rows.values(), columns=MATCH_LINEUPS_COLUMNS)
    formations = pd.DataFrame(formation_rows.values(), columns=FORMATION_HISTORY_COLUMNS)
    substitutions = pd.DataFrame(columns=MATCH_SUBSTITUTIONS_COLUMNS)
    stats = {"raw_rows": len(frame), "matched_team_rows": matched, "unmatched_team_rows": unmatched}
    return lineups, appearances, formations, substitutions, stats


def validate_lineup_tables(match_lineups: pd.DataFrame, player_appearances: pd.DataFrame) -> pd.DataFrame:
    if player_appearances.empty:
        return pd.DataFrame(
            [{"check": "player_appearances", "status": "missing", "details": "No historical lineup rows available."}]
        )

    starters = player_appearances[player_appearances["started"] >= 1]
    starter_counts = starters.groupby(["match_id", "team"]).size().reset_index(name="starters")
    team_rows_per_match = match_lineups.groupby("match_id")["team"].nunique() if not match_lineups.empty else pd.Series(dtype=float)
    duplicate_players = player_appearances.duplicated(["match_id", "team", "player"]).sum()
    duplicate_lineups = match_lineups.duplicated(["match_id", "team"]).sum() if not match_lineups.empty else 0
    missing_dates = int(player_appearances["date"].isna().sum())
    rows = [
        {
            "check": "duplicate_player_appearances",
            "status": "pass" if duplicate_players == 0 else "warn",
            "details": f"{duplicate_players} duplicated match/team/player rows.",
        },
        {
            "check": "duplicate_team_lineups",
            "status": "pass" if duplicate_lineups == 0 else "warn",
            "details": f"{duplicate_lineups} duplicated match/team rows.",
        },
        {
            "check": "missing_dates",
            "status": "pass" if missing_dates == 0 else "fail",
            "details": f"{missing_dates} appearance rows without date.",
        },
        {
            "check": "starter_count",
            "status": "pass" if starter_counts["starters"].between(10, 12).mean() > 0.95 else "warn",
            "details": json.dumps(starter_counts["starters"].describe().to_dict()),
        },
        {
            "check": "two_team_lineups_per_match",
            "status": "pass" if (not team_rows_per_match.empty and team_rows_per_match.eq(2).mean() > 0.95) else "warn",
            "details": json.dumps(team_rows_per_match.value_counts().sort_index().to_dict()),
        },
    ]
    return pd.DataFrame(rows)


def write_outputs(
    tables: tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame, pd.DataFrame],
    stats: dict[str, int],
    fetch_attempted: bool,
) -> FbrefLineupIngestionResult:
    match_lineups, player_appearances, formation_history, substitutions = tables
    DATA_OUTPUTS = {
        MATCH_LINEUPS_PATH: match_lineups,
        PLAYER_APPEARANCES_PATH: player_appearances,
        FORMATION_HISTORY_PATH: formation_history,
        MATCH_SUBSTITUTIONS_PATH: substitutions,
    }
    for path, frame in DATA_OUTPUTS.items():
        path.parent.mkdir(exist_ok=True)
        frame.to_csv(path, index=False)

    validation = validate_lineup_tables(match_lineups, player_appearances)
    validation_path = Path("evaluation") / "lineup_stability_engine" / "lineup_data_validation.csv"
    validation_path.parent.mkdir(parents=True, exist_ok=True)
    validation.to_csv(validation_path, index=False)
    source_note = (
        "soccerdata fetch was requested; raw FBref rows were normalized when available."
        if fetch_attempted
        else "Local raw FBref/soccerdata rows were normalized. Run with `--fetch` to refresh the raw source file."
    )
    coverage = (
        player_appearances.assign(date=pd.to_datetime(player_appearances["date"], errors="coerce"))
        if not player_appearances.empty
        else player_appearances
    )
    seasons = (
        _markdown_table(coverage.groupby("season")["match_id"].nunique().reset_index(name="matches_with_lineups"))
        if not coverage.empty
        else "No seasons covered."
    )
    Path("lineup_data_quality_report.md").write_text(
        f"""# Lineup Data Quality Report

## Source

{source_note}

## Normalized Table Coverage

- `data/match_lineups.csv`: {len(match_lineups)} rows
- `data/player_appearances.csv`: {len(player_appearances)} rows
- `data/formation_history.csv`: {len(formation_history)} rows
- `data/match_substitutions.csv`: {len(substitutions)} rows

## Match Coverage

{seasons}

## Ingestion Stats

- Raw rows: {stats.get('raw_rows', 0)}
- Matched team rows: {stats.get('matched_team_rows', 0)}
- Unmatched team rows: {stats.get('unmatched_team_rows', 0)}

## Validation

{_markdown_table(validation)}

## Leakage Controls

- Actual lineups are stored as post-match facts with `source_collected_at = date + 1 day`.
- Pre-match features only use appearance rows dated before the fixture being predicted.
- Current-match actual XI is not used for normal production predictions.
- Expected/projected lineups can be added later only if `source_collected_at` is before kickoff.

## Production Decision

{'Lineup rows are available. Run the lineup stability experiment before activation.' if len(player_appearances) else 'Do not activate lineup stability features. No historical player appearance rows are available locally yet.'}
"""
    )
    return FbrefLineupIngestionResult(
        raw_rows=stats.get("raw_rows", 0),
        match_lineup_rows=len(match_lineups),
        player_appearance_rows=len(player_appearances),
        formation_rows=len(formation_history),
        substitution_rows=len(substitutions),
        matched_team_rows=stats.get("matched_team_rows", 0),
        unmatched_team_rows=stats.get("unmatched_team_rows", 0),
        output_files={str(path): str(path) for path in DATA_OUTPUTS},
    )


def run_ingestion(seasons: list[int] | None = None, fetch: bool = False, force_cache: bool = False) -> FbrefLineupIngestionResult:
    seasons = seasons or DEFAULT_SEASONS
    raw = load_or_fetch_raw_lineups(seasons=seasons, fetch=fetch, force_cache=force_cache)
    if raw.empty and PLAYER_APPEARANCES_PATH.exists() and PLAYER_APPEARANCES_PATH.stat().st_size > 0:
        existing_appearances = pd.read_csv(PLAYER_APPEARANCES_PATH)
        if not existing_appearances.empty:
            return FbrefLineupIngestionResult(
                raw_rows=0,
                match_lineup_rows=len(pd.read_csv(MATCH_LINEUPS_PATH)) if MATCH_LINEUPS_PATH.exists() else 0,
                player_appearance_rows=len(existing_appearances),
                formation_rows=len(pd.read_csv(FORMATION_HISTORY_PATH)) if FORMATION_HISTORY_PATH.exists() else 0,
                substitution_rows=len(pd.read_csv(MATCH_SUBSTITUTIONS_PATH)) if MATCH_SUBSTITUTIONS_PATH.exists() else 0,
                matched_team_rows=0,
                unmatched_team_rows=0,
                output_files={
                    str(MATCH_LINEUPS_PATH): str(MATCH_LINEUPS_PATH),
                    str(PLAYER_APPEARANCES_PATH): str(PLAYER_APPEARANCES_PATH),
                    str(FORMATION_HISTORY_PATH): str(FORMATION_HISTORY_PATH),
                    str(MATCH_SUBSTITUTIONS_PATH): str(MATCH_SUBSTITUTIONS_PATH),
                },
            )
    matches = load_matches()
    tables_with_stats = normalize_fbref_lineups(raw, matches)
    tables = tables_with_stats[:4]
    stats = tables_with_stats[4]
    return write_outputs(tables, stats, fetch_attempted=fetch)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Ingest FBref/soccerdata lineup rows into normalized project tables.")
    parser.add_argument("--fetch", action="store_true", help="Fetch FBref lineups via soccerdata if no local raw file exists.")
    parser.add_argument("--force-cache", action="store_true", help="Force soccerdata to use cached FBref data.")
    parser.add_argument("--seasons", nargs="*", type=int, default=DEFAULT_SEASONS, help="FBref seasons to fetch, e.g. 2024 2025.")
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    result = run_ingestion(seasons=args.seasons, fetch=args.fetch, force_cache=args.force_cache)
    print(json.dumps(result.__dict__, indent=2))


if __name__ == "__main__":
    main()
