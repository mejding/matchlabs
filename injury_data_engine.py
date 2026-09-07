from __future__ import annotations

import argparse
import json
import os
from dataclasses import dataclass
from datetime import date
from pathlib import Path
import urllib.parse
import urllib.request

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
API_FOOTBALL_BASE_URL = "https://v3.football.api-sports.io/injuries"
SPORTMONKS_BASE_URL = "https://api.sportmonks.com/v3/football"
DEFAULT_API_FOOTBALL_PREMIER_LEAGUE_ID = 39
DEFAULT_API_FOOTBALL_SEASON = 2026

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


@dataclass(frozen=True)
class RemoteFetchResult:
    provider: str
    status: str
    rows: int
    path: Path | None = None
    message: str = ""


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


def _as_date(value: object) -> date | pd.NaT:
    parsed = pd.to_datetime(value, errors="coerce", utc=False)
    return parsed.date() if pd.notna(parsed) else pd.NaT


def _text(*values: object) -> str:
    parts = []
    for value in values:
        if value is None or value is pd.NA:
            continue
        if isinstance(value, float) and pd.isna(value):
            continue
        text = str(value).strip()
        if text:
            parts.append(text)
    return " ".join(parts)


def _status_from_reason(reason: object) -> str:
    text = str(reason or "").lower()
    return "suspension" if "suspend" in text or "ban" in text or "red card" in text else "injury"


def _blank_canonical_row(source: str, collected_at: date) -> dict[str, object]:
    return {
        "report_date": collected_at,
        "team": pd.NA,
        "player": pd.NA,
        "unavailable_from": pd.NaT,
        "expected_return_date": pd.NaT,
        "status_type": pd.NA,
        "injury_or_suspension": pd.NA,
        "is_expected_starter": 0.0,
        "is_key_player": 0.0,
        "is_long_term_injury": 0.0,
        "is_suspended": 0.0,
        "minutes_played_last_365": 0.0,
        "goals_last_365": 0.0,
        "xg_contribution_last_365": 0.0,
        "xa_contribution_last_365": 0.0,
        "defensive_contribution_last_365": 0.0,
        "market_value_eur": 0.0,
        "source": source,
        "source_url": pd.NA,
        "source_collected_at": collected_at,
    }


def _request_json(url: str, headers: dict[str, str] | None = None) -> dict[str, object]:
    request = urllib.request.Request(url, headers=headers or {"User-Agent": "Mozilla/5.0"})
    with urllib.request.urlopen(request, timeout=45) as response:
        return json.loads(response.read().decode("utf-8"))


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


def normalize_api_football_payload(payload: dict[str, object], collected_at: date | None = None) -> pd.DataFrame:
    collected = collected_at or date.today()
    rows: list[dict[str, object]] = []
    for item in payload.get("response", []) or []:
        if not isinstance(item, dict):
            continue
        player = item.get("player") if isinstance(item.get("player"), dict) else {}
        team = item.get("team") if isinstance(item.get("team"), dict) else {}
        fixture = item.get("fixture") if isinstance(item.get("fixture"), dict) else {}
        reason = item.get("reason") or item.get("type") or item.get("description")
        fixture_date = _as_date(fixture.get("date"))
        row = _blank_canonical_row("api-football", collected)
        row.update(
            {
                "report_date": fixture_date if pd.notna(fixture_date) else collected,
                "team": team.get("name"),
                "player": player.get("name"),
                "unavailable_from": fixture_date if pd.notna(fixture_date) else collected,
                "expected_return_date": fixture_date if pd.notna(fixture_date) else pd.NaT,
                "status_type": _status_from_reason(reason),
                "injury_or_suspension": reason,
                "source_url": API_FOOTBALL_BASE_URL,
            }
        )
        row["is_suspended"] = 1.0 if row["status_type"] == "suspension" else 0.0
        rows.append(row)
    return pd.DataFrame(rows, columns=CANONICAL_INJURY_COLUMNS) if rows else empty_canonical_frame()


def fetch_api_football_injuries(
    api_key: str,
    league_id: int = DEFAULT_API_FOOTBALL_PREMIER_LEAGUE_ID,
    season: int = DEFAULT_API_FOOTBALL_SEASON,
) -> pd.DataFrame:
    query = urllib.parse.urlencode({"league": league_id, "season": season})
    payload = _request_json(f"{API_FOOTBALL_BASE_URL}?{query}", headers={"x-apisports-key": api_key})
    return normalize_api_football_payload(payload)


def _sportmonks_items(payload: dict[str, object]) -> list[dict[str, object]]:
    data = payload.get("data", [])
    if isinstance(data, dict):
        data = [data]
    items: list[dict[str, object]] = []
    for entity in data if isinstance(data, list) else []:
        if not isinstance(entity, dict):
            continue
        sidelined = entity.get("sidelined", [])
        if isinstance(sidelined, dict):
            sidelined = sidelined.get("data", [])
        if isinstance(sidelined, list):
            items.extend(item for item in sidelined if isinstance(item, dict))
        elif {"player_id", "type_id", "sideline_id"} & set(entity):
            items.append(entity)
    return items


def normalize_sportmonks_payload(payload: dict[str, object], collected_at: date | None = None) -> pd.DataFrame:
    collected = collected_at or date.today()
    rows: list[dict[str, object]] = []
    for item in _sportmonks_items(payload):
        sideline = item.get("sideline") if isinstance(item.get("sideline"), dict) else item
        player = item.get("player") if isinstance(item.get("player"), dict) else sideline.get("player") if isinstance(sideline.get("player"), dict) else {}
        team = (
            item.get("participant")
            if isinstance(item.get("participant"), dict)
            else item.get("team")
            if isinstance(item.get("team"), dict)
            else sideline.get("team")
            if isinstance(sideline.get("team"), dict)
            else {}
        )
        type_info = item.get("type") if isinstance(item.get("type"), dict) else sideline.get("type") if isinstance(sideline.get("type"), dict) else {}
        reason = _text(sideline.get("category"), type_info.get("name"), type_info.get("developer_name"))
        start_date = _as_date(sideline.get("start_date"))
        end_date = _as_date(sideline.get("end_date"))
        row = _blank_canonical_row("sportmonks", collected)
        row.update(
            {
                "report_date": start_date if pd.notna(start_date) else collected,
                "team": team.get("name"),
                "player": player.get("display_name") or player.get("common_name") or player.get("name"),
                "unavailable_from": start_date if pd.notna(start_date) else collected,
                "expected_return_date": end_date,
                "status_type": _status_from_reason(reason),
                "injury_or_suspension": reason,
                "source_url": SPORTMONKS_BASE_URL,
            }
        )
        row["is_suspended"] = 1.0 if row["status_type"] == "suspension" else 0.0
        rows.append(row)
    return pd.DataFrame(rows, columns=CANONICAL_INJURY_COLUMNS) if rows else empty_canonical_frame()


def fetch_sportmonks_sidelined(api_token: str, season_id: str | None = None, team_ids: list[str] | None = None) -> pd.DataFrame:
    frames: list[pd.DataFrame] = []
    if team_ids:
        for team_id in team_ids:
            query = urllib.parse.urlencode({"api_token": api_token, "include": "sidelined.player;sidelined.sideline;sidelined.type"})
            frames.append(normalize_sportmonks_payload(_request_json(f"{SPORTMONKS_BASE_URL}/teams/{team_id}?{query}")))
    elif season_id:
        query = urllib.parse.urlencode({"api_token": api_token, "include": "sidelined.player;sidelined.sideline;sidelined.type"})
        frames.append(normalize_sportmonks_payload(_request_json(f"{SPORTMONKS_BASE_URL}/teams/seasons/{season_id}?{query}")))
    else:
        return empty_canonical_frame()
    return pd.concat(frames, ignore_index=True) if frames else empty_canonical_frame()


def fetch_remote_injuries(args: argparse.Namespace) -> tuple[list[pd.DataFrame], list[RemoteFetchResult]]:
    frames: list[pd.DataFrame] = []
    results: list[RemoteFetchResult] = []
    api_football_key = os.environ.get("API_FOOTBALL_KEY") or os.environ.get("APISPORTS_KEY")
    sportmonks_token = os.environ.get("SPORTMONKS_API_TOKEN")

    if args.provider in {"api-football", "all"}:
        if not api_football_key:
            results.append(RemoteFetchResult("api-football", "skipped", 0, message="Set API_FOOTBALL_KEY or APISPORTS_KEY to enable."))
        elif args.dry_run:
            results.append(RemoteFetchResult("api-football", "dry_run", 0, message="Would call API-Football injuries endpoint."))
        else:
            frame = fetch_api_football_injuries(api_football_key, args.api_football_league_id, args.api_football_season)
            frames.append(frame)
            results.append(RemoteFetchResult("api-football", "fetched", len(frame), message=f"league={args.api_football_league_id}, season={args.api_football_season}"))

    if args.provider in {"sportmonks", "all"}:
        team_ids = [team.strip() for team in args.sportmonks_team_ids.split(",") if team.strip()] if args.sportmonks_team_ids else None
        if not sportmonks_token:
            results.append(RemoteFetchResult("sportmonks", "skipped", 0, message="Set SPORTMONKS_API_TOKEN to enable."))
        elif not args.sportmonks_season_id and not team_ids:
            results.append(RemoteFetchResult("sportmonks", "skipped", 0, message="Pass --sportmonks-season-id or --sportmonks-team-ids."))
        elif args.dry_run:
            results.append(RemoteFetchResult("sportmonks", "dry_run", 0, message="Would call Sportmonks sidelined includes."))
        else:
            frame = fetch_sportmonks_sidelined(sportmonks_token, args.sportmonks_season_id, team_ids)
            frames.append(frame)
            results.append(RemoteFetchResult("sportmonks", "fetched", len(frame), message=f"season_id={args.sportmonks_season_id or ''}, team_ids={args.sportmonks_team_ids or ''}"))

    return frames, results


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


def build_injury_master_table(remote_frames: list[pd.DataFrame] | None = None) -> pd.DataFrame:
    frames = [normalize_existing_injuries()]
    frames.extend(remote_frames or [])
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


def write_injury_data_quality_report(master: pd.DataFrame, discoveries: list[SourceDiscovery], remote_results: list[RemoteFetchResult]) -> None:
    source_lines = "\n".join(
        f"- {item.name}: {'found' if item.exists else 'missing'} at `{item.path}`; rows={item.rows}; usable={item.usable}; {item.note}"
        for item in discoveries
    )
    remote_lines = "\n".join(
        f"- {item.provider}: {item.status}; rows={item.rows}; {item.message}"
        for item in remote_results
    ) or "- No remote provider attempted."
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

## Remote Provider Refresh

{remote_lines}

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


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Build the canonical injury/suspension table.")
    parser.add_argument(
        "--provider",
        choices=["local", "api-football", "sportmonks", "all"],
        default="local",
        help="Remote provider to query before rebuilding data/injuries.csv.",
    )
    parser.add_argument("--dry-run", action="store_true", help="Validate provider configuration without writing refreshed data.")
    parser.add_argument("--api-football-league-id", type=int, default=DEFAULT_API_FOOTBALL_PREMIER_LEAGUE_ID)
    parser.add_argument("--api-football-season", type=int, default=DEFAULT_API_FOOTBALL_SEASON)
    parser.add_argument("--sportmonks-season-id", default=os.environ.get("SPORTMONKS_PREMIER_LEAGUE_SEASON_ID"))
    parser.add_argument("--sportmonks-team-ids", default=os.environ.get("SPORTMONKS_PREMIER_LEAGUE_TEAM_IDS", ""))
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    DATA_DIR.mkdir(exist_ok=True)
    discoveries = discover_sources()
    remote_frames, remote_results = fetch_remote_injuries(args) if args.provider != "local" else ([], [])
    master = build_injury_master_table(remote_frames)
    if not args.dry_run:
        master.to_csv(INJURY_PATH, index=False)
    write_injury_data_quality_report(master, discoveries, remote_results)
    action = "Would write" if args.dry_run else "Wrote"
    print(f"{action} {INJURY_PATH} with {len(master)} rows.")
    print("Wrote injury_data_quality_report.md")


if __name__ == "__main__":
    main()
