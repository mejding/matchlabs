from __future__ import annotations

from pathlib import Path

import pandas as pd

from tactical_data import TACTICAL_EVENT_COLUMNS
from tactical_data_ingestion import _empty_tactical_row, _mapped_features, make_match_id


FBREF_DIR = Path("data") / "fbref"
FBREF_COLUMN_ALIASES = {
    "date": ["Date", "date"],
    "team": ["Team", "Squad", "team"],
    "opponent": ["Opponent", "Opp", "opponent"],
    "venue": ["Venue", "venue"],
    "possession": ["Poss", "Possession", "Poss%"],
    "passes_attempted": ["Att", "Passes_Att", "Passes Attempted"],
    "passes_completed": ["Cmp", "Passes_Cmp", "Passes Completed"],
    "pass_completion_pct": ["Cmp%", "Pass Completion %"],
    "progressive_passes": ["PrgP", "Progressive Passes"],
    "progressive_carries": ["PrgC", "Progressive Carries"],
    "crosses": ["Crs", "Crosses"],
    "long_balls": ["Long", "Long Balls"],
    "shots": ["Sh", "Shots"],
    "shots_on_target": ["SoT", "Shots on Target"],
    "tackles": ["Tkl", "Tackles"],
    "interceptions": ["Int", "Interceptions"],
    "blocks": ["Blocks", "Blocks_Blocks"],
}


def _first_existing(frame: pd.DataFrame, aliases: list[str]) -> str | None:
    for alias in aliases:
        if alias in frame.columns:
            return alias
    return None


def load_fbref_exports(directory: Path = FBREF_DIR) -> pd.DataFrame:
    """Load user-provided FBref CSV exports.

    This function does not scrape or invent data. Place one or more FBref team match
    stats CSV files in data/fbref/ with date, team, opponent, and any supported stat
    columns. Missing stats are kept null.
    """
    if not directory.exists():
        return pd.DataFrame(columns=TACTICAL_EVENT_COLUMNS)

    rows = []
    for path in sorted(directory.glob("*.csv")):
        frame = pd.read_csv(path)
        date_col = _first_existing(frame, FBREF_COLUMN_ALIASES["date"])
        team_col = _first_existing(frame, FBREF_COLUMN_ALIASES["team"])
        opponent_col = _first_existing(frame, FBREF_COLUMN_ALIASES["opponent"])
        if not date_col or not team_col or not opponent_col:
            continue

        frame[date_col] = pd.to_datetime(frame[date_col], errors="coerce")
        season = path.stem
        for _, source_row in frame.dropna(subset=[date_col, team_col, opponent_col]).iterrows():
            team = source_row[team_col]
            opponent = source_row[opponent_col]
            date = source_row[date_col]
            row = _empty_tactical_row()
            row.update(
                {
                    "match_id": make_match_id(season, date, team, opponent),
                    "season": season,
                    "date": date.date().isoformat(),
                    "team": team,
                    "opponent": opponent,
                    "source": f"fbref_export:{path.name}",
                    "source_collected_at": (date + pd.Timedelta(days=1)).date().isoformat(),
                }
            )
            for target, aliases in FBREF_COLUMN_ALIASES.items():
                if target in {"date", "team", "opponent"}:
                    continue
                source_col = _first_existing(frame, aliases)
                if source_col:
                    row[target] = source_row[source_col]
            rows.append(_mapped_features(row))

    return pd.DataFrame(rows, columns=TACTICAL_EVENT_COLUMNS)


def save_fbref_ingestion(output_path: Path = Path("data") / "team_match_tactics_fbref.csv") -> pd.DataFrame:
    frame = load_fbref_exports()
    output_path.parent.mkdir(exist_ok=True)
    frame.to_csv(output_path, index=False)
    return frame


if __name__ == "__main__":
    output = save_fbref_ingestion()
    print(f"Saved {len(output)} FBref-derived team-match rows.")
