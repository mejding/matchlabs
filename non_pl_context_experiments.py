from __future__ import annotations

import os
from pathlib import Path

Path("evaluation", ".matplotlib-cache").mkdir(parents=True, exist_ok=True)
os.environ.setdefault("MPLCONFIGDIR", str(Path("evaluation") / ".matplotlib-cache"))

import matplotlib
import pandas as pd
from matplotlib import pyplot as plt
from sklearn.metrics import log_loss, recall_score

from calibration.calibration import calibration_summary, calibration_table, expected_calibration_error
from elo_rating_features import build_elo_features
from evaluation.model_evaluation import evaluate_probabilities, time_based_split
from feature_experiments import _markdown_table, train_xgb
from non_pl_context_features import (
    build_non_pl_context_features,
    load_non_pl_team_matches,
    non_pl_context_feature_columns,
    non_pl_source_coverage,
)
from train_model import ELO_CONFIG, PRODUCTION_FEATURE_COLUMNS, build_features, load_matches_with_xg

matplotlib.use("Agg")

OUTPUT_DIR = Path("evaluation") / "non_pl_context"
RESULTS_PATH = Path("experiments") / "non_pl_context_results.csv"


def build_dataset() -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame, dict[str, list[str]]]:
    matches = load_matches_with_xg().sort_values("Date").reset_index(drop=True)
    production_base, _ = build_features(matches, include_xg=True, include_schedule=True, include_shot_volume=True)
    elo_features, _ = build_elo_features(matches, ELO_CONFIG)
    non_pl_rows = load_non_pl_team_matches()
    non_pl_features = build_non_pl_context_features(matches, non_pl_rows)
    dataset = pd.concat(
        [
            production_base.reset_index(drop=True),
            elo_features.reset_index(drop=True),
            non_pl_features.reset_index(drop=True),
        ],
        axis=1,
    )
    metadata = matches[["Season", "Date", "HomeTeam", "AwayTeam", "FTR"]].reset_index(drop=True)
    feature_sets = {
        "model_a_current_production": PRODUCTION_FEATURE_COLUMNS,
        "model_b_production_plus_non_pl_context": PRODUCTION_FEATURE_COLUMNS + non_pl_context_feature_columns(),
    }
    return dataset, metadata, non_pl_rows, feature_sets


def evaluate_feature_set(
    dataset: pd.DataFrame,
    metadata: pd.DataFrame,
    feature_columns: list[str],
    model_version: str,
) -> dict[str, object]:
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
    draw_prob = probabilities[:, 1].clip(1e-12, 1 - 1e-12)
    draw_pred = (predictions == 1).astype(int)
    return {
        "model_version": model_version,
        "model": model,
        "split": split,
        "feature_columns": feature_columns,
        "accuracy": metrics["accuracy"],
        "log_loss": metrics["log_loss"],
        "brier_score": metrics["brier_score_multiclass"],
        "calibration_score": cal_summary["mean_absolute_calibration_error"],
        "expected_calibration_error": expected_calibration_error(calibration),
        "draw_recall": float(recall_score(draw_actual, draw_pred, zero_division=0)),
        "draw_log_loss": float(log_loss(draw_actual, pd.DataFrame({"not_draw": 1 - draw_prob, "draw": draw_prob}), labels=[0, 1])),
        "train_period": f"{split.train_metadata['Date'].iloc[0]} to {split.train_metadata['Date'].iloc[-1]}",
        "test_period": f"{split.test_metadata['Date'].iloc[0]} to {split.test_metadata['Date'].iloc[-1]}",
    }


def save_results(results: list[dict[str, object]]) -> pd.DataFrame:
    rows = []
    for result in results:
        rows.append(
            {
                "model_version": result["model_version"],
                "features_added": "|".join(
                    column for column in result["feature_columns"] if column in set(non_pl_context_feature_columns())
                ),
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
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    RESULTS_PATH.parent.mkdir(exist_ok=True)
    output.to_csv(OUTPUT_DIR / "model_comparison.csv", index=False)
    output.to_csv(RESULTS_PATH, index=False)
    return output


def plot_model_comparison(results: pd.DataFrame) -> None:
    metrics = ["log_loss", "Brier_score", "expected_calibration_error", "draw_log_loss"]
    fig, axes = plt.subplots(1, len(metrics), figsize=(14, 4))
    for ax, metric in zip(axes, metrics):
        ax.bar(results["model_version"], results[metric])
        ax.set_title(metric)
        ax.tick_params(axis="x", rotation=25)
        ax.grid(axis="y", alpha=0.25)
    fig.suptitle("Non-PL Context Evaluation")
    fig.tight_layout()
    fig.savefig(OUTPUT_DIR / "model_comparison.png", dpi=160)
    plt.close(fig)


def write_report(results: pd.DataFrame, coverage: pd.DataFrame, dataset: pd.DataFrame) -> None:
    baseline = results[results["model_version"] == "model_a_current_production"].iloc[0]
    candidate = results[results["model_version"] == "model_b_production_plus_non_pl_context"].iloc[0]
    log_loss_delta = float(candidate["log_loss"] - baseline["log_loss"])
    brier_delta = float(candidate["Brier_score"] - baseline["Brier_score"])
    ece_delta = float(candidate["expected_calibration_error"] - baseline["expected_calibration_error"])
    context_available_columns = ["home_non_pl_context_available", "away_non_pl_context_available"]
    rows_with_context = int((dataset[context_available_columns].sum(axis=1) > 0).sum())
    decision = (
        "Do not move into production yet. Local source coverage is too thin and the candidate must improve "
        "out-of-sample Log Loss or Brier before activation."
    )
    if (log_loss_delta < 0 or brier_delta < 0) and ece_delta <= 0.01 and rows_with_context > 100:
        decision = "Candidate for a controlled production follow-up after source timing is verified."

    (OUTPUT_DIR / "non_pl_context_report.md").write_text(
        f"""# Non-PL Match Context Evaluation

## Goal

Test whether pre-season friendlies, European qualifiers and other competitive non-Premier-League matches should inform the match prediction model.

## Feature Design

These features are generated chronologically and use only matches before kickoff:

- recent non-PL match activity
- days since any known match
- pre-season match count
- competitive non-PL match count
- European qualifier flag
- weighted non-PL points, goals and shot volume

First-version weighting:

- Championship: `0.55`
- Champions League: `0.80`
- Europa League: `0.75`
- Conference League / European qualifier: `0.70`
- Domestic cups: `0.45`
- Friendlies / pre-season: `0.25`

The intent is to let non-PL matches help with match rhythm and early-season context without treating them as Premier League-equivalent.

## Local Source Coverage

{_markdown_table(coverage, ['source_file', 'competition', 'team_rows', 'teams', 'first_date', 'last_date']) if not coverage.empty else 'No populated non-PL source rows were found locally.'}

Premier League training/evaluation rows with actual non-PL context available: `{rows_with_context}`.

## Model Comparison

{_markdown_table(results, ['model_version', 'accuracy', 'log_loss', 'Brier_score', 'expected_calibration_error', 'draw_recall', 'draw_log_loss', 'test_period'])}

Candidate deltas versus production:

- Log Loss: `{log_loss_delta:+.6f}`
- Brier Score: `{brier_delta:+.6f}`
- ECE: `{ece_delta:+.6f}`

## Answer

European qualifiers and cup matches are conceptually stronger than friendlies because they are competitive and affect fatigue. Pre-season friendlies are much noisier and should only be weak context.

However, the current local project does not yet contain reliable historical pre-season or European qualifier rows for Premier League teams. The available Championship file is useful for promoted-team season projection context, but it does not provide broad historical non-PL coverage for the Premier League match training set.

## Production Decision

{decision}

## Next Data Needed

To make this feature family genuinely testable, add historically reproducible rows for:

- European qualifiers and European group-stage matches before each Premier League fixture
- domestic cup matches
- selected pre-season friendlies with kickoff dates, teams, result and ideally shots/xG

Each source must include match date and competition so timing and weighting stay transparent.
""",
        encoding="utf-8",
    )


def run_evaluation() -> pd.DataFrame:
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    dataset, metadata, non_pl_rows, feature_sets = build_dataset()
    coverage = non_pl_source_coverage(non_pl_rows)
    coverage.to_csv(OUTPUT_DIR / "source_coverage.csv", index=False)
    dataset[non_pl_context_feature_columns()].describe().transpose().to_csv(OUTPUT_DIR / "feature_summary.csv")
    results = [evaluate_feature_set(dataset, metadata, columns, name) for name, columns in feature_sets.items()]
    comparison = save_results(results)
    plot_model_comparison(comparison)
    write_report(comparison, coverage, dataset)
    return comparison


if __name__ == "__main__":
    output = run_evaluation()
    print(output.to_string(index=False))
