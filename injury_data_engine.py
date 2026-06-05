from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

import pandas as pd


DATA_DIR = Path("data")
INJURY_PATH = DATA_DIR / "injuries.csv"
TRANSFERMARKT_CANDIDATES = [
    DATA_DIR / "transfermarkt_injuries.csv",
    DATA_DIR / "transfermarkt_injury_history.csv",
    DATA_DIR / "raw" / "transfermarkt_injuries.csv",
]
PREMIER_INJURIES_CANDIDATES = [
    DATA_DIR / "premier_injuries.csv",
    DATA_DIR / "premier_injuries_history.csv",
    DATA_DIR / "raw" / "premier_injuries.csv",
]

CANONICAL_INJURY_COLUMNS = [
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


@dataclass(frozen=True)
class SourceDiscovery:
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


def _to_date(series: pd.Series) -> pd.Series:
    return pd.to_datetime(series, errors="coerce").dt.date


def _to_number(series: pd.Series) -> pd.Series:
    return pd.to_numeric(series, errors="coerce").fillna(0.0)


def _normalize_market_value(series: pd.Series) -> pd.Series:
    if series.empty:
        return series
    cleaned = series.astype(str).str.replace("€", "", regex=False).str.replace(",", "", regex=False).str.strip()
    multiplier = cleaned.str.extract(r"([mkMK])", expand=False).str.lower()
    numbers = pd.to_numeric(cleaned.str.extract(r"([0-9.]+)", expand=False), errors="coerce").fillna(0.0)
    return numbers * multiplier.map({"m": 1_000_000.0, "k": 1_000.0}).fillna(1.0)


def empty_canonical_frame() -> pd.DataFrame:
    return pd.DataFrame(columns=CANONICAL_INJURY_COLUMNS)


def normalize_existing_injuries(path: Path = INJURY_PATH) -> pd.DataFrame:
    frame = _read_csv_if_exists(path)
    if frame.empty:
        return empty_canonical_frame()
    normalized = frame.copy()
    for column in CANONICAL_INJURY_COLUMNS:
        if column not in normalized.columns:
            normalized[column] = 0.0 if column.startswith(("is_", "minutes_", "goals_", "xg_", "xa_", "defensive_", "market_")) else pd.NA
    normalized["source"] = normalized["source"].fillna("manual_injuries_csv")
    return normalized[CANONICAL_INJURY_COLUMNS]


def normalize_transfermarkt(path: Path) -> pd.DataFrame:
    raw = _read_csv_if_exists(path)
    if raw.empty:
        return empty_canonical_frame()
    normalized = empty_canonical_frame().reindex(range(len(raw))).copy()
    normalized["report_date"] = _to_date(_column(raw, ["report_date", "date", "from", "unavailable_from"]))
    normalized["team"] = _column(raw, ["team", "club", "squad", "Team"])
    normalized["player"] = _column(raw, ["player", "name", "Player"])
    normalized["unavailable_from"] = _to_date(_column(raw, ["unavailable_from", "from", "start_date", "injury_from"]))
    normalized["expected_return_date"] = _to_date(_column(raw, ["expected_return_date", "until", "return_date", "injury_until"]))
    normalized["status_type"] = "injury"
    normalized["injury_or_suspension"] = _column(raw, ["injury", "reason", "type", "description"])
    normalized["is_expected_starter"] = _to_number(_column(raw, ["is_expected_starter", "expected_starter"]))
    normalized["is_key_player"] = _to_number(_column(raw, ["is_key_player", "key_player"]))
    normalized["is_long_term_injury"] = _to_number(_column(raw, ["is_long_term_injury", "long_term"]))
    normalized["is_suspended"] = 0.0
    normalized["minutes_played_last_365"] = _to_number(_column(raw, ["minutes_played_last_365", "minutes", "mins_last_365"]))
    normalized["goals_last_365"] = _to_number(_column(raw, ["goals_last_365", "goals"]))
    normalized["xg_contribution_last_365"] = _to_number(_column(raw, ["xg_contribution_last_365", "xg"]))
    normalized["xa_contribution_last_365"] = _to_number(_column(raw, ["xa_contribution_last_365", "xa"]))
    normalized["defensive_contribution_last_365"] = _to_number(
        _column(raw, ["defensive_contribution_last_365", "defensive_contribution", "def_actions"])
    )
    normalized["market_value_eur"] = _normalize_market_value(_column(raw, ["market_value_eur", "market_value", "value"]))
    normalized["source"] = "transfermarkt"
    normalized["source_url"] = _column(raw, ["source_url", "url"])
    normalized["source_collected_at"] = _to_date(_column(raw, ["source_collected_at", "collected_at", "scraped_at"]))
    return normalized[CANONICAL_INJURY_COLUMNS]


def normalize_premier_injuries(path: Path) -> pd.DataFrame:
    raw = _read_csv_if_exists(path)
    if raw.empty:
        return empty_canonical_frame()
    normalized = empty_canonical_frame().reindex(range(len(raw))).copy()
    normalized["report_date"] = _to_date(_column(raw, ["report_date", "date", "updated", "last_updated"]))
    normalized["team"] = _column(raw, ["team", "club"])
    normalized["player"] = _column(raw, ["player", "name"])
    normalized["unavailable_from"] = _to_date(_column(raw, ["unavailable_from", "start_date", "date"]))
    normalized["expected_return_date"] = _to_date(_column(raw, ["expected_return_date", "return_date", "expected_return"]))
    reason = _column(raw, ["injury_or_suspension", "injury", "reason", "status"])
    normalized["status_type"] = reason.astype(str).str.contains("suspend", case=False, na=False).map(
        {True: "suspension", False: "injury"}
    )
    normalized["injury_or_suspension"] = reason
    normalized["is_expected_starter"] = _to_number(_column(raw, ["is_expected_starter", "expected_starter"]))
    normalized["is_key_player"] = _to_number(_column(raw, ["is_key_player", "key_player"]))
    normalized["is_long_term_injury"] = _to_number(_column(raw, ["is_long_term_injury", "long_term"]))
    normalized["is_suspended"] = normalized["status_type"].eq("suspension").astype(float)
    normalized["minutes_played_last_365"] = _to_number(_column(raw, ["minutes_played_last_365", "minutes"]))
    normalized["goals_last_365"] = _to_number(_column(raw, ["goals_last_365", "goals"]))
    normalized["xg_contribution_last_365"] = _to_number(_column(raw, ["xg_contribution_last_365", "xg"]))
    normalized["xa_contribution_last_365"] = _to_number(_column(raw, ["xa_contribution_last_365", "xa"]))
    normalized["defensive_contribution_last_365"] = _to_number(
        _column(raw, ["defensive_contribution_last_365", "defensive_contribution", "def_actions"])
    )
    normalized["market_value_eur"] = _normalize_market_value(_column(raw, ["market_value_eur", "market_value", "value"]))
    normalized["source"] = "premier_injuries"
    normalized["source_url"] = _column(raw, ["source_url", "url"])
    normalized["source_collected_at"] = _to_date(_column(raw, ["source_collected_at", "collected_at"]))
    return normalized[CANONICAL_INJURY_COLUMNS]


def discover_sources() -> list[SourceDiscovery]:
    discoveries: list[SourceDiscovery] = []
    for name, candidates in [
        ("existing injuries.csv", [INJURY_PATH]),
        ("Transfermarkt injury history", TRANSFERMARKT_CANDIDATES),
        ("Premier Injuries history", PREMIER_INJURIES_CANDIDATES),
    ]:
        path = _first_existing(candidates)
        if path is None:
            discoveries.append(SourceDiscovery(name, candidates[0], False, 0, False, "No local source file found."))
            continue
        frame = _read_csv_if_exists(path)
        has_minimum_columns = {"team", "player"} & {column.lower() for column in frame.columns}
        discoveries.append(
            SourceDiscovery(
                name,
                path,
                True,
                len(frame),
                bool(len(frame) and has_minimum_columns),
                "Found local source file." if len(frame) else "File is empty.",
            )
        )
    return discoveries


def build_injury_master_table() -> pd.DataFrame:
    frames = [normalize_existing_injuries()]
    transfermarkt_path = _first_existing(TRANSFERMARKT_CANDIDATES)
    premier_injuries_path = _first_existing(PREMIER_INJURIES_CANDIDATES)
    if transfermarkt_path:
        frames.append(normalize_transfermarkt(transfermarkt_path))
    if premier_injuries_path:
        frames.append(normalize_premier_injuries(premier_injuries_path))

    combined = pd.concat(frames, ignore_index=True) if frames else empty_canonical_frame()
    if combined.empty:
        return empty_canonical_frame()
    combined = combined.dropna(subset=["report_date", "team", "player", "unavailable_from"])
    combined = combined.drop_duplicates(
        subset=["report_date", "team", "player", "unavailable_from", "expected_return_date", "status_type"],
        keep="last",
    )
    return combined[CANONICAL_INJURY_COLUMNS].sort_values(["report_date", "team", "player"]).reset_index(drop=True)


def write_injury_data_quality_report(master: pd.DataFrame, discoveries: list[SourceDiscovery]) -> None:
    source_lines = "\n".join(
        f"- {item.name}: {'found' if item.exists else 'missing'} at `{item.path}`; rows={item.rows}; usable={item.usable}; {item.note}"
        for item in discoveries
    )
    if master.empty:
        coverage = "No historical injury/suspension rows are currently available locally."
        active_decision = "Do not activate injury features."
    else:
        coverage = (
            f"Rows: {len(master)}. Date range: {master['report_date'].min()} to {master['report_date'].max()}. "
            f"Teams covered: {master['team'].nunique()}."
        )
        active_decision = "Evaluate before activation; do not activate unless out-of-sample metrics improve."
    missing = {column: int(master[column].isna().sum()) for column in CANONICAL_INJURY_COLUMNS} if not master.empty else {}
    missing_lines = "\n".join(f"- `{column}`: {count}" for column, count in missing.items()) or "- n/a"

    Path("injury_data_quality_report.md").write_text(
        f"""# Injury Data Quality Report

## Source Discovery

{source_lines}

## Coverage

{coverage}

## Missing Values

{missing_lines}

## Leakage Controls

- A player is unavailable for a fixture only when `report_date <= match_date` and `unavailable_from <= match_date`.
- `expected_return_date` must be blank or on/after the match date.
- Source rows with collection dates after kickoff should not be used in future ingestion.
- No missing injury values are inferred or simulated.

## Production Decision

{active_decision}
"""
    )


def main() -> None:
    DATA_DIR.mkdir(exist_ok=True)
    discoveries = discover_sources()
    master = build_injury_master_table()
    master.to_csv(INJURY_PATH, index=False)
    write_injury_data_quality_report(master, discoveries)
    print(f"Wrote {INJURY_PATH} with {len(master)} rows.")
    print("Wrote injury_data_quality_report.md")


if __name__ == "__main__":
    main()
