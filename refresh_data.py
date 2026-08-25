from __future__ import annotations

import argparse
import gzip
import json
import os
import subprocess
import sys
import urllib.request
from dataclasses import dataclass
from pathlib import Path

import pandas as pd

from train_model import BASE_URL, DATA_DIR, SEASONS, UNDERSTAT_URL


DEFAULT_UNDERSTAT_SEASONS = [2019, 2020, 2021, 2022, 2023, 2024, 2025, 2026]
REPORT_PATH = Path("data_refresh_report.md")


@dataclass(frozen=True)
class DownloadResult:
    source: str
    season: str
    path: Path
    status: str
    rows: int | None = None
    latest_date: str | None = None
    message: str = ""


def _read_csv_summary(path: Path) -> tuple[int, str | None]:
    if not path.exists():
        return 0, None
    frame = pd.read_csv(path)
    if "Date" not in frame.columns or frame.empty:
        return int(len(frame)), None
    dates = pd.to_datetime(frame["Date"], dayfirst=True, errors="coerce").dropna()
    latest = str(dates.max().date()) if not dates.empty else None
    return int(len(frame)), latest


def _download_bytes(url: str) -> bytes:
    request = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
    with urllib.request.urlopen(request, timeout=45) as response:
        return response.read()


def refresh_football_data_season(season: str, force: bool, dry_run: bool) -> DownloadResult:
    DATA_DIR.mkdir(exist_ok=True)
    path = DATA_DIR / f"premier_league_{season}.csv"
    if path.exists() and not force:
        rows, latest = _read_csv_summary(path)
        return DownloadResult("football-data", season, path, "kept_existing", rows, latest)

    url = BASE_URL.format(season=season)
    if dry_run:
        rows, latest = _read_csv_summary(path)
        return DownloadResult("football-data", season, path, "dry_run", rows, latest, f"Would download {url}")

    try:
        raw = _download_bytes(url)
        path.write_bytes(raw)
        rows, latest = _read_csv_summary(path)
        return DownloadResult("football-data", season, path, "downloaded", rows, latest, url)
    except Exception as exc:
        rows, latest = _read_csv_summary(path)
        return DownloadResult("football-data", season, path, "failed", rows, latest, str(exc))


def refresh_understat_season(season: int, force: bool, dry_run: bool) -> DownloadResult:
    DATA_DIR.mkdir(exist_ok=True)
    path = DATA_DIR / f"understat_epl_{season}.json"
    if path.exists() and not force:
        return DownloadResult("understat", str(season), path, "kept_existing", message="Existing cached JSON kept.")

    url = UNDERSTAT_URL.format(season=season)
    if dry_run:
        return DownloadResult("understat", str(season), path, "dry_run", message=f"Would download {url}")

    request = urllib.request.Request(
        url,
        headers={
            "User-Agent": "Mozilla/5.0",
            "Referer": f"https://understat.com/league/EPL/{season}",
            "X-Requested-With": "XMLHttpRequest",
        },
    )
    try:
        raw = urllib.request.urlopen(request, timeout=45).read()
        try:
            text = gzip.decompress(raw).decode("utf-8")
        except gzip.BadGzipFile:
            text = raw.decode("utf-8")
        path.write_text(text, encoding="utf-8")
        data = json.loads(text)
        result_rows = [match for match in data.get("dates", []) if match.get("isResult")]
        latest = None
        if result_rows:
            latest_date = pd.to_datetime([match["datetime"] for match in result_rows], errors="coerce").max()
            latest = str(latest_date.date()) if pd.notna(latest_date) else None
        return DownloadResult("understat", str(season), path, "downloaded", len(result_rows), latest, url)
    except Exception as exc:
        return DownloadResult("understat", str(season), path, "failed", message=str(exc))


def load_football_data_for_seasons(seasons: list[str]) -> pd.DataFrame:
    frames: list[pd.DataFrame] = []
    for season in seasons:
        path = DATA_DIR / f"premier_league_{season}.csv"
        if not path.exists():
            continue
        frame = pd.read_csv(path)
        required = ["Date", "HomeTeam", "AwayTeam", "FTHG", "FTAG", "FTR"]
        missing = [column for column in required if column not in frame.columns]
        if missing:
            continue
        shot_columns = [column for column in ["HS", "AS", "HST", "AST"] if column in frame.columns]
        frame = frame[required + shot_columns].copy()
        frame["Season"] = season
        frame["Date"] = pd.to_datetime(frame["Date"], dayfirst=True, errors="coerce").dt.date
        frame = frame.dropna(subset=["Date", "HomeTeam", "AwayTeam", "FTHG", "FTAG", "FTR"])
        frames.append(frame)
    if not frames:
        return pd.DataFrame(columns=["Date", "HomeTeam", "AwayTeam", "FTHG", "FTAG", "FTR", "Season"])
    return pd.concat(frames, ignore_index=True).sort_values("Date").reset_index(drop=True)


def validate_local_data(seasons: list[str]) -> dict[str, object]:
    validation: dict[str, object] = {}
    matches = load_football_data_for_seasons(seasons)
    validation["football_data_rows"] = int(len(matches))
    validation["football_data_first_date"] = str(matches["Date"].min()) if not matches.empty else ""
    validation["football_data_latest_date"] = str(matches["Date"].max()) if not matches.empty else ""
    validation["football_data_seasons"] = ", ".join(sorted(matches["Season"].astype(str).unique())) if not matches.empty else ""
    validation["football_data_matches_by_season"] = (
        matches.groupby("Season").size().reset_index(name="matches").to_dict("records")
        if not matches.empty
        else []
    )
    xg_files = sorted(DATA_DIR.glob("understat_epl_*.json"))
    validation["understat_files"] = ", ".join(path.name for path in xg_files)
    validation["xg_merge_status"] = "checked_by_training"
    validation["xg_rows"] = ""
    validation["xg_missing_rows"] = ""

    return validation


def run_command(command: list[str], seasons: list[str], understat_seasons: list[int]) -> tuple[str, int, str]:
    env = os.environ.copy()
    env["FOOTBALL_DATA_SEASONS"] = " ".join(seasons)
    env["UNDERSTAT_SEASONS"] = " ".join(str(season) for season in understat_seasons)
    completed = subprocess.run(command, check=False, text=True, capture_output=True, env=env)
    output = "\n".join(part for part in [completed.stdout.strip(), completed.stderr.strip()] if part)
    return " ".join(command), int(completed.returncode), output[-4000:]


def result_table(results: list[DownloadResult]) -> str:
    if not results:
        return "No download checks were run."
    lines = [
        "| Source | Season | Status | Rows | Latest date | Path |",
        "| --- | --- | --- | ---: | --- | --- |",
    ]
    for result in results:
        lines.append(
            f"| {result.source} | {result.season} | {result.status} | {result.rows if result.rows is not None else ''} | "
            f"{result.latest_date or ''} | `{result.path}` |"
        )
    return "\n".join(lines)


def validation_section(validation: dict[str, object]) -> str:
    by_season = pd.DataFrame(validation.get("football_data_matches_by_season", []))
    season_table = "No season rows found."
    if not by_season.empty:
        season_table = "\n".join(
            [
                "| Season | Matches |",
                "| --- | ---: |",
                *[f"| {row.Season} | {int(row.matches)} |" for row in by_season.itertuples(index=False)],
            ]
        )

    lines = [
        "## Validation",
        "",
        f"- Football-data rows: `{validation.get('football_data_rows', 0)}`",
        f"- First local match date: `{validation.get('football_data_first_date', '')}`",
        f"- Latest local match date: `{validation.get('football_data_latest_date', '')}`",
        f"- Local seasons: `{validation.get('football_data_seasons', '')}`",
        f"- xG merge status: `{validation.get('xg_merge_status', 'unknown')}`",
        f"- xG rows: `{validation.get('xg_rows', '')}`",
        f"- xG missing rows: `{validation.get('xg_missing_rows', '')}`",
    ]
    if validation.get("xg_error"):
        lines.append(f"- xG error: `{validation['xg_error']}`")
    lines.extend(["", "### Matches By Season", "", season_table])
    return "\n".join(lines)


def write_report(
    football_results: list[DownloadResult],
    understat_results: list[DownloadResult],
    validation: dict[str, object],
    commands: list[tuple[str, int, str]],
    args: argparse.Namespace,
) -> None:
    command_lines = []
    for command, code, output in commands:
        command_lines.append(f"### `{command}`\n\nExit code: `{code}`\n\n```text\n{output or '(no output)'}\n```")

    REPORT_PATH.write_text(
        f"""# Data Refresh Report

## Run Configuration

- Force download: `{args.force}`
- Dry run: `{args.dry_run}`
- Train model: `{not args.skip_train}`
- Calibrate probabilities: `{not args.skip_calibration}`
- Run full evaluation: `{not args.skip_evaluation}`

## Football-Data Refresh

{result_table(football_results)}

## Understat Refresh

{result_table(understat_results)}

{validation_section(validation)}

## Commands

{chr(10).join(command_lines) if command_lines else 'No training/evaluation commands were run.'}

## Notes

- `football-data.co.uk` CSV files are cached locally unless `--force` is used.
- Understat JSON files are cached locally unless `--force` is used.
- The production model is only updated after `python train_model.py --mode production` succeeds.
- Streamlit Cloud only updates after the changed files are committed and pushed to GitHub.
""",
        encoding="utf-8",
    )


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Refresh local match data and optionally retrain/evaluate the model.")
    parser.add_argument("--seasons", nargs="+", default=SEASONS, help="football-data.co.uk season codes, e.g. 2526 2627.")
    parser.add_argument(
        "--understat-seasons",
        nargs="+",
        type=int,
        default=None,
        help="Understat season years, e.g. 2025 2026.",
    )
    parser.add_argument("--force", action="store_true", help="Re-download files even when local cached files exist.")
    parser.add_argument("--dry-run", action="store_true", help="Show what would be downloaded without network writes.")
    parser.add_argument("--skip-train", action="store_true", help="Skip production model retraining.")
    parser.add_argument("--skip-calibration", action="store_true", help="Skip calibration refresh.")
    parser.add_argument("--skip-evaluation", action="store_true", help="Skip full model evaluation.")
    args = parser.parse_args()
    if args.understat_seasons is None:
        if args.seasons == SEASONS:
            args.understat_seasons = DEFAULT_UNDERSTAT_SEASONS
        else:
            args.understat_seasons = [2000 + int(str(season)[:2]) for season in args.seasons]
    if len(args.understat_seasons) != len(args.seasons):
        raise SystemExit("--understat-seasons must contain the same number of entries as --seasons.")
    return args


def main() -> None:
    args = parse_args()
    football_results = [refresh_football_data_season(season, args.force, args.dry_run) for season in args.seasons]
    understat_results = [refresh_understat_season(season, args.force, args.dry_run) for season in args.understat_seasons]
    validation = validate_local_data(args.seasons)

    commands: list[tuple[str, int, str]] = []
    if not args.dry_run and not args.skip_train:
        commands.append(run_command([sys.executable, "train_model.py", "--mode", "production"], args.seasons, args.understat_seasons))
    if not args.dry_run and not args.skip_calibration:
        commands.append(run_command([sys.executable, "calibration_improvement.py"], args.seasons, args.understat_seasons))
    if not args.dry_run and not args.skip_evaluation:
        commands.append(run_command([sys.executable, "evaluate_model.py"], args.seasons, args.understat_seasons))

    write_report(football_results, understat_results, validation, commands, args)

    print(f"Wrote {REPORT_PATH}")
    print(
        json.dumps(
            {
                "football_data_latest_date": validation.get("football_data_latest_date"),
                "xg_merge_status": validation.get("xg_merge_status"),
                "report": str(REPORT_PATH),
            },
            indent=2,
        )
    )


if __name__ == "__main__":
    main()
