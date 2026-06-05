from __future__ import annotations

from pathlib import Path

import numpy as np
import pandas as pd

from tactical_data import RAW_TACTICAL_FIELDS, TACTICAL_EVENT_COLUMNS, TACTICAL_EVENTS_PATH, TACTICAL_METRICS


DATA_DIR = Path("data")
FOOTBALL_DATA_SEASONS = ["1920", "2021", "2122", "2223", "2324", "2425"]
FOOTBALL_DATA_FIELD_MAP = {
    "shots": ("HS", "AS"),
    "shots_on_target": ("HST", "AST"),
}
TARGET_RAW_FIELDS = [
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


def make_match_id(season: str, date: object, home_team: str, away_team: str) -> str:
    date_text = pd.to_datetime(date).strftime("%Y%m%d")
    home_slug = str(home_team).lower().replace(" ", "_").replace("'", "")
    away_slug = str(away_team).lower().replace(" ", "_").replace("'", "")
    return f"{season}_{date_text}_{home_slug}_{away_slug}"


def inspect_existing_sources() -> pd.DataFrame:
    rows = []
    for season in FOOTBALL_DATA_SEASONS:
        path = DATA_DIR / f"premier_league_{season}.csv"
        if not path.exists():
            continue
        frame = pd.read_csv(path)
        columns = set(frame.columns)
        for field, source_columns in FOOTBALL_DATA_FIELD_MAP.items():
            rows.append(
                {
                    "source": path.name,
                    "field": field,
                    "available": all(column in columns for column in source_columns),
                    "source_columns": "|".join(source_columns),
                }
            )
        for field in sorted(set(TARGET_RAW_FIELDS) - set(FOOTBALL_DATA_FIELD_MAP)):
            rows.append(
                {
                    "source": path.name,
                    "field": field,
                    "available": False,
                    "source_columns": "",
                }
            )
    return pd.DataFrame(rows)


def _empty_tactical_row() -> dict[str, object]:
    row = {column: pd.NA for column in TACTICAL_EVENT_COLUMNS}
    return row


def _mapped_features(row: dict[str, object]) -> dict[str, object]:
    possession = pd.to_numeric(row.get("possession"), errors="coerce")
    passes_attempted = pd.to_numeric(row.get("passes_attempted"), errors="coerce")
    progressive_passes = pd.to_numeric(row.get("progressive_passes"), errors="coerce")
    progressive_carries = pd.to_numeric(row.get("progressive_carries"), errors="coerce")
    crosses = pd.to_numeric(row.get("crosses"), errors="coerce")
    long_balls = pd.to_numeric(row.get("long_balls"), errors="coerce")
    shots = pd.to_numeric(row.get("shots"), errors="coerce")
    shots_on_target = pd.to_numeric(row.get("shots_on_target"), errors="coerce")
    tackles = pd.to_numeric(row.get("tackles"), errors="coerce")
    interceptions = pd.to_numeric(row.get("interceptions"), errors="coerce")
    blocks = pd.to_numeric(row.get("blocks"), errors="coerce")

    row["average_possession"] = possession
    row["possession_score"] = possession
    row["progression_score"] = (
        progressive_passes + progressive_carries
        if pd.notna(progressive_passes) and pd.notna(progressive_carries)
        else pd.NA
    )
    row["directness_score"] = (
        long_balls / passes_attempted
        if pd.notna(long_balls) and pd.notna(passes_attempted) and passes_attempted > 0
        else pd.NA
    )
    row["crosses_per_match"] = crosses
    row["crossing_score"] = crosses
    row["attacking_pressure_score"] = (
        shots + 2.0 * shots_on_target if pd.notna(shots) and pd.notna(shots_on_target) else pd.NA
    )
    row["defensive_activity_score"] = (
        tackles + interceptions + blocks
        if pd.notna(tackles) and pd.notna(interceptions) and pd.notna(blocks)
        else pd.NA
    )
    return row


def ingest_football_data_team_stats() -> pd.DataFrame:
    rows = []
    for season in FOOTBALL_DATA_SEASONS:
        path = DATA_DIR / f"premier_league_{season}.csv"
        if not path.exists():
            continue
        frame = pd.read_csv(path)
        frame["Date"] = pd.to_datetime(frame["Date"], dayfirst=True, errors="coerce")
        frame = frame.dropna(subset=["Date", "HomeTeam", "AwayTeam"])

        for _, match in frame.iterrows():
            match_id = make_match_id(season, match["Date"], match["HomeTeam"], match["AwayTeam"])
            collected_at = match["Date"] + pd.Timedelta(days=1)
            for is_home, team_col, opponent_col, venue, shot_col, sot_col in (
                (1, "HomeTeam", "AwayTeam", "home", "HS", "HST"),
                (0, "AwayTeam", "HomeTeam", "away", "AS", "AST"),
            ):
                row = _empty_tactical_row()
                row.update(
                    {
                        "match_id": match_id,
                        "season": season,
                        "date": match["Date"].date().isoformat(),
                        "team": match[team_col],
                        "opponent": match[opponent_col],
                        "is_home": is_home,
                        "venue": venue,
                        "source": "football-data.co.uk",
                        "source_collected_at": collected_at.date().isoformat(),
                        "shots": pd.to_numeric(match.get(shot_col), errors="coerce"),
                        "shots_on_target": pd.to_numeric(match.get(sot_col), errors="coerce"),
                    }
                )
                rows.append(_mapped_features(row))

    output = pd.DataFrame(rows, columns=TACTICAL_EVENT_COLUMNS)
    output = output.drop_duplicates(subset=["match_id", "team"]).sort_values(["date", "match_id", "is_home"])
    TACTICAL_EVENTS_PATH.parent.mkdir(exist_ok=True)
    output.to_csv(TACTICAL_EVENTS_PATH, index=False)
    return output


def missing_value_report(tactics: pd.DataFrame) -> pd.DataFrame:
    rows = []
    for column in dict.fromkeys(RAW_TACTICAL_FIELDS + TACTICAL_METRICS):
        if column not in tactics.columns:
            continue
        rows.append(
            {
                "field": column,
                "non_null_rows": int(tactics[column].notna().sum()),
                "missing_rows": int(tactics[column].isna().sum()),
                "coverage_pct": float(tactics[column].notna().mean()) if len(tactics) else 0.0,
            }
        )
    return pd.DataFrame(rows).sort_values(["coverage_pct", "field"], ascending=[False, True])


def season_coverage_report(tactics: pd.DataFrame) -> pd.DataFrame:
    if tactics.empty:
        return pd.DataFrame(columns=["season", "team_rows", "matches_with_two_team_rows"])
    grouped = tactics.groupby("match_id").size().reset_index(name="team_rows_per_match")
    match_seasons = tactics[["match_id", "season"]].drop_duplicates()
    grouped = grouped.merge(match_seasons, on="match_id", how="left")
    return grouped.groupby("season", as_index=False).agg(
        team_rows=("team_rows_per_match", "sum"),
        matches=("match_id", "nunique"),
        matches_with_two_team_rows=("team_rows_per_match", lambda values: int((values == 2).sum())),
    )


def duplicate_report(tactics: pd.DataFrame) -> pd.DataFrame:
    duplicates = tactics[tactics.duplicated(subset=["match_id", "team"], keep=False)]
    return duplicates[["match_id", "team", "date", "source"]] if not duplicates.empty else pd.DataFrame()


def markdown_table(frame: pd.DataFrame) -> str:
    if frame.empty:
        return "No rows."
    table = frame.copy()
    for column in table.columns:
        if pd.api.types.is_float_dtype(table[column]):
            table[column] = table[column].map(lambda value: f"{value:.4f}")
    columns = list(table.columns)
    header = "| " + " | ".join(columns) + " |"
    separator = "| " + " | ".join(["---"] * len(columns)) + " |"
    rows = [
        "| " + " | ".join(str(row[column]).replace("|", "\\|") for column in columns) + " |"
        for _, row in table.iterrows()
    ]
    return "\n".join([header, separator] + rows)


def write_quality_report(
    tactics: pd.DataFrame,
    source_inventory: pd.DataFrame,
    output_path: Path = Path("tactical_data_quality_report.md"),
) -> None:
    missing = missing_value_report(tactics)
    season = season_coverage_report(tactics)
    duplicates = duplicate_report(tactics)
    match_counts = tactics.groupby("match_id").size() if not tactics.empty else pd.Series(dtype=int)
    bad_match_count = int((match_counts != 2).sum()) if len(match_counts) else 0
    available_fields = missing[missing["non_null_rows"] > 0]["field"].tolist()
    unavailable_fields = missing[missing["non_null_rows"] == 0]["field"].tolist()
    available_source = source_inventory[source_inventory["available"]]

    output_path.write_text(
        f"""# Tactical Data Quality Report

## Source Discovery

Existing local football-data CSV files contain these usable tactical/stat fields:

{markdown_table(available_source[['field', 'source_columns']].drop_duplicates()) if not available_source.empty else 'No usable tactical fields found in local sources.'}

Fields requested but not available in local football-data CSVs are left null.

## Ingested Rows

- Team-match rows: {len(tactics)}
- Unique matches: {tactics['match_id'].nunique() if not tactics.empty else 0}
- Duplicate `(match_id, team)` rows: {len(duplicates)}
- Matches without exactly two team rows: {bad_match_count}

## Season Coverage

{markdown_table(season) if not season.empty else 'No season coverage.'}

## Available Fields

{', '.join(f'`{field}`' for field in available_fields) if available_fields else 'No fields have non-null values.'}

## Missing Fields

{', '.join(f'`{field}`' for field in unavailable_fields) if unavailable_fields else 'No missing fields.'}

## Feature Mapping Formulas

- `attacking_pressure_score = shots + 2 * shots_on_target`
- `possession_score = possession`
- `progression_score = progressive_passes + progressive_carries`
- `directness_score = long_balls / passes_attempted`
- `crossing_score = crosses`
- `defensive_activity_score = tackles + interceptions + blocks`

If a required input is unavailable, the mapped feature remains null.

## Missing Value Report

{markdown_table(missing)}
"""
    )


def run() -> None:
    source_inventory = inspect_existing_sources()
    tactics = ingest_football_data_team_stats()
    source_inventory.to_csv("evaluation/tactical_intelligence/source_field_inventory.csv", index=False)
    missing_value_report(tactics).to_csv("evaluation/tactical_intelligence/tactical_missing_values.csv", index=False)
    season_coverage_report(tactics).to_csv("evaluation/tactical_intelligence/tactical_season_coverage.csv", index=False)
    write_quality_report(tactics, source_inventory)
    print(f"Populated {TACTICAL_EVENTS_PATH} with {len(tactics)} team-match rows.")
    print("Saved tactical_data_quality_report.md")


if __name__ == "__main__":
    Path("evaluation/tactical_intelligence").mkdir(parents=True, exist_ok=True)
    run()
