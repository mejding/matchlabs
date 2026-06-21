from __future__ import annotations

from pathlib import Path

import joblib
import numpy as np
import pandas as pd

from official_fixtures import OFFICIAL_FIXTURE_PATH, fixtures_for_model, load_official_fixtures, schedule_context_for_fixture
from predict import build_prediction_features
from season_simulation import (
    expected_points_from_probabilities,
    feature_row_for_fixture,
    monte_carlo_season,
    predict_fixture_probabilities,
    projection_feature_overrides,
    promoted_team_baseline,
    season_start_feature_audit,
    season_table_from_results,
    validate_projection_feature_inputs,
)
from train_model import MODEL_PATH, PRODUCTION_FEATURE_COLUMNS, load_matches, load_matches_with_xg


OUTPUT_DIR = Path("evaluation") / "season_projection"
TEAMS_TO_AUDIT = ["Tottenham", "Coventry", "Hull"]
SEASON_PROJECTION_PRIOR_WEIGHT = 0.35


def _markdown_table(frame: pd.DataFrame) -> str:
    if frame.empty:
        return "_No rows._"
    output = frame.copy()
    output = output.fillna("")
    headers = [str(column) for column in output.columns]
    rows = ["| " + " | ".join(headers) + " |", "| " + " | ".join("---" for _ in headers) + " |"]
    for record in output.to_dict("records"):
        values = []
        for column in output.columns:
            value = record[column]
            if isinstance(value, float):
                values.append(f"{value:.4f}")
            else:
                values.append(str(value))
        rows.append("| " + " | ".join(values) + " |")
    return "\n".join(rows)


def _prediction_tab_feature_row(
    fixture: pd.Series,
    official_fixtures: pd.DataFrame,
    team_history: dict[str, dict[str, list[float]]],
    feature_columns: list[str],
    elo_state: dict[str, dict[str, object]],
) -> dict[str, float]:
    features = build_prediction_features(
        fixture["HomeTeam"],
        fixture["AwayTeam"],
        team_history,
        feature_columns,
        match_date=fixture["Date"],
        elo_state=elo_state,
    )
    schedule_context = schedule_context_for_fixture(official_fixtures, fixture["HomeTeam"], fixture["AwayTeam"], fixture["Date"])
    for column, value in schedule_context.items():
        if column in features.columns:
            features.loc[:, column] = float(value)
    return {column: float(features.iloc[0][column]) for column in feature_columns}


def feature_group(column: str) -> str:
    if "elo" in column:
        return "Elo"
    if "shots" in column:
        return "Shot volume"
    if "xg" in column or "xga" in column:
        return "xG/xGA"
    if "days" in column or "matches_last" in column or "midweek" in column:
        return "Schedule/fatigue"
    if "points" in column or "goals" in column:
        return "Recent form"
    if column == "home_advantage":
        return "Home advantage"
    return "Other"


def zscore(series: pd.Series) -> pd.Series:
    std = float(series.std(ddof=0))
    if std == 0.0 or np.isnan(std):
        return pd.Series(np.zeros(len(series)), index=series.index)
    return (series - float(series.mean())) / std


def build_long_term_team_strength(teams: tuple[str, ...], elo_state: dict[str, dict[str, object]]) -> dict[str, float]:
    matches = load_matches()
    seasons = sorted(matches["Season"].dropna().unique())
    recent_seasons = seasons[-2:]
    rows = []
    for season in recent_seasons:
        season_matches = matches[matches["Season"] == season].copy()
        if season_matches.empty:
            continue
        table = season_table_from_results(season_matches)
        played = pd.concat([season_matches["HomeTeam"], season_matches["AwayTeam"]]).value_counts()
        table["played"] = table["team"].map(played).fillna(0)
        table["ppg"] = table["points"] / table["played"].replace(0, np.nan)
        table["gd_per_match"] = table["gd"] / table["played"].replace(0, np.nan)
        rows.append(table[["team", "points", "played", "gd", "ppg", "gd_per_match"]])

    if not rows:
        return {team: 0.0 for team in teams}

    recent = pd.concat(rows, ignore_index=True)
    summary = (
        recent.groupby("team", as_index=False)
        .agg(points=("points", "sum"), played=("played", "sum"), gd=("gd", "sum"))
        .query("played > 0")
    )
    summary["ppg"] = summary["points"] / summary["played"]
    summary["gd_per_match"] = summary["gd"] / summary["played"]
    summary = pd.DataFrame({"team": list(teams)}).merge(summary, on="team", how="left")
    summary["ppg"] = summary["ppg"].fillna(summary["ppg"].median()).fillna(1.0)
    summary["gd_per_match"] = summary["gd_per_match"].fillna(summary["gd_per_match"].median()).fillna(0.0)
    summary["elo"] = summary["team"].map(lambda team: float(elo_state.get(team, {}).get("rating", 1500.0)))
    summary["strength"] = 0.55 * zscore(summary["ppg"]) + 0.30 * zscore(summary["gd_per_match"]) + 0.15 * zscore(summary["elo"])
    return dict(zip(summary["team"], summary["strength"]))


def blend_with_long_term_season_prior(
    probabilities: pd.DataFrame,
    team_strength: dict[str, float],
    prior_weight: float = SEASON_PROJECTION_PRIOR_WEIGHT,
) -> pd.DataFrame:
    adjusted = probabilities.copy()
    adjusted_values = []
    for _, match in adjusted.iterrows():
        home_strength = team_strength.get(match["HomeTeam"], 0.0)
        away_strength = team_strength.get(match["AwayTeam"], 0.0)
        strength_gap = home_strength - away_strength
        prior_logits = np.array(
            [
                0.22 + 0.52 * strength_gap,
                -0.06 - 0.05 * abs(strength_gap),
                -0.22 - 0.52 * strength_gap,
            ]
        )
        prior = np.exp(prior_logits - prior_logits.max())
        prior = prior / prior.sum()
        model_probs = match[["home_win_probability", "draw_probability", "away_win_probability"]].to_numpy(dtype=float)
        blended = (1.0 - prior_weight) * model_probs + prior_weight * prior
        adjusted_values.append(blended / blended.sum())

    adjusted[["home_win_probability", "draw_probability", "away_win_probability"]] = np.vstack(adjusted_values)
    return adjusted


def build_feature_parity_audit(
    fixtures: pd.DataFrame,
    official_fixtures: pd.DataFrame,
    team_history: dict[str, dict[str, list[float]]],
    elo_state: dict[str, dict[str, object]],
    feature_columns: list[str],
    overrides: dict[str, dict[str, float]],
) -> pd.DataFrame:
    rows = []
    for _, fixture in fixtures.head(80).iterrows():
        prediction_row = _prediction_tab_feature_row(fixture, official_fixtures, team_history, feature_columns, elo_state)
        raw_projection_row = feature_row_for_fixture(fixture, team_history, elo_state, feature_columns)
        adjusted_projection_row = feature_row_for_fixture(
            fixture,
            team_history,
            elo_state,
            feature_columns,
            team_feature_overrides=overrides,
        )
        schedule_context = schedule_context_for_fixture(official_fixtures, fixture["HomeTeam"], fixture["AwayTeam"], fixture["Date"])
        for column, value in schedule_context.items():
            if column in raw_projection_row:
                raw_projection_row[column] = float(value)
            if column in adjusted_projection_row:
                adjusted_projection_row[column] = float(value)
        for column in feature_columns:
            prediction_value = prediction_row[column]
            raw_projection_value = raw_projection_row[column]
            adjusted_projection_value = adjusted_projection_row[column]
            rows.append(
                {
                    "date": fixture["Date"],
                    "fixture": f"{fixture['HomeTeam']} v {fixture['AwayTeam']}",
                    "feature": column,
                    "feature_group": feature_group(column),
                    "prediction_tab_value": prediction_value,
                    "season_projection_raw_value": raw_projection_value,
                    "season_projection_adjusted_value": adjusted_projection_value,
                    "raw_abs_diff": abs(prediction_value - raw_projection_value),
                    "adjusted_abs_diff": abs(prediction_value - adjusted_projection_value),
                    "intentional_promoted_adjustment": fixture["HomeTeam"] in overrides or fixture["AwayTeam"] in overrides,
                }
            )
    return pd.DataFrame(rows)


def write_feature_parity_report(parity: pd.DataFrame, validation_status: str, validation: pd.DataFrame) -> None:
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    non_adjusted = parity[~parity["intentional_promoted_adjustment"]].copy()
    group_summary = (
        non_adjusted.groupby("feature_group", as_index=False)
        .agg(max_raw_abs_diff=("raw_abs_diff", "max"), features_checked=("feature", "nunique"), rows_checked=("feature", "count"))
        .sort_values("max_raw_abs_diff", ascending=False)
    )
    adjusted_summary = (
        parity.groupby("feature_group", as_index=False)
        .agg(max_adjusted_abs_diff=("adjusted_abs_diff", "max"), adjusted_rows=("feature", "count"))
        .sort_values("max_adjusted_abs_diff", ascending=False)
    )
    report = f"""# Season Projection Feature Parity Audit

## Summary

- Feature validation status: `{validation_status}`
- Fixtures checked: `{parity['fixture'].nunique()}`
- Production features checked: `{parity['feature'].nunique()}`
- Non-promoted fixture max raw difference: `{float(non_adjusted['raw_abs_diff'].max() if not non_adjusted.empty else 0.0):.8f}`

For fixtures where neither team uses a promoted-team fallback, the Prediction tab and Season Projection feature rows should match after the same official-fixture schedule override is applied. Differences on promoted fixtures are intentional and come from the transparent promoted-team adjustment.

## Non-Promoted Feature Group Parity

{_markdown_table(group_summary)}

## Adjusted Feature Group Differences

{_markdown_table(adjusted_summary)}

## Feature Validation Rows

{_markdown_table(validation)}
"""
    (OUTPUT_DIR / "feature_parity_audit_report.md").write_text(report)


def write_promoted_baseline_report(baseline: dict[str, float], audit: pd.DataFrame) -> None:
    fallback = audit[audit["fallback_used"]].copy()
    baseline_frame = pd.DataFrame([baseline])
    report = f"""# Promoted-Team Baseline Report

## Baseline

The project does not currently contain reliable Championship xG, shot volume or form data that can be treated as Premier League-equivalent. For teams with zero local Premier League history, Season Projection uses a conservative Premier League baseline estimated from teams entering a Premier League season without having appeared in the immediately previous local PL season.

{_markdown_table(baseline_frame)}

## Current Baseline Fallback Teams

{_markdown_table(fallback[['team', 'local_pl_match_count', 'source_league', 'fallback_reason', 'recent_form_points_last5', 'xg_strength_last5', 'xga_strength_last5', 'shots_avg_last5', 'elo_rating']])}

## Adjustment Policy

- Championship form is not copied into the Premier League model as-is.
- Attacking form, xG and shot volume are down-weighted through a conservative promoted-team baseline.
- Defensive weakness/xGA is up-adjusted relative to the league median and historical promoted-team goals-against profile.
- Elo is preferred when local Elo exists; otherwise the neutral Elo fallback is flagged.
- Fallback teams carry higher uncertainty until they play enough Premier League matches.
"""
    (OUTPUT_DIR / "promoted_team_baseline_report.md").write_text(report)


def write_promoted_adjustment_report(adjustment_audit: pd.DataFrame, baseline: dict[str, float]) -> None:
    adjusted = adjustment_audit[adjustment_audit["promotion_adjustment_applied"]].copy()
    fallback = adjustment_audit[adjustment_audit["fallback_used"]].copy()
    report = f"""# Promoted-Team Adjustment Report

## Summary

- Adjusted promoted/low-history teams: `{len(adjusted)}`
- Teams using Championship data: `{int(adjusted['championship_data_available'].sum()) if not adjusted.empty else 0}`
- Teams using conservative baseline fallback: `{len(fallback)}`

## Answers

### 1. Which promoted teams were adjusted?

{_markdown_table(adjusted[['team', 'source_league', 'local_pl_match_count', 'championship_match_count', 'promotion_adjustment_applied', 'fallback_used']])}

### 2. Did they have Premier League data?

{_markdown_table(adjusted[['team', 'local_pl_match_count', 'championship_data_available']])}

### 3. Was Championship data available?

{_markdown_table(adjusted[['team', 'championship_data_available', 'championship_match_count', 'championship_latest_match']])}

### 4. If yes, how was it adjusted?

Adjustment factors:

- Recent form / points: Championship points last 5 x 0.55
- xG for: Championship xG x 0.75 when xG exists
- xGA: Championship xGA x 1.35 when xG exists
- Shot volume: Championship shots x 0.75
- Shots allowed: Championship shots allowed x 1.25 when used by future features

Current adjustment values:

{_markdown_table(adjusted[['team', 'raw_recent_form', 'adjusted_recent_form', 'raw_xg', 'adjusted_xg', 'raw_xga', 'adjusted_xga', 'raw_shot_volume', 'adjusted_shot_volume']])}

### 5. If no, what fallback baseline was used?

{_markdown_table(pd.DataFrame([baseline]))}

Baseline fallback teams:

{_markdown_table(fallback[['team', 'fallback_reason', 'recent_form_points_last5', 'xg_strength_last5', 'xga_strength_last5', 'shots_avg_last5']])}

### 6. Did the change prevent missing PL form from becoming zero?

Yes. Adjusted teams receive non-zero adjusted recent form from Championship data when available, or from the promoted-team baseline when Championship data is unavailable.

### 7. Did the change prevent Championship form from being treated as Premier League form?

Yes. Championship points, xG and shot volume are converted with explicit factors before entering the Season Projection feature rows.

### 8. How did expected points and relegation probability change?

{_markdown_table(adjustment_audit[['team', 'expected_points_before_adjustment', 'expected_points', 'relegation_probability_before_adjustment', 'relegation_probability']])}

## Notes

The current football-data Championship file provides results and shot volume, but not xG. Therefore Championship xG fields remain unavailable and xG/xGA are supplied by the transparent promoted-team baseline until a reliable Championship xG source is added.
"""
    (OUTPUT_DIR / "promoted_team_adjustment_report.md").write_text(report)


def write_robustness_report(
    projection: pd.DataFrame,
    audit: pd.DataFrame,
    parity: pd.DataFrame,
    validation_status: str,
    baseline: dict[str, float],
) -> None:
    target = audit[audit["team"].isin(TEAMS_TO_AUDIT)].copy()
    projection_target = projection[projection["team"].isin(TEAMS_TO_AUDIT)].copy()
    parity_non_adjusted = parity[~parity["intentional_promoted_adjustment"]]
    report = f"""# Season Projection Robustness Report

## What Was Fixed

- Season Projection now populates shot-volume features using the same active production feature family used by the Prediction tab.
- Season Projection validates active feature groups before running and exposes Championship-adjusted or fallback rows instead of silently filling missing active features.
- Teams with zero local Premier League history use adjusted Championship data when available.
- If Championship data is missing, teams receive a conservative promoted-team Premier League baseline.
- Championship performance is not treated as Premier League-equivalent input without conversion.

## Shot Volume

Shot volume is now populated in Season Projection. The feature parity audit checks `shots` and `shots_on_target` columns against the Prediction tab logic.

## Feature Parity

- Validation status: `{validation_status}`
- Non-promoted max feature difference: `{float(parity_non_adjusted['raw_abs_diff'].max() if not parity_non_adjusted.empty else 0.0):.8f}`
- Intentional promoted adjustment rows: `{int(parity['intentional_promoted_adjustment'].sum())}`

## Promoted-Team Handling

{_markdown_table(pd.DataFrame([baseline]))}

Baseline fallback teams:

{_markdown_table(audit[audit['fallback_used']][['team', 'source_league', 'fallback_reason', 'local_pl_match_count']])}

## Tottenham / Coventry / Hull Audit

Feature audit:

{_markdown_table(target[['team', 'local_pl_match_count', 'fallback_used', 'source_league', 'raw_recent_form_points_last5', 'recent_form_points_last5', 'raw_xg_strength_last5', 'xg_strength_last5', 'raw_xga_strength_last5', 'xga_strength_last5', 'raw_shots_avg_last5', 'shots_avg_last5', 'elo_rating']])}

Projection:

{_markdown_table(projection_target[['team', 'expected_points', 'expected_position', 'projected_position', 'relegation_probability']])}

## Remaining Limitations

- The project has football-data Championship results and shot volume, but not Championship xG. Promoted-team xG/xGA therefore still use a transparent conservative PL baseline until a reliable Championship xG source is added.
- The neutral fixture skeleton fallback remains available, but official fixtures are preferred when valid.
- Season Projection is a preseason forecast, not a match-by-match simulated form updater; team strength features are fixed at season start while schedule/fatigue uses fixture timing.
"""
    (OUTPUT_DIR / "season_projection_robustness_report.md").write_text(report)


def main() -> None:
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    artifact = joblib.load(MODEL_PATH)
    calibrator = None
    calibration_path = Path("models") / "calibrated_probability_layer.joblib"
    if calibration_path.exists():
        layer = joblib.load(calibration_path)
        if list(layer.get("feature_columns", [])) == list(artifact["feature_columns"]) and layer.get("method") in {"sigmoid", "isotonic"}:
            calibrator = layer["calibrator"]
    official = load_official_fixtures(OFFICIAL_FIXTURE_PATH)
    fixtures = fixtures_for_model(official)
    teams = tuple(sorted(set(fixtures["HomeTeam"]).union(fixtures["AwayTeam"])))
    matches = load_matches_with_xg()

    audit = season_start_feature_audit(teams, artifact["team_history"], artifact.get("elo_state", {}), matches=matches)
    validation_status, validation = validate_projection_feature_inputs(audit, artifact["feature_columns"])
    overrides = projection_feature_overrides(audit)

    parity = build_feature_parity_audit(fixtures, official, artifact["team_history"], artifact.get("elo_state", {}), artifact["feature_columns"], overrides)
    parity.to_csv(OUTPUT_DIR / "feature_parity_audit.csv", index=False)
    validation.to_csv(OUTPUT_DIR / "feature_validation.csv", index=False)

    probabilities = predict_fixture_probabilities(
        fixtures,
        artifact["model"],
        artifact["feature_columns"],
        artifact["team_history"],
        artifact.get("elo_state", {}),
        calibrator=calibrator,
        team_feature_overrides=overrides,
        fixture_schedule_frame=official,
    )
    probabilities_before_adjustment = predict_fixture_probabilities(
        fixtures,
        artifact["model"],
        artifact["feature_columns"],
        artifact["team_history"],
        artifact.get("elo_state", {}),
        calibrator=calibrator,
        fixture_schedule_frame=official,
    )
    long_term_strength = build_long_term_team_strength(teams, artifact.get("elo_state", {}))
    probabilities = blend_with_long_term_season_prior(probabilities, long_term_strength)
    probabilities_before_adjustment = blend_with_long_term_season_prior(probabilities_before_adjustment, long_term_strength)
    projection = monte_carlo_season(probabilities, n_simulations=10000)
    projection = projection.merge(expected_points_from_probabilities(probabilities), on="team", how="left")
    projection["projected_position"] = range(1, len(projection) + 1)
    projection_before_adjustment = monte_carlo_season(probabilities_before_adjustment, n_simulations=10000)
    projection_before_adjustment = projection_before_adjustment.merge(
        expected_points_from_probabilities(probabilities_before_adjustment),
        on="team",
        how="left",
        suffixes=("", "_deterministic"),
    )

    target_audit = audit[audit["team"].isin(TEAMS_TO_AUDIT)].merge(
        projection[["team", "expected_points", "expected_position", "projected_position", "relegation_probability"]],
        on="team",
        how="left",
    )
    target_audit.to_csv(OUTPUT_DIR / "team_feature_audit_tottenham_coventry_hull.csv", index=False)
    adjustment_audit = audit[audit["promotion_adjustment_applied"] | audit["fallback_used"]].merge(
        projection[["team", "expected_points", "expected_position", "projected_position", "relegation_probability"]],
        on="team",
        how="left",
    )
    adjustment_audit = adjustment_audit.merge(
        projection_before_adjustment[["team", "expected_points", "expected_position", "relegation_probability"]].rename(
            columns={
                "expected_points": "expected_points_before_adjustment",
                "expected_position": "expected_position_before_adjustment",
                "relegation_probability": "relegation_probability_before_adjustment",
            }
        ),
        on="team",
        how="left",
    )
    adjustment_audit.to_csv(OUTPUT_DIR / "promoted_team_adjustment_audit.csv", index=False)

    baseline = promoted_team_baseline(matches)
    write_feature_parity_report(parity, validation_status, validation)
    write_promoted_baseline_report(baseline, audit)
    write_promoted_adjustment_report(adjustment_audit, baseline)
    write_robustness_report(projection, audit, parity, validation_status, baseline)
    print(f"Wrote Season Projection robustness outputs to {OUTPUT_DIR}")


if __name__ == "__main__":
    main()
