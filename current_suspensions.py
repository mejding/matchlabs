from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

import numpy as np
import pandas as pd


SUSPENSION_PATH = Path("data") / "current_suspensions.csv"
SUSPENSION_COLUMNS = [
    "team",
    "player",
    "suspended_from",
    "suspended_until",
    "matches_remaining",
    "reason",
    "expected_starter",
    "importance_score",
    "source",
    "last_updated",
]
MAX_TEAM_IMPACT = 0.06


@dataclass(frozen=True)
class SuspensionAdjustment:
    probabilities: np.ndarray
    total_home_impact: float
    total_away_impact: float
    active_rows: pd.DataFrame

    @property
    def applied(self) -> bool:
        return bool(self.total_home_impact or self.total_away_impact)


def ensure_current_suspensions_template(path: Path = SUSPENSION_PATH) -> None:
    path.parent.mkdir(exist_ok=True)
    if not path.exists():
        pd.DataFrame(columns=SUSPENSION_COLUMNS).to_csv(path, index=False)


def load_current_suspensions(path: Path = SUSPENSION_PATH) -> pd.DataFrame:
    ensure_current_suspensions_template(path)
    frame = pd.read_csv(path)
    if frame.empty:
        return pd.DataFrame(columns=SUSPENSION_COLUMNS)
    for column in SUSPENSION_COLUMNS:
        if column not in frame.columns:
            frame[column] = 0.0 if column in {"matches_remaining", "expected_starter", "importance_score"} else pd.NA
    for column in ["suspended_from", "suspended_until", "last_updated"]:
        frame[column] = pd.to_datetime(frame[column], errors="coerce")
    for column in ["matches_remaining", "expected_starter", "importance_score"]:
        frame[column] = pd.to_numeric(frame[column], errors="coerce").fillna(0.0)
    return frame[SUSPENSION_COLUMNS].dropna(subset=["team", "player", "suspended_from"]).reset_index(drop=True)


def active_suspensions(
    suspensions: pd.DataFrame,
    home_team: str,
    away_team: str,
    match_date,
) -> pd.DataFrame:
    if suspensions.empty:
        return suspensions
    current_date = pd.to_datetime(match_date, errors="coerce")
    if pd.isna(current_date):
        current_date = pd.Timestamp.today().normalize()
    teams = {str(home_team), str(away_team)}
    active = suspensions[
        suspensions["team"].astype(str).isin(teams)
        & (suspensions["suspended_from"] <= current_date)
        & (suspensions["matches_remaining"] > 0)
        & (suspensions["suspended_until"].isna() | (suspensions["suspended_until"] >= current_date))
    ].copy()
    return active.reset_index(drop=True)


def suspension_row_impact(row: pd.Series) -> float:
    expected_starter = float(row.get("expected_starter", 0.0))
    importance = float(row.get("importance_score", 0.0))
    matches_remaining = float(row.get("matches_remaining", 0.0))
    impact = 0.004 + 0.010 * min(max(expected_starter, 0.0), 1.0) + 0.026 * min(max(importance, 0.0), 1.0)
    if matches_remaining >= 2:
        impact += 0.004
    return float(min(max(impact, 0.0), 0.04))


def _team_impact(active: pd.DataFrame, team: str) -> float:
    team_rows = active[active["team"].astype(str) == str(team)]
    if team_rows.empty:
        return 0.0
    return float(min(team_rows.apply(suspension_row_impact, axis=1).sum(), MAX_TEAM_IMPACT))


def _normalize(probabilities: np.ndarray) -> np.ndarray:
    clipped = np.clip(probabilities.astype(float), 1e-9, 1.0)
    return clipped / clipped.sum()


def apply_suspension_adjustment(
    probabilities,
    home_team: str,
    away_team: str,
    match_date,
    suspensions: pd.DataFrame | None = None,
) -> SuspensionAdjustment:
    base = _normalize(np.asarray(probabilities, dtype=float))
    suspension_rows = load_current_suspensions() if suspensions is None else suspensions
    active = active_suspensions(suspension_rows, home_team, away_team, match_date)
    home_impact = _team_impact(active, home_team)
    away_impact = _team_impact(active, away_team)
    adjusted = base.copy()

    if home_impact:
        available = min(home_impact, adjusted[0] - 1e-9)
        adjusted[0] -= available
        adjusted[1] += available * 0.35
        adjusted[2] += available * 0.65
    if away_impact:
        available = min(away_impact, adjusted[2] - 1e-9)
        adjusted[2] -= available
        adjusted[1] += available * 0.35
        adjusted[0] += available * 0.65

    return SuspensionAdjustment(
        probabilities=_normalize(adjusted),
        total_home_impact=home_impact,
        total_away_impact=away_impact,
        active_rows=active,
    )
