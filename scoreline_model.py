from __future__ import annotations

from dataclasses import dataclass
from math import exp, factorial
from typing import Mapping

import numpy as np


@dataclass(frozen=True)
class ScorelineProbability:
    home_goals: int
    away_goals: int
    probability: float

    @property
    def scoreline(self) -> str:
        return f"{self.home_goals}-{self.away_goals}"


def _feature_value(match_features: Mapping[str, object], key: str, fallback: float) -> float:
    try:
        value = float(match_features.get(key, fallback))
    except (TypeError, ValueError):
        return fallback
    if not np.isfinite(value) or value <= 0:
        return fallback
    return value


def estimate_expected_goals(
    match_features: Mapping[str, object],
    model_probabilities: np.ndarray | list[float],
    league_home_goals: float = 1.45,
    league_away_goals: float = 1.15,
) -> tuple[float, float]:
    """Estimate pragmatic expected goals from available pre-match xG/xGA features."""
    probabilities = np.asarray(model_probabilities, dtype=float)
    probabilities = probabilities / probabilities.sum() if probabilities.sum() else np.array([1 / 3, 1 / 3, 1 / 3])

    home_attack = _feature_value(match_features, "home_xg_avg", league_home_goals)
    away_attack = _feature_value(match_features, "away_xg_avg", league_away_goals)
    home_defense_allowed = _feature_value(match_features, "home_xga_avg", league_away_goals)
    away_defense_allowed = _feature_value(match_features, "away_xga_avg", league_home_goals)

    expected_home = 0.55 * home_attack + 0.45 * away_defense_allowed
    expected_away = 0.55 * away_attack + 0.45 * home_defense_allowed

    # Nudge expected goals toward the displayed 1X2 model view without replacing it.
    win_balance = float(probabilities[0] - probabilities[2])
    expected_home *= float(np.exp(0.22 * win_balance))
    expected_away *= float(np.exp(-0.22 * win_balance))

    return float(np.clip(expected_home, 0.2, 4.0)), float(np.clip(expected_away, 0.2, 4.0))


def _poisson_probabilities(expected_goals: float, max_goals: int) -> np.ndarray:
    return np.array(
        [exp(-expected_goals) * (expected_goals**goals) / factorial(goals) for goals in range(max_goals + 1)],
        dtype=float,
    )


def calculate_scoreline_probabilities(home_expected_goals: float, away_expected_goals: float, max_goals: int = 6) -> np.ndarray:
    home_probs = _poisson_probabilities(float(home_expected_goals), max_goals)
    away_probs = _poisson_probabilities(float(away_expected_goals), max_goals)
    matrix = np.outer(home_probs, away_probs)
    total = matrix.sum()
    return matrix / total if total else np.full((max_goals + 1, max_goals + 1), 1 / ((max_goals + 1) ** 2))


def bucket_probabilities(scoreline_matrix: np.ndarray) -> tuple[float, float, float]:
    home_total = 0.0
    draw_total = 0.0
    away_total = 0.0
    for home_goals in range(scoreline_matrix.shape[0]):
        for away_goals in range(scoreline_matrix.shape[1]):
            probability = float(scoreline_matrix[home_goals, away_goals])
            if home_goals > away_goals:
                home_total += probability
            elif home_goals == away_goals:
                draw_total += probability
            else:
                away_total += probability
    return home_total, draw_total, away_total


def align_scorelines_to_1x2(
    scoreline_matrix: np.ndarray,
    model_home_prob: float,
    model_draw_prob: float,
    model_away_prob: float,
) -> np.ndarray:
    targets = np.asarray([model_home_prob, model_draw_prob, model_away_prob], dtype=float)
    targets = np.clip(targets, 1e-12, 1.0)
    targets = targets / targets.sum()
    current = np.asarray(bucket_probabilities(scoreline_matrix), dtype=float)
    scaled = scoreline_matrix.astype(float).copy()

    for home_goals in range(scaled.shape[0]):
        for away_goals in range(scaled.shape[1]):
            if home_goals > away_goals:
                bucket_index = 0
            elif home_goals == away_goals:
                bucket_index = 1
            else:
                bucket_index = 2
            if current[bucket_index] > 0:
                scaled[home_goals, away_goals] *= targets[bucket_index] / current[bucket_index]

    total = scaled.sum()
    return scaled / total if total else scoreline_matrix


def get_top_scorelines(scoreline_matrix: np.ndarray, top_n: int = 5) -> list[ScorelineProbability]:
    rows: list[ScorelineProbability] = []
    for home_goals in range(scoreline_matrix.shape[0]):
        for away_goals in range(scoreline_matrix.shape[1]):
            rows.append(ScorelineProbability(home_goals, away_goals, float(scoreline_matrix[home_goals, away_goals])))
    return sorted(rows, key=lambda row: row.probability, reverse=True)[:top_n]


def _best_matching(scoreline_matrix: np.ndarray, predicate) -> ScorelineProbability | None:
    candidates = [
        ScorelineProbability(home_goals, away_goals, float(scoreline_matrix[home_goals, away_goals]))
        for home_goals in range(scoreline_matrix.shape[0])
        for away_goals in range(scoreline_matrix.shape[1])
        if predicate(home_goals, away_goals)
    ]
    return max(candidates, key=lambda row: row.probability) if candidates else None


def summarize_scorelines(scoreline_matrix: np.ndarray, top_n: int = 5) -> dict[str, object]:
    return {
        "most_likely": get_top_scorelines(scoreline_matrix, 1)[0],
        "most_likely_home_win": _best_matching(scoreline_matrix, lambda home, away: home > away),
        "most_likely_draw": _best_matching(scoreline_matrix, lambda home, away: home == away),
        "most_likely_away_win": _best_matching(scoreline_matrix, lambda home, away: home < away),
        "top_scorelines": get_top_scorelines(scoreline_matrix, top_n),
    }


def estimate_scorelines(
    match_features: Mapping[str, object],
    model_probabilities: np.ndarray | list[float],
    max_goals: int = 6,
    league_home_goals: float = 1.45,
    league_away_goals: float = 1.15,
) -> dict[str, object]:
    home_expected, away_expected = estimate_expected_goals(
        match_features,
        model_probabilities,
        league_home_goals=league_home_goals,
        league_away_goals=league_away_goals,
    )
    raw_matrix = calculate_scoreline_probabilities(home_expected, away_expected, max_goals=max_goals)
    probabilities = np.asarray(model_probabilities, dtype=float)
    probabilities = probabilities / probabilities.sum() if probabilities.sum() else np.array([1 / 3, 1 / 3, 1 / 3])
    aligned_matrix = align_scorelines_to_1x2(raw_matrix, probabilities[0], probabilities[1], probabilities[2])
    summary = summarize_scorelines(aligned_matrix)
    predicted_outcome_index = int(np.argmax(probabilities))
    predicted_outcome_scoreline = [
        summary["most_likely_home_win"],
        summary["most_likely_draw"],
        summary["most_likely_away_win"],
    ][predicted_outcome_index]
    return {
        "expected_home_goals": home_expected,
        "expected_away_goals": away_expected,
        "scoreline_matrix": aligned_matrix,
        "predicted_outcome_index": predicted_outcome_index,
        "most_likely_predicted_outcome": predicted_outcome_scoreline,
        **summary,
    }
