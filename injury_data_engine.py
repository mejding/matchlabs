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
AVAILABILITY_DATA_CANDIDATES = [
    DATA_DIR / "availability-data",
    DATA_DIR / "raw" / "availability-data",
    Path("/tmp") / "availability-data",
]
API_FOOTBALL_BASE_URL = "https://v3.football.api-sports.io/injuries"
SPORTMONKS_BASE_URL = "https://api.sportmonks.com/v3/football"
DEFAULT_API_FOOTBALL_PREMIER_LEAGUE_ID = 39
DEFAULT_API_FOOTBALL_SEASON = 2026
AVAILABILITY_TEAM_ALIASES = {
    "AFC Bournemouth": "Bournemouth",
    "Arsenal FC": "Arsenal",
    "Brighton & Hove Albion": "Brighton",
    "Brentford FC": "Brentford",
    "Burnley FC": "Burnley",
    "Chelsea FC": "Chelsea",
    "Everton FC": "Everton",
    "Fulham FC": "Fulham",
    "Liverpool FC": "Liverpool",
    "Manchester City": "Man City",
    "Manchester United": "Man United",
    "Newcastle United": "Newcastle",
    "Nottingham Forest": "Nott'm Forest",
    "Sunderland AFC": "Sunderland",
    "Tottenham Hotspur": "Tottenham",
    "West Ham United": "West Ham",
    "Wolverhampton Wanderers": "Wolves",
}

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
    if not path.exists() or path.is_dir() or path.stat().st_size == 0:
        return pd.DataFrame()
    try:
        return pd.read_csv(path)
    except (pd.errors.EmptyDataError, IsADirectoryError):
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
    text = str(value or "")
    dayfirst = not bool(pd.Series([text]).str.match(r"^[0-9]{4}-[0-9]{2}-[0-9]{2}").iloc[0])
    parsed = pd.to_datetime(value, errors="coerce", utc=False, dayfirst=dayfirst)
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


def _season_start_to_code(season_start_year: int) -> str:
    start = int(season_start_year) % 100
    return f"{start:02d}{(start + 1) % 100:02d}"


def _normalize_availability_team(team: str) -> str:
    return AVAILABILITY_TEAM_ALIASES.get(str(team), str(team).removesuffix(" FC"))


def _availability_detail_return_date(detail: object) -> date | pd.NaT:
    text = str(detail or "")
    match = pd.Series([text]).str.extract(r"Return expected on ([0-9]{2}/[0-9]{2}/[0-9]{4})", expand=False).iloc[0]
    return _as_date(match)


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


def _team_round_dates_for_availability(raw_root: Path) -> dict[tuple[int, str, int], date]:
    seasons = sorted(path.name for path in (raw_root / "GB1").iterdir() if path.is_dir()) if (raw_root / "GB1").exists() else []
    schedule: dict[tuple[int, str, int], date] = {}
    for season_start in seasons:
        season_code = _season_start_to_code(int(season_start))
        match_path = DATA_DIR / f"premier_league_{season_code}.csv"
        if not match_path.exists():
            continue
        matches = pd.read_csv(match_path)
        if not {"Date", "HomeTeam", "AwayTeam"}.issubset(matches.columns):
            continue
        matches["Date"] = pd.to_datetime(matches["Date"], dayfirst=True, errors="coerce").dt.date
        matches = matches.dropna(subset=["Date", "HomeTeam", "AwayTeam"]).sort_values(["Date", "HomeTeam", "AwayTeam"])
        team_counts: dict[str, int] = {}
        for match in matches.itertuples(index=False):
            for team in (str(match.HomeTeam), str(match.AwayTeam)):
                team_counts[team] = team_counts.get(team, 0) + 1
                schedule[(int(season_start), team, team_counts[team])] = match.Date
    return schedule


def normalize_availability_data(raw_root: Path, collected_at: date | None = None) -> pd.DataFrame:
    raw_root = Path(raw_root)
    gb1_root = raw_root / "raw" / "GB1" if (raw_root / "raw" / "GB1").exists() else raw_root / "GB1"
    if not gb1_root.exists():
        return empty_canonical_frame()
    schedule_dates = _team_round_dates_for_availability(raw_root / "raw" if (raw_root / "raw").exists() else raw_root)
    rows: list[dict[str, object]] = []
    for club_path in sorted(gb1_root.glob("*/*.json")):
        payload = json.loads(club_path.read_text(encoding="utf-8"))
        season_start = int(payload.get("season", club_path.parent.name))
        team = _normalize_availability_team(str(payload.get("club", "")))
        scraped_at = _as_date(payload.get("scrapedAt"))
        collected = collected_at or (scraped_at if pd.notna(scraped_at) else date.today())
        for competition in payload.get("competitions", []) or []:
            if competition.get("code") != "GB1":
                continue
            for player in competition.get("players", []) or []:
                prior_statuses: list[str] = []
                prior_minutes = 0.0
                matches = sorted(player.get("matches", []) or [], key=lambda item: int(str(item.get("round", "0")).split(".")[0] or 0))
                for availability in matches:
                    status = str(availability.get("status", "")).lower()
                    try:
                        round_number = int(str(availability.get("round", "0")).split(".")[0])
                    except ValueError:
                        continue
                    match_date = schedule_dates.get((season_start, team, round_number))
                    if match_date is None:
                        if status in {"starting", "sub_in"}:
                            prior_minutes += 90.0 if status == "starting" else 25.0
                            prior_statuses.append(status)
                        continue
                    if status in {"injured", "suspended"}:
                        detail = availability.get("detail")
                        expected_return = _availability_detail_return_date(detail)
                        recent_starts = prior_statuses[-5:].count("starting")
                        row = _blank_canonical_row("availability-data", collected)
                        row.update(
                            {
                                "report_date": match_date,
                                "team": team,
                                "player": player.get("name"),
                                "unavailable_from": match_date,
                                "expected_return_date": match_date,
                                "status_type": "suspension" if status == "suspended" else "injury",
                                "injury_or_suspension": detail or status,
                                "is_expected_starter": 1.0 if recent_starts >= 3 or (prior_statuses[-1:] == ["starting"]) else 0.0,
                                "is_key_player": 1.0 if prior_minutes >= 900 else 0.0,
                                "is_long_term_injury": 1.0
                                if pd.notna(expected_return) and (expected_return - match_date).days >= 30
                                else 0.0,
                                "is_suspended": 1.0 if status == "suspended" else 0.0,
                                "minutes_played_last_365": prior_minutes,
                                "source_url": "https://github.com/withqwerty/availability-data",
                            }
                        )
                        rows.append(row)
                    if status == "starting":
                        prior_minutes += 90.0
                    elif status == "sub_in":
                        prior_minutes += 25.0
                    prior_statuses.append(status)
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
        ("withqwerty availability-data", AVAILABILITY_DATA_CANDIDATES),
    ]:
        path = _first_existing(candidates)
        if path is None:
            discoveries.append(SourceDiscovery(name, candidates[0], False, 0, False, "No local source file found."))
            continue
        if path.is_dir():
            raw_files = list(path.glob("raw/GB1/*/*.json")) or list(path.glob("GB1/*/*.json"))
            discoveries.append(SourceDiscovery(name, path, True, len(raw_files), bool(raw_files), "Found availability-data JSON files."))
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
    availability_data_path = _first_existing(AVAILABILITY_DATA_CANDIDATES)
    if transfermarkt_path:
        frames.append(normalize_transfermarkt(transfermarkt_path))
    if premier_injuries_path:
        frames.append(normalize_premier_injuries(premier_injuries_path))
    if availability_data_path:
        frames.append(normalize_availability_data(availability_data_path))

    combined = pd.concat(frames, ignore_index=True) if frames else empty_canonical_frame()
    if combined.empty:
        return empty_canonical_frame()
    for column in ["report_date", "unavailable_from", "expected_return_date", "source_collected_at"]:
        combined[column] = pd.to_datetime(combined[column], errors="coerce").dt.date
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
        combined[column] = pd.to_numeric(combined[column], errors="coerce").fillna(0.0)
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
