from __future__ import annotations

from datetime import datetime
from pathlib import Path
from typing import Any

from model_feature_status import FEATURE_STATUS, active_feature_statuses, inactive_feature_statuses


def _bullet_lines(items: list[str]) -> str:
    return "\n".join(f"- {item}" for item in items)


def how_model_works_text() -> str:
    return (
        "Modellen bruger machine learning til at estimere sandsynligheder for hjemmesejr, uafgjort og udesejr. "
        "Den er trænet og testet på historiske Premier League-kampe og bruger kun produktionsfeatures, der kan "
        "beregnes ud fra data, som findes før kampen. Den forudsiger sandsynligheder, ikke sikre resultater."
    )


def active_features_text(feature_columns: list[str]) -> str:
    entries = active_feature_statuses(feature_columns)
    if not entries:
        return "Der er ikke registreret aktive produktionsfeatures for den indlæste model."
    lines = []
    for name, entry in entries.items():
        if name == "Calibrated probabilities":
            lines.append(f"**{name}**: {entry.short_description} Det gør de viste sandsynligheder mere realistiske historisk.")
        else:
            lines.append(f"**{name}**: {entry.short_description} Det hjælper modellen med at vurdere kampens styrkeforhold.")
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
        "**Probability** er modellens estimerede chance for et udfald. Hvis Arsenal står til 58%, betyder det ikke, "
        "at Arsenal vinder med sikkerhed, men at modellen vurderer hjemmesejr som mest sandsynlig.\n\n"
        "**Confidence** beskriver hvor stabil og pålidelig selve estimatet virker. En kamp kan godt have en klar "
        "favorit, men stadig lavere confidence, hvis data er mangelfuld, sandsynlighederne er tætte, eller modellen "
        "historisk har haft sværere ved den type kamp."
    )


def raw_vs_displayed_probability_text() -> str:
    return (
        "**Raw probability** er den direkte sandsynlighed fra XGBoost-modellen.\n\n"
        "**Displayed probability** er den sandsynlighed brugeren ser. Hvis et valideret kalibreringslag er aktivt, "
        "justeres raw output, så sandsynlighederne bedre matcher historiske udfald i testperioden."
    )


def fair_odds_text() -> str:
    return (
        "Fair odds beregnes som `1 / sandsynlighed`. Hvis modellen giver 50% sandsynlighed, er fair odds 2.00. "
        "Et bookmakerodds over modellens fair odds kan ligne value, men det er ikke i sig selv et betsignal. "
        "Det skal valideres historisk mod bookmaker odds og timing, før det kan bruges seriøst."
    )


def season_projection_text() -> str:
    return (
        "Sæsonprojektionen forudsiger hver kamp med matchmodellen og simulerer derefter sæsonen mange gange. "
        "Resultatet viser forventede point, forventet placering og sandsynligheder for titel, top 4, top 6 og nedrykning. "
        "Hvis der ikke findes en officiel fixtureliste i `data/upcoming_fixtures.csv`, bruger appen en neutral "
        "home/away fixture-skeleton. Så er projektionen nyttig som styrkebillede, men ikke som en fuld fixture-aware forecast."
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
            f"Test period starts: {row.get('test_start_date', 'unknown')}",
            f"Test matches: {int(row.get('test_rows', 0))}",
            f"Model file updated: {updated}",
        ]
    )


def status_summary_for_readme() -> str:
    lines = []
    for name, entry in FEATURE_STATUS.items():
        production = "yes" if entry.used_in_production else "no"
        lines.append(f"| {name} | {entry.status} | {production} | {entry.evidence} |")
    return "\n".join(lines)
