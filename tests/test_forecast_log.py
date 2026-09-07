from datetime import datetime, timezone

import pandas as pd

import forecast_log


def test_append_forecast_snapshot_writes_latest_and_appends_log(tmp_path, monkeypatch) -> None:
    snapshot = pd.DataFrame(
        [
            {
                "snapshot_time_utc": "2026-09-07T10:00:00+00:00",
                "model_version": "test",
                "calibration_method": "sigmoid",
                "Date": "2026-09-12",
                "Season": "2627",
                "HomeTeam": "Arsenal",
                "AwayTeam": "Chelsea",
                "home_win_probability": 0.5,
                "draw_probability": 0.25,
                "away_win_probability": 0.25,
                "favorite": "H",
                "favorite_probability": 0.5,
            }
        ]
    )
    monkeypatch.setattr(forecast_log, "build_forecast_snapshot", lambda snapshot_time=None: snapshot)
    log_path = tmp_path / "forecast_log.csv"
    latest_path = tmp_path / "latest_forecast_snapshot.csv"

    first = forecast_log.append_forecast_snapshot(log_path, latest_path, datetime(2026, 9, 7, tzinfo=timezone.utc))
    second = forecast_log.append_forecast_snapshot(log_path, latest_path, datetime(2026, 9, 7, tzinfo=timezone.utc))

    log = pd.read_csv(log_path)
    latest = pd.read_csv(latest_path)
    assert len(first) == 1
    assert len(second) == 1
    assert len(log) == 2
    assert len(latest) == 1
    assert latest.loc[0, "favorite"] == "H"
