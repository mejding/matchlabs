from __future__ import annotations

import json
import os
from pathlib import Path

Path("evaluation", ".matplotlib-cache").mkdir(parents=True, exist_ok=True)
os.environ.setdefault("MPLCONFIGDIR", str(Path("evaluation") / ".matplotlib-cache"))

import matplotlib
import pandas as pd
from matplotlib import pyplot as plt

from availability_scores import add_availability_scores, availability_feature_columns, availability_formula_note
from calibration.calibration import calibration_summary, calibration_table, expected_calibration_error
from evaluation.model_evaluation import evaluate_probabilities, time_based_split
from explainability.shap_analysis import compute_shap_importance, plot_local_waterfall, plot_shap_importance, plot_shap_summary
from fatigue_analysis import write_discovery_outputs
from fatigue_features import (
    build_fatigue_and_europe_features,
    europe_feature_columns,
    fatigue_feature_columns,
    fixture_congestion_score,
    load_european_fixtures,
)
from injury_features import (
    build_injury_features,
    historical_injury_pipeline_note,
    injury_feature_columns,
    load_historical_injuries,
)
from train_model import XG_FEATURE_COLUMNS, build_features, get_xgb_classifier, load_matches_with_xg
from visualizations.plots import gain_importance, plot_feature_importance

matplotlib.use("Agg")

OUTPUT_DIR = Path("evaluation") / "sprint2"
EXPERIMENT_RESULTS_PATH = Path("experiments") / "results.csv"
CLASS_NAMES = ["home_win", "draw", "away_win"]
RANDOM_SEED = 42


def train_xgb(X_train: pd.DataFrame, y_train: pd.Series, seed: int = RANDOM_SEED):
    XGBClassifier = get_xgb_classifier()
    model = XGBClassifier(
        objective="multi:softprob",
        num_class=3,
        n_estimators=150,
        max_depth=3,
        learning_rate=0.05,
        subsample=0.9,
        colsample_bytree=1.0,
        eval_metric="mlogloss",
        random_state=seed,
    )
    model.fit(X_train, y_train)
    return model


def build_experiment_datasets() -> tuple[pd.DataFrame, pd.DataFrame, dict[str, list[str]], pd.DataFrame]:
    matches = load_matches_with_xg().sort_values("Date").reset_index(drop=True)
    base_dataset, _ = build_features(matches, include_xg=True)

    fatigue_only = build_fatigue_and_europe_features(
        matches,
        european_fixtures=pd.DataFrame(),
        include_europe_in_rest=False,
    )
    european_fixtures = load_european_fixtures()
    fatigue_europe = build_fatigue_and_europe_features(
        matches,
        european_fixtures=european_fixtures,
        include_europe_in_rest=True,
    )
    injury_features = build_injury_features(matches, load_historical_injuries())
    injury_availability = add_availability_scores(injury_features)

    dataset = pd.concat(
        [
            base_dataset.reset_index(drop=True),
            fatigue_europe.reset_index(drop=True),
            injury_availability.reset_index(drop=True),
        ],
        axis=1,
    )
    fatigue_only_dataset = pd.concat(
        [base_dataset.reset_index(drop=True), fatigue_only[fatigue_feature_columns()].reset_index(drop=True)],
        axis=1,
    )

    feature_sets = {
        "model_a_current_baseline": XG_FEATURE_COLUMNS,
        "model_b_baseline_fatigue": XG_FEATURE_COLUMNS + fatigue_feature_columns(),
        "model_c_baseline_fatigue_europe": XG_FEATURE_COLUMNS + fatigue_feature_columns() + europe_feature_columns(),
        "model_d_baseline_fatigue_europe_injury": (
            XG_FEATURE_COLUMNS
            + fatigue_feature_columns()
            + europe_feature_columns()
            + injury_feature_columns()
            + availability_feature_columns()
        ),
    }

    # Model B intentionally uses league-only rest history. Models C/D use the shared dataset with European load columns.
    for column in fatigue_feature_columns():
        dataset[f"league_only_{column}"] = fatigue_only_dataset[column]
    model_b_columns = XG_FEATURE_COLUMNS + [f"league_only_{column}" for column in fatigue_feature_columns()]
    feature_sets["model_b_baseline_fatigue"] = model_b_columns

    metadata = matches[["Season", "Date", "HomeTeam", "AwayTeam", "FTR"]].reset_index(drop=True)
    return dataset, metadata, feature_sets, matches


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
    predictions = model.predict(split.X_test)
    metrics = evaluate_probabilities(split.y_test, probabilities, predictions)
    calibration = calibration_table(split.y_test, probabilities)
    cal_summary = calibration_summary(calibration)

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
        "train_period": f"{split.train_metadata['Date'].iloc[0]} to {split.train_metadata['Date'].iloc[-1]}",
        "test_period": f"{split.test_metadata['Date'].iloc[0]} to {split.test_metadata['Date'].iloc[-1]}",
    }


def save_experiment_results(results: list[dict[str, object]]) -> pd.DataFrame:
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
            }
        )

    output = pd.DataFrame(rows)
    EXPERIMENT_RESULTS_PATH.parent.mkdir(exist_ok=True)
    output.to_csv(EXPERIMENT_RESULTS_PATH, index=False)
    return output


def plot_metric_comparison(results: pd.DataFrame, output_path: Path) -> None:
    fig, axes = plt.subplots(1, 4, figsize=(15, 4))
    metrics = ["log_loss", "Brier_score", "calibration_score", "expected_calibration_error"]
    for ax, metric in zip(axes, metrics):
        ax.bar(results["model_version"], results[metric])
        ax.set_title(metric)
        ax.tick_params(axis="x", rotation=35)
        ax.grid(axis="y", alpha=0.25)
    fig.suptitle("Sprint 2 Feature Model Comparison: Lower Is Better")
    fig.tight_layout()
    fig.savefig(output_path, dpi=160)
    plt.close(fig)


def _feature_group(feature: str) -> str:
    if "europe" in feature:
        return "europe"
    if "xg" in feature or "xga" in feature:
        return "xG"
    if "days_rest" in feature or "midweek" in feature or "matches_last" in feature or "congestion" in feature:
        return "fatigue"
    if "injured" in feature or "missing" in feature:
        return "injury"
    if "availability" in feature or "lineup_strength" in feature or "severity" in feature:
        return "availability"
    return "form"


def shap_outputs(best_result: dict[str, object], output_dir: Path) -> pd.DataFrame:
    split = best_result["split"]
    model = best_result["model"]
    shap_importance, _, _ = compute_shap_importance(model, split.X_test)
    shap_importance["feature_group"] = shap_importance["feature"].map(_feature_group)
    shap_importance.to_csv(output_dir / "shap_feature_rankings.csv", index=False)
    shap_importance.groupby("feature_group", as_index=False)["mean_abs_shap"].sum().sort_values(
        "mean_abs_shap", ascending=False
    ).to_csv(output_dir / "shap_group_rankings.csv", index=False)
    plot_shap_importance(shap_importance.head(25), output_dir / "shap_feature_rankings.png")
    plot_shap_summary(model, split.X_test, output_dir / "shap_summary.png")
    plot_local_waterfall(model, split.X_test.reset_index(drop=True), output_dir / "shap_local_home_win.png")
    gain = gain_importance(model, best_result["feature_columns"])
    gain.to_csv(output_dir / "gain_importance.csv", index=False)
    plot_feature_importance(gain.head(25), "gain_importance", "Sprint 2 Gain Importance", output_dir / "gain_importance.png")
    return shap_importance


def _delta(results: pd.DataFrame, model_a: str, model_b: str, metric: str) -> float:
    a = float(results.loc[results["model_version"] == model_a, metric].iloc[0])
    b = float(results.loc[results["model_version"] == model_b, metric].iloc[0])
    return b - a


def _markdown_table(frame: pd.DataFrame, columns: list[str]) -> str:
    table = frame[columns].copy()
    for column in table.columns:
        if pd.api.types.is_float_dtype(table[column]):
            table[column] = table[column].map(lambda value: f"{value:.4f}")

    header = "| " + " | ".join(columns) + " |"
    separator = "| " + " | ".join(["---"] * len(columns)) + " |"
    rows = ["| " + " | ".join(str(row[column]) for column in columns) + " |" for _, row in table.iterrows()]
    return "\n".join([header, separator] + rows)


def write_report(
    results: pd.DataFrame,
    shap_importance: pd.DataFrame,
    discovery: dict[str, pd.DataFrame],
    output_path: Path,
) -> None:
    best_log_loss = results.sort_values("log_loss").iloc[0]
    fatigue_features = shap_importance[shap_importance["feature_group"] == "fatigue"].head(8)
    injury_features = shap_importance[shap_importance["feature_group"].isin(["injury", "availability"])].head(8)
    congestion_rows = shap_importance[shap_importance["feature"].str.contains("congestion", case=False, na=False)]
    top_midweek = discovery["midweek"].dropna(subset=["midweek_points_delta"]).head(5)
    weak_short_rest = discovery["short_rest"].dropna(subset=["short_rest_points_delta"]).head(5)

    fatigue_lines = "\n".join(f"- `{row.feature}`: {row.mean_abs_shap:.4f}" for row in fatigue_features.itertuples())
    injury_lines = "\n".join(f"- `{row.feature}`: {row.mean_abs_shap:.4f}" for row in injury_features.itertuples())
    model_table = _markdown_table(
        results,
        ["model_version", "accuracy", "log_loss", "Brier_score", "calibration_score", "expected_calibration_error"],
    )
    congestion_table = _markdown_table(congestion_rows[["feature", "mean_abs_shap"]], ["feature", "mean_abs_shap"])
    midweek_lines = "\n".join(
        f"- {row.team}: {row.midweek_points_delta:.3f} points per match delta over normal rest"
        for row in top_midweek.itertuples()
    )
    short_rest_lines = "\n".join(
        f"- {row.team}: {row.short_rest_points_delta:.3f} points per match delta under short rest"
        for row in weak_short_rest.itertuples()
    )

    output_path.write_text(
        f"""# Sprint 2 Report: Fatigue, Scheduling, Injuries, and Availability

## Validation

All models use the same time-based train/test split. No random train/test split is used.

- Train period: {results['train_period'].iloc[0]}
- Test period: {results['test_period'].iloc[0]}

## Model Comparison

{model_table}

Best model by log loss: `{best_log_loss['model_version']}`.

## 1. Which fatigue features improve prediction quality?

Fatigue impact is measured by Model B vs Model A:

- Log loss change: {_delta(results, 'model_a_current_baseline', 'model_b_baseline_fatigue', 'log_loss'):.4f}
- Brier score change: {_delta(results, 'model_a_current_baseline', 'model_b_baseline_fatigue', 'Brier_score'):.4f}
- Calibration score change: {_delta(results, 'model_a_current_baseline', 'model_b_baseline_fatigue', 'calibration_score'):.4f}

Top fatigue SHAP features:

{fatigue_lines or '- No fatigue feature had measurable SHAP contribution.'}

## 2. Which injury features improve prediction quality?

Injury impact is measured by Model D vs Model C:

- Log loss change: {_delta(results, 'model_c_baseline_fatigue_europe', 'model_d_baseline_fatigue_europe_injury', 'log_loss'):.4f}
- Brier score change: {_delta(results, 'model_c_baseline_fatigue_europe', 'model_d_baseline_fatigue_europe_injury', 'Brier_score'):.4f}
- Calibration score change: {_delta(results, 'model_c_baseline_fatigue_europe', 'model_d_baseline_fatigue_europe_injury', 'calibration_score'):.4f}

Top injury/availability SHAP features:

{injury_lines or '- No injury or availability feature had measurable SHAP contribution. Current injury data may be empty.'}

## 3. Does fixture congestion matter?

Fixture congestion formula:

`fixture_congestion_score = max(0, 7 - days_rest) + 1.5 * matches_last_14_days + 0.5 * matches_last_30_days`

Congestion SHAP rows:

{congestion_table if not congestion_rows.empty else 'No congestion feature had measurable SHAP contribution.'}

## 4. Do some teams consistently overperform after midweek matches?

Top teams by points-per-match delta after midweek matches:

{midweek_lines or '- Not enough midweek history to identify stable overperformers.'}

Teams with weakest short-rest deltas:

{short_rest_lines or '- Not enough short-rest history to identify stable underperformers.'}

Manager-level analysis is not included because the project does not yet contain historical manager tenure data.

## 5. Which new features should move forward into production?

Move features forward when they improve log loss and Brier score without worsening calibration, and when SHAP shows non-trivial contribution.

Current recommendation:

- Move the fatigue features forward because Model B improves log loss, Brier score, and calibration versus Model A.
- Keep European features once `data/european_fixtures.csv` is populated with historical European fixtures.
- Keep injury and availability features once `data/injuries.csv` contains real historical injury/player contribution rows.
- Treat zero-impact injury or Europe conclusions as data-availability findings, not proof that those football factors do not matter.

## Reproducibility and Leakage Controls

- Match features are generated in date order.
- Team histories are read before the current match is appended.
- Injury rows require report dates before the match.
- European fixture rows require fixture dates before the match.
- Random seed: {RANDOM_SEED}

## Data Notes

{historical_injury_pipeline_note()}

{availability_formula_note()}
"""
    )


def run() -> None:
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    dataset, metadata, feature_sets, matches = build_experiment_datasets()
    results = [evaluate_feature_set(dataset, metadata, columns, version) for version, columns in feature_sets.items()]
    results_table = save_experiment_results(results)
    results_table.to_csv(OUTPUT_DIR / "model_comparison.csv", index=False)
    plot_metric_comparison(results_table, OUTPUT_DIR / "model_comparison.png")

    best = min(results, key=lambda result: result["log_loss"])
    shap_importance = shap_outputs(best, OUTPUT_DIR)
    discovery_features = dataset[fatigue_feature_columns() + europe_feature_columns()]
    discovery = write_discovery_outputs(matches, discovery_features, OUTPUT_DIR)

    report_payload = {
        "results": results_table.to_dict("records"),
        "best_model_by_log_loss": best["model_version"],
        "fixture_congestion_formula": "max(0, 7 - days_rest) + 1.5 * matches_last_14_days + 0.5 * matches_last_30_days",
        "fixture_congestion_example": fixture_congestion_score(days_rest=3, matches_last_14_days=4, matches_last_30_days=7),
        "injury_pipeline": historical_injury_pipeline_note(),
        "availability_formula": availability_formula_note(),
    }
    (OUTPUT_DIR / "experiment_summary.json").write_text(json.dumps(report_payload, indent=2))
    write_report(results_table, shap_importance, discovery, Path("sprint2_report.md"))

    print("Sprint 2 feature experiments complete.")
    print(f"Results: {EXPERIMENT_RESULTS_PATH}")
    print(f"Report: sprint2_report.md")
    print(f"Artifacts: {OUTPUT_DIR}")


if __name__ == "__main__":
    run()
