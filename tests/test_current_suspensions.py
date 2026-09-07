from __future__ import annotations

import pandas as pd

from current_suspensions import active_suspensions, apply_suspension_adjustment, suspension_row_impact


def test_active_suspensions_filters_by_team_date_and_matches_remaining() -> None:
    suspensions = pd.DataFrame(
        [
            {
                "team": "Arsenal",
                "player": "Starter",
                "suspended_from": pd.Timestamp("2026-09-01"),
                "suspended_until": pd.Timestamp("2026-09-20"),
                "matches_remaining": 1,
                "expected_starter": 1,
                "importance_score": 0.8,
            },
            {
                "team": "Chelsea",
                "player": "Returned",
                "suspended_from": pd.Timestamp("2026-08-01"),
                "suspended_until": pd.Timestamp("2026-08-20"),
                "matches_remaining": 1,
                "expected_starter": 1,
                "importance_score": 0.8,
            },
            {
                "team": "Arsenal",
                "player": "Served",
                "suspended_from": pd.Timestamp("2026-09-01"),
                "suspended_until": pd.Timestamp("2026-09-20"),
                "matches_remaining": 0,
                "expected_starter": 1,
                "importance_score": 0.8,
            },
        ]
    )

    active = active_suspensions(suspensions, "Arsenal", "Chelsea", "2026-09-12")

    assert list(active["player"]) == ["Starter"]


def test_suspension_adjustment_moves_probability_away_from_affected_team() -> None:
    suspensions = pd.DataFrame(
        [
            {
                "team": "Arsenal",
                "player": "Key Starter",
                "suspended_from": pd.Timestamp("2026-09-01"),
                "suspended_until": pd.Timestamp("2026-09-20"),
                "matches_remaining": 1,
                "expected_starter": 1,
                "importance_score": 1.0,
            }
        ]
    )

    result = apply_suspension_adjustment([0.55, 0.25, 0.20], "Arsenal", "Chelsea", "2026-09-12", suspensions)

    assert result.applied
    assert result.probabilities[0] < 0.55
    assert result.probabilities[1] > 0.25
    assert result.probabilities[2] > 0.20
    assert round(float(result.probabilities.sum()), 6) == 1.0


def test_suspension_impact_is_capped_per_player() -> None:
    row = pd.Series({"expected_starter": 1, "importance_score": 5, "matches_remaining": 3})

    assert suspension_row_impact(row) == 0.04
