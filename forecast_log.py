from __future__ import annotations

import argparse
from datetime import datetime, timezone
from pathlib import Path

import joblib
import pandas as pd

from official_fixtures import OFFICIAL_FIXTURE_PATH, fixtures_for_model, load_official_fixtures
from season_simulation import filter_unplayed_fixtures, load_completed_current_season_matches, predict_fixture_probabilities
from train_model import MODEL_PATH


FORECAST_LOG_PATH = Path("evaluation") / "fixtures_2026_27" / "forecast_log.csv"
LATEST_FORECAST_PATH = Path("evaluation") / "fixtures_2026_27" / "latest_forecast_snapshot.csv"
CALIBRATION_PATH = Path("models") / "calibrated_probability_layer.joblib"


def load_calibrator(feature_columns: list[str], calibration_path: Path = CALIBRATION_PATH):
    if not calibration_path.exists():
        return None, "raw"
    layer = joblib.load(calibration_path)
    if list(layer.get("feature_columns", [])) != list(feature_columns):
        return None, "raw"
    method = str(layer.get("method", "calibrated"))
    if method in {"sigmoid", "isotonic"}:
        return layer["calibrator"], method
    return None, "raw"


def build_forecast_snapshot(snapshot_time: datetime | None = None) -> pd.DataFrame:
    if not MODEL_PATH.exists():
        raise FileNotFoundError("Model not found. Run `python train_model.py --mode production` first.")
    if not OFFICIAL_FIXTURE_PATH.exists():
        raise FileNotFoundError(f"Official fixture file not found: {OFFICIAL_FIXTURE_PATH}")

    snapshot_time = snapshot_time or datetime.now(timezone.utc)
    official_fixtures = load_official_fixtures(OFFICIAL_FIXTURE_PATH)
    fixtures = fixtures_for_model(official_fixtures)
    completed = load_completed_current_season_matches()
    upcoming = filter_unplayed_fixtures(fixtures, completed)

    artifact = joblib.load(MODEL_PATH)
    feature_columns = artifact["feature_columns"]
    calibrator, calibration_method = load_calibrator(feature_columns)
    probabilities = predict_fixture_probabilities(
        upcoming,
        artifact["model"],
        feature_columns,
        artifact["team_history"],
        artifact.get("elo_state", {}),
        calibrator=calibrator,
        fixture_schedule_frame=official_fixtures,
    )
    if probabilities.empty:
        return probabilities

    output = probabilities.copy()
    output.insert(0, "snapshot_time_utc", snapshot_time.isoformat())
    output.insert(1, "model_version", str(artifact.get("production_model_version", "unknown")))
    output.insert(2, "calibration_method", calibration_method)
    output["favorite"] = output[
        ["home_win_probability", "draw_probability", "away_win_probability"]
    ].idxmax(axis=1).map(
        {
            "home_win_probability": "H",
            "draw_probability": "D",
            "away_win_probability": "A",
        }
    )
    output["favorite_probability"] = output[
        ["home_win_probability", "draw_probability", "away_win_probability"]
    ].max(axis=1)
    return output


def append_forecast_snapshot(
    log_path: Path = FORECAST_LOG_PATH,
    latest_path: Path = LATEST_FORECAST_PATH,
    snapshot_time: datetime | None = None,
) -> pd.DataFrame:
    snapshot = build_forecast_snapshot(snapshot_time=snapshot_time)
    log_path.parent.mkdir(parents=True, exist_ok=True)
    snapshot.to_csv(latest_path, index=False)
    if log_path.exists():
        existing = pd.read_csv(log_path)
        combined = pd.concat([existing, snapshot], ignore_index=True)
    else:
        combined = snapshot
    combined.to_csv(log_path, index=False)
    return snapshot


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Append a timestamped forecast snapshot for upcoming Premier League fixtures.")
    parser.add_argument("--log-path", type=Path, default=FORECAST_LOG_PATH)
    parser.add_argument("--latest-path", type=Path, default=LATEST_FORECAST_PATH)
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    snapshot = append_forecast_snapshot(log_path=args.log_path, latest_path=args.latest_path)
    print(f"Logged {len(snapshot)} upcoming fixture forecasts to {args.log_path}")
    print(f"Wrote latest snapshot to {args.latest_path}")


if __name__ == "__main__":
    main()
