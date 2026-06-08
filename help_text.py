from __future__ import annotations

from datetime import datetime
from pathlib import Path
from typing import Any

from model_feature_status import FEATURE_STATUS, active_feature_statuses, inactive_feature_statuses


def _bullet_lines(items: list[str]) -> str:
    return "\n".join(f"- {item}" for item in items)


def how_model_works_text() -> str:
    return (
        "The model uses machine learning to estimate probabilities for home win, draw and away win. "
        "It is trained and tested on historical Premier League matches and only uses production features "
        "that can be calculated from information available before kickoff. It predicts probabilities, not certainties."
    )


def active_features_text(feature_columns: list[str]) -> str:
    entries = active_feature_statuses(feature_columns)
    if not entries:
        return "No active production features are registered for the loaded model."
    lines = []
    for name, entry in entries.items():
        if name == "Calibrated probabilities":
            lines.append(f"**{name}**: {entry.short_description} This makes the displayed probabilities more realistic historically.")
        else:
            lines.append(f"**{name}**: {entry.short_description} This helps the model assess the balance of the match.")
    return "\n\n".join(lines)


def investigated_features_text() -> str:
    entries = inactive_feature_statuses()
    grouped: dict[str, list[str]] = {}
    for name, entry in entries.items():
        grouped.setdefault(entry.status, []).append(f"**{name}**: {entry.short_description} _Status_: {entry.evidence}")

    order = ["Candidate", "Tested - Not adopted", "Research", "Missing", "Benchmark only"]
    sections = []
    for status in order:
        values = grouped.get(status, [])
        if values:
            sections.append(f"**{status}**\n\n" + "\n\n".join(values))
    return "\n\n".join(sections)


def probability_confidence_text() -> str:
    return (
        "**Probability** is the model's estimated chance of an outcome. If Arsenal is shown at 58%, it does not mean "
        "Arsenal will definitely win; it means the model rates that outcome as the most likely one.\n\n"
        "**Confidence** describes how stable and reliable the estimate appears. A match can have a clear favorite "
        "but still lower confidence if data quality is weaker, the probabilities are close, or this type of match "
        "has historically been harder for the model."
    )


def raw_vs_displayed_probability_text() -> str:
    return (
        "**Raw probability** is the direct probability output from the XGBoost model.\n\n"
        "**Displayed probability** is the probability shown to users. If a validated calibration layer is active, "
        "the raw output is adjusted so predicted probabilities better match historical outcomes in the test period."
    )


def fair_odds_text() -> str:
    return (
        "Fair odds are calculated as `1 / probability`. If the model gives an outcome a 50% probability, the fair odds are 2.00. "
        "A bookmaker price above the model's fair odds may look like value, but it is not a betting signal by itself. "
        "It must be validated historically against bookmaker odds and odds timing before it can be used seriously."
    )


def season_projection_text() -> str:
    return (
        "The season projection predicts every fixture with the match model and then simulates the season many times. "
        "The output includes expected points, expected position, and probabilities for title, top 4, top 6 and relegation. "
        "If no official fixture list exists in `data/upcoming_fixtures.csv`, the app uses a neutral home/away fixture skeleton. "
        "In that case, the projection is useful as a strength estimate, but not as a fully fixture-aware forecast."
    )


def validation_metrics(metrics: dict[str, Any]) -> dict[str, Any] | None:
    if not metrics:
        return None
    candidates = [
        "xg_schedule_elo_shot_volume_model",
        "xg_schedule_elo_model",
        "xg_schedule_model",
    ]
    for key in candidates:
        if key in metrics:
            row = dict(metrics[key])
            row["model_key"] = key
            return row
    return None


def validation_text(metrics: dict[str, Any], model_path: Path) -> str:
    row = validation_metrics(metrics)
    if row is None:
        return "Validation metrics are not available yet. Run `python evaluate_model.py`."
    updated = "unknown"
    if model_path.exists():
        updated = datetime.fromtimestamp(model_path.stat().st_mtime).strftime("%Y-%m-%d %H:%M")
    return _bullet_lines(
        [
            f"Model version: `{row.get('model_key', 'unknown')}`",
            f"Accuracy: {float(row.get('accuracy', 0.0)):.4f}",
            f"Log Loss: {float(row.get('log_loss', 0.0)):.4f}",
            f"Brier Score: {float(row.get('brier_score', 0.0)):.4f}",
            f"Calibration Error/ECE: {float(row.get('mean_absolute_calibration_error', 0.0)):.4f}",
            f"Training data: matches before {row.get('test_start_date', 'unknown')}",
            f"Test data: {int(row.get('test_rows', 0))} later matches from {row.get('test_start_date', 'unknown')}",
            f"Model file updated: {updated}",
        ]
    )


def status_summary_for_readme() -> str:
    lines = []
    for name, entry in FEATURE_STATUS.items():
        production = "yes" if entry.used_in_production else "no"
        lines.append(f"| {name} | {entry.status} | {production} | {entry.evidence} |")
    return "\n".join(lines)
