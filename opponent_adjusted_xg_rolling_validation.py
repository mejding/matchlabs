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

from calibration.calibration import calibration_summary, calibration_table, expected_calibration_error
from evaluation.model_evaluation import multiclass_brier_score
from feature_experiments import _markdown_table, train_xgb
from opponent_adjusted_xg_replacement_experiments import (
    NON_XG_PRODUCTION_COLUMNS,
    XG_DIFF_COLUMNS,
    build_replacement_dataset,
)
from opponent_adjusted_xg_features import RATING_FEATURE_COLUMNS
from train_model import PRODUCTION_FEATURE_COLUMNS

matplotlib.use("Agg")

OUTPUT_DIR = Path("evaluation") / "opponent_adjusted_xg"
TEST_SEASONS = ["2122", "2223", "2324", "2425", "2526"]
SEASON_LABELS = {
    "2122": "2021/22",
    "2223": "2022/23",
    "2324": "2023/24",
    "2425": "2024/25",
    "2526": "2025/26",
}


def normalize_probabilities(probabilities: np.ndarray) -> np.ndarray:
    probabilities = np.clip(probabilities, 1e-15, 1.0)
    return probabilities / probabilities.sum(axis=1, keepdims=True)


def evaluate_probs(y_true: pd.Series, probabilities: np.ndarray) -> dict[str, float]:
    probabilities = normalize_probabilities(probabilities)
    predictions = probabilities.argmax(axis=1)
    calibration = calibration_table(y_true, probabilities)
    draw_actual = (y_true.to_numpy() == 1).astype(int)
    draw_prob = np.clip(probabilities[:, 1], 1e-15, 1.0)
    draw_pred = (predictions == 1).astype(int)
    return {
        "accuracy": float((predictions == y_true.to_numpy()).mean()),
        "log_loss": float(-np.log(probabilities[np.arange(len(y_true)), y_true.to_numpy()]).mean()),
        "Brier_score": multiclass_brier_score(y_true, probabilities),
        "expected_calibration_error": expected_calibration_error(calibration),
        "calibration_score": calibration_summary(calibration)["mean_absolute_calibration_error"],
        "draw_recall": float(((draw_pred == 1) & (draw_actual == 1)).sum() / draw_actual.sum()) if draw_actual.sum() else 0.0,
        "draw_log_loss": float(-np.mean(draw_actual * np.log(draw_prob) + (1 - draw_actual) * np.log(1 - draw_prob))),
    }


def rolling_feature_sets() -> dict[str, list[str]]:
    return {
        "production": PRODUCTION_FEATURE_COLUMNS,
        "production_minus_xg_diff": [column for column in PRODUCTION_FEATURE_COLUMNS if column not in set(XG_DIFF_COLUMNS)],
        "candidate_minus_xg_diff_plus_ratings": [
            column for column in PRODUCTION_FEATURE_COLUMNS if column not in set(XG_DIFF_COLUMNS)
        ]
        + RATING_FEATURE_COLUMNS,
        "production_plus_full_ratings": PRODUCTION_FEATURE_COLUMNS + RATING_FEATURE_COLUMNS,
        "ratings_replace_all_raw_xg": NON_XG_PRODUCTION_COLUMNS + RATING_FEATURE_COLUMNS,
    }


def evaluate_one_split(
    dataset: pd.DataFrame,
    metadata: pd.DataFrame,
    feature_columns: list[str],
    model_name: str,
    test_season: str,
) -> dict[str, object]:
    train_mask = metadata["Season"].astype(str) < test_season
    test_mask = metadata["Season"].astype(str) == test_season
    X_train = dataset.loc[train_mask, feature_columns]
    y_train = dataset.loc[train_mask, "target"]
    X_test = dataset.loc[test_mask, feature_columns]
    y_test = dataset.loc[test_mask, "target"]
    model = train_xgb(X_train, y_train)
    probabilities = normalize_probabilities(model.predict_proba(X_test))
    metrics = evaluate_probs(y_test, probabilities)
    return {
        "test_season": test_season,
        "test_season_label": SEASON_LABELS.get(test_season, test_season),
        "model_version": model_name,
        "train_start": str(metadata.loc[train_mask, "Date"].iloc[0]),
        "train_end": str(metadata.loc[train_mask, "Date"].iloc[-1]),
        "test_start": str(metadata.loc[test_mask, "Date"].iloc[0]),
        "test_end": str(metadata.loc[test_mask, "Date"].iloc[-1]),
        "train_matches": int(train_mask.sum()),
        "test_matches": int(test_mask.sum()),
        **metrics,
    }


def run_rolling_validation() -> pd.DataFrame:
    dataset, metadata, _ = build_replacement_dataset()
    rows = []
    for season in TEST_SEASONS:
        for model_name, columns in rolling_feature_sets().items():
            rows.append(evaluate_one_split(dataset, metadata, columns, model_name, season))
    output = pd.DataFrame(rows)
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    output.to_csv(OUTPUT_DIR / "rolling_validation_results.csv", index=False)
    return output


def summarize(results: pd.DataFrame) -> pd.DataFrame:
    baseline = results[results["model_version"] == "production"][
        ["test_season", "log_loss", "Brier_score", "expected_calibration_error", "accuracy", "draw_recall", "draw_log_loss"]
    ].rename(
        columns={
            "log_loss": "baseline_log_loss",
            "Brier_score": "baseline_Brier_score",
            "expected_calibration_error": "baseline_expected_calibration_error",
            "accuracy": "baseline_accuracy",
            "draw_recall": "baseline_draw_recall",
            "draw_log_loss": "baseline_draw_log_loss",
        }
    )
    merged = results.merge(baseline, on="test_season", how="left")
    for metric in ["log_loss", "Brier_score", "expected_calibration_error", "accuracy", "draw_recall", "draw_log_loss"]:
        merged[f"{metric}_delta_vs_production"] = merged[metric] - merged[f"baseline_{metric}"]
    candidates = merged[merged["model_version"] != "production"].copy()
    summary = (
        candidates.groupby("model_version", as_index=False)
        .agg(
            mean_log_loss_delta=("log_loss_delta_vs_production", "mean"),
            mean_Brier_delta=("Brier_score_delta_vs_production", "mean"),
            mean_ECE_delta=("expected_calibration_error_delta_vs_production", "mean"),
            mean_accuracy_delta=("accuracy_delta_vs_production", "mean"),
            mean_draw_recall_delta=("draw_recall_delta_vs_production", "mean"),
            mean_draw_log_loss_delta=("draw_log_loss_delta_vs_production", "mean"),
            seasons_log_loss_improved=("log_loss_delta_vs_production", lambda values: int((values < 0).sum())),
            seasons_Brier_improved=("Brier_score_delta_vs_production", lambda values: int((values < 0).sum())),
            seasons_ECE_not_worse=("expected_calibration_error_delta_vs_production", lambda values: int((values <= 0.01).sum())),
            seasons_tested=("test_season", "nunique"),
        )
        .sort_values(["mean_log_loss_delta", "mean_Brier_delta"])
    )
    summary.to_csv(OUTPUT_DIR / "rolling_validation_summary.csv", index=False)
    merged.to_csv(OUTPUT_DIR / "rolling_validation_deltas.csv", index=False)
    return summary


def plot_summary(summary: pd.DataFrame) -> None:
    metrics = ["mean_log_loss_delta", "mean_Brier_delta", "mean_ECE_delta"]
    fig, axes = plt.subplots(1, 3, figsize=(14, 4))
    for ax, metric in zip(axes, metrics):
        ax.bar(summary["model_version"], summary[metric])
        ax.axhline(0, color="black", linewidth=1)
        ax.set_title(metric)
        ax.tick_params(axis="x", rotation=28)
        ax.grid(axis="y", alpha=0.25)
    fig.suptitle("Rolling Validation: Delta vs Production")
    fig.tight_layout()
    fig.savefig(OUTPUT_DIR / "rolling_validation_summary.png", dpi=160)
    plt.close(fig)


def write_report(results: pd.DataFrame, summary: pd.DataFrame) -> None:
    best = summary.iloc[0]
    candidate = summary[summary["model_version"] == "candidate_minus_xg_diff_plus_ratings"]
    candidate_row = candidate.iloc[0] if not candidate.empty else best
    stable_candidate = (
        float(candidate_row["mean_log_loss_delta"]) < 0
        and float(candidate_row["mean_Brier_delta"]) < 0
        and int(candidate_row["seasons_log_loss_improved"]) >= 3
        and int(candidate_row["seasons_Brier_improved"]) >= 3
        and int(candidate_row["seasons_ECE_not_worse"]) >= 4
    )
    decision = (
        "Promote to a production-candidate retrain, but do not overwrite production until the saved artifact is evaluated."
        if stable_candidate
        else "Do not promote yet. Keep as Candidate/Research until the improvement is stable across more seasons or a simpler feature subset."
    )
    lines = [
        "# Sprint 4F: Rolling Validation for Opponent-Adjusted xG Candidate",
        "",
        "## Goal",
        "",
        "Validate whether the best Sprint 4E configuration holds across multiple season-based forward splits.",
        "",
        "Tested seasons: " + ", ".join(SEASON_LABELS[season] for season in TEST_SEASONS),
        "",
        "## Models",
        "",
        "- `production`: current production feature set.",
        "- `production_minus_xg_diff`: production without xG differential.",
        "- `candidate_minus_xg_diff_plus_ratings`: production without xG differential plus opponent-adjusted ratings.",
        "- `production_plus_full_ratings`: production plus ratings.",
        "- `ratings_replace_all_raw_xg`: raw xG/xGA/xG-diff removed, ratings used instead.",
        "",
        "## Rolling Summary",
        "",
        _markdown_table(
            summary,
            [
                "model_version",
                "mean_log_loss_delta",
                "mean_Brier_delta",
                "mean_ECE_delta",
                "seasons_log_loss_improved",
                "seasons_Brier_improved",
                "seasons_ECE_not_worse",
                "seasons_tested",
            ],
        ),
        "",
        "Negative deltas are better for Log Loss, Brier and ECE.",
        "",
        "## Per-Season Results",
        "",
        _markdown_table(
            results,
            ["test_season_label", "model_version", "accuracy", "log_loss", "Brier_score", "expected_calibration_error", "draw_recall", "draw_log_loss"],
        ),
        "",
        "## Decision",
        "",
        f"Best average Log Loss delta model: `{best['model_version']}`.",
        "",
        f"Candidate `candidate_minus_xg_diff_plus_ratings` mean Log Loss delta: {float(candidate_row['mean_log_loss_delta']):.4f}.",
        f"Candidate mean Brier delta: {float(candidate_row['mean_Brier_delta']):.4f}.",
        f"Candidate mean ECE delta: {float(candidate_row['mean_ECE_delta']):.4f}.",
        "",
        decision,
        "",
        "Production gate remains: improve Log Loss or Brier across most rolling splits without materially worsening calibration.",
    ]
    (OUTPUT_DIR / "rolling_validation_report.md").write_text("\n".join(lines))


def main() -> None:
    results = run_rolling_validation()
    summary = summarize(results)
    plot_summary(summary)
    write_report(results, summary)
    print(json.dumps({"best_model": str(summary.iloc[0]["model_version"]), "report": str(OUTPUT_DIR / "rolling_validation_report.md")}, indent=2))


if __name__ == "__main__":
    main()
