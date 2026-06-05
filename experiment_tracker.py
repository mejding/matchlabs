from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import pandas as pd


EXPERIMENT_DIR = Path("experiments")
CSV_PATH = EXPERIMENT_DIR / "experiments.csv"
JSON_PATH = EXPERIMENT_DIR / "experiments.json"


def append_experiment(record: dict[str, Any]) -> None:
    EXPERIMENT_DIR.mkdir(exist_ok=True)
    record = {
        "created_at": datetime.now(timezone.utc).isoformat(),
        **record,
    }

    existing = []
    if JSON_PATH.exists():
        existing = json.loads(JSON_PATH.read_text())
    existing.append(record)
    JSON_PATH.write_text(json.dumps(existing, indent=2))

    rows = pd.json_normalize(existing)
    rows.to_csv(CSV_PATH, index=False)
