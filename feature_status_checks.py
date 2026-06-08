from __future__ import annotations

from pathlib import Path

import joblib

from model_feature_status import FEATURE_STATUS, validate_active_features
from predict import MODEL_PATH


def main() -> None:
    artifact = joblib.load(MODEL_PATH)
    feature_columns = list(artifact.get("feature_columns", []))
    errors = validate_active_features(feature_columns)

    inactive_active = [
        name
        for name, entry in FEATURE_STATUS.items()
        if entry.status == "Active" and not entry.used_in_production
    ]
    if inactive_active:
        errors.append(f"Active entries with used_in_production=false: {', '.join(inactive_active)}")

    app_source = Path("app.py").read_text()
    forbidden_metric_literals = ["1.0453", "0.6273", "0.4822"]
    hardcoded = [value for value in forbidden_metric_literals if value in app_source]
    if hardcoded:
        errors.append(f"app.py appears to hardcode validation metrics: {', '.join(hardcoded)}")

    if errors:
        raise SystemExit("\n".join(errors))

    print("Feature status checks passed.")


if __name__ == "__main__":
    main()
