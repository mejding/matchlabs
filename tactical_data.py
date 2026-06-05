from __future__ import annotations

from pathlib import Path

import pandas as pd


DATA_DIR = Path("data")
TACTICAL_EVENTS_PATH = DATA_DIR / "team_match_tactics.csv"
TACTICAL_PROFILES_PATH = DATA_DIR / "tactical_profiles_history.csv"
STYLE_EMBEDDINGS_PATH = DATA_DIR / "team_style_embeddings.csv"

RAW_TACTICAL_FIELDS = [
    "venue",
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

TACTICAL_METRICS = [
    "average_possession",
    "possession_score",
    "progressive_passes",
    "passes_per_sequence",
    "build_up_speed",
    "long_pass_ratio",
    "progression_score",
    "directness_score",
    "PPDA",
    "high_press_events",
    "press_success_rate",
    "turnovers_forced",
    "counterpress_actions",
    "press_intensity_score",
    "crosses_per_match",
    "crossing_score",
    "through_balls",
    "counter_attacks",
    "fast_break_frequency",
    "attacking_pressure_score",
    "attacking_width_score",
    "attacking_verticality_score",
    "defensive_line_height_proxy",
    "blocks",
    "interceptions",
    "tackles",
    "low_block_score",
    "high_line_score",
    "defensive_activity_score",
    "defensive_aggression_score",
]

TACTICAL_EVENT_COLUMNS = [
    "match_id",
    "season",
    "date",
    "team",
    "opponent",
    "is_home",
    "source",
    "source_collected_at",
] + list(dict.fromkeys(RAW_TACTICAL_FIELDS + TACTICAL_METRICS))


def ensure_tactical_tables() -> None:
    DATA_DIR.mkdir(exist_ok=True)
    if not TACTICAL_EVENTS_PATH.exists():
        pd.DataFrame(columns=TACTICAL_EVENT_COLUMNS).to_csv(TACTICAL_EVENTS_PATH, index=False)
    if not TACTICAL_PROFILES_PATH.exists():
        pd.DataFrame().to_csv(TACTICAL_PROFILES_PATH, index=False)
    if not STYLE_EMBEDDINGS_PATH.exists():
        pd.DataFrame().to_csv(STYLE_EMBEDDINGS_PATH, index=False)


def load_team_match_tactics(path: Path = TACTICAL_EVENTS_PATH) -> pd.DataFrame:
    ensure_tactical_tables()
    tactics = pd.read_csv(path)
    if tactics.empty:
        return pd.DataFrame(columns=TACTICAL_EVENT_COLUMNS)

    for column in TACTICAL_EVENT_COLUMNS:
        if column not in tactics.columns:
            tactics[column] = pd.NA

    tactics["date"] = pd.to_datetime(tactics["date"], errors="coerce")
    tactics["source_collected_at"] = pd.to_datetime(tactics["source_collected_at"], errors="coerce")
    for metric in RAW_TACTICAL_FIELDS + TACTICAL_METRICS:
        if metric == "venue":
            continue
        tactics[metric] = pd.to_numeric(tactics[metric], errors="coerce")

    return tactics.dropna(subset=["date", "team"]).sort_values("date").reset_index(drop=True)


def tactical_data_note() -> str:
    return (
        "Tactical features require event-provider rows in data/team_match_tactics.csv. "
        "Rows are used only when date and source_collected_at are before the predicted fixture, "
        "so profiles are historically reproducible and leakage-safe."
    )
