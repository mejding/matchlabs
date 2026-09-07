from __future__ import annotations

from datetime import date

import pandas as pd

from injury_data_engine import normalize_api_football_payload, normalize_sportmonks_payload
from injury_features import active_injuries


def test_api_football_injury_payload_normalizes_to_canonical_rows() -> None:
    payload = {
        "response": [
            {
                "player": {"name": "Example Midfielder"},
                "team": {"name": "Arsenal"},
                "fixture": {"date": "2026-09-12T14:00:00+00:00"},
                "type": "Missing Fixture",
                "reason": "Hamstring Injury",
            },
            {
                "player": {"name": "Example Defender"},
                "team": {"name": "Chelsea"},
                "fixture": {"date": "2026-09-12T16:30:00+00:00"},
                "type": "Suspended",
                "reason": "Red card suspension",
            },
        ]
    }

    frame = normalize_api_football_payload(payload, collected_at=date(2026, 9, 10))

    assert len(frame) == 2
    assert set(frame["team"]) == {"Arsenal", "Chelsea"}
    assert frame.loc[frame["player"] == "Example Midfielder", "status_type"].iloc[0] == "injury"
    suspended = frame[frame["player"] == "Example Defender"].iloc[0]
    assert suspended["status_type"] == "suspension"
    assert float(suspended["is_suspended"]) == 1.0


def test_sportmonks_sidelined_payload_normalizes_nested_sideline_data() -> None:
    payload = {
        "data": {
            "id": 123,
            "name": "Hull",
            "sidelined": [
                {
                    "participant": {"name": "Hull"},
                    "player": {"display_name": "Example Forward"},
                    "type": {"name": "Muscle Injury"},
                    "sideline": {
                        "category": "injury",
                        "start_date": "2026-09-01",
                        "end_date": "2026-10-01",
                    },
                }
            ],
        }
    }

    frame = normalize_sportmonks_payload(payload, collected_at=date(2026, 9, 7))

    assert len(frame) == 1
    row = frame.iloc[0]
    assert row["team"] == "Hull"
    assert row["player"] == "Example Forward"
    assert row["unavailable_from"] == date(2026, 9, 1)
    assert row["expected_return_date"] == date(2026, 10, 1)
    assert row["status_type"] == "injury"


def test_active_injuries_respects_report_date_and_return_date() -> None:
    injuries = pd.DataFrame(
        [
            {
                "report_date": pd.Timestamp("2026-09-01"),
                "team": "Hull",
                "player": "Active Absence",
                "unavailable_from": pd.Timestamp("2026-09-01"),
                "expected_return_date": pd.Timestamp("2026-09-20"),
            },
            {
                "report_date": pd.Timestamp("2026-09-15"),
                "team": "Hull",
                "player": "Future Report",
                "unavailable_from": pd.Timestamp("2026-09-01"),
                "expected_return_date": pd.Timestamp("2026-09-20"),
            },
            {
                "report_date": pd.Timestamp("2026-08-20"),
                "team": "Hull",
                "player": "Already Returned",
                "unavailable_from": pd.Timestamp("2026-08-20"),
                "expected_return_date": pd.Timestamp("2026-09-05"),
            },
        ]
    )

    active = active_injuries(injuries, "Hull", pd.Timestamp("2026-09-12"))

    assert list(active["player"]) == ["Active Absence"]
