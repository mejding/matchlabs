from __future__ import annotations

from pathlib import Path

import joblib
import numpy as np
import pandas as pd

from evaluate_model import load_current_dataset
from evaluation.model_evaluation import LABEL_TO_RESULT, time_based_split
from train_model import MODEL_PATH


EVALUATION_DIR = Path("evaluation")
TOP_SIX = {"Arsenal", "Chelsea", "Liverpool", "Man City", "Man United", "Tottenham"}
PROMOTED_RECENT = {"Leeds", "Leicester", "Ipswich", "Southampton", "Burnley", "Luton", "Nott'm Forest"}


def build_prediction_table() -> pd.DataFrame:
    artifact = joblib.load(MODEL_PATH)
    model = artifact["model"]
    feature_columns = artifact["feature_columns"]
    dataset, metadata = load_current_dataset(feature_columns)
    split = time_based_split(dataset[feature_columns], dataset["target"], metadata)
    probabilities = model.predict_proba(split.X_test)
    predictions = probabilities.argmax(axis=1)

    rows = split.test_metadata.reset_index(drop=True).copy()
    features = split.X_test.reset_index(drop=True)
    rows["actual"] = split.y_test.reset_index(drop=True).map(LABEL_TO_RESULT)
    rows["predicted"] = pd.Series(predictions).map(LABEL_TO_RESULT)
    rows["predicted_confidence"] = probabilities.max(axis=1)
    rows["home_win_probability"] = probabilities[:, 0]
    rows["draw_probability"] = probabilities[:, 1]
    rows["away_win_probability"] = probabilities[:, 2]
    rows["individual_log_loss"] = -np.log(np.clip(probabilities[np.arange(len(rows)), split.y_test.to_numpy()], 1e-15, 1.0))
    for column in [
        "home_days_rest",
        "away_days_rest",
        "home_team_points_last_5",
        "away_team_points_last_5",
        "home_xg_diff",
        "away_xg_diff",
    ]:
        if column in features:
            rows[column] = features[column]
    rows["home_favorite"] = rows["home_win_probability"] >= rows[["draw_probability", "away_win_probability"]].max(axis=1)
    rows["top_six_home_favorite"] = rows["HomeTeam"].isin(TOP_SIX) & rows["home_favorite"]
    rows["promoted_team_involved"] = rows["HomeTeam"].isin(PROMOTED_RECENT) | rows["AwayTeam"].isin(PROMOTED_RECENT)
    rows["suspicious_rest_gap"] = (rows.get("home_days_rest", 0) > 30) | (rows.get("away_days_rest", 0) > 30)
    rows["wrong"] = rows["actual"] != rows["predicted"]
    return rows


def write_report(predictions: pd.DataFrame) -> None:
    high_conf_wrong = predictions[(predictions["predicted_confidence"] > 0.70) & predictions["wrong"]]
    home_favorite_failures = predictions[predictions["home_favorite"] & (predictions["actual"] != "home_win")]
    draws_as_home = predictions[(predictions["actual"] == "draw") & (predictions["predicted"] == "home_win")]
    worst_teams = (
        pd.concat(
            [
                high_conf_wrong[["HomeTeam"]].rename(columns={"HomeTeam": "team"}),
                high_conf_wrong[["AwayTeam"]].rename(columns={"AwayTeam": "team"}),
            ]
        )["team"]
        .value_counts()
        .head(10)
    )

    lines = [
        "# Worst Prediction Analysis",
        "",
        "The analysis uses the saved model on the held-out chronological test period only.",
        "",
        "## Main Failure Patterns",
        "",
        f"- Confident wrong predictions above 70%: {len(high_conf_wrong)}",
        f"- Home favorites that lost or drew: {len(home_favorite_failures)}",
        f"- Draws predicted as home wins: {len(draws_as_home)}",
        f"- Matches involving recent promoted/relegation-context teams: {int(predictions['promoted_team_involved'].sum())}",
        f"- Matches with suspicious rest gaps above 30 days: {int(predictions['suspicious_rest_gap'].sum())}",
        "",
        "## Interpretation",
        "",
        "The model remains most vulnerable when a home favorite has strong historical/xG indicators but the match outcome is a draw. This is consistent with draws being the least separable class.",
        "Large rest gaps are treated as data-quality warnings because they often mean the selected prediction date is beyond the latest saved fixture history for one team.",
        "",
        "## Teams Repeatedly Involved In Confident Wrong Predictions",
        "",
    ]
    if worst_teams.empty:
        lines.append("- No teams crossed the high-confidence-wrong threshold.")
    else:
        lines.extend(f"- {team}: {count}" for team, count in worst_teams.items())
    lines.extend(
        [
            "",
            "## Production Recommendation",
            "",
            "Do not hide these failures in the frontend. Surface low confidence and data-quality warnings when favorite probabilities are high but rest gaps, missing injuries, or missing lineup data are present.",
        ]
    )
    (EVALUATION_DIR / "worst_prediction_analysis.md").write_text("\n".join(lines) + "\n")


def main() -> None:
    EVALUATION_DIR.mkdir(exist_ok=True)
    predictions = build_prediction_table()
    favorite_failures = predictions[predictions["home_favorite"] & (predictions["actual"] != "home_win")]
    draws_as_home = predictions[(predictions["actual"] == "draw") & (predictions["predicted"] == "home_win")]
    favorite_failures.to_csv(EVALUATION_DIR / "favorite_overconfidence.csv", index=False)
    draws_as_home.to_csv(EVALUATION_DIR / "draw_misclassification.csv", index=False)
    write_report(predictions)
    print(f"Wrote {len(favorite_failures)} favorite failures and {len(draws_as_home)} draw misclassifications.")


if __name__ == "__main__":
    main()
