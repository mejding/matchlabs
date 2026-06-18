from __future__ import annotations

import json
from pathlib import Path

import numpy as np
import pandas as pd

from elo_rating_features import build_elo_features
from evaluation.model_evaluation import time_based_split
from feature_experiments import _markdown_table, train_xgb
from scoreline_model import bucket_probabilities, estimate_scorelines
from train_model import ELO_CONFIG, PRODUCTION_FEATURE_COLUMNS, build_features, load_matches_with_xg

OUTPUT_DIR = Path("evaluation") / "scoreline"
CLASS_LABELS = ["home_win", "draw", "away_win"]


def normalize_probabilities(probabilities: np.ndarray) -> np.ndarray:
    clipped = np.clip(probabilities, 1e-15, 1.0)
    return clipped / clipped.sum(axis=1, keepdims=True)


def scoreline_probability_for_actual(matrix: np.ndarray, home_goals: int, away_goals: int) -> float:
    if home_goals >= matrix.shape[0] or away_goals >= matrix.shape[1]:
        return 1e-15
    return float(max(matrix[home_goals, away_goals], 1e-15))


def evaluate_scorelines() -> tuple[pd.DataFrame, dict[str, float]]:
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    matches = load_matches_with_xg().sort_values("Date").reset_index(drop=True)
    base_dataset, _ = build_features(matches, include_xg=True, include_schedule=True, include_shot_volume=True)
    elo_features, _ = build_elo_features(matches, ELO_CONFIG)
    dataset = pd.concat([base_dataset.reset_index(drop=True), elo_features.reset_index(drop=True)], axis=1)
    metadata = matches[["Season", "Date", "HomeTeam", "AwayTeam", "FTHG", "FTAG", "FTR"]].reset_index(drop=True)

    split = time_based_split(dataset[PRODUCTION_FEATURE_COLUMNS], dataset["target"], metadata)
    model = train_xgb(split.X_train, split.y_train)
    probabilities = normalize_probabilities(model.predict_proba(split.X_test))

    rows: list[dict[str, object]] = []
    actual_probs: list[float] = []
    top1_hits = []
    top3_hits = []
    top5_hits = []
    consistency_errors = []

    for position, (_, feature_row) in enumerate(split.X_test.iterrows()):
        meta = split.test_metadata.iloc[position]
        model_probs = probabilities[position]
        result = estimate_scorelines(feature_row.to_dict(), model_probs)
        matrix = result["scoreline_matrix"]
        top_scorelines = result["top_scorelines"]
        actual = (int(meta["FTHG"]), int(meta["FTAG"]))
        top_pairs = [(item.home_goals, item.away_goals) for item in top_scorelines]
        actual_probability = scoreline_probability_for_actual(matrix, actual[0], actual[1])
        actual_probs.append(actual_probability)
        top1_hits.append(actual == top_pairs[0])
        top3_hits.append(actual in top_pairs[:3])
        top5_hits.append(actual in top_pairs[:5])
        bucket_sums = np.asarray(bucket_probabilities(matrix))
        consistency_errors.append(float(np.abs(bucket_sums - model_probs).max()))
        rows.append(
            {
                "Date": meta["Date"],
                "Match": f"{meta['HomeTeam']} vs {meta['AwayTeam']}",
                "Actual score": f"{actual[0]}-{actual[1]}",
                "Most likely scoreline": top_scorelines[0].scoreline,
                "Most likely probability": top_scorelines[0].probability,
                "Actual scoreline probability": actual_probability,
                "Actual in top 3": bool(top3_hits[-1]),
                "Actual in top 5": bool(top5_hits[-1]),
                "expected_home_goals": result["expected_home_goals"],
                "expected_away_goals": result["expected_away_goals"],
                "max_1x2_alignment_error": consistency_errors[-1],
            }
        )

    detail = pd.DataFrame(rows)
    detail.to_csv(OUTPUT_DIR / "scoreline_predictions.csv", index=False)
    metrics = {
        "test_matches": float(len(detail)),
        "correct_score_accuracy": float(np.mean(top1_hits)),
        "top_3_hit_rate": float(np.mean(top3_hits)),
        "top_5_hit_rate": float(np.mean(top5_hits)),
        "mean_probability_assigned_to_actual": float(np.mean(actual_probs)),
        "scoreline_log_loss": float(-np.mean(np.log(np.clip(actual_probs, 1e-15, 1.0)))),
        "mean_1x2_alignment_error": float(np.mean(consistency_errors)),
        "max_1x2_alignment_error": float(np.max(consistency_errors)),
    }
    pd.DataFrame([metrics]).to_csv(OUTPUT_DIR / "scoreline_metrics.csv", index=False)
    write_report(detail, metrics, split)
    return detail, metrics


def write_report(detail: pd.DataFrame, metrics: dict[str, float], split) -> None:
    worked = detail[detail["Actual in top 5"]].sort_values("Actual scoreline probability", ascending=False).head(8)
    failed = detail[~detail["Actual in top 5"]].sort_values("Actual scoreline probability", ascending=True).head(8)
    Path(OUTPUT_DIR / "scoreline_evaluation_report.md").write_text(
        f"""# Scoreline Evaluation Report

## Purpose

Evaluate the scoreline interpretation layer on historical matches where final scores are known.

The scoreline layer is not a replacement for the 1X2 model. It estimates likely correct scores from expected goals and then aligns scoreline buckets with the production model's home/draw/away probabilities.

## Validation Period

- Train period: {split.train_metadata['Date'].iloc[0]} to {split.train_metadata['Date'].iloc[-1]}
- Test period: {split.test_metadata['Date'].iloc[0]} to {split.test_metadata['Date'].iloc[-1]}
- Test matches: {int(metrics['test_matches'])}

## Metrics

| Metric | Value |
| --- | ---: |
| Correct score accuracy | {metrics['correct_score_accuracy']:.3f} |
| Top 3 scoreline hit rate | {metrics['top_3_hit_rate']:.3f} |
| Top 5 scoreline hit rate | {metrics['top_5_hit_rate']:.3f} |
| Mean probability assigned to actual scoreline | {metrics['mean_probability_assigned_to_actual']:.3f} |
| Scoreline log loss | {metrics['scoreline_log_loss']:.3f} |
| Mean 1X2 alignment error | {metrics['mean_1x2_alignment_error']:.6f} |
| Max 1X2 alignment error | {metrics['max_1x2_alignment_error']:.6f} |

## Examples Where It Worked

{_markdown_table(worked, ['Date', 'Match', 'Actual score', 'Most likely scoreline', 'Actual scoreline probability'])}

## Examples Where It Failed

{_markdown_table(failed, ['Date', 'Match', 'Actual score', 'Most likely scoreline', 'Actual scoreline probability'])}

## Interpretation

Correct-score prediction is inherently difficult. Even a useful scoreline layer will usually have low top-1 accuracy because many individual scorelines have small probabilities.

The useful validation check for this sprint is whether the layer provides plausible context and remains consistent with the main 1X2 probabilities. The alignment error should be effectively zero after scoreline bucket scaling.

## Production Guidance

Use the scoreline layer as supporting context only:

- show "Most likely scoreline"
- do not show "Predicted final score"
- do not claim a correct-score betting edge
- keep the main home/draw/away probabilities as the primary prediction
"""
    )


def main() -> None:
    _, metrics = evaluate_scorelines()
    print(json.dumps(metrics, indent=2))


if __name__ == "__main__":
    main()
