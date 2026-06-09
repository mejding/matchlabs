from __future__ import annotations

import argparse
import json
import os
from pathlib import Path

Path("evaluation", ".matplotlib-cache").mkdir(parents=True, exist_ok=True)
os.environ.setdefault("MPLCONFIGDIR", str(Path("evaluation") / ".matplotlib-cache"))

import matplotlib
import numpy as np
import pandas as pd
from matplotlib import pyplot as plt
from sklearn.metrics import accuracy_score, log_loss

from calibration.calibration import calibration_summary, calibration_table, expected_calibration_error
from evaluation.model_evaluation import multiclass_brier_score, time_based_split
from explainability.shap_analysis import compute_shap_importance, plot_shap_importance, plot_shap_summary
from feature_experiments import _markdown_table, train_xgb
from market_odds_features import add_market_features
from odds_timing_audit import safe_prematch_columns, write_odds_column_inventory
from tactical_data import ensure_tactical_tables, load_team_match_tactics
from tactical_features import build_tactical_features
from elo_rating_features import build_elo_features
from train_model import ELO_CONFIG, PRODUCTION_FEATURE_COLUMNS, build_features, load_matches_with_xg
from visualizations.plots import gain_importance, plot_feature_importance

matplotlib.use("Agg")

OUTPUT_DIR = Path("evaluation") / "market_intelligence"
RESULTS_PATH = Path("experiments") / "market_intelligence_results.csv"
MARKET_PROB_COLUMNS = ["market_home_prob", "market_draw_prob", "market_away_prob"]
MARKET_COLUMNS = MARKET_PROB_COLUMNS + ["market_margin", "market_favorite_prob", "market_favorite_class"]
EDGE_COLUMNS = [
    "model_vs_market_home_edge",
    "model_vs_market_draw_edge",
    "model_vs_market_away_edge",
]
TACTICAL_PRESSURE_COLUMNS = [
    "home_attacking_pressure_score_last5",
    "home_attacking_pressure_score_last10",
    "home_attacking_pressure_score_season",
    "away_attacking_pressure_score_last5",
    "away_attacking_pressure_score_last10",
    "away_attacking_pressure_score_season",
]
LABELS = ["home_win", "draw", "away_win"]


def normalize_probabilities(probabilities: np.ndarray) -> np.ndarray:
    probabilities = np.clip(probabilities, 1e-15, 1.0)
    return probabilities / probabilities.sum(axis=1, keepdims=True)


def temperature_scale(probabilities: np.ndarray, temperature: float) -> np.ndarray:
    logits = np.log(normalize_probabilities(probabilities)) / temperature
    logits -= logits.max(axis=1, keepdims=True)
    exp_values = np.exp(logits)
    return exp_values / exp_values.sum(axis=1, keepdims=True)


def choose_temperature(y_true: pd.Series, probabilities: np.ndarray) -> float:
    candidates = np.linspace(0.6, 2.6, 81)
    losses = [log_loss(y_true, temperature_scale(probabilities, float(candidate)), labels=[0, 1, 2]) for candidate in candidates]
    return float(candidates[int(np.argmin(losses))])


def available_columns(dataset: pd.DataFrame, columns: list[str]) -> list[str]:
    return [column for column in columns if column in dataset.columns and dataset[column].notna().sum() > 0]


def build_market_dataset(market_mode: str = "benchmark") -> tuple[pd.DataFrame, pd.DataFrame, list[str]]:
    matches = add_market_features(load_matches_with_xg().sort_values("Date").reset_index(drop=True), market_mode=market_mode)
    if market_mode == "none" or not all(column in matches.columns for column in MARKET_COLUMNS):
        matches = load_matches_with_xg().sort_values("Date").reset_index(drop=True)
    else:
        matches = matches.dropna(subset=MARKET_COLUMNS).reset_index(drop=True)
    base_dataset, _ = build_features(matches, include_xg=True, include_schedule=True, include_shot_volume=True)
    elo_features, _ = build_elo_features(matches, ELO_CONFIG)
    base_dataset = pd.concat([base_dataset.reset_index(drop=True), elo_features.reset_index(drop=True)], axis=1)

    tactical_columns: list[str] = []
    try:
        ensure_tactical_tables()
        tactics = load_team_match_tactics()
        tactical_features, _ = build_tactical_features(matches, tactics)
        tactical_columns = available_columns(tactical_features, TACTICAL_PRESSURE_COLUMNS)
        dataset = pd.concat([base_dataset.reset_index(drop=True), tactical_features[tactical_columns].reset_index(drop=True)], axis=1)
    except Exception as exc:
        print(f"Warning: tactical pressure unavailable for market experiment: {exc}")
        dataset = base_dataset.reset_index(drop=True)

    if all(column in matches.columns for column in MARKET_COLUMNS):
        for column in MARKET_COLUMNS:
            dataset[column] = matches[column].astype(float)
        metadata_columns = ["Season", "Date", "HomeTeam", "AwayTeam", "FTR", "odds_source", "market_mode"]
    else:
        metadata_columns = ["Season", "Date", "HomeTeam", "AwayTeam", "FTR"]
    metadata = matches[metadata_columns].reset_index(drop=True)
    return dataset, metadata, PRODUCTION_FEATURE_COLUMNS + tactical_columns


def evaluate_probabilities(name: str, y_true: pd.Series, probabilities: np.ndarray) -> dict[str, float | str]:
    probabilities = normalize_probabilities(probabilities)
    predictions = probabilities.argmax(axis=1)
    calibration = calibration_table(y_true, probabilities)
    cal_summary = calibration_summary(calibration)
    return {
        "model": name,
        "accuracy": float(accuracy_score(y_true, predictions)),
        "log_loss": float(log_loss(y_true, probabilities, labels=[0, 1, 2])),
        "brier_score": multiclass_brier_score(y_true, probabilities),
        "calibration_score": cal_summary["mean_absolute_calibration_error"],
        "ece": expected_calibration_error(calibration),
    }


def add_market_edges(dataset: pd.DataFrame, production_probabilities: np.ndarray) -> pd.DataFrame:
    enriched = dataset.copy()
    for index, column in enumerate(EDGE_COLUMNS):
        enriched[column] = production_probabilities[:, index] - enriched[MARKET_PROB_COLUMNS[index]]
    return enriched


def fit_calibrated_blend(
    train_y: pd.Series,
    train_model_probs: np.ndarray,
    test_model_probs: np.ndarray,
    test_market_probs: np.ndarray,
) -> np.ndarray:
    temperature = choose_temperature(train_y, train_model_probs)
    calibrated_test_model = temperature_scale(test_model_probs, temperature)
    return normalize_probabilities((calibrated_test_model + test_market_probs) / 2.0)


def fit_weighted_blend(
    train_y: pd.Series,
    train_model_probs: np.ndarray,
    train_market_probs: np.ndarray,
    test_model_probs: np.ndarray,
    test_market_probs: np.ndarray,
) -> tuple[np.ndarray, float, float]:
    """Fit a simple model/market probability blend on the latest slice of the training period."""
    split_index = max(int(len(train_y) * 0.8), 1)
    tune_y = train_y.iloc[split_index:] if hasattr(train_y, "iloc") else train_y[split_index:]
    tune_model_probs = train_model_probs[split_index:]
    tune_market_probs = train_market_probs[split_index:]
    if len(tune_y) < 30:
        tune_y = train_y
        tune_model_probs = train_model_probs
        tune_market_probs = train_market_probs
    temperature = choose_temperature(tune_y, tune_model_probs)
    calibrated_tune_model = temperature_scale(tune_model_probs, temperature)
    calibrated_test_model = temperature_scale(test_model_probs, temperature)
    weights = np.linspace(0.0, 1.0, 41)
    losses = [
        log_loss(
            tune_y,
            normalize_probabilities((float(weight) * calibrated_tune_model) + ((1.0 - float(weight)) * tune_market_probs)),
            labels=[0, 1, 2],
        )
        for weight in weights
    ]
    best_weight = float(weights[int(np.argmin(losses))])
    test_blend = normalize_probabilities((best_weight * calibrated_test_model) + ((1.0 - best_weight) * test_market_probs))
    return test_blend, best_weight, float(temperature)


def disagreement_table(
    metadata: pd.DataFrame,
    y_true: pd.Series,
    model_probs: np.ndarray,
    market_probs: np.ndarray,
) -> pd.DataFrame:
    rows = metadata.reset_index(drop=True).copy()
    rows["match"] = rows["HomeTeam"].astype(str) + " vs " + rows["AwayTeam"].astype(str)
    rows["actual"] = y_true.reset_index(drop=True).map({0: "home_win", 1: "draw", 2: "away_win"})
    rows["model_pick"] = pd.Series(model_probs.argmax(axis=1)).map({0: "home_win", 1: "draw", 2: "away_win"})
    rows["market_pick"] = pd.Series(market_probs.argmax(axis=1)).map({0: "home_win", 1: "draw", 2: "away_win"})
    rows["model_confidence"] = model_probs.max(axis=1)
    rows["market_confidence"] = market_probs.max(axis=1)
    rows["model_market_disagree"] = rows["model_pick"] != rows["market_pick"]
    for index, label in enumerate(["home", "draw", "away"]):
        rows[f"model_{label}_prob"] = model_probs[:, index]
        rows[f"market_{label}_prob"] = market_probs[:, index]
        rows[f"model_vs_market_{label}_edge"] = model_probs[:, index] - market_probs[:, index]
    rows["max_abs_edge"] = rows[
        ["model_vs_market_home_edge", "model_vs_market_draw_edge", "model_vs_market_away_edge"]
    ].abs().max(axis=1)
    rows["model_correct"] = rows["model_pick"] == rows["actual"]
    rows["market_correct"] = rows["market_pick"] == rows["actual"]
    actual_indices = y_true.reset_index(drop=True).to_numpy()
    rows["model_log_loss"] = -np.log(np.clip(model_probs[np.arange(len(rows)), actual_indices], 1e-15, 1.0))
    rows["market_log_loss"] = -np.log(np.clip(market_probs[np.arange(len(rows)), actual_indices], 1e-15, 1.0))
    rows["log_loss_difference_model_minus_market"] = rows["model_log_loss"] - rows["market_log_loss"]
    rows["edge_correct"] = rows["model_correct"] & (rows["model_log_loss"] < rows["market_log_loss"])
    return rows.sort_values("max_abs_edge", ascending=False)


def disagreement_summary(disagreements: pd.DataFrame) -> pd.DataFrame:
    rows = []
    for label, frame in [
        ("all_test_matches", disagreements),
        ("model_market_disagreements", disagreements[disagreements["model_market_disagree"]]),
        ("large_edges_top_quartile", disagreements[disagreements["max_abs_edge"] >= disagreements["max_abs_edge"].quantile(0.75)]),
    ]:
        if frame.empty:
            continue
        rows.append(
            {
                "segment": label,
                "matches": int(len(frame)),
                "model_accuracy": float(frame["model_correct"].mean()),
                "market_accuracy": float(frame["market_correct"].mean()),
                "mean_abs_edge": float(frame["max_abs_edge"].mean()),
            }
        )
    return pd.DataFrame(rows)


def plot_model_comparison(results: pd.DataFrame, output_path: Path) -> None:
    metrics = ["accuracy", "log_loss", "brier_score", "calibration_score", "ece"]
    fig, axes = plt.subplots(1, len(metrics), figsize=(17, 4))
    for ax, metric in zip(axes, metrics):
        ax.bar(results["model"], results[metric])
        ax.set_title(metric)
        ax.tick_params(axis="x", rotation=25)
        ax.grid(axis="y", alpha=0.25)
    fig.suptitle("Market Intelligence Model Comparison")
    fig.tight_layout()
    fig.savefig(output_path, dpi=160)
    plt.close(fig)


def shap_outputs(model, X_test: pd.DataFrame) -> pd.DataFrame:
    shap_importance, _, _ = compute_shap_importance(model, X_test)
    shap_importance["feature_group"] = shap_importance["feature"].map(
        lambda feature: "market" if feature.startswith("market_") else "edge" if "model_vs_market" in feature else "production"
    )
    shap_importance.to_csv(OUTPUT_DIR / "market_shap_feature_rankings.csv", index=False)
    shap_importance.groupby("feature_group", as_index=False)["mean_abs_shap"].sum().sort_values(
        "mean_abs_shap", ascending=False
    ).to_csv(OUTPUT_DIR / "market_shap_group_rankings.csv", index=False)
    plot_shap_importance(shap_importance.head(35), OUTPUT_DIR / "market_shap_feature_rankings.png")
    plot_shap_summary(model, X_test, OUTPUT_DIR / "market_shap_summary.png")
    return shap_importance


def write_report(
    results: pd.DataFrame,
    disagreements: pd.DataFrame,
    summary: pd.DataFrame,
    shap_importance: pd.DataFrame,
    market_mode: str,
    blend_weight: float | None = None,
    blend_temperature: float | None = None,
) -> None:
    best = results.sort_values(["log_loss", "brier_score"]).iloc[0]
    model_a = results[results["model"].str.startswith("Model A")].iloc[0]
    model_b = results[results["model"].str.startswith("Model B")].iloc[0]
    model_c = results[results["model"].str.startswith("Model C")].iloc[0]
    blend_rows = results[results["model"].str.startswith("Model D")]
    model_d = blend_rows.iloc[0] if not blend_rows.empty else None
    market_beats_model = float(model_b["log_loss"]) < float(model_a["log_loss"]) and float(model_b["brier_score"]) < float(model_a["brier_score"])
    model_plus_market_improves = float(model_c["log_loss"]) < float(model_a["log_loss"]) and float(model_c["brier_score"]) < float(model_a["brier_score"])
    blend_improves = (
        model_d is not None
        and pd.notna(model_d["log_loss"])
        and float(model_d["log_loss"]) < float(model_a["log_loss"])
        and float(model_d["brier_score"]) < float(model_a["brier_score"])
        and float(model_d["ece"]) <= float(model_a["ece"]) + 0.01
    )
    market_shap = shap_importance[shap_importance["feature_group"].isin(["market", "edge"])].head(12)
    shap_lines = "\n".join(f"- `{row.feature}` ({row.feature_group}): {row.mean_abs_shap:.4f}" for row in market_shap.itertuples())

    safe_columns = safe_prematch_columns()
    Path("market_timing_audit_report.md").write_text(
        f"""# Market Intelligence Report

Bookmaker odds are converted from decimal odds to normalized implied probabilities:

- `market_home_prob`
- `market_draw_prob`
- `market_away_prob`
- `market_margin`
- `market_favorite_prob`

Edges are calculated as model probability minus market probability.

Important timing note: football-data non-C 1X2 odds are documented as pre-closing odds, not opening odds. C-suffixed odds are closing odds. Pre-closing odds do not leak the final result, but they are only production-safe if the live prediction path uses an equivalent pre-closing feed before kickoff.

Market mode evaluated in this run: `{market_mode}`.

Safe pre-match odds fields currently verified: {', '.join(safe_columns) if safe_columns else 'None'}.

Blend parameters: {f'model weight={blend_weight:.2f}, temperature={blend_temperature:.2f}' if blend_weight is not None and blend_temperature is not None else 'not fitted for this run'}.

## Model Comparison

{_markdown_table(results, ['model', 'accuracy', 'log_loss', 'brier_score', 'calibration_score', 'ece'])}

Best model by log loss: `{best['model']}`.

## 1. Does market information improve predictions?

Model C vs Model A:

- Log loss change: {float(model_c['log_loss'] - model_a['log_loss']):.4f}
- Brier score change: {float(model_c['brier_score'] - model_a['brier_score']):.4f}

Answer: {'Yes, the model + market feature set improves the current model.' if model_plus_market_improves else 'No, adding market odds as model features did not improve the current model in this run.'}

## 1b. Does a calibrated model-market blend improve predictions?

Answer: {'Yes, the calibrated blend improves Log Loss and Brier without materially worsening ECE.' if blend_improves else 'No, the calibrated blend does not pass the production promotion rule in this run.'}

## 2. Is the market stronger than the model?

Model B vs Model A:

- Log loss change: {float(model_b['log_loss'] - model_a['log_loss']):.4f}
- Brier score change: {float(model_b['brier_score'] - model_a['brier_score']):.4f}

Answer: {'Yes. Market-only probabilities are stronger than the current model on this historical test period.' if market_beats_model else 'No. The current model beats market-only probabilities on this historical test period.'}

## 3. Where does the model disagree with the market?

Disagreement summary:

{_markdown_table(summary, ['segment', 'matches', 'model_accuracy', 'market_accuracy', 'mean_abs_edge'])}

Largest individual disagreements are saved to `evaluation/market_intelligence/market_disagreements.csv`.

## 4. Are disagreements predictive?

If model accuracy on disagreement segments is higher than market accuracy, the model has exploitable edge. In this run, inspect the disagreement summary above. If the market remains more accurate on disagreement rows, model disagreement is not yet a reliable signal.

## SHAP

Top market/edge SHAP features:

{shap_lines or '- No market or edge features had measurable SHAP contribution.'}

Full SHAP outputs:

- `evaluation/market_intelligence/market_shap_feature_rankings.csv`
- `evaluation/market_intelligence/market_shap_group_rankings.csv`
- `evaluation/market_intelligence/market_shap_summary.png`

## Production Decision

{'Move pre-closing market odds forward as a production candidate, but only if the app obtains an equivalent live pre-closing odds feed.' if (model_plus_market_improves or blend_improves) and market_mode in {'preclosing', 'opening', 'safe-prematch'} else 'Do not activate market odds as XGBoost production features. Keep them as benchmark/fair-odds context and test a separate market-overlay probability layer once live pre-closing odds timing is controlled.'}
"""
    )
    Path("market_intelligence_report.md").write_text(Path("market_timing_audit_report.md").read_text())


def run_comparison(market_mode: str = "benchmark") -> pd.DataFrame:
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    write_odds_column_inventory()
    evaluated_market_mode = market_mode if market_mode != "none" else "benchmark"
    dataset, metadata, production_columns = build_market_dataset(market_mode="none")
    split = time_based_split(dataset[production_columns], dataset["target"], metadata)
    model_a = train_xgb(split.X_train, split.y_train)
    model_a_train_probs = normalize_probabilities(model_a.predict_proba(split.X_train))
    model_a_test_probs = normalize_probabilities(model_a.predict_proba(split.X_test))

    benchmark_dataset, benchmark_metadata, benchmark_production_columns = build_market_dataset(market_mode=evaluated_market_mode)
    has_evaluated_market = all(column in benchmark_dataset.columns for column in MARKET_COLUMNS)
    if not has_evaluated_market:
        rows = [
            evaluate_probabilities("Model A: current production model", split.y_test, model_a_test_probs),
            {
                "model": f"Model B: market-only {evaluated_market_mode} model",
                "accuracy": np.nan,
                "log_loss": np.nan,
                "brier_score": np.nan,
                "calibration_score": np.nan,
                "ece": np.nan,
            },
            {
                "model": f"Model C: current model + {evaluated_market_mode} odds",
                "accuracy": np.nan,
                "log_loss": np.nan,
                "brier_score": np.nan,
                "calibration_score": np.nan,
                "ece": np.nan,
            },
            {
                "model": "Model D: production + safe-prematch odds",
                "accuracy": np.nan,
                "log_loss": np.nan,
                "brier_score": np.nan,
                "calibration_score": np.nan,
                "ece": np.nan,
            },
        ]
        results = pd.DataFrame(rows)
        results.to_csv(OUTPUT_DIR / "market_model_comparison.csv", index=False)
        results.to_csv(OUTPUT_DIR / f"market_model_comparison_{evaluated_market_mode}.csv", index=False)
        results.to_csv("market_intelligence_results.csv", index=False)
        results.to_csv(RESULTS_PATH, index=False)
        Path("market_timing_audit_report.md").write_text(
            f"""# Market Intelligence Report

Market mode evaluated in this run: `{evaluated_market_mode}`.

No usable market odds were available for this mode.

For `opening` mode, create `data/oddsportal_opening_odds.csv` with verified pre-match opening prices before rerunning the experiment.

## Model Comparison

{_markdown_table(results, ['model', 'accuracy', 'log_loss', 'brier_score', 'calibration_score', 'ece'])}

## Production Decision

Do not move market odds into production. There is not enough verified opening/pre-match data in the project yet.
"""
        )
        Path("market_intelligence_report.md").write_text(Path("market_timing_audit_report.md").read_text())
        (OUTPUT_DIR / f"market_timing_audit_report_{evaluated_market_mode}.md").write_text(
            Path("market_timing_audit_report.md").read_text()
        )
        return results

    benchmark_split = time_based_split(benchmark_dataset[benchmark_production_columns], benchmark_dataset["target"], benchmark_metadata)
    benchmark_model = train_xgb(benchmark_split.X_train, benchmark_split.y_train)
    benchmark_model_train_probs = normalize_probabilities(benchmark_model.predict_proba(benchmark_split.X_train))
    benchmark_model_test_probs = normalize_probabilities(benchmark_model.predict_proba(benchmark_split.X_test))
    market_train_probs = benchmark_dataset.loc[benchmark_split.X_train.index, MARKET_PROB_COLUMNS].to_numpy()
    market_test_probs = benchmark_dataset.loc[benchmark_split.X_test.index, MARKET_PROB_COLUMNS].to_numpy()

    market_dataset = add_market_edges(
        benchmark_dataset,
        normalize_probabilities(benchmark_model.predict_proba(benchmark_dataset[benchmark_production_columns])),
    )
    market_feature_columns = benchmark_production_columns + MARKET_COLUMNS + EDGE_COLUMNS
    split_c = time_based_split(market_dataset[market_feature_columns], market_dataset["target"], benchmark_metadata)
    model_c = train_xgb(split_c.X_train, split_c.y_train)
    model_c_probs = normalize_probabilities(model_c.predict_proba(split_c.X_test))

    blend_probs, blend_weight, blend_temperature = fit_weighted_blend(
        benchmark_split.y_train,
        benchmark_model_train_probs,
        market_train_probs,
        benchmark_model_test_probs,
        market_test_probs,
    )

    rows = [
        evaluate_probabilities("Model A: current production model", split.y_test, model_a_test_probs),
        evaluate_probabilities(f"Model B: market-only {evaluated_market_mode} model", benchmark_split.y_test, market_test_probs),
        evaluate_probabilities(f"Model C: current model + {evaluated_market_mode} odds (research only)", split_c.y_test, model_c_probs),
        evaluate_probabilities(f"Model D: calibrated model-market blend ({evaluated_market_mode})", benchmark_split.y_test, blend_probs),
    ]

    safe_dataset, safe_metadata, safe_production_columns = build_market_dataset(market_mode="safe-prematch")
    if all(column in safe_dataset.columns for column in MARKET_COLUMNS):
        safe_feature_columns = safe_production_columns + MARKET_COLUMNS
        split_d = time_based_split(safe_dataset[safe_feature_columns], safe_dataset["target"], safe_metadata)
        model_d = train_xgb(split_d.X_train, split_d.y_train)
        model_d_probs = normalize_probabilities(model_d.predict_proba(split_d.X_test))
        rows.append(evaluate_probabilities("Model E: production + safe-prematch odds", split_d.y_test, model_d_probs))
    else:
        rows.append(
            {
                "model": "Model E: production + safe-prematch odds",
                "accuracy": np.nan,
                "log_loss": np.nan,
                "brier_score": np.nan,
                "calibration_score": np.nan,
                "ece": np.nan,
            }
        )

    if evaluated_market_mode == "benchmark":
        # Keep the previously useful calibrated benchmark blend as a side artifact, not a production model.
        blend_probs = fit_calibrated_blend(
            benchmark_split.y_train,
            benchmark_model_train_probs,
            benchmark_model_test_probs,
            market_test_probs,
        )
        pd.DataFrame([evaluate_probabilities("calibrated_model_market_blend_benchmark", benchmark_split.y_test, blend_probs)]).to_csv(
            OUTPUT_DIR / "calibrated_market_blend_benchmark.csv",
            index=False,
        )

    results = pd.DataFrame(rows)
    results.to_csv(OUTPUT_DIR / "market_model_comparison.csv", index=False)
    results.to_csv(OUTPUT_DIR / f"market_model_comparison_{evaluated_market_mode}.csv", index=False)
    results.to_csv("market_intelligence_results.csv", index=False)
    results.to_csv(RESULTS_PATH, index=False)
    plot_model_comparison(results, OUTPUT_DIR / "market_model_comparison.png")

    disagreements = disagreement_table(benchmark_split.test_metadata, benchmark_split.y_test, benchmark_model_test_probs, market_test_probs)
    disagreements.to_csv(OUTPUT_DIR / "market_disagreements.csv", index=False)
    edge_columns = [
        "Date",
        "match",
        "HomeTeam",
        "AwayTeam",
        "actual",
        "model_home_prob",
        "model_draw_prob",
        "model_away_prob",
        "market_home_prob",
        "market_draw_prob",
        "market_away_prob",
        "model_vs_market_home_edge",
        "model_vs_market_draw_edge",
        "model_vs_market_away_edge",
        "edge_correct",
        "log_loss_difference_model_minus_market",
    ]
    disagreements[edge_columns].to_csv("market_edge_analysis.csv", index=False)
    disagreements[edge_columns].to_csv(OUTPUT_DIR / "market_edge_analysis.csv", index=False)
    summary = disagreement_summary(disagreements)
    summary.to_csv(OUTPUT_DIR / "market_disagreement_summary.csv", index=False)

    gain = gain_importance(model_c, market_feature_columns)
    gain.to_csv(OUTPUT_DIR / "market_gain_importance.csv", index=False)
    plot_feature_importance(gain.head(35), "gain_importance", "Market Intelligence Gain Importance", OUTPUT_DIR / "market_gain_importance.png")
    shap_importance = shap_outputs(model_c, split_c.X_test)
    write_report(results, disagreements, summary, shap_importance, evaluated_market_mode, blend_weight, blend_temperature)
    (OUTPUT_DIR / f"market_timing_audit_report_{evaluated_market_mode}.md").write_text(
        Path("market_timing_audit_report.md").read_text()
    )
    return results


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Run market timing and odds intelligence experiments.")
    parser.add_argument(
        "--market-mode",
        choices=["none", "benchmark", "research", "preclosing", "safe-prematch", "opening"],
        default="benchmark",
        help="Controls odds feature usage. preclosing uses football-data non-C 1X2 odds; benchmark uses closing/aggregate odds.",
    )
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    results = run_comparison(market_mode=args.market_mode)
    best = results.dropna(subset=["log_loss"]).sort_values("log_loss").iloc[0]
    print(json.dumps({"market_mode": args.market_mode, "best_model": str(best["model"])}, indent=2))


if __name__ == "__main__":
    main()
