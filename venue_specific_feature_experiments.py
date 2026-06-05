from __future__ import annotations

import json
import os
from pathlib import Path

Path("evaluation", ".matplotlib-cache").mkdir(parents=True, exist_ok=True)
os.environ.setdefault("MPLCONFIGDIR", str(Path("evaluation") / ".matplotlib-cache"))

import matplotlib
import pandas as pd
from matplotlib import pyplot as plt

from calibration.calibration import calibration_summary, calibration_table, expected_calibration_error
from evaluation.model_evaluation import evaluate_probabilities, time_based_split
from explainability.shap_analysis import compute_shap_importance, plot_shap_importance, plot_shap_summary
from feature_experiments import _markdown_table, train_xgb
from train_model import SCHEDULE_FEATURE_COLUMNS, build_features, load_matches_with_xg
from visualizations.plots import gain_importance, plot_feature_importance

matplotlib.use("Agg")

OUTPUT_DIR = Path("evaluation") / "venue_specific_features"
VENUE_FEATURE_COLUMNS = [
    "home_points_last_5_home_matches",
    "away_points_last_5_away_matches",
    "home_xg_last_5_home_matches",
    "away_xg_last_5_away_matches",
    "home_xga_last_5_home_matches",
    "away_xga_last_5_away_matches",
    "home_goal_diff_home_matches",
    "away_goal_diff_away_matches",
]


def average(values: list[float]) -> float:
    return sum(values) / len(values) if values else 0.0


def points_from_result(row: pd.Series, team_is_home: bool) -> int:
    if row["FTR"] == "D":
        return 1
    if team_is_home:
        return 3 if row["FTR"] == "H" else 0
    return 3 if row["FTR"] == "A" else 0


def build_venue_specific_features(matches: pd.DataFrame) -> pd.DataFrame:
    history: dict[str, dict[str, list[dict[str, float]]]] = {}
    rows = []

    for _, match in matches.iterrows():
        home_team = match["HomeTeam"]
        away_team = match["AwayTeam"]
        for team in (home_team, away_team):
            history.setdefault(team, {"home": [], "away": []})

        home_home_matches = history[home_team]["home"][-5:]
        away_away_matches = history[away_team]["away"][-5:]

        home_goal_diff_values = [item["goals_for"] - item["goals_against"] for item in home_home_matches]
        away_goal_diff_values = [item["goals_for"] - item["goals_against"] for item in away_away_matches]

        rows.append(
            {
                "home_points_last_5_home_matches": sum(item["points"] for item in home_home_matches),
                "away_points_last_5_away_matches": sum(item["points"] for item in away_away_matches),
                "home_xg_last_5_home_matches": average([item["xg"] for item in home_home_matches]),
                "away_xg_last_5_away_matches": average([item["xg"] for item in away_away_matches]),
                "home_xga_last_5_home_matches": average([item["xga"] for item in home_home_matches]),
                "away_xga_last_5_away_matches": average([item["xga"] for item in away_away_matches]),
                "home_goal_diff_home_matches": average(home_goal_diff_values),
                "away_goal_diff_away_matches": average(away_goal_diff_values),
            }
        )

        history[home_team]["home"].append(
            {
                "points": points_from_result(match, team_is_home=True),
                "goals_for": float(match["FTHG"]),
                "goals_against": float(match["FTAG"]),
                "xg": float(match["home_xg"]),
                "xga": float(match["away_xg"]),
            }
        )
        history[away_team]["away"].append(
            {
                "points": points_from_result(match, team_is_home=False),
                "goals_for": float(match["FTAG"]),
                "goals_against": float(match["FTHG"]),
                "xg": float(match["away_xg"]),
                "xga": float(match["home_xg"]),
            }
        )

    return pd.DataFrame(rows)


def evaluate_feature_set(dataset: pd.DataFrame, metadata: pd.DataFrame, feature_columns: list[str], model_name: str) -> dict[str, object]:
    split = time_based_split(dataset[feature_columns], dataset["target"], metadata)
    model = train_xgb(split.X_train, split.y_train)
    probabilities = model.predict_proba(split.X_test)
    predictions = model.predict(split.X_test)
    metrics = evaluate_probabilities(split.y_test, probabilities, predictions)
    calibration = calibration_table(split.y_test, probabilities)
    cal_summary = calibration_summary(calibration)
    return {
        "model_name": model_name,
        "model": model,
        "split": split,
        "feature_columns": feature_columns,
        "probabilities": probabilities,
        "accuracy": metrics["accuracy"],
        "log_loss": metrics["log_loss"],
        "brier_score": metrics["brier_score_multiclass"],
        "calibration_score": cal_summary["mean_absolute_calibration_error"],
        "ece": expected_calibration_error(calibration),
        "train_period": f"{split.train_metadata['Date'].iloc[0]} to {split.train_metadata['Date'].iloc[-1]}",
        "test_period": f"{split.test_metadata['Date'].iloc[0]} to {split.test_metadata['Date'].iloc[-1]}",
    }


def plot_model_comparison(results: pd.DataFrame, output_path: Path) -> None:
    metrics = ["accuracy", "log_loss", "brier_score", "calibration_score", "ece"]
    fig, axes = plt.subplots(1, len(metrics), figsize=(16, 4))
    for ax, metric in zip(axes, metrics):
        ax.bar(results["model_name"], results[metric])
        ax.set_title(metric)
        ax.tick_params(axis="x", rotation=20)
        ax.grid(axis="y", alpha=0.25)
    fig.suptitle("Venue-Specific Feature Experiment")
    fig.tight_layout()
    fig.savefig(output_path, dpi=160)
    plt.close(fig)


def shap_outputs(result: dict[str, object]) -> pd.DataFrame:
    model = result["model"]
    split = result["split"]
    shap_importance, _, _ = compute_shap_importance(model, split.X_test)
    shap_importance["feature_group"] = shap_importance["feature"].map(
        lambda feature: "venue_specific" if feature in VENUE_FEATURE_COLUMNS else "current_model"
    )
    shap_importance.to_csv(OUTPUT_DIR / "shap_feature_rankings.csv", index=False)
    shap_importance.groupby("feature_group", as_index=False)["mean_abs_shap"].sum().sort_values(
        "mean_abs_shap", ascending=False
    ).to_csv(OUTPUT_DIR / "shap_group_rankings.csv", index=False)
    plot_shap_importance(shap_importance.head(30), OUTPUT_DIR / "shap_feature_rankings.png")
    plot_shap_summary(model, split.X_test, OUTPUT_DIR / "shap_summary.png")
    gain = gain_importance(model, result["feature_columns"])
    gain.to_csv(OUTPUT_DIR / "gain_importance.csv", index=False)
    plot_feature_importance(gain.head(30), "gain_importance", "Venue-Specific Gain Importance", OUTPUT_DIR / "gain_importance.png")
    return shap_importance


def write_audit_report() -> None:
    Path("feature_engineering_audit.md").write_text(
        """# Feature Engineering Audit

This audit inspects the production feature engineering in `train_model.py`.

## Summary

The inspected form and xG features use all recent matches combined. They are not venue-specific. For a home team, the latest 5 matches can include both home and away matches. For an away team, the latest 5 matches can also include both home and away matches.

## Feature Details

| Feature | Exact calculation | Data window | Venue-specific? | Potential information loss |
| --- | --- | --- | --- | --- |
| `home_team_points_last_5` | Sum of `team_history[home_team]["points"][-5:]` before the fixture. Points are 3/1/0 from each previous match regardless of venue. | Latest 5 matches played by the home team before the fixture. | No. Uses all recent home-team matches combined. | Home form at the stadium is blended with away form. |
| `away_team_points_last_5` | Sum of `team_history[away_team]["points"][-5:]` before the fixture. | Latest 5 matches played by the away team before the fixture. | No. Uses all recent away-team matches combined. | Away-specific travel/performance signal is blended with home form. |
| `home_goals_scored_avg` | Average of `team_history[home_team]["goals_scored"][-5:]`. | Latest 5 matches played by the home team before the fixture. | No. | Home scoring strength may be diluted by away scoring context. |
| `away_goals_scored_avg` | Average of `team_history[away_team]["goals_scored"][-5:]`. | Latest 5 matches played by the away team before the fixture. | No. | Away scoring strength may be overstated if recent goals came mostly at home. |
| `home_xg_avg` | Average of `team_history[home_team]["xg"][-5:]`. | Latest 5 matches played by the home team before the fixture. | No. | Home chance creation is blended with away chance creation. |
| `away_xg_avg` | Average of `team_history[away_team]["xg"][-5:]`. | Latest 5 matches played by the away team before the fixture. | No. | Away attacking quality can be misrepresented if recent xG came at home. |
| `home_xga_avg` | Average of `team_history[home_team]["xga"][-5:]`. | Latest 5 matches played by the home team before the fixture. | No. | Home defensive strength can be blended with away defensive difficulty. |
| `away_xga_avg` | Average of `team_history[away_team]["xga"][-5:]`. | Latest 5 matches played by the away team before the fixture. | No. | Away defensive weakness/strength can be hidden by home matches. |
| `home_xg_diff` | `home_xg_avg - home_xga_avg`. | Same latest 5 all-venue matches. | No. | Venue-specific xG balance is not captured. |
| `away_xg_diff` | `away_xg_avg - away_xga_avg`. | Same latest 5 all-venue matches. | No. | Away-specific xG balance is not captured. |

## Leakage Assessment

The current features are historically safe: each feature is calculated before the current fixture, then the match result is appended to history afterward. The issue is not leakage; it is information loss from mixing home and away contexts.

## Experimental Venue-Specific Features

Because production venue-specific versions did not exist, this sprint adds research features in `venue_specific_feature_experiments.py`:

- `home_points_last_5_home_matches`
- `away_points_last_5_away_matches`
- `home_xg_last_5_home_matches`
- `away_xg_last_5_away_matches`
- `home_xga_last_5_home_matches`
- `away_xga_last_5_away_matches`
- `home_goal_diff_home_matches`
- `away_goal_diff_away_matches`
"""
    )


def write_experiment_report(results: pd.DataFrame, shap_importance: pd.DataFrame) -> None:
    baseline = results[results["model_name"] == "current_model"].iloc[0]
    venue = results[results["model_name"] == "current_model_plus_venue_specific"].iloc[0]
    venue_shap = shap_importance[shap_importance["feature_group"] == "venue_specific"].copy()
    top_venue = venue_shap.head(10)
    away_features = venue_shap[venue_shap["feature"].str.startswith("away_")]
    home_features = venue_shap[venue_shap["feature"].str.startswith("home_")]
    improves = float(venue["log_loss"]) < float(baseline["log_loss"]) and float(venue["brier_score"]) < float(baseline["brier_score"])
    away_more_important = float(away_features["mean_abs_shap"].sum()) > float(home_features["mean_abs_shap"].sum())

    Path("venue_specific_features_report.md").write_text(
        f"""# Venue-Specific Features Report

## Model Comparison

{_markdown_table(results, ['model_name', 'accuracy', 'log_loss', 'brier_score', 'calibration_score', 'ece', 'train_period', 'test_period'])}

Metric deltas, venue model minus current model:

- Accuracy: {float(venue['accuracy'] - baseline['accuracy']):.4f}
- Log loss: {float(venue['log_loss'] - baseline['log_loss']):.4f}
- Brier score: {float(venue['brier_score'] - baseline['brier_score']):.4f}
- Calibration score: {float(venue['calibration_score'] - baseline['calibration_score']):.4f}
- ECE: {float(venue['ece'] - baseline['ece']):.4f}

Lower is better for log loss, Brier score, calibration score and ECE.

## SHAP

Top venue-specific features:

{_markdown_table(top_venue[['feature', 'mean_abs_shap']], ['feature', 'mean_abs_shap']) if not top_venue.empty else 'No venue-specific features had non-zero SHAP importance.'}

Venue feature group total SHAP: {float(venue_shap['mean_abs_shap'].sum()):.4f}  
Home venue feature SHAP total: {float(home_features['mean_abs_shap'].sum()):.4f}  
Away venue feature SHAP total: {float(away_features['mean_abs_shap'].sum()):.4f}

## 1. Do venue-specific features improve prediction quality?

Answer: {'Yes. The venue-specific feature set improves both out-of-sample log loss and Brier score.' if improves else 'No. The venue-specific feature set does not improve both out-of-sample log loss and Brier score in this run.'}

## 2. Which venue-specific features matter most?

Answer: The highest-ranked venue-specific SHAP features are listed above. These are the only venue-specific signals with measurable contribution in this experiment.

## 3. Are away-performance features particularly important?

Answer: {'Yes. Away venue features have higher total SHAP contribution than home venue features in this run.' if away_more_important else 'No. Away venue features do not dominate home venue features in total SHAP contribution in this run.'}

## 4. Should venue-specific features move into production?

Answer: {'Yes, they are a production candidate because they improved the main probability metrics. Before activation, rerun after the next data refresh and check calibration by class.' if improves else 'No. Keep them research-only until they improve out-of-sample log loss and Brier score robustly.'}

## Artifacts

- `evaluation/venue_specific_features/model_comparison.csv`
- `evaluation/venue_specific_features/model_comparison.png`
- `evaluation/venue_specific_features/shap_feature_rankings.csv`
- `evaluation/venue_specific_features/shap_group_rankings.csv`
- `evaluation/venue_specific_features/shap_feature_rankings.png`
- `evaluation/venue_specific_features/shap_summary.png`
- `evaluation/venue_specific_features/gain_importance.csv`
- `evaluation/venue_specific_features/gain_importance.png`
"""
    )


def run_experiment() -> pd.DataFrame:
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    write_audit_report()
    matches = load_matches_with_xg().sort_values("Date").reset_index(drop=True)
    base_dataset, _ = build_features(matches, include_xg=True, include_schedule=True)
    venue_features = build_venue_specific_features(matches)
    dataset = pd.concat([base_dataset.reset_index(drop=True), venue_features.reset_index(drop=True)], axis=1)
    metadata = matches[["Season", "Date", "HomeTeam", "AwayTeam", "FTR"]].reset_index(drop=True)

    current = evaluate_feature_set(dataset, metadata, SCHEDULE_FEATURE_COLUMNS, "current_model")
    venue = evaluate_feature_set(
        dataset,
        metadata,
        SCHEDULE_FEATURE_COLUMNS + VENUE_FEATURE_COLUMNS,
        "current_model_plus_venue_specific",
    )
    results = pd.DataFrame(
        [
            {key: value for key, value in current.items() if key not in {"model", "split", "feature_columns", "probabilities"}},
            {key: value for key, value in venue.items() if key not in {"model", "split", "feature_columns", "probabilities"}},
        ]
    )
    results.to_csv(OUTPUT_DIR / "model_comparison.csv", index=False)
    plot_model_comparison(results, OUTPUT_DIR / "model_comparison.png")
    shap_importance = shap_outputs(venue)
    write_experiment_report(results, shap_importance)
    return results


def main() -> None:
    results = run_experiment()
    best = results.sort_values("log_loss").iloc[0]
    print(json.dumps({"best_model": str(best["model_name"]), "log_loss": float(best["log_loss"])}, indent=2))


if __name__ == "__main__":
    main()
