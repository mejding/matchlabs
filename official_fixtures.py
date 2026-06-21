from __future__ import annotations

import json
import urllib.request
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from zoneinfo import ZoneInfo

import pandas as pd


OFFICIAL_FIXTURE_PATH = Path("data") / "upcoming_fixtures_2026_27.csv"
LEGACY_FIXTURE_PATH = Path("data") / "upcoming_fixtures.csv"
FIXTURE_EVALUATION_DIR = Path("evaluation") / "fixtures_2026_27"
PREMIER_LEAGUE_FIXTURE_API_URL = (
    "https://footballapi.pulselive.com/football/fixtures?"
    "comps=1&compSeasons=841&page=0&pageSize=380&sort=asc"
)
PREMIER_LEAGUE_FIXTURE_PAGE_URL = "https://www.premierleague.com/fixtures?co=1&se=841"
SEASON_LABEL = "2026/27"


TEAM_NAME_MAP = {
    "AFC Bournemouth": "Bournemouth",
    "Bournemouth": "Bournemouth",
    "Brighton & Hove Albion": "Brighton",
    "Brighton and Hove Albion": "Brighton",
    "Coventry City": "Coventry",
    "Hull City": "Hull",
    "Ipswich Town": "Ipswich",
    "Leeds United": "Leeds",
    "Manchester City": "Man City",
    "Manchester United": "Man United",
    "Newcastle United": "Newcastle",
    "Nottingham Forest": "Nott'm Forest",
    "Tottenham Hotspur": "Tottenham",
}


@dataclass(frozen=True)
class FixtureMode:
    mode: str
    message: str
    fixture_count: int
    team_count: int
    last_updated: str | None
    validation_ok: bool
    path: Path | None


def normalize_team_name(name: str) -> str:
    return TEAM_NAME_MAP.get(name, name)


def fetch_official_fixtures_json() -> dict:
    request = urllib.request.Request(
        PREMIER_LEAGUE_FIXTURE_API_URL,
        headers={
            "Origin": "https://www.premierleague.com",
            "User-Agent": "Mozilla/5.0",
        },
    )
    with urllib.request.urlopen(request, timeout=30) as response:
        return json.loads(response.read())


def _format_time(dt: datetime, tz_name: str) -> str:
    return dt.astimezone(ZoneInfo(tz_name)).strftime("%H:%M")


def transform_api_fixtures(payload: dict, last_updated: str | None = None) -> pd.DataFrame:
    rows = []
    now = last_updated or datetime.now(ZoneInfo("Europe/Copenhagen")).date().isoformat()
    for item in payload.get("content", []):
        kickoff_millis = int(float(item["kickoff"]["millis"]))
        kickoff_utc = datetime.fromtimestamp(kickoff_millis / 1000, tz=ZoneInfo("UTC"))
        kickoff_uk = kickoff_utc.astimezone(ZoneInfo("Europe/London"))
        teams = item["teams"]
        home_team = normalize_team_name(teams[0]["team"]["club"]["name"])
        away_team = normalize_team_name(teams[1]["team"]["club"]["name"])
        rows.append(
            {
                "season": SEASON_LABEL,
                "matchweek": int(float(item["gameweek"]["gameweek"])),
                "date": kickoff_uk.date().isoformat(),
                "kickoff_time_uk": _format_time(kickoff_utc, "Europe/London"),
                "kickoff_time_dk": _format_time(kickoff_utc, "Europe/Copenhagen"),
                "home_team": home_team,
                "away_team": away_team,
                "source": "Premier League official fixtures",
                "source_url": PREMIER_LEAGUE_FIXTURE_PAGE_URL,
                "fixture_status": "scheduled_subject_to_change",
                "last_updated": now,
            }
        )
    return pd.DataFrame(rows).sort_values(["date", "kickoff_time_uk", "home_team", "away_team"]).reset_index(drop=True)


def validate_fixture_frame(frame: pd.DataFrame) -> dict[str, object]:
    errors: list[str] = []
    required = {
        "season",
        "matchweek",
        "date",
        "kickoff_time_uk",
        "kickoff_time_dk",
        "home_team",
        "away_team",
        "source",
        "source_url",
        "fixture_status",
        "last_updated",
    }
    missing = sorted(required - set(frame.columns))
    if missing:
        errors.append(f"Missing required columns: {missing}")

    fixture_count = int(len(frame))
    teams = sorted(set(frame.get("home_team", pd.Series(dtype=str))).union(set(frame.get("away_team", pd.Series(dtype=str)))))
    if fixture_count != 380:
        errors.append(f"Expected 380 fixtures, found {fixture_count}")
    if len(teams) != 20:
        errors.append(f"Expected 20 teams, found {len(teams)}")

    duplicate_count = int(frame.duplicated(subset=["date", "home_team", "away_team"]).sum()) if not frame.empty else 0
    if duplicate_count:
        errors.append(f"Found {duplicate_count} duplicate date/home/away fixtures")

    parsed_dates = pd.to_datetime(frame.get("date", pd.Series(dtype=str)), errors="coerce")
    invalid_dates = int(parsed_dates.isna().sum())
    if invalid_dates:
        errors.append(f"Found {invalid_dates} invalid dates")

    kickoff_pattern = r"^\d{2}:\d{2}$"
    invalid_uk_times = int((~frame.get("kickoff_time_uk", pd.Series(dtype=str)).astype(str).str.match(kickoff_pattern)).sum())
    invalid_dk_times = int((~frame.get("kickoff_time_dk", pd.Series(dtype=str)).astype(str).str.match(kickoff_pattern)).sum())
    if invalid_uk_times:
        errors.append(f"Found {invalid_uk_times} invalid UK kickoff times")
    if invalid_dk_times:
        errors.append(f"Found {invalid_dk_times} invalid DK kickoff times")

    team_rows = []
    for team in teams:
        home_matches = int((frame["home_team"] == team).sum())
        away_matches = int((frame["away_team"] == team).sum())
        total_matches = home_matches + away_matches
        team_rows.append({"team": team, "matches": total_matches, "home": home_matches, "away": away_matches})
        if total_matches != 38:
            errors.append(f"{team} has {total_matches} matches")
        if home_matches != 19:
            errors.append(f"{team} has {home_matches} home matches")
        if away_matches != 19:
            errors.append(f"{team} has {away_matches} away matches")

    return {
        "valid": not errors,
        "errors": errors,
        "fixture_count": fixture_count,
        "team_count": len(teams),
        "teams": teams,
        "team_counts": pd.DataFrame(team_rows),
        "duplicate_count": duplicate_count,
        "invalid_dates": invalid_dates,
        "invalid_uk_times": invalid_uk_times,
        "invalid_dk_times": invalid_dk_times,
    }


def write_validation_report(frame: pd.DataFrame, validation: dict[str, object], output_path: Path) -> None:
    output_path.parent.mkdir(parents=True, exist_ok=True)
    team_counts = validation["team_counts"]
    errors = validation["errors"]
    team_table = "| team | matches | home | away |\n| --- | ---: | ---: | ---: |\n" + "\n".join(
        f"| {row.team} | {int(row.matches)} | {int(row.home)} | {int(row.away)} |" for row in team_counts.itertuples(index=False)
    )
    output_path.write_text(
        f"""# Fixture Import Validation Report

## Source

- Source: Premier League official fixtures
- Source URL: {PREMIER_LEAGUE_FIXTURE_PAGE_URL}
- API URL: `{PREMIER_LEAGUE_FIXTURE_API_URL}`

## Summary

- Valid: {validation['valid']}
- Fixtures: {validation['fixture_count']}
- Teams: {validation['team_count']}
- Duplicate fixtures: {validation['duplicate_count']}
- Invalid dates: {validation['invalid_dates']}
- Invalid UK kickoff times: {validation['invalid_uk_times']}
- Invalid DK kickoff times: {validation['invalid_dk_times']}

## Teams

{team_table}

## Errors

{chr(10).join(f'- {error}' for error in errors) if errors else '- None'}

## Notes

Fixtures are scheduled subject to change. Premier League fixtures alone do not include European or domestic cup fixtures.
"""
    )


def import_official_fixtures() -> pd.DataFrame:
    payload = fetch_official_fixtures_json()
    frame = transform_api_fixtures(payload)
    validation = validate_fixture_frame(frame)
    OFFICIAL_FIXTURE_PATH.parent.mkdir(parents=True, exist_ok=True)
    frame.to_csv(OFFICIAL_FIXTURE_PATH, index=False)
    write_validation_report(frame, validation, FIXTURE_EVALUATION_DIR / "fixture_import_validation_report.md")
    if not validation["valid"]:
        raise ValueError(f"Official fixture validation failed: {validation['errors']}")
    return frame


def load_official_fixtures(path: Path = OFFICIAL_FIXTURE_PATH) -> pd.DataFrame:
    frame = pd.read_csv(path)
    validation = validate_fixture_frame(frame)
    if not validation["valid"]:
        raise ValueError(f"Official fixture file failed validation: {validation['errors']}")
    return frame


def fixtures_for_model(frame: pd.DataFrame) -> pd.DataFrame:
    output = frame.rename(columns={"season": "Season", "date": "Date", "home_team": "HomeTeam", "away_team": "AwayTeam"}).copy()
    output["Date"] = pd.to_datetime(output["Date"], errors="coerce").dt.date
    return output[["Season", "Date", "HomeTeam", "AwayTeam", "matchweek", "kickoff_time_uk", "kickoff_time_dk"]].sort_values(
        ["Date", "kickoff_time_uk", "HomeTeam", "AwayTeam"]
    )


def team_fixture_dates(frame: pd.DataFrame, team: str) -> list:
    team_rows = frame[(frame["home_team"] == team) | (frame["away_team"] == team)].copy()
    dates = pd.to_datetime(team_rows["date"], errors="coerce").dt.date.dropna().tolist()
    return sorted(dates)


def _matches_between(dates: list, match_date, start_days: int, end_days: int) -> int:
    return sum(1 for fixture_date in dates if start_days <= (fixture_date - match_date).days <= end_days)


def schedule_context_for_team(frame: pd.DataFrame, team: str, match_date) -> dict[str, float]:
    match_date = pd.to_datetime(match_date, errors="coerce").date()
    dates = team_fixture_dates(frame, team)
    previous = [fixture_date for fixture_date in dates if fixture_date < match_date]
    days_since = float((match_date - max(previous)).days) if previous else 14.0
    last_7 = _matches_between(dates, match_date, -7, -1)
    last_14 = _matches_between(dates, match_date, -14, -1)
    next_7 = _matches_between(dates, match_date, 1, 7)
    next_14 = _matches_between(dates, match_date, 1, 14)
    midweek = int(match_date.weekday() in {1, 2, 3})
    festive = int(match_date.month == 12 and match_date.day >= 20 or match_date.month == 1 and match_date.day <= 4)
    return {
        "days_rest": days_since,
        "matches_last_7_days": float(last_7),
        "matches_last_14_days": float(last_14),
        "matches_next_7_days": float(next_7),
        "matches_next_14_days": float(next_14),
        "short_rest_flag": float(days_since < 5),
        "midweek_fixture_flag": float(midweek),
        "festive_congestion_flag": float(festive),
    }


def schedule_context_for_fixture(frame: pd.DataFrame, home_team: str, away_team: str, match_date) -> dict[str, float]:
    home = schedule_context_for_team(frame, home_team, match_date)
    away = schedule_context_for_team(frame, away_team, match_date)
    return {
        "home_days_rest": home["days_rest"],
        "away_days_rest": away["days_rest"],
        "home_days_since_last_match": home["days_rest"],
        "away_days_since_last_match": away["days_rest"],
        "home_matches_last_14_days": home["matches_last_14_days"],
        "away_matches_last_14_days": away["matches_last_14_days"],
        "home_had_midweek_match": home["midweek_fixture_flag"],
        "away_had_midweek_match": away["midweek_fixture_flag"],
        "home_matches_last_7_days": home["matches_last_7_days"],
        "away_matches_last_7_days": away["matches_last_7_days"],
        "home_matches_next_7_days": home["matches_next_7_days"],
        "away_matches_next_7_days": away["matches_next_7_days"],
        "home_matches_next_14_days": home["matches_next_14_days"],
        "away_matches_next_14_days": away["matches_next_14_days"],
        "home_short_rest_flag": home["short_rest_flag"],
        "away_short_rest_flag": away["short_rest_flag"],
        "home_festive_congestion_flag": home["festive_congestion_flag"],
        "away_festive_congestion_flag": away["festive_congestion_flag"],
    }


def detect_fixture_mode(path: Path = OFFICIAL_FIXTURE_PATH) -> FixtureMode:
    if not path.exists():
        return FixtureMode("Missing fixtures", "Official 2026/27 fixtures are not loaded.", 0, 0, None, False, None)
    try:
        frame = pd.read_csv(path)
        validation = validate_fixture_frame(frame)
    except Exception as exc:
        return FixtureMode("Fixture data outdated", f"Fixture file could not be validated: {exc}", 0, 0, None, False, path)
    last_updated = None if frame.empty or "last_updated" not in frame else str(frame["last_updated"].dropna().max())
    mode = "Official fixtures loaded" if validation["valid"] else "Fixture data outdated"
    message = (
        f"Official fixtures loaded: {validation['fixture_count']} matches · {validation['team_count']} teams · last updated {last_updated}"
        if validation["valid"]
        else f"Official fixture file failed validation: {validation['errors']}"
    )
    return FixtureMode(mode, message, int(validation["fixture_count"]), int(validation["team_count"]), last_updated, bool(validation["valid"]), path)


if __name__ == "__main__":
    imported = import_official_fixtures()
    print(f"Imported {len(imported)} official fixtures to {OFFICIAL_FIXTURE_PATH}")
