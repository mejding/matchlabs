from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

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
    ensure_lineup_tables,
)


DATA_DIR = Path("data")
RAW_DIR = DATA_DIR / "raw"
FBREF_CANDIDATES = [
    DATA_DIR / "fbref_lineups.csv",
    DATA_DIR / "fbref_match_lineups.csv",
    RAW_DIR / "fbref_lineups.csv",
]
UNDERSTAT_CANDIDATES = [
    DATA_DIR / "understat_lineups.csv",
    RAW_DIR / "understat_lineups.csv",
]
AVAILABLE_LINEUP_CANDIDATES = [
    DATA_DIR / "lineups.csv",
    DATA_DIR / "historical_lineups.csv",
    RAW_DIR / "lineups.csv",
]


@dataclass(frozen=True)
class LineupSourceDiscovery:
    name: str
    path: Path
    exists: bool
    rows: int
    usable: bool
    note: str


def _read_csv_if_exists(path: Path) -> pd.DataFrame:
    if not path.exists() or path.stat().st_size == 0:
        return pd.DataFrame()
    try:
        return pd.read_csv(path)
    except pd.errors.EmptyDataError:
        return pd.DataFrame()


def _first_existing(paths: list[Path]) -> Path | None:
    for path in paths:
        if path.exists() and path.stat().st_size > 0:
            return path
    return None


def _column(frame: pd.DataFrame, candidates: list[str]) -> pd.Series:
    lookup = {column.lower().strip(): column for column in frame.columns}
    for candidate in candidates:
        key = candidate.lower().strip()
        if key in lookup:
            return frame[lookup[key]]
    return pd.Series([pd.NA] * len(frame))


def _to_number(series: pd.Series) -> pd.Series:
    return pd.to_numeric(series, errors="coerce").fillna(0.0)


def _to_date(series: pd.Series) -> pd.Series:
    return pd.to_datetime(series, errors="coerce").dt.date


def _empty(columns: list[str]) -> pd.DataFrame:
    return pd.DataFrame(columns=columns)


def discover_lineup_sources() -> list[LineupSourceDiscovery]:
    discoveries: list[LineupSourceDiscovery] = []
    for name, candidates in [
        ("existing match_lineups.csv", [MATCH_LINEUPS_PATH]),
        ("existing player_appearances.csv", [PLAYER_APPEARANCES_PATH]),
        ("FBref lineup export", FBREF_CANDIDATES),
        ("Understat lineup export", UNDERSTAT_CANDIDATES),
        ("generic available lineup dataset", AVAILABLE_LINEUP_CANDIDATES),
    ]:
        path = _first_existing(candidates)
        if path is None:
            discoveries.append(LineupSourceDiscovery(name, candidates[0], False, 0, False, "No local source file found."))
            continue
        frame = _read_csv_if_exists(path)
        columns = {column.lower() for column in frame.columns}
        usable = bool(len(frame) and {"team", "player"} <= columns)
        discoveries.append(
            LineupSourceDiscovery(
                name=name,
                path=path,
                exists=True,
                rows=len(frame),
                usable=usable,
                note="Found local source file." if usable else "File exists but lacks required team/player rows.",
            )
        )
    return discoveries


def normalize_lineup_rows(raw: pd.DataFrame, source: str) -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    if raw.empty:
        return (
            _empty(MATCH_LINEUPS_COLUMNS),
            _empty(PLAYER_APPEARANCES_COLUMNS),
            _empty(FORMATION_HISTORY_COLUMNS),
            _empty(MATCH_SUBSTITUTIONS_COLUMNS),
        )

    match_id = _column(raw, ["match_id", "game_id", "fixture_id"])
    season = _column(raw, ["season", "Season"])
    date = _to_date(_column(raw, ["date", "Date", "match_date"]))
    team = _column(raw, ["team", "squad", "club"])
    opponent = _column(raw, ["opponent", "opp"])
    is_home = _to_number(_column(raw, ["is_home", "home", "venue_home"]))
    player = _column(raw, ["player", "name", "Player"])
    position = _column(raw, ["position", "pos"])
    position_group = _column(raw, ["position_group", "line", "unit"])
    started = _to_number(_column(raw, ["started", "start", "is_starter", "starter"]))
    is_substitute = _to_number(_column(raw, ["is_substitute", "substitute", "bench"]))
    minutes = _to_number(_column(raw, ["minutes", "mins", "Min"]))
    formation = _column(raw, ["formation", "Formation"])
    captain = _column(raw, ["captain", "is_captain"])
    lineup_type = _column(raw, ["lineup_type", "type"]).fillna("actual")
    source_collected_at = _to_date(_column(raw, ["source_collected_at", "scraped_at", "collected_at"]))

    appearances = pd.DataFrame(
        {
            "match_id": match_id,
            "season": season,
            "date": date,
            "team": team,
            "opponent": opponent,
            "player": player,
            "position": position,
            "position_group": position_group,
            "started": started,
            "is_substitute": is_substitute,
            "minutes": minutes,
            "sub_on_minute": _to_number(_column(raw, ["sub_on_minute", "sub_on"])),
            "sub_off_minute": _to_number(_column(raw, ["sub_off_minute", "sub_off"])),
            "lineup_type": lineup_type,
            "source": source,
            "source_collected_at": source_collected_at,
        }
    ).dropna(subset=["match_id", "date", "team", "player"])

    lineups = (
        pd.DataFrame(
            {
                "match_id": match_id,
                "season": season,
                "date": date,
                "team": team,
                "opponent": opponent,
                "is_home": is_home,
                "formation": formation,
                "captain": captain,
                "lineup_type": lineup_type,
                "source": source,
                "source_collected_at": source_collected_at,
            }
        )
        .dropna(subset=["match_id", "date", "team"])
        .drop_duplicates(subset=["match_id", "team"], keep="last")
    )

    formations = (
        pd.DataFrame(
            {
                "match_id": match_id,
                "season": season,
                "date": date,
                "team": team,
                "formation": formation,
                "manager": _column(raw, ["manager", "coach"]),
                "source": source,
                "source_collected_at": source_collected_at,
            }
        )
        .dropna(subset=["match_id", "date", "team"])
        .drop_duplicates(subset=["match_id", "team"], keep="last")
    )

    substitutions = pd.DataFrame(
        {
            "match_id": match_id,
            "season": season,
            "date": date,
            "team": team,
            "player_off": _column(raw, ["player_off", "sub_off_player"]),
            "player_on": _column(raw, ["player_on", "sub_on_player"]),
            "minute": _to_number(_column(raw, ["minute", "sub_minute"])),
            "source": source,
            "source_collected_at": source_collected_at,
        }
    ).dropna(subset=["match_id", "date", "team", "player_on"], how="any")

    return (
        lineups[MATCH_LINEUPS_COLUMNS],
        appearances[PLAYER_APPEARANCES_COLUMNS],
        formations[FORMATION_HISTORY_COLUMNS],
        substitutions[MATCH_SUBSTITUTIONS_COLUMNS],
    )


def build_lineup_master_tables() -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    ensure_lineup_tables()
    frames_lineups = []
    frames_appearances = []
    frames_formations = []
    frames_substitutions = []

    for source, candidates in [
        ("fbref", FBREF_CANDIDATES),
        ("understat", UNDERSTAT_CANDIDATES),
        ("available_lineup_dataset", AVAILABLE_LINEUP_CANDIDATES),
    ]:
        path = _first_existing(candidates)
        if path is None:
            continue
        lineups, appearances, formations, substitutions = normalize_lineup_rows(_read_csv_if_exists(path), source)
        frames_lineups.append(lineups)
        frames_appearances.append(appearances)
        frames_formations.append(formations)
        frames_substitutions.append(substitutions)

    if frames_lineups:
        match_lineups = pd.concat(frames_lineups, ignore_index=True).drop_duplicates(["match_id", "team"], keep="last")
        player_appearances = pd.concat(frames_appearances, ignore_index=True).drop_duplicates(
            ["match_id", "team", "player"], keep="last"
        )
        formation_history = pd.concat(frames_formations, ignore_index=True).drop_duplicates(["match_id", "team"], keep="last")
        match_substitutions = pd.concat(frames_substitutions, ignore_index=True)
    else:
        match_lineups = _empty(MATCH_LINEUPS_COLUMNS)
        player_appearances = _empty(PLAYER_APPEARANCES_COLUMNS)
        formation_history = _empty(FORMATION_HISTORY_COLUMNS)
        match_substitutions = _empty(MATCH_SUBSTITUTIONS_COLUMNS)

    return match_lineups, player_appearances, formation_history, match_substitutions


def write_lineup_data_quality_report(discoveries: list[LineupSourceDiscovery], tables: tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame, pd.DataFrame]) -> None:
    match_lineups, player_appearances, formation_history, substitutions = tables
    source_lines = "\n".join(
        f"- {item.name}: {'found' if item.exists else 'missing'} at `{item.path}`; rows={item.rows}; usable={item.usable}; {item.note}"
        for item in discoveries
    )
    Path("lineup_data_quality_report.md").write_text(
        f"""# Lineup Data Quality Report

## Source Discovery

{source_lines}

## Normalized Table Coverage

- `data/match_lineups.csv`: {len(match_lineups)} rows
- `data/player_appearances.csv`: {len(player_appearances)} rows
- `data/formation_history.csv`: {len(formation_history)} rows
- `data/match_substitutions.csv`: {len(substitutions)} rows

## Production Decision

{'Evaluate before activation; normalized lineup rows are available.' if len(player_appearances) else 'Do not activate lineup stability features. No historical player appearance rows are available locally.'}

## Leakage Controls

- Actual current-match XIs are not used as pre-match features.
- Historical actual appearances are used only before the fixture date.
- Expected/projected lineups require `source_collected_at` before kickoff.
- No lineup, captain, formation or substitution rows are simulated.
"""
    )


def main() -> None:
    ensure_lineup_tables()
    discoveries = discover_lineup_sources()
    tables = build_lineup_master_tables()
    for frame, path in zip(tables, [MATCH_LINEUPS_PATH, PLAYER_APPEARANCES_PATH, FORMATION_HISTORY_PATH, MATCH_SUBSTITUTIONS_PATH]):
        frame.to_csv(path, index=False)
    write_lineup_data_quality_report(discoveries, tables)
    print(f"Wrote {PLAYER_APPEARANCES_PATH} with {len(tables[1])} player appearance rows.")
    print("Wrote lineup_data_quality_report.md")


if __name__ == "__main__":
    main()
