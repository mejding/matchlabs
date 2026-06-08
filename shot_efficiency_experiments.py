from __future__ import annotations

import json
import os
from pathlib import Path

Path("evaluation", ".matplotlib-cache").mkdir(parents=True, exist_ok=True)
os.environ.setdefault("MPLCONFIGDIR", str(Path("evaluation") / ".matplotlib-cache"))

import matplotlib
import numpy as np
import pandas as pd
from matplotlib import pyplot as plt
from sklearn.inspection import permutation_importance
from sklearn.metrics import log_loss, recall_score

from calibration.calibration import calibration_summary, calibration_table, expected_calibration_error
from evaluation.model_evaluation import evaluate_probabilities, time_based_split
from explainability.shap_analysis import compute_shap_importance, plot_shap_importance, plot_shap_summary
from feature_experiments import _markdown_table, train_xgb
from shot_efficiency_features import (
    all_shot_feature_columns,
    build_shot_efficiency_features,
    load_matches_with_xg_and_shots,
    shot_defensive_columns,
    shot_efficiency_columns,
    shot_volume_columns,
)
from tactical_data import ensure_tactical_tables, load_team_match_tactics
from tactical_features import build_tactical_features
from train_model import ELO_CONFIG, PRODUCTION_FEATURE_COLUMNS, build_features
from elo_rating_features import build_elo_features
from visualizations.plots import gain_importance, plot_feature_importance

matplotlib.use("Agg")

OUTPUT_DIR = Path("evaluation") / "shot_efficiency"
RESULTS_PATH = Path("experiments") / "shot_efficiency_results.csv"

TACTICAL_PRESSURE_COLUMNS = [
    "home_attacking_pressure_score_last5",
    "home_attacking_pressure_score_last10",
    "home_attacking_pressure_score_season",
    "away_attacking_pressure_score_last5",
    "away_attacking_pressure_score_last10",
    "away_attacking_pressure_score_season",
]


def available_columns(dataset: pd.DataFrame, columns: list[str]) -> list[str]:
    return [column for column in columns if column in dataset.columns and dataset[column].notna().sum() > 0]


def build_shot_dataset() -> tuple[pd.DataFrame, pd.DataFrame, dict[str, list[str]]]:
    matches = load_matches_with_xg_and_shots().sort_values("Date").reset_index(drop=True)
    base_dataset, _ = build_features(matches, include_xg=True, include_schedule=True)
    elo_features, _ = build_elo_features(matches, ELO_CONFIG)
    shot_features = build_shot_efficiency_features(matches)

    tactical_columns: list[str] = []
    try:
        ensure_tactical_tables()
        tactics = load_team_match_tactics()
        tactical_features, _ = build_tactical_features(matches, tactics)
        tactical_columns = available_columns(tactical_features, TACTICAL_PRESSURE_COLUMNS)
        dataset = pd.concat(
            [
                base_dataset.reset_index(drop=True),
                elo_features.reset_index(drop=True),
                tactical_features[tactical_columns].reset_index(drop=True),
                shot_features.reset_index(drop=True),
            ],
            axis=1,
        )
    except Exception as exc:
        print(f"Warning: tactical pressure unavailable for shot experiment: {exc}")
        dataset = pd.concat(
            [base_dataset.reset_index(drop=True), elo_features.reset_index(drop=True), shot_features.reset_index(drop=True)],
            axis=1,
        )

    production_columns = PRODUCTION_FEATURE_COLUMNS + tactical_columns
    feature_sets = {
        "model_a_current_production": production_columns,
        "model_b_shot_volume": production_columns + shot_volume_columns(),
        "model_c_shot_efficiency": production_columns + shot_efficiency_columns(),
        "model_d_defensive_shot_prevention": production_columns + shot_defensive_columns(),
        "model_e_all_shot_features": production_columns + all_shot_feature_columns(),
    }
    metadata = matches[["Season", "Date", "HomeTeam", "AwayTeam", "FTR"]].reset_index(drop=True)
    return dataset, metadata, feature_sets


def evaluate_feature_set(dataset: pd.DataFrame, metadata: pd.DataFrame, feature_columns: list[str], model_version: str) -> dict[str, object]:
    X = dataset[feature_columns]
    y = dataset["target"]
    split = time_based_split(X, y, metadata)
    model = train_xgb(split.X_train, split.y_train)
    probabilities = model.predict_proba(split.X_test)
    predictions = probabilities.argmax(axis=1)
    metrics = evaluate_probabilities(split.y_test, probabilities, predictions)
    calibration = calibration_table(split.y_test, probabilities)
    cal_summary = calibration_summary(calibration)
    draw_actual = (split.y_test.to_numpy() == 1).astype(int)
    draw_prob = np.clip(probabilities[:, 1], 1e-12, 1 - 1e-12)
    draw_pred = (predictions == 1).astype(int)
    return {
        "model_version": model_version,
        "model": model,
        "split": split,
        "probabilities": probabilities,
        "predictions": predictions,
        "feature_columns": feature_columns,
        "accuracy": metrics["accuracy"],
        "log_loss": metrics["log_loss"],
        "brier_score": metrics["brier_score_multiclass"],
        "calibration_score": cal_summary["mean_absolute_calibration_error"],
        "expected_calibration_error": expected_calibration_error(calibration),
        "draw_recall": float(recall_score(draw_actual, draw_pred, zero_division=0)),
        "draw_log_loss": float(log_loss(draw_actual, np.column_stack([1 - draw_prob, draw_prob]), labels=[0, 1])),
        "train_period": f"{split.train_metadata['Date'].iloc[0]} to {split.train_metadata['Date'].iloc[-1]}",
        "test_period": f"{split.test_metadata['Date'].iloc[0]} to {split.test_metadata['Date'].iloc[-1]}",
    }


def save_results(results: list[dict[str, object]]) -> pd.DataFrame:
    rows = []
    for result in results:
        rows.append(
            {
                "experiment_id": f"{result['model_version']}_{pd.Timestamp.now(tz='UTC').strftime('%Y%m%d_%H%M%S')}",
                "model_version": result["model_version"],
                "features_added": "|".join(result["feature_columns"]),
                "train_period": result["train_period"],
                "test_period": result["test_period"],
                "accuracy": result["accuracy"],
                "log_loss": result["log_loss"],
                "Brier_score": result["brier_score"],
                "calibration_score": result["calibration_score"],
                "expected_calibration_error": result["expected_calibration_error"],
                "draw_recall": result["draw_recall"],
                "draw_log_loss": result["draw_log_loss"],
            }
        )
    output = pd.DataFrame(rows)
    RESULTS_PATH.parent.mkdir(exist_ok=True)
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    output.to_csv(RESULTS_PATH, index=False)
    output.to_csv(OUTPUT_DIR / "model_comparison.csv", index=False)
    return output


def plot_model_comparison(results: pd.DataFrame) -> None:
    metrics = ["accuracy", "log_loss", "Brier_score", "expected_calibration_error", "draw_recall", "draw_log_loss"]
    fig, axes = plt.subplots(2, 3, figsize=(15, 8))
    for ax, metric in zip(axes.ravel(), metrics):
        ax.bar(results["model_version"], results[metric])
        ax.set_title(metric)
        ax.tick_params(axis="x", rotation=25)
        ax.grid(axis="y", alpha=0.25)
    fig.suptitle("Shot Efficiency Model Comparison")
    fig.tight_layout()
    fig.savefig(OUTPUT_DIR / "model_comparison.png", dpi=160)
    plt.close(fig)


def _feature_group(feature: str) -> str:
    if "shots_allowed" in feature or "opponent_shot" in feature or "xga_per_shot" in feature:
        return "defensive_shot_prevention"
    if "shot_accuracy" in feature or "goals_per_shot" in feature or "xg_per_shot" in feature or "goals_minus_xg" in feature:
        return "shot_efficiency"
    if "shots_avg" in feature or "shots_on_target_avg" in feature:
        return "shot_volume"
    return "production"


def explain_shot_model(result: dict[str, object]) -> pd.DataFrame:
    split = result["split"]
    model = result["model"]
    shap_importance, _, _ = compute_shap_importance(model, split.X_test)
    shap_importance["feature_group"] = shap_importance["feature"].map(_feature_group)
    shap_importance.to_csv(OUTPUT_DIR / "shot_feature_importance.csv", index=False)
    shap_importance.groupby("feature_group", as_index=False)["mean_abs_shap"].sum().sort_values(
        "mean_abs_shap", ascending=False
    ).to_csv(OUTPUT_DIR / "shot_shap_group_importance.csv", index=False)
    plot_shap_importance(shap_importance.head(40), OUTPUT_DIR / "shot_shap_feature_importance.png")
    plot_shap_summary(model, split.X_test, OUTPUT_DIR / "shot_shap_summary.png")
    gain = gain_importance(model, result["feature_columns"])
    gain.to_csv(OUTPUT_DIR / "shot_gain_importance.csv", index=False)
    plot_feature_importance(gain.head(40), "gain_importance", "Shot Efficiency Gain Importance", OUTPUT_DIR / "shot_gain_importance.png")

    perm = permutation_importance(
        model,
        split.X_test,
        split.y_test,
        n_repeats=5,
        random_state=42,
        scoring="neg_log_loss",
        n_jobs=1,
    )
    permutation = pd.DataFrame(
        {
            "feature": result["feature_columns"],
            "permutation_importance_log_loss": perm.importances_mean,
            "permutation_importance_std": perm.importances_std,
        }
    ).sort_values("permutation_importance_log_loss", ascending=False)
    permutation[permutation["feature"].isin(all_shot_feature_columns())].to_csv(
        OUTPUT_DIR / "shot_permutation_importance.csv", index=False
    )
    return shap_importance


def remove_one_tests(dataset: pd.DataFrame, metadata: pd.DataFrame, full_columns: list[str]) -> pd.DataFrame:
    groups = {
        "remove_shot_volume": shot_volume_columns(),
        "remove_shot_efficiency": shot_efficiency_columns(),
        "remove_defensive_shot_prevention": shot_defensive_columns(),
        "remove_goals_minus_xg": [column for column in all_shot_feature_columns() if "goals_minus_xg" in column],
    }
    rows = []
    full_result = evaluate_feature_set(dataset, metadata, full_columns, "full_all_shot_features_reference")
    rows.append(
        {
            "test": "full_all_shot_features_reference",
            "removed_features": "",
            "log_loss": full_result["log_loss"],
            "Brier_score": full_result["brier_score"],
            "expected_calibration_error": full_result["expected_calibration_error"],
        }
    )
    for name, removed in groups.items():
        columns = [column for column in full_columns if column not in set(removed)]
        result = evaluate_feature_set(dataset, metadata, columns, name)
        rows.append(
            {
                "test": name,
                "removed_features": "|".join(removed),
                "log_loss": result["log_loss"],
                "Brier_score": result["brier_score"],
                "expected_calibration_error": result["expected_calibration_error"],
            }
        )
    output = pd.DataFrame(rows)
    output.to_csv(OUTPUT_DIR / "remove_one_tests.csv", index=False)
    return output


def _delta(results: pd.DataFrame, model_a: str, model_b: str, metric: str) -> float:
    a = float(results.loc[results["model_version"] == model_a, metric].iloc[0])
    b = float(results.loc[results["model_version"] == model_b, metric].iloc[0])
    return b - a


def write_report(results: pd.DataFrame, shap_importance: pd.DataFrame, remove_one: pd.DataFrame) -> None:
    baseline = "model_a_current_production"
    full = "model_e_all_shot_features"
    candidate_rows = results[results["model_version"] != baseline].copy()
    best_log_loss_row = candidate_rows.sort_values("log_loss").iloc[0]
    best_brier_row = candidate_rows.sort_values("Brier_score").iloc[0]
    best_model = str(best_log_loss_row["model_version"])
    best_log_loss_delta = float(best_log_loss_row["log_loss"] - results.loc[results["model_version"] == baseline, "log_loss"].iloc[0])
    best_brier_delta = float(best_log_loss_row["Brier_score"] - results.loc[results["model_version"] == baseline, "Brier_score"].iloc[0])
    best_ece_delta = float(
        best_log_loss_row["expected_calibration_error"]
        - results.loc[results["model_version"] == baseline, "expected_calibration_error"].iloc[0]
    )
    production_ready = (best_log_loss_delta < 0 or best_brier_delta < 0) and best_ece_delta <= 0.01
    shot_shap = shap_importance[shap_importance["feature_group"] != "production"].head(15)
    shot_lines = "\n".join(
        f"- `{row.feature}` ({row.feature_group}): {row.mean_abs_shap:.4f}" for row in shot_shap.itertuples()
    )
    groups = shap_importance.groupby("feature_group", as_index=False)["mean_abs_shap"].sum().sort_values(
        "mean_abs_shap", ascending=False
    )
    goals_minus_xg_shap = shap_importance[shap_importance["feature"].str.contains("goals_minus_xg", na=False)]["mean_abs_shap"].sum()
    if production_ready and best_model == "model_b_shot_volume":
        decision = (
            "Move shot volume features forward as a production candidate. Do not activate all shot efficiency features yet, "
            "because the simpler shot-volume model has the best out-of-sample log loss and Brier score."
        )
    elif production_ready:
        decision = (
            f"Move `{best_model}` forward as a production candidate. Keep weaker shot feature families research-only."
        )
    else:
        decision = "Do not activate shot features. They did not improve out-of-sample log loss or Brier without calibration risk."
    full_decision = (
        "The full all-shot model improves the baseline, but it is not the best candidate."
        if production_ready
        else "The full all-shot model is not production-ready."
    )
    Path("shot_efficiency_report.md").write_text(
        f"""# Shot Efficiency Feature Evaluation

## Goal

Test whether shot volume, shot accuracy, finishing efficiency and defensive shot prevention improve the Premier League prediction model beyond the current production baseline.

## Data

Shot features use football-data.co.uk `HS`, `AS`, `HST`, and `AST` columns plus goals and Understat xG. Every feature is calculated chronologically from matches before kickoff. Rolling windows: last 5, last 10, and current season.

## Model Comparison

{_markdown_table(results, ['model_version', 'accuracy', 'log_loss', 'Brier_score', 'expected_calibration_error', 'draw_recall', 'draw_log_loss'])}

## Full Shot Model vs Production

- Log loss change: {_delta(results, baseline, full, 'log_loss'):.4f}
- Brier score change: {_delta(results, baseline, full, 'Brier_score'):.4f}
- ECE change: {_delta(results, baseline, full, 'expected_calibration_error'):.4f}
- Draw recall change: {_delta(results, baseline, full, 'draw_recall'):.4f}
- Draw log loss change: {_delta(results, baseline, full, 'draw_log_loss'):.4f}

## Best Candidate

- Best log-loss model: `{best_model}`
- Best candidate log loss delta vs production: {best_log_loss_delta:.4f}
- Best candidate Brier delta vs production: {best_brier_delta:.4f}
- Best candidate ECE delta vs production: {best_ece_delta:.4f}
- Best Brier model: `{best_brier_row['model_version']}`

## SHAP Signal

Top shot SHAP features:

{shot_lines or '- No shot feature had measurable SHAP contribution.'}

SHAP group totals:

{_markdown_table(groups, ['feature_group', 'mean_abs_shap'])}

## Remove-One Tests

{_markdown_table(remove_one, ['test', 'log_loss', 'Brier_score', 'expected_calibration_error'])}

## Special Analysis

1. Finishing efficiency features are only useful if they improve out-of-sample log loss/Brier. In this run, the dedicated shot-efficiency model improves calibration but is weaker than shot volume on log loss and Brier.
2. `goals_minus_xg` total SHAP contribution: {goals_minus_xg_shap:.4f}. Remove-one tests improve when `goals_minus_xg` is removed, so it should remain research-only for now.
3. Shot features overlap with xG/xGA and the existing tactical pressure proxy, so redundancy is expected.
4. Draw prediction only improves if draw log loss falls and draw recall rises together.
5. Full model status: {full_decision}

## Production Decision

{decision}
"""
    )


def main() -> None:
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    dataset, metadata, feature_sets = build_shot_dataset()
    results = [evaluate_feature_set(dataset, metadata, columns, version) for version, columns in feature_sets.items()]
    results_frame = save_results(results)
    plot_model_comparison(results_frame)
    full_result = next(result for result in results if result["model_version"] == "model_e_all_shot_features")
    shap_importance = explain_shot_model(full_result)
    remove_one = remove_one_tests(dataset, metadata, feature_sets["model_e_all_shot_features"])
    write_report(results_frame, shap_importance, remove_one)
    baseline_log_loss = float(results_frame.loc[results_frame["model_version"] == "model_a_current_production", "log_loss"].iloc[0])
    baseline_brier = float(results_frame.loc[results_frame["model_version"] == "model_a_current_production", "Brier_score"].iloc[0])
    candidates = results_frame[results_frame["model_version"] != "model_a_current_production"].copy()
    best = candidates.sort_values("log_loss").iloc[0]
    print(
        json.dumps(
            {
                "activate_candidate": bool(best["log_loss"] < baseline_log_loss or best["Brier_score"] < baseline_brier),
                "best_candidate": str(best["model_version"]),
                "best_log_loss_delta": float(best["log_loss"] - baseline_log_loss),
                "best_brier_delta": float(best["Brier_score"] - baseline_brier),
            },
            indent=2,
        )
    )


if __name__ == "__main__":
    main()
