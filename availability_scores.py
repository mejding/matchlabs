from __future__ import annotations

import numpy as np
import pandas as pd


AVAILABILITY_FEATURES = [
    "availability_score",
    "lineup_strength_score",
    "injury_severity_score",
]


def _score_team_availability(row: pd.Series, prefix: str) -> dict[str, float]:
    injured_players = float(row.get(f"{prefix}_injured_players_count", 0.0))
    injured_starters = float(row.get(f"{prefix}_injured_starters_count", 0.0))
    missing_minutes = float(row.get(f"{prefix}_missing_minutes", 0.0))
    missing_xg = float(row.get(f"{prefix}_missing_xg", 0.0))
    missing_xa = float(row.get(f"{prefix}_missing_xa", 0.0))
    missing_market_value = float(row.get(f"{prefix}_missing_market_value", 0.0))

    starter_penalty = 6.0 * injured_starters
    squad_penalty = 1.5 * max(0.0, injured_players - injured_starters)
    minutes_penalty = missing_minutes / 450.0
    attacking_penalty = 3.0 * (missing_xg + missing_xa)
    value_penalty = missing_market_value / 15_000_000.0

    injury_severity = starter_penalty + squad_penalty + minutes_penalty + attacking_penalty + value_penalty
    availability = float(np.clip(100.0 - injury_severity, 0.0, 100.0))
    lineup_strength = float(np.clip(100.0 - starter_penalty - minutes_penalty - attacking_penalty, 0.0, 100.0))

    return {
        "availability_score": availability,
        "lineup_strength_score": lineup_strength,
        "injury_severity_score": float(injury_severity),
    }


def add_availability_scores(features: pd.DataFrame) -> pd.DataFrame:
    """Add 0-100 availability metrics derived from historical injury features."""
    rows = []
    for _, row in features.iterrows():
        scored = {}
        for prefix in ("home", "away"):
            values = _score_team_availability(row, prefix)
            for feature, value in values.items():
                scored[f"{prefix}_{feature}"] = value
        rows.append(scored)

    return pd.concat([features.reset_index(drop=True), pd.DataFrame(rows)], axis=1)


def availability_feature_columns() -> list[str]:
    return [f"{side}_{feature}" for side in ("home", "away") for feature in AVAILABILITY_FEATURES]


def availability_formula_note() -> str:
    return (
        "availability_score = 100 - weighted injury severity. Severity weights starters, squad "
        "depth, missing minutes, missing xG/xA, and missing market value. Scores are clipped to 0-100."
    )
