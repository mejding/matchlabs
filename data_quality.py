from __future__ import annotations

from dataclasses import dataclass
from datetime import date, timedelta
from pathlib import Path
from typing import Any

import pandas as pd


DATA_DIR = Path("data")
TACTICAL_FIELDS = [
    "possession",
    "passes_attempted",
    "passes_completed",
    "pass_completion_pct",
    "progressive_passes",
    "progressive_carries",
    "crosses",
    "long_balls",
    "shots",
    "shots_on_target",
    "tackles",
    "interceptions",
    "blocks",
]


@dataclass(frozen=True)
class DataQualityResult:
    status: str
    warnings: list[str]
    explanations: list[str]
    checks: dict[str, str]


def file_has_rows(path: str | Path) -> bool:
    file_path = Path(path)
    if not file_path.exists() or file_path.stat().st_size == 0:
        return False
    try:
        return len(pd.read_csv(file_path)) > 0
    except pd.errors.EmptyDataError:
        return False


def csv_columns(path: str | Path) -> list[str]:
    file_path = Path(path)
    if not file_path.exists() or file_path.stat().st_size == 0:
        return []
    try:
        return list(pd.read_csv(file_path, nrows=1).columns)
    except pd.errors.EmptyDataError:
        return []


def populated_csv_columns(path: str | Path, columns: list[str]) -> list[str]:
    file_path = Path(path)
    if not file_has_rows(file_path):
        return []
    frame = pd.read_csv(file_path, usecols=lambda column: column in columns)
    return [column for column in columns if column in frame.columns and frame[column].notna().any()]


def _as_float(value: Any, default: float = 0.0) -> float:
    try:
        return float(value)
    except (TypeError, ValueError):
        return default


def assess_prediction_data_quality(
    feature_row: dict[str, Any],
    home_team: str,
    away_team: str,
    team_history: dict[str, Any] | None = None,
    match_date: date | None = None,
    latest_data_date: date | None = None,
) -> DataQualityResult:
    warnings: list[str] = []
    explanations: list[str] = []
    checks = {
        "Match results data": "Active",
        "xG data": "Active",
        "Fatigue features": "Active",
        "Market odds": "Benchmark only",
    }

    if match_date and latest_data_date and match_date > latest_data_date + timedelta(days=14):
        warnings.append(
            f"The selected fixture date is after the latest match in the local dataset ({latest_data_date}). "
            "The prediction uses the most recent available team form and should be refreshed when newer results are imported."
        )
        checks["Match results data"] = "Stale"

    for side, team in (("home", home_team), ("away", away_team)):
        days_rest = _as_float(feature_row.get(f"{side}_days_rest"))
        if days_rest > 30 and not (match_date and latest_data_date and match_date > latest_data_date + timedelta(days=14)):
            warnings.append(
                f"{team} has a very large gap since its last match in the dataset. Prediction reliability may be reduced."
            )
        if team_history is not None and team not in team_history:
            warnings.append(f"{team} is not present in the saved team history.")

    xg_keys = ["home_xg_avg", "away_xg_avg", "home_xga_avg", "away_xga_avg"]
    if any(key not in feature_row for key in xg_keys):
        checks["xG data"] = "Missing"
        warnings.append("xG features are missing from this model artifact.")

    if file_has_rows(DATA_DIR / "injuries.csv"):
        checks["Injury data"] = "Available"

    if file_has_rows(DATA_DIR / "player_appearances.csv"):
        checks["Lineup stability"] = "Available"

    tactics_path = DATA_DIR / "team_match_tactics.csv"
    if file_has_rows(tactics_path):
        available_tactical = populated_csv_columns(tactics_path, TACTICAL_FIELDS)
        missing_tactical = [field for field in TACTICAL_FIELDS if field not in available_tactical]
        if available_tactical:
            checks["Tactical pressure"] = "Candidate"
            explanations.append(
                "Tactical pressure has partial real data, mainly shots-based proxies from football-data.co.uk."
            )
        if missing_tactical:
            explanations.append(
                "Advanced tactical fields such as possession, passing and pressing are still missing or incomplete."
            )

    if len(warnings) == 0:
        status = "Good"
    elif len(warnings) <= 2:
        status = "Warning"
    else:
        status = "Poor"

    return DataQualityResult(status=status, warnings=warnings, explanations=explanations, checks=checks)


def build_project_data_quality_report() -> str:
    sections = ["# Data Quality Report", ""]
    files = [
        ("Premier League 2024/25 results", DATA_DIR / "premier_league_2425.csv"),
        ("Understat 2024 xG", DATA_DIR / "understat_epl_2024.json"),
        ("Injury data", DATA_DIR / "injuries.csv"),
        ("Lineup appearances", DATA_DIR / "player_appearances.csv"),
        ("Team match tactics", DATA_DIR / "team_match_tactics.csv"),
        ("FBref team match stats", DATA_DIR / "fbref_team_match_stats.csv"),
    ]
    for label, path in files:
        if path.suffix == ".json":
            status = "Present" if path.exists() and path.stat().st_size > 0 else "Missing"
            rows = "n/a"
        else:
            status = "Has rows" if file_has_rows(path) else "Missing or template-only"
            rows = str(len(pd.read_csv(path))) if path.exists() and path.suffix == ".csv" else "0"
        sections.append(f"- {label}: {status} ({rows} rows)")

    tactics_path = DATA_DIR / "team_match_tactics.csv"
    available = populated_csv_columns(tactics_path, TACTICAL_FIELDS)
    missing = [field for field in TACTICAL_FIELDS if field not in available]
    sections.extend(
        [
            "",
            "## Tactical Field Availability",
            "",
            f"- Available fields: {', '.join(available) if available else 'None'}",
            f"- Missing fields: {', '.join(missing) if missing else 'None'}",
            "",
            "## Production Interpretation",
            "",
            "Injuries and lineup stability are treated as template/research data unless their CSV files contain real historical rows.",
            "Tactical pressure is only a candidate feature because current coverage is mostly shots-based, not full tactical event data.",
        ]
    )
    return "\n".join(sections) + "\n"


def main() -> None:
    Path("data_quality_report.md").write_text(build_project_data_quality_report())
    print("Wrote data_quality_report.md")


if __name__ == "__main__":
    main()
