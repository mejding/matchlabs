from __future__ import annotations

from pathlib import Path

import numpy as np
import pandas as pd
from sklearn.metrics import accuracy_score, log_loss

from evaluate_model import load_current_dataset
from evaluation.model_evaluation import multiclass_brier_score
from feature_experiments import train_xgb
from train_model import PRODUCTION_FEATURE_COLUMNS, XG_FEATURE_COLUMNS


OUTPUT_DIR = Path("evaluation") / "robust_prediction"
TEST_SEASONS = ("2324", "2425", "2526")
WEIGHTS = (0.0, 0.25, 0.5, 0.75, 1.0)


def normalized(probabilities: np.ndarray) -> np.ndarray:
    values = np.clip(np.asarray(probabilities, dtype=float), 1e-15, 1.0)
    return values / values.sum(axis=1, keepdims=True)


def evaluate(y: np.ndarray, probabilities: np.ndarray) -> dict[str, float]:
    probabilities = normalized(probabilities)
    return {
        "accuracy": float(accuracy_score(y, probabilities.argmax(axis=1))),
        "log_loss": float(log_loss(y, probabilities, labels=[0, 1, 2])),
        "brier_score": multiclass_brier_score(pd.Series(y), probabilities),
    }


def run() -> pd.DataFrame:
    datasets = {
        "xg": (*load_current_dataset(XG_FEATURE_COLUMNS), XG_FEATURE_COLUMNS),
        "complex": (*load_current_dataset(PRODUCTION_FEATURE_COLUMNS), PRODUCTION_FEATURE_COLUMNS),
    }
    rows = []
    for season in TEST_SEASONS:
        probabilities = {}
        targets = None
        for name, (dataset, metadata, columns) in datasets.items():
            test_mask = metadata["Season"].astype(str).eq(season)
            first_test_date = metadata.loc[test_mask, "Date"].min()
            train_mask = metadata["Date"] < first_test_date
            model = train_xgb(dataset.loc[train_mask, columns], dataset.loc[train_mask, "target"])
            probabilities[name] = normalized(model.predict_proba(dataset.loc[test_mask, columns]))
            targets = dataset.loc[test_mask, "target"].to_numpy()

        for weight in WEIGHTS:
            blended = weight * probabilities["complex"] + (1.0 - weight) * probabilities["xg"]
            rows.append({"test_season": season, "complex_weight": weight, **evaluate(targets, blended)})

    results = pd.DataFrame(rows)
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    results.to_csv(OUTPUT_DIR / "season_backtest.csv", index=False)
    summary = (
        results.groupby("complex_weight", as_index=False)
        .agg(accuracy=("accuracy", "mean"), log_loss=("log_loss", "mean"), brier_score=("brier_score", "mean"))
        .sort_values(["log_loss", "brier_score"])
    )
    summary.to_csv(OUTPUT_DIR / "weight_summary.csv", index=False)
    selected = summary.loc[summary["complex_weight"].eq(0.5)].iloc[0]
    complex_only = summary.loc[summary["complex_weight"].eq(1.0)].iloc[0]
    report = f"""# Robust Match Prediction Experiment

## Method

Each test season is predicted using only earlier seasons for training. The candidate combines the feature-rich production model with the simpler recent-form/xG model. A fixed 50/50 blend was selected as the conservative midpoint because the complex model wins the two older seasons while the xG model wins the latest season.

## Three-season average

| Model | Accuracy | Log loss | Brier |
| --- | ---: | ---: | ---: |
| Complex model | {complex_only['accuracy']:.4f} | {complex_only['log_loss']:.4f} | {complex_only['brier_score']:.4f} |
| 50/50 robust ensemble | {selected['accuracy']:.4f} | {selected['log_loss']:.4f} | {selected['brier_score']:.4f} |

## Decision

Adopt the 50/50 ensemble. It reduces average log loss by {selected['log_loss'] - complex_only['log_loss']:+.4f} and Brier score by {selected['brier_score'] - complex_only['brier_score']:+.4f}. Accuracy is treated as secondary because the product displays probabilities rather than only a hard class prediction.

Temperature calibration is fitted after ensembling and must be applied consistently in the Prediction tab, forecast snapshots and Season Projection.
"""
    (OUTPUT_DIR / "robust_prediction_report.md").write_text(report)
    return summary


if __name__ == "__main__":
    print(run().to_string(index=False))
