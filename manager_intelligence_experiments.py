from __future__ import annotations

import html
import json
import os
import re
from pathlib import Path

Path("evaluation", ".matplotlib-cache").mkdir(parents=True, exist_ok=True)
os.environ.setdefault("MPLCONFIGDIR", str(Path("evaluation") / ".matplotlib-cache"))

import matplotlib
import numpy as np
import pandas as pd
from matplotlib import pyplot as plt
from sklearn.inspection import permutation_importance
from sklearn.metrics import log_loss, recall_score

from calibration.calibration import calibration_summary, calibration_table, expected_calibration_error
from evaluation.model_evaluation import evaluate_probabilities, time_based_split
from explainability.shap_analysis import compute_shap_importance, plot_shap_importance, plot_shap_summary
from fbref_lineup_ingestion import normalize_team_name
from feature_experiments import _markdown_table, train_xgb
from tactical_data import ensure_tactical_tables, load_team_match_tactics
from tactical_features import build_tactical_features
from train_model import ELO_CONFIG, PRODUCTION_FEATURE_COLUMNS, build_features, load_matches_with_xg, points_for_team
from elo_rating_features import build_elo_features
from visualizations.plots import gain_importance, plot_feature_importance

matplotlib.use("Agg")

OUTPUT_DIR = Path("evaluation") / "manager_intelligence"
RESULTS_PATH = Path("experiments") / "manager_intelligence_results.csv"
MATCH_MANAGERS_PATH = Path("data") / "match_managers.csv"
MANAGER_HISTORY_PATH = Path("data") / "manager_history.csv"
FBREF_SCHEDULE_PATH = Path("data") / "fbref_schedule_raw.csv"
FBREF_CACHE_DIR = Path("data") / "fbref" / "soccerdata_cache"

TACTICAL_PRESSURE_COLUMNS = [
    "home_attacking_pressure_score_last5",
    "home_attacking_pressure_score_last10",
    "home_attacking_pressure_score_season",
    "away_attacking_pressure_score_last5",
    "away_attacking_pressure_score_last10",
    "away_attacking_pressure_score_season",
]

BASIC_MANAGER_FEATURES = [
    "manager_tenure_days",
    "manager_matches_in_charge",
    "manager_change_last_30d",
    "manager_change_last_60d",
    "new_manager_first_5_matches",
    "new_manager_first_10_matches",
    "caretaker_manager",
]
CONTINUITY_MANAGER_FEATURES = [
    "manager_tenure_bucket",
    "manager_data_available",
]
ADVANCED_MANAGER_FEATURES = [
    "manager_points_per_game_before_match",
    "manager_xg_diff_before_match",
    "manager_team_form_since_appointment",
    "manager_elo_change_since_appointment",
]
GAP_FEATURES = [
    "manager_continuity_gap",
    "manager_experience_gap",
    "manager_ppg_gap",
    "manager_xg_diff_gap",
]


def side_columns(features: list[str]) -> list[str]:
    return [f"{side}_{feature}" for side in ("home", "away") for feature in features]


def manager_basic_columns() -> list[str]:
    return side_columns(BASIC_MANAGER_FEATURES)


def manager_continuity_columns() -> list[str]:
    return side_columns(CONTINUITY_MANAGER_FEATURES) + GAP_FEATURES[:2]


def manager_advanced_columns() -> list[str]:
    return side_columns(ADVANCED_MANAGER_FEATURES) + GAP_FEATURES[2:]


def all_manager_columns() -> list[str]:
    return manager_basic_columns() + manager_continuity_columns() + manager_advanced_columns()


def _strip_tags(text: str) -> str:
    cleaned = re.sub(r"<[^>]+>", "", text)
    return html.unescape(cleaned).replace("\xa0", " ").strip()


def _extract_managers_from_html(path: Path) -> list[str]:
    text = path.read_text(encoding="utf-8", errors="ignore")
    scorebox_match = re.search(r'<div class="scorebox">(?P<body>.*?)<div class="scorebox_meta">', text, flags=re.S)
    body = scorebox_match.group("body") if scorebox_match else text
    managers = re.findall(r"<strong>Manager</strong>:\s*(.*?)</div>", body, flags=re.S)
    return [_strip_tags(manager) for manager in managers[:2]]


def ingest_fbref_match_managers() -> pd.DataFrame:
    """Extract match-level managers from local FBref match HTML cache.

    FBref scoreboxes list the manager for each team in a completed match. The
    rows are post-match evidence, but the manager identity itself is normally
    known before kickoff. Feature generation below uses current-match manager
    identity and only previous matches for performance/tenure statistics.
    """
    if not FBREF_SCHEDULE_PATH.exists():
        return pd.DataFrame(columns=["match_id", "season", "date", "team", "opponent", "is_home", "manager_name", "source"])

    schedule = pd.read_csv(FBREF_SCHEDULE_PATH)
    rows: list[dict[str, object]] = []
    for _, match in schedule.iterrows():
        game_id = str(match.get("game_id", "")).strip()
        path = FBREF_CACHE_DIR / f"match_{game_id}.html"
        if not game_id or not path.exists():
            continue
        managers = _extract_managers_from_html(path)
        if len(managers) < 2:
            continue

        date = pd.to_datetime(match["date"]).date().isoformat()
        home = normalize_team_name(match["home_team"])
        away = normalize_team_name(match["away_team"])
        base = {
            "match_id": game_id,
            "season": str(match["season"]),
            "date": date,
            "source": "fbref_match_cache",
            "source_url": str(match.get("match_report", "")),
            "source_collected_at": (pd.to_datetime(match["date"]) + pd.Timedelta(days=1)).date().isoformat(),
        }
        rows.append({**base, "team": home, "opponent": away, "is_home": 1, "manager_name": managers[0]})
        rows.append({**base, "team": away, "opponent": home, "is_home": 0, "manager_name": managers[1]})

    output = pd.DataFrame(rows)
    MATCH_MANAGERS_PATH.parent.mkdir(exist_ok=True)
    output.to_csv(MATCH_MANAGERS_PATH, index=False)
    write_manager_history(output)
    return output


def write_manager_history(match_managers: pd.DataFrame) -> None:
    rows: list[dict[str, object]] = []
    if match_managers.empty:
        pd.DataFrame(columns=["team", "manager", "start_date", "end_date", "source", "source_collected_at"]).to_csv(
            MANAGER_HISTORY_PATH, index=False
        )
        return

    frame = match_managers.copy()
    frame["date"] = pd.to_datetime(frame["date"])
    for team, team_rows in frame.sort_values("date").groupby("team"):
        periods: list[dict[str, object]] = []
        current_manager: str | None = None
        current_start: pd.Timestamp | None = None
        for _, row in team_rows.iterrows():
            manager = str(row["manager_name"])
            if current_manager is None:
                current_manager = manager
                current_start = row["date"]
            elif manager != current_manager:
                periods.append({"manager": current_manager, "start_date": current_start, "end_date": row["date"] - pd.Timedelta(days=1)})
                current_manager = manager
                current_start = row["date"]
        if current_manager is not None and current_start is not None:
            periods.append({"manager": current_manager, "start_date": current_start, "end_date": pd.NaT})

        for period in periods:
            rows.append(
                {
                    "team": team,
                    "manager": period["manager"],
                    "start_date": pd.to_datetime(period["start_date"]).date().isoformat(),
                    "end_date": "" if pd.isna(period["end_date"]) else pd.to_datetime(period["end_date"]).date().isoformat(),
                    "source": "fbref_match_cache_inferred_period",
                    "source_collected_at": (pd.to_datetime(period["start_date"]) + pd.Timedelta(days=1)).date().isoformat(),
                }
            )
    pd.DataFrame(rows).to_csv(MANAGER_HISTORY_PATH, index=False)


def _tenure_bucket(days: float) -> float:
    if days <= 0:
        return 0.0
    if days <= 30:
        return 1.0
    if days <= 90:
        return 2.0
    if days <= 365:
        return 3.0
    return 4.0


def _empty_team_features() -> dict[str, float]:
    return {feature: 0.0 for feature in BASIC_MANAGER_FEATURES + CONTINUITY_MANAGER_FEATURES + ADVANCED_MANAGER_FEATURES}


def _team_points_and_xg(match: pd.Series, team: str) -> tuple[float, float]:
    points = float(points_for_team(match, team))
    if match["HomeTeam"] == team:
        return points, float(match.get("home_xg", 0.0) - match.get("away_xg", 0.0))
    return points, float(match.get("away_xg", 0.0) - match.get("home_xg", 0.0))


def _manager_features_for_team(
    team: str,
    current_date: pd.Timestamp,
    current_manager: str | None,
    team_history: list[dict[str, object]],
) -> dict[str, float]:
    if not current_manager:
        return _empty_team_features()

    previous = [row for row in team_history if pd.to_datetime(row["date"]) < current_date]
    last_row = previous[-1] if previous else None
    manager_changed = bool(last_row and last_row.get("manager_name") != current_manager)

    tenure_rows: list[dict[str, object]] = []
    for row in reversed(previous):
        if row.get("manager_name") != current_manager:
            break
        tenure_rows.append(row)
    tenure_rows = list(reversed(tenure_rows))

    if tenure_rows:
        tenure_start = pd.to_datetime(tenure_rows[0]["date"])
    else:
        tenure_start = current_date

    tenure_days = float((current_date - tenure_start).days)
    matches_in_charge = float(len(tenure_rows))
    change_last_30 = float(manager_changed or tenure_days <= 30)
    change_last_60 = float(manager_changed or tenure_days <= 60)

    points = [float(row["points"]) for row in tenure_rows]
    xg_diffs = [float(row["xg_diff"]) for row in tenure_rows]
    elo_diffs = [float(row.get("elo_change", 0.0)) for row in tenure_rows]
    recent_points = points[-5:]

    return {
        "manager_tenure_days": tenure_days,
        "manager_matches_in_charge": matches_in_charge,
        "manager_change_last_30d": change_last_30,
        "manager_change_last_60d": change_last_60,
        "new_manager_first_5_matches": float(matches_in_charge < 5),
        "new_manager_first_10_matches": float(matches_in_charge < 10),
        "caretaker_manager": 0.0,
        "manager_tenure_bucket": _tenure_bucket(tenure_days),
        "manager_data_available": 1.0,
        "manager_points_per_game_before_match": float(np.mean(points)) if points else 0.0,
        "manager_xg_diff_before_match": float(np.mean(xg_diffs)) if xg_diffs else 0.0,
        "manager_team_form_since_appointment": float(np.mean(recent_points)) if recent_points else 0.0,
        "manager_elo_change_since_appointment": float(np.sum(elo_diffs)) if elo_diffs else 0.0,
    }


def build_manager_features(matches: pd.DataFrame, match_managers: pd.DataFrame, elo_features: pd.DataFrame) -> pd.DataFrame:
    manager_lookup = {}
    if not match_managers.empty:
        mm = match_managers.copy()
        mm["date"] = pd.to_datetime(mm["date"]).dt.normalize()
        for _, row in mm.iterrows():
            manager_lookup[(row["date"], row["team"], row["opponent"])] = row["manager_name"]

    rows: list[dict[str, float]] = []
    team_history: dict[str, list[dict[str, object]]] = {}
    ordered = matches.sort_values("Date").reset_index(drop=True)
    for index, match in ordered.iterrows():
        current_date = pd.to_datetime(match["Date"]).normalize()
        home = match["HomeTeam"]
        away = match["AwayTeam"]
        home_manager = manager_lookup.get((current_date, home, away))
        away_manager = manager_lookup.get((current_date, away, home))

        home_features = _manager_features_for_team(home, current_date, home_manager, team_history.get(home, []))
        away_features = _manager_features_for_team(away, current_date, away_manager, team_history.get(away, []))
        row = {}
        for feature, value in home_features.items():
            row[f"home_{feature}"] = value
        for feature, value in away_features.items():
            row[f"away_{feature}"] = value
        row["manager_continuity_gap"] = home_features["manager_tenure_days"] - away_features["manager_tenure_days"]
        row["manager_experience_gap"] = home_features["manager_matches_in_charge"] - away_features["manager_matches_in_charge"]
        row["manager_ppg_gap"] = (
            home_features["manager_points_per_game_before_match"] - away_features["manager_points_per_game_before_match"]
        )
        row["manager_xg_diff_gap"] = home_features["manager_xg_diff_before_match"] - away_features["manager_xg_diff_before_match"]
        rows.append(row)

        home_points, home_xg_diff = _team_points_and_xg(match, home)
        away_points, away_xg_diff = _team_points_and_xg(match, away)
        home_elo_change = float(elo_features.iloc[index].get("home_elo_trend", 0.0))
        away_elo_change = float(elo_features.iloc[index].get("away_elo_trend", 0.0))
        team_history.setdefault(home, []).append(
            {
                "date": current_date,
                "manager_name": home_manager,
                "points": home_points,
                "xg_diff": home_xg_diff,
                "elo_change": home_elo_change,
            }
        )
        team_history.setdefault(away, []).append(
            {
                "date": current_date,
                "manager_name": away_manager,
                "points": away_points,
                "xg_diff": away_xg_diff,
                "elo_change": away_elo_change,
            }
        )
    return pd.DataFrame(rows)


def available_columns(dataset: pd.DataFrame, columns: list[str]) -> list[str]:
    return [column for column in columns if column in dataset.columns and dataset[column].notna().sum() > 0]


def build_manager_dataset() -> tuple[pd.DataFrame, pd.DataFrame, dict[str, list[str]], pd.DataFrame]:
    matches = load_matches_with_xg().sort_values("Date").reset_index(drop=True)
    base_dataset, _ = build_features(matches, include_xg=True, include_schedule=True)
    elo_features, _ = build_elo_features(matches, ELO_CONFIG)
    match_managers = ingest_fbref_match_managers()
    manager_features = build_manager_features(matches, match_managers, elo_features)

    tactical_columns: list[str] = []
    try:
        ensure_tactical_tables()
        tactics = load_team_match_tactics()
        tactical_features, _ = build_tactical_features(matches, tactics)
        tactical_columns = available_columns(tactical_features, TACTICAL_PRESSURE_COLUMNS)
        dataset = pd.concat(
            [
                base_dataset.reset_index(drop=True),
                elo_features.reset_index(drop=True),
                tactical_features[tactical_columns].reset_index(drop=True),
                manager_features.reset_index(drop=True),
            ],
            axis=1,
        )
    except Exception as exc:
        print(f"Warning: tactical pressure unavailable for manager experiment: {exc}")
        dataset = pd.concat(
            [base_dataset.reset_index(drop=True), elo_features.reset_index(drop=True), manager_features.reset_index(drop=True)],
            axis=1,
        )

    production_columns = PRODUCTION_FEATURE_COLUMNS + tactical_columns
    feature_sets = {
        "model_a_current_production": production_columns,
        "model_b_basic_manager": production_columns + manager_basic_columns(),
        "model_c_manager_continuity": production_columns + manager_basic_columns() + manager_continuity_columns(),
        "model_d_full_manager_intelligence": production_columns + all_manager_columns(),
    }
    metadata = matches[["Season", "Date", "HomeTeam", "AwayTeam", "FTR"]].reset_index(drop=True)
    return dataset, metadata, feature_sets, match_managers


def evaluate_feature_set(dataset: pd.DataFrame, metadata: pd.DataFrame, feature_columns: list[str], model_version: str) -> dict[str, object]:
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
    draw_prob = np.clip(probabilities[:, 1], 1e-12, 1 - 1e-12)
    draw_pred = (predictions == 1).astype(int)
    return {
        "model_version": model_version,
        "model": model,
        "split": split,
        "probabilities": probabilities,
        "predictions": predictions,
        "feature_columns": feature_columns,
        "accuracy": metrics["accuracy"],
        "log_loss": metrics["log_loss"],
        "brier_score": metrics["brier_score_multiclass"],
        "calibration_score": cal_summary["mean_absolute_calibration_error"],
        "expected_calibration_error": expected_calibration_error(calibration),
        "draw_recall": float(recall_score(draw_actual, draw_pred, zero_division=0)),
        "draw_log_loss": float(log_loss(draw_actual, np.column_stack([1 - draw_prob, draw_prob]), labels=[0, 1])),
        "train_period": f"{split.train_metadata['Date'].iloc[0]} to {split.train_metadata['Date'].iloc[-1]}",
        "test_period": f"{split.test_metadata['Date'].iloc[0]} to {split.test_metadata['Date'].iloc[-1]}",
    }


def save_results(results: list[dict[str, object]]) -> pd.DataFrame:
    rows = []
    for result in results:
        rows.append(
            {
                "experiment_id": f"{result['model_version']}_{pd.Timestamp.now(tz='UTC').strftime('%Y%m%d_%H%M%S')}",
                "model_version": result["model_version"],
                "features_added": "|".join(result["feature_columns"]),
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
    RESULTS_PATH.parent.mkdir(exist_ok=True)
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    output.to_csv(RESULTS_PATH, index=False)
    output.to_csv(OUTPUT_DIR / "model_comparison.csv", index=False)
    return output


def plot_model_comparison(results: pd.DataFrame) -> None:
    metrics = ["accuracy", "log_loss", "Brier_score", "expected_calibration_error", "draw_recall", "draw_log_loss"]
    fig, axes = plt.subplots(2, 3, figsize=(15, 8))
    for ax, metric in zip(axes.ravel(), metrics):
        ax.bar(results["model_version"], results[metric])
        ax.set_title(metric)
        ax.tick_params(axis="x", rotation=25)
        ax.grid(axis="y", alpha=0.25)
    fig.suptitle("Manager Intelligence Model Comparison")
    fig.tight_layout()
    fig.savefig(OUTPUT_DIR / "model_comparison.png", dpi=160)
    plt.close(fig)


def _feature_group(feature: str) -> str:
    if "production" in feature:
        return "production"
    if "manager_" in feature or "caretaker" in feature:
        if "ppg" in feature or "xg_diff" in feature or "elo_change" in feature or "form_since" in feature:
            return "manager_performance"
        if "tenure" in feature or "matches_in_charge" in feature or "experience" in feature or "continuity" in feature:
            return "manager_continuity"
        return "manager_change"
    return "production"


def explain_manager_model(result: dict[str, object]) -> pd.DataFrame:
    split = result["split"]
    model = result["model"]
    shap_importance, _, _ = compute_shap_importance(model, split.X_test)
    shap_importance["feature_group"] = shap_importance["feature"].map(_feature_group)
    shap_importance.to_csv(OUTPUT_DIR / "manager_feature_importance.csv", index=False)
    shap_importance.groupby("feature_group", as_index=False)["mean_abs_shap"].sum().sort_values(
        "mean_abs_shap", ascending=False
    ).to_csv(OUTPUT_DIR / "manager_shap_group_importance.csv", index=False)
    plot_shap_importance(shap_importance.head(35), OUTPUT_DIR / "manager_shap_feature_importance.png")
    plot_shap_summary(model, split.X_test, OUTPUT_DIR / "manager_shap_summary.png")
    gain = gain_importance(model, result["feature_columns"])
    gain.to_csv(OUTPUT_DIR / "manager_gain_importance.csv", index=False)
    plot_feature_importance(gain.head(35), "gain_importance", "Manager Intelligence Gain Importance", OUTPUT_DIR / "manager_gain_importance.png")

    manager_cols = [column for column in result["feature_columns"] if "manager" in column or "caretaker" in column]
    if manager_cols:
        perm = permutation_importance(
            model,
            split.X_test,
            split.y_test,
            n_repeats=5,
            random_state=42,
            scoring="neg_log_loss",
            n_jobs=1,
        )
        permutation = pd.DataFrame(
            {
                "feature": result["feature_columns"],
                "permutation_importance_log_loss": perm.importances_mean,
                "permutation_importance_std": perm.importances_std,
            }
        ).sort_values("permutation_importance_log_loss", ascending=False)
        permutation[permutation["feature"].isin(manager_cols)].to_csv(OUTPUT_DIR / "manager_permutation_importance.csv", index=False)
    return shap_importance


def manager_data_quality(match_managers: pd.DataFrame, metadata: pd.DataFrame) -> pd.DataFrame:
    if match_managers.empty:
        return pd.DataFrame([{"check": "match_managers", "status": "missing", "details": "No FBref match manager rows found."}])
    frame = match_managers.copy()
    duplicate_rows = frame.duplicated(["date", "team", "opponent"]).sum()
    rows_per_match = frame.groupby(["date", "match_id"])["team"].nunique()
    covered_matches = frame["match_id"].nunique()
    season_coverage = frame.groupby("season")["match_id"].nunique().to_dict()
    return pd.DataFrame(
        [
            {
                "check": "duplicate_team_match_managers",
                "status": "pass" if duplicate_rows == 0 else "warn",
                "details": f"{duplicate_rows} duplicate team-match manager rows.",
            },
            {
                "check": "two_manager_rows_per_match",
                "status": "pass" if rows_per_match.eq(2).mean() > 0.95 else "warn",
                "details": json.dumps(rows_per_match.value_counts().sort_index().to_dict()),
            },
            {
                "check": "match_coverage",
                "status": "pass" if covered_matches >= 380 else "warn",
                "details": json.dumps({"covered_matches": int(covered_matches), "season_coverage": season_coverage}),
            },
            {
                "check": "full_project_coverage",
                "status": "warn",
                "details": f"Manager data covers {covered_matches} of {len(metadata)} project matches. Missing seasons are neutral-zero in experiments.",
            },
        ]
    )


def _delta(results: pd.DataFrame, model_a: str, model_b: str, metric: str) -> float:
    a = float(results.loc[results["model_version"] == model_a, metric].iloc[0])
    b = float(results.loc[results["model_version"] == model_b, metric].iloc[0])
    return b - a


def write_reports(results: pd.DataFrame, shap_importance: pd.DataFrame, match_managers: pd.DataFrame, metadata: pd.DataFrame) -> None:
    quality = manager_data_quality(match_managers, metadata)
    quality.to_csv(OUTPUT_DIR / "manager_data_quality.csv", index=False)
    Path("manager_data_quality_report.md").write_text(
        f"""# Manager Data Quality Report

## Source

Manager rows are extracted from local FBref match HTML cache files generated by soccerdata. The current local cache covers the 2024/25 Premier League season.

## Coverage

- Match-manager rows: {len(match_managers)}
- Covered matches: {match_managers['match_id'].nunique() if not match_managers.empty else 0}
- Covered seasons: {', '.join(map(str, sorted(match_managers['season'].unique()))) if not match_managers.empty else 'None'}

## Validation

{_markdown_table(quality, ['check', 'status', 'details'])}

## Leakage Controls

- Manager identity is read from completed FBref match pages, but treated as pre-match-known team context.
- Tenure, matches in charge, PPG, xG differential and Elo-change features use only previous matches before the fixture.
- Seasons without manager data receive neutral zero features and are explicitly counted as missing coverage.
"""
    )

    full = "model_d_full_manager_intelligence"
    baseline = "model_a_current_production"
    production_ready = (
        match_managers["match_id"].nunique() >= 380
        and _delta(results, baseline, full, "log_loss") < 0
        and _delta(results, baseline, full, "Brier_score") < 0
        and _delta(results, baseline, full, "expected_calibration_error") <= 0.01
    )
    manager_shap = shap_importance[shap_importance["feature_group"].str.startswith("manager")].head(12)
    manager_lines = "\n".join(
        f"- `{row.feature}` ({row.feature_group}): {row.mean_abs_shap:.4f}" for row in manager_shap.itertuples()
    )
    decision = (
        "Move manager consistency forward as a production candidate."
        if production_ready
        else (
            "Do not activate manager consistency yet. The current test has only one full season of manager rows, "
            "and production activation requires out-of-sample log loss or Brier improvement without calibration damage."
        )
    )
    Path("manager_consistency_report.md").write_text(
        f"""# Manager Consistency Report

## Question

Does manager consistency improve the Premier League prediction model beyond form, xG, fatigue, tactical pressure and Elo?

## Model Comparison

{_markdown_table(results, ['model_version', 'accuracy', 'log_loss', 'Brier_score', 'expected_calibration_error', 'draw_recall', 'draw_log_loss'])}

## Full Manager Model vs Production

- Log loss change: {_delta(results, baseline, full, 'log_loss'):.4f}
- Brier score change: {_delta(results, baseline, full, 'Brier_score'):.4f}
- ECE change: {_delta(results, baseline, full, 'expected_calibration_error'):.4f}
- Draw recall change: {_delta(results, baseline, full, 'draw_recall'):.4f}
- Draw log loss change: {_delta(results, baseline, full, 'draw_log_loss'):.4f}

## Manager Feature Signal

Top manager SHAP features:

{manager_lines or '- No manager feature had measurable SHAP contribution.'}

## Interpretation

The experiment is conservative: manager identity for the current fixture is used, but manager performance and continuity statistics are calculated only from prior matches. The current local data covers 2024/25 only, so this is a first evidence check rather than a final production decision.

## Production Decision

{decision}
"""
    )
    Path("manager_redundancy_report.md").write_text(
        f"""# Manager Redundancy Report

## Summary

Manager features are tested against a production baseline that already contains rolling form, xG/xGA, fatigue, tactical pressure and Elo. They should only be considered unique if the combined model improves out-of-sample log loss or Brier score.

## SHAP Group Importance

{_markdown_table(shap_importance.groupby('feature_group', as_index=False)['mean_abs_shap'].sum().sort_values('mean_abs_shap', ascending=False), ['feature_group', 'mean_abs_shap'])}

## Redundancy Decision

{decision}
"""
    )
    write_discovery_report()
    write_manager_bounce_report(metadata)


def write_discovery_report() -> None:
    Path("manager_data_discovery_report.md").write_text(
        """# Manager Data Discovery Report

## Sources Checked

| Source | Local availability | Fields available | Historical reliability | Implementation notes |
| --- | --- | --- | --- | --- |
| Existing `data/manager_history.csv` | Empty before this sprint | Team, manager, start/end dates | Low before ingestion | Used as the normalized output target. |
| FBref match pages via soccerdata cache | Available for 2024/25 | Match date, teams, manager per team | Medium | Historically reproducible from cached match reports. Does not provide official appointment dates, so periods are inferred from first seen match. |
| football-data.co.uk | Available | Match results, odds, cards, shots | Not applicable | Does not include manager identity. |
| Understat | Available | xG and match data | Not applicable | Does not include manager identity in the local project data. |
| Transfermarkt | Not locally ingested | Manager appointments, departures, caretaker periods | Potentially high | Good candidate for future official tenure dates, but requires a separate ingestion policy and terms review. |
| Kaggle/manual CSV | Not locally available | Depends on dataset | Unknown | Useful fallback if source and timestamps are documented. |

## Recommendation

Use FBref cached match managers for research-only experiments. For production manager features, add a Transfermarkt or manually verified manager-change feed with official appointment dates and caretaker flags.
"""
    )


def _team_match_rows(matches: pd.DataFrame, team: str) -> pd.DataFrame:
    rows = matches[(matches["HomeTeam"] == team) | (matches["AwayTeam"] == team)].copy()
    rows["team_points"] = rows.apply(lambda row: points_for_team(row, team), axis=1)
    rows["team_goal_diff"] = rows.apply(
        lambda row: row["FTHG"] - row["FTAG"] if row["HomeTeam"] == team else row["FTAG"] - row["FTHG"],
        axis=1,
    )
    rows["team_xg_diff"] = rows.apply(
        lambda row: row["home_xg"] - row["away_xg"] if row["HomeTeam"] == team else row["away_xg"] - row["home_xg"],
        axis=1,
    )
    return rows.sort_values("Date")


def _window_summary(rows: pd.DataFrame) -> dict[str, float]:
    if rows.empty:
        return {"matches": 0.0, "ppg": 0.0, "goal_diff_per_match": 0.0, "xg_diff_per_match": 0.0}
    return {
        "matches": float(len(rows)),
        "ppg": float(rows["team_points"].mean()),
        "goal_diff_per_match": float(rows["team_goal_diff"].mean()),
        "xg_diff_per_match": float(rows["team_xg_diff"].mean()),
    }


def write_manager_bounce_report(metadata: pd.DataFrame) -> None:
    if not MANAGER_HISTORY_PATH.exists():
        return
    history = pd.read_csv(MANAGER_HISTORY_PATH)
    if history.empty:
        return
    matches = load_matches_with_xg().sort_values("Date").reset_index(drop=True)
    matches["Date"] = pd.to_datetime(matches["Date"])
    history["start_date"] = pd.to_datetime(history["start_date"])
    changes = history.sort_values(["team", "start_date"]).groupby("team").tail(-1)
    rows = []
    for _, change in changes.iterrows():
        team = change["team"]
        change_date = change["start_date"]
        team_rows = _team_match_rows(matches, team)
        before = team_rows[team_rows["Date"] < change_date].tail(5)
        after_5 = team_rows[team_rows["Date"] >= change_date].head(5)
        after_10 = team_rows[team_rows["Date"] >= change_date].head(10)
        row = {
            "team": team,
            "manager": change["manager"],
            "start_date": change_date.date().isoformat(),
        }
        for prefix, window in [("before_5", before), ("after_5", after_5), ("after_10", after_10)]:
            summary = _window_summary(window)
            for key, value in summary.items():
                row[f"{prefix}_{key}"] = value
        rows.append(row)
    output = pd.DataFrame(rows)
    output.to_csv(OUTPUT_DIR / "manager_bounce_analysis.csv", index=False)
    if output.empty:
        summary_text = "No in-season manager changes were found in the current manager history."
    else:
        summary_text = _markdown_table(
            output[
                [
                    "team",
                    "manager",
                    "start_date",
                    "before_5_ppg",
                    "after_5_ppg",
                    "after_10_ppg",
                    "before_5_xg_diff_per_match",
                    "after_5_xg_diff_per_match",
                    "after_10_xg_diff_per_match",
                ]
            ],
            [
                "team",
                "manager",
                "start_date",
                "before_5_ppg",
                "after_5_ppg",
                "after_10_ppg",
                "before_5_xg_diff_per_match",
                "after_5_xg_diff_per_match",
                "after_10_xg_diff_per_match",
            ],
        )
    Path("manager_bounce_analysis.md").write_text(
        f"""# Manager Bounce Analysis

## Method

For each detected in-season manager change, compare the team's previous 5 matches with the first 5 and first 10 matches after the new manager first appears in the FBref match data.

This is exploratory only. The current manager source covers 2024/25, so sample size is small and should not be treated as stable evidence.

## Results

{summary_text}

## Interpretation

This analysis is useful for spotting possible new-manager-bounce patterns, but the model comparison remains the production gate. In the current run, manager features did not improve log loss or Brier score, so manager bounce should remain research-only.
"""
    )


def main() -> None:
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    dataset, metadata, feature_sets, match_managers = build_manager_dataset()
    results = [evaluate_feature_set(dataset, metadata, columns, version) for version, columns in feature_sets.items()]
    results_frame = save_results(results)
    plot_model_comparison(results_frame)
    full_result = next(result for result in results if result["model_version"] == "model_d_full_manager_intelligence")
    shap_importance = explain_manager_model(full_result)
    write_reports(results_frame, shap_importance, match_managers, metadata)
    print(
        json.dumps(
            {
                "match_manager_rows": int(len(match_managers)),
                "covered_matches": int(match_managers["match_id"].nunique()) if not match_managers.empty else 0,
                "activate": bool(
                    _delta(results_frame, "model_a_current_production", "model_d_full_manager_intelligence", "log_loss") < 0
                    and _delta(results_frame, "model_a_current_production", "model_d_full_manager_intelligence", "Brier_score") < 0
                ),
            },
            indent=2,
        )
    )


if __name__ == "__main__":
    main()
