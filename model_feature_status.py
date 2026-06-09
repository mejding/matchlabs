from __future__ import annotations

from dataclasses import dataclass
from typing import Literal


FeatureStatus = Literal["Active", "Candidate", "Tested - Not adopted", "Research", "Missing", "Benchmark only"]


@dataclass(frozen=True)
class FeatureStatusEntry:
    status: FeatureStatus
    used_in_production: bool
    short_description: str
    evidence: str
    production_columns: tuple[str, ...] = ()


FEATURE_STATUS: dict[str, FeatureStatusEntry] = {
    "Recent form": FeatureStatusEntry(
        status="Active",
        used_in_production=True,
        short_description="Points and goals from each team's latest five known matches.",
        evidence="Present in models/football_model.joblib as team points last 5 and goals scored averages.",
        production_columns=(
            "home_team_points_last_5",
            "away_team_points_last_5",
            "home_goals_scored_avg",
            "away_goals_scored_avg",
        ),
    ),
    "Home advantage": FeatureStatusEntry(
        status="Active",
        used_in_production=True,
        short_description="A home-team indicator that lets the model learn the historical home advantage.",
        evidence="Present in models/football_model.joblib as home_advantage.",
        production_columns=("home_advantage",),
    ),
    "xG strength": FeatureStatusEntry(
        status="Active",
        used_in_production=True,
        short_description="Rolling xG, xGA and xG differential from Understat historical data.",
        evidence="Present in models/football_model.joblib as home/away xG, xGA and xG differential columns.",
        production_columns=(
            "home_xg_avg",
            "away_xg_avg",
            "home_xga_avg",
            "away_xga_avg",
            "home_xg_diff",
            "away_xg_diff",
        ),
    ),
    "Schedule and fatigue": FeatureStatusEntry(
        status="Active",
        used_in_production=True,
        short_description="Rest days, days since last match, recent match count and midweek-match indicators.",
        evidence="Present in models/football_model.joblib as rest and last-14-days scheduling columns.",
        production_columns=(
            "home_days_rest",
            "away_days_rest",
            "home_matches_last_14_days",
            "away_matches_last_14_days",
            "home_had_midweek_match",
            "away_had_midweek_match",
            "home_days_since_last_match",
            "away_days_since_last_match",
        ),
    ),
    "Elo rating": FeatureStatusEntry(
        status="Active",
        used_in_production=True,
        short_description="Chronological team-strength rating and Elo trend features.",
        evidence="Elo was promoted after Sprint 4B and is present in models/football_model.joblib.",
        production_columns=(
            "home_elo",
            "away_elo",
            "elo_difference",
            "elo_ratio",
            "elo_gap_bucket",
            "elo_recent_change",
            "home_elo_trend",
            "away_elo_trend",
            "rolling_elo_form",
        ),
    ),
    "Shot volume": FeatureStatusEntry(
        status="Active",
        used_in_production=True,
        short_description="Rolling shots and shots-on-target averages over last 5, last 10 and current season.",
        evidence="Activated after shot_efficiency_report.md and production retrain improved Log Loss and Brier.",
        production_columns=(
            "home_shots_avg_last5",
            "away_shots_avg_last5",
            "home_shots_on_target_avg_last5",
            "away_shots_on_target_avg_last5",
            "home_shots_avg_last10",
            "away_shots_avg_last10",
            "home_shots_on_target_avg_last10",
            "away_shots_on_target_avg_last10",
            "home_shots_avg_season",
            "away_shots_avg_season",
            "home_shots_on_target_avg_season",
            "away_shots_on_target_avg_season",
        ),
    ),
    "Calibrated probabilities": FeatureStatusEntry(
        status="Active",
        used_in_production=True,
        short_description="Displayed probabilities are adjusted by the saved calibration layer when it improves validation metrics.",
        evidence="models/calibrated_probability_layer.joblib is loaded by app.py when its feature list matches the production model.",
    ),
    "Market odds": FeatureStatusEntry(
        status="Benchmark only",
        used_in_production=False,
        short_description="Bookmaker odds are used for comparison and fair-odds context, not as model inputs.",
        evidence="market_timing_audit_report.md keeps odds out of production because timing may reflect closing prices.",
    ),
    "Opponent-adjusted xG": FeatureStatusEntry(
        status="Tested - Not adopted",
        used_in_production=False,
        short_description="Chronological xG attack and defense ratings adjusted for opponent strength.",
        evidence="rolling_validation_report.md shows the ratings candidate did not improve average rolling Log Loss/Brier versus production.",
    ),
    "Head-to-head": FeatureStatusEntry(
        status="Tested - Not adopted",
        used_in_production=False,
        short_description="Historical meetings were tested as trained features but did not beat the production baseline overall.",
        evidence="head_to_head_intelligence_report.md keeps H2H research-only despite some draw-metric improvement.",
    ),
    "Manager consistency": FeatureStatusEntry(
        status="Tested - Not adopted",
        used_in_production=False,
        short_description="Manager tenure, continuity and performance features were tested on cached FBref manager rows.",
        evidence="manager_consistency_report.md shows worse Log Loss, Brier and ECE than production.",
    ),
    "Lineup stability": FeatureStatusEntry(
        status="Research",
        used_in_production=False,
        short_description="Lineup continuity and familiarity features exist but are not active.",
        evidence="lineup_stability_report.md shows worse out-of-sample Log Loss and Brier than production.",
    ),
    "Injuries and suspensions": FeatureStatusEntry(
        status="Missing",
        used_in_production=False,
        short_description="Injury feature templates exist, but reliable historical injury rows are not available locally.",
        evidence="injury_data_quality_report.md and injury_engine_report.md say injury features should not be activated.",
    ),
    "Tactical intelligence": FeatureStatusEntry(
        status="Research",
        used_in_production=False,
        short_description="Advanced possession, passing, pressing and matchup features are incomplete or not validated for production.",
        evidence="tactical_intelligence_report.md says only limited shots-derived tactical data is available; broader tactics stay research-only.",
    ),
    "Venue-specific form": FeatureStatusEntry(
        status="Tested - Not adopted",
        used_in_production=False,
        short_description="Home-only and away-only rolling form/xG features were tested.",
        evidence="venue_specific_features_report.md says the venue-specific set did not improve both Log Loss and Brier robustly.",
    ),
    "Shot efficiency": FeatureStatusEntry(
        status="Tested - Not adopted",
        used_in_production=False,
        short_description="Shot accuracy, goals per shot and goals-minus-xG were tested but not activated.",
        evidence="shot_efficiency_report.md keeps finishing-efficiency and goals-minus-xG research-only/noisy.",
    ),
}


def active_feature_statuses(feature_columns: list[str]) -> dict[str, FeatureStatusEntry]:
    feature_set = set(feature_columns)
    return {
        name: entry
        for name, entry in FEATURE_STATUS.items()
        if entry.used_in_production
        and (not entry.production_columns or set(entry.production_columns).issubset(feature_set))
    }


def inactive_feature_statuses() -> dict[str, FeatureStatusEntry]:
    return {name: entry for name, entry in FEATURE_STATUS.items() if not entry.used_in_production}


def status_tone(status: str) -> str:
    if status == "Active":
        return "good"
    if status in {"Candidate", "Benchmark only", "Research"}:
        return "warn"
    return "bad"


def validate_active_features(feature_columns: list[str]) -> list[str]:
    feature_set = set(feature_columns)
    errors: list[str] = []
    for name, entry in FEATURE_STATUS.items():
        if entry.status != "Active":
            continue
        missing = sorted(set(entry.production_columns) - feature_set)
        if entry.used_in_production and missing:
            errors.append(f"{name} is marked Active but missing production columns: {', '.join(missing)}")
        if not entry.used_in_production:
            errors.append(f"{name} is marked Active but used_in_production is false.")
    return errors
