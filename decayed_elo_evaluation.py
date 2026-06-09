from __future__ import annotations

import json
import os
from pathlib import Path

Path("evaluation", ".matplotlib-cache").mkdir(parents=True, exist_ok=True)
os.environ.setdefault("MPLCONFIGDIR", str(Path("evaluation") / ".matplotlib-cache"))

import matplotlib
import pandas as pd
from matplotlib import pyplot as plt

from elo_evaluation import draw_metrics, evaluate_calibrated, evaluate_columns
from elo_rating_features import EloConfig, build_elo_features, elo_feature_columns
from feature_experiments import _markdown_table
from train_model import ELO_CONFIG, SCHEDULE_FEATURE_COLUMNS, SHOT_VOLUME_FEATURE_COLUMNS, build_features, load_matches_with_xg

matplotlib.use("Agg")

OUTPUT_DIR = Path("evaluation") / "elo"
BASE_FEATURE_COLUMNS = SCHEDULE_FEATURE_COLUMNS + SHOT_VOLUME_FEATURE_COLUMNS


def carryover_grid() -> list[float]:
    return [1.0, 0.9, 0.85, 0.75, 0.65, 0.5]


def decayed_config(carryover: float) -> EloConfig:
    return EloConfig(
        k_factor=ELO_CONFIG.k_factor,
        home_advantage=ELO_CONFIG.home_advantage,
        margin_of_victory=ELO_CONFIG.margin_of_victory,
        initial_rating=ELO_CONFIG.initial_rating,
        season_carryover=carryover,
    )


def result_row(result: dict[str, object], carryover: float | None = None, model_type: str = "model") -> dict[str, object]:
    row = {
        key: value
        for key, value in result.items()
        if key not in {"model", "split", "feature_columns", "probabilities", "predictions"}
    }
    row["model_type"] = model_type
    if carryover is not None:
        row["season_carryover"] = carryover
    return row


def plot_decayed_elo_results(results: pd.DataFrame, output_path: Path) -> None:
    elo_rows = results[results["model_type"] == "production_plus_elo"].copy()
    metrics = ["log_loss", "brier_score", "ece"]
    fig, axes = plt.subplots(1, len(metrics), figsize=(13, 4))
    for ax, metric in zip(axes, metrics):
        ax.plot(elo_rows["season_carryover"], elo_rows[metric], marker="o")
        ax.invert_xaxis()
        ax.set_title(metric)
        ax.set_xlabel("season carryover")
        ax.grid(alpha=0.25)
    fig.suptitle("Decayed Elo Carryover Evaluation")
    fig.tight_layout()
    fig.savefig(output_path, dpi=160)
    plt.close(fig)


def write_report(results: pd.DataFrame, draw_results: pd.DataFrame) -> None:
    baseline = results[results["model_name"] == "production_without_elo"].iloc[0]
    current = results[results["model_name"] == "production_plus_current_elo"].iloc[0]
    elo_rows = results[results["model_type"] == "production_plus_elo"].copy()
    decayed_rows = elo_rows[elo_rows["season_carryover"] < 1.0].copy()
    best_log_loss = elo_rows.sort_values(["log_loss", "brier_score"]).iloc[0]
    best_decayed_log_loss = decayed_rows.sort_values(["log_loss", "brier_score"]).iloc[0]
    best_brier = elo_rows.sort_values(["brier_score", "log_loss"]).iloc[0]
    best_ece = elo_rows.sort_values(["ece", "log_loss"]).iloc[0]
    best_vs_current_log_loss = float(best_log_loss["log_loss"] - current["log_loss"])
    best_vs_current_brier = float(best_log_loss["brier_score"] - current["brier_score"])
    best_vs_current_ece = float(best_log_loss["ece"] - current["ece"])
    should_promote = (
        float(best_log_loss["log_loss"]) < float(current["log_loss"])
        or float(best_log_loss["brier_score"]) < float(current["brier_score"])
    ) and float(best_log_loss["ece"]) <= float(current["ece"]) + 0.01

    Path("decayed_elo_evaluation_report.md").write_text(
        f"""# Decayed Elo Evaluation Report

## Goal

Test whether season-weighted Elo improves the football prediction model by reducing the influence of older seasons.

The test uses the active production feature family:

- form
- xG / xGA / xG differential
- schedule and fatigue
- shot volume
- Elo

No future information is used. Elo is calculated chronologically before each match, then updated after the match result.

## Method

At each new season boundary, ratings are optionally regressed toward the league mean:

```text
new_rating = 1500 + season_carryover * (old_rating - 1500)
```

Tested carryover values:

{', '.join(str(value) for value in carryover_grid())}

`1.0` equals the current production behavior: no explicit season decay.

## Model Comparison

{_markdown_table(results, ['model_name', 'model_type', 'season_carryover', 'accuracy', 'log_loss', 'brier_score', 'calibration_score', 'ece', 'train_period', 'test_period'])}

## Draw Analysis

{_markdown_table(draw_results, ['model_name', 'season_carryover', 'draw_recall', 'draw_precision', 'draw_log_loss', 'draw_calibration_error'])}

## Key Findings

Current production Elo:

- Log Loss: {float(current['log_loss']):.4f}
- Brier Score: {float(current['brier_score']):.4f}
- ECE: {float(current['ece']):.4f}

Best carryover setting by Log Loss:

- Configuration: `{best_log_loss['model_name']}`
- Season carryover: {float(best_log_loss['season_carryover']):.2f}
- Log Loss delta vs current Elo: {best_vs_current_log_loss:+.4f}
- Brier delta vs current Elo: {best_vs_current_brier:+.4f}
- ECE delta vs current Elo: {best_vs_current_ece:+.4f}

Best actual decayed setting by Log Loss:

- Configuration: `{best_decayed_log_loss['model_name']}`
- Season carryover: {float(best_decayed_log_loss['season_carryover']):.2f}
- Log Loss delta vs current Elo: {float(best_decayed_log_loss['log_loss'] - current['log_loss']):+.4f}
- Brier delta vs current Elo: {float(best_decayed_log_loss['brier_score'] - current['brier_score']):+.4f}
- ECE delta vs current Elo: {float(best_decayed_log_loss['ece'] - current['ece']):+.4f}

Best decayed Elo by Brier Score:

- Configuration: `{best_brier['model_name']}`
- Season carryover: {float(best_brier['season_carryover']):.2f}
- Brier Score: {float(best_brier['brier_score']):.4f}

Best decayed Elo by ECE:

- Configuration: `{best_ece['model_name']}`
- Season carryover: {float(best_ece['season_carryover']):.2f}
- ECE: {float(best_ece['ece']):.4f}

## Production Decision

Recommended decision: {'Promote decayed Elo to production candidate.' if should_promote else 'Keep current Elo in production and keep decayed Elo as research-only.'}

Reason: {'The best decayed Elo configuration improves Log Loss or Brier without materially worsening calibration.' if should_promote else 'The decayed Elo configurations do not beat current production Elo on the primary promotion rule.'}

## Practical Interpretation

Season decay is useful only if teams' old strength ratings are carrying too much stale information. If current Elo already adapts quickly enough through K-factor and recent results, season decay may add little or make ratings too reactive.

## Artifacts

- `evaluation/elo/decayed_elo_model_comparison.csv`
- `evaluation/elo/decayed_elo_draw_analysis.csv`
- `evaluation/elo/decayed_elo_model_comparison.png`
"""
    )


def run_evaluation() -> pd.DataFrame:
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    matches = load_matches_with_xg().sort_values("Date").reset_index(drop=True)
    base_dataset, _ = build_features(matches, include_xg=True, include_schedule=True, include_shot_volume=True)
    metadata = matches[["Season", "Date", "HomeTeam", "AwayTeam", "FTR"]].reset_index(drop=True)

    results: list[dict[str, object]] = []
    draw_rows: list[dict[str, object]] = []

    baseline = evaluate_columns(base_dataset, metadata, BASE_FEATURE_COLUMNS, "production_without_elo")
    results.append(result_row(baseline, model_type="production_without_elo"))
    draw_base = draw_metrics(baseline)
    draw_base["season_carryover"] = None
    draw_rows.append(draw_base)

    for carryover in carryover_grid():
        config = decayed_config(carryover)
        elo_features, _ = build_elo_features(matches, config)
        dataset = pd.concat([base_dataset.reset_index(drop=True), elo_features.reset_index(drop=True)], axis=1)
        model_name = "production_plus_current_elo" if carryover == 1.0 else f"production_plus_decayed_elo_carry{int(carryover * 100)}"
        result = evaluate_columns(dataset, metadata, BASE_FEATURE_COLUMNS + elo_feature_columns(), model_name)
        results.append(result_row(result, carryover=carryover, model_type="production_plus_elo"))
        draw = draw_metrics(result)
        draw["season_carryover"] = carryover
        draw_rows.append(draw)

        if carryover == 1.0:
            calibrated = evaluate_calibrated(result)
            calibrated["model_name"] = "production_plus_current_elo_calibrated"
            results.append(result_row(calibrated, carryover=carryover, model_type="calibrated_current_elo"))
            draw_cal = draw_metrics(calibrated, calibrated["probabilities"], calibrated["predictions"])
            draw_cal["season_carryover"] = carryover
            draw_rows.append(draw_cal)

    comparison = pd.DataFrame(results)
    draw_results = pd.DataFrame(draw_rows)
    comparison.to_csv(OUTPUT_DIR / "decayed_elo_model_comparison.csv", index=False)
    draw_results.to_csv(OUTPUT_DIR / "decayed_elo_draw_analysis.csv", index=False)
    plot_decayed_elo_results(comparison, OUTPUT_DIR / "decayed_elo_model_comparison.png")
    write_report(comparison, draw_results)
    return comparison


def main() -> None:
    comparison = run_evaluation()
    best = comparison.sort_values(["log_loss", "brier_score"]).iloc[0]
    print(
        json.dumps(
            {
                "best_model": str(best["model_name"]),
                "season_carryover": None if pd.isna(best.get("season_carryover")) else float(best["season_carryover"]),
                "log_loss": float(best["log_loss"]),
                "brier_score": float(best["brier_score"]),
                "ece": float(best["ece"]),
            },
            indent=2,
        )
    )


if __name__ == "__main__":
    main()
