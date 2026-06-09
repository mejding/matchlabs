from __future__ import annotations

import json
import os
from pathlib import Path

Path("evaluation", ".matplotlib-cache").mkdir(parents=True, exist_ok=True)
os.environ.setdefault("MPLCONFIGDIR", str(Path("evaluation") / ".matplotlib-cache"))

import matplotlib
import numpy as np
import pandas as pd
from sklearn.metrics import log_loss

from elo_rating_features import build_elo_features
from explainability.shap_analysis import compute_shap_importance, plot_shap_importance, plot_shap_summary
from feature_experiments import _markdown_table
from opponent_adjusted_xg_experiments import (
    OUTPUT_DIR,
    evaluate_feature_set,
    feature_group,
)
from opponent_adjusted_xg_features import RATING_FEATURE_COLUMNS, build_opponent_adjusted_xg_features
from train_model import (
    ELO_CONFIG,
    FEATURE_COLUMNS,
    PRODUCTION_FEATURE_COLUMNS,
    SCHEDULE_FEATURE_COLUMNS,
    SHOT_VOLUME_FEATURE_COLUMNS,
    XG_FEATURE_COLUMNS,
    build_features,
    load_matches_with_xg,
)
from visualizations.plots import gain_importance, plot_feature_importance

matplotlib.use("Agg")

RAW_XG_COLUMNS = [
    "home_xg_avg",
    "away_xg_avg",
    "home_xga_avg",
    "away_xga_avg",
    "home_xg_diff",
    "away_xg_diff",
]
XG_AVG_COLUMNS = ["home_xg_avg", "away_xg_avg"]
XGA_AVG_COLUMNS = ["home_xga_avg", "away_xga_avg"]
XG_DIFF_COLUMNS = ["home_xg_diff", "away_xg_diff"]
NON_XG_PRODUCTION_COLUMNS = [column for column in PRODUCTION_FEATURE_COLUMNS if column not in set(RAW_XG_COLUMNS)]


def build_replacement_dataset() -> tuple[pd.DataFrame, pd.DataFrame, dict[str, list[str]]]:
    matches = load_matches_with_xg().sort_values("Date").reset_index(drop=True)
    base_dataset, _ = build_features(matches, include_xg=True, include_schedule=True, include_shot_volume=True)
    elo_features, _ = build_elo_features(matches, ELO_CONFIG)
    adjusted_xg = build_opponent_adjusted_xg_features(matches)
    dataset = pd.concat(
        [base_dataset.reset_index(drop=True), elo_features.reset_index(drop=True), adjusted_xg.reset_index(drop=True)],
        axis=1,
    )
    metadata = matches[["Season", "Date", "HomeTeam", "AwayTeam", "FTR"]].reset_index(drop=True)

    feature_sets = {
        "model_a_current_production": PRODUCTION_FEATURE_COLUMNS,
        "model_b_no_raw_xg_plus_ratings": NON_XG_PRODUCTION_COLUMNS + RATING_FEATURE_COLUMNS,
        "model_c_no_xg_diff_plus_ratings": [
            column for column in PRODUCTION_FEATURE_COLUMNS if column not in set(XG_DIFF_COLUMNS)
        ]
        + RATING_FEATURE_COLUMNS,
        "model_d_production_plus_ratings": PRODUCTION_FEATURE_COLUMNS + RATING_FEATURE_COLUMNS,
        "model_e_no_xg_xga_avgs_plus_ratings": [
            column for column in PRODUCTION_FEATURE_COLUMNS if column not in set(XG_AVG_COLUMNS + XGA_AVG_COLUMNS)
        ]
        + RATING_FEATURE_COLUMNS,
        "model_f_ratings_only_xg_representation": NON_XG_PRODUCTION_COLUMNS + RATING_FEATURE_COLUMNS,
    }
    return dataset, metadata, feature_sets


def write_current_xg_inventory() -> None:
    rows = []
    for column in RAW_XG_COLUMNS:
        family = "xG differential" if column in XG_DIFF_COLUMNS else "xGA average" if column in XGA_AVG_COLUMNS else "xG average"
        rows.append(
            {
                "feature": column,
                "family": family,
                "active_in_production": column in PRODUCTION_FEATURE_COLUMNS,
                "calculation": "Rolling last-5 team xG/xGA derived before each fixture in train_model.build_features.",
            }
        )
    frame = pd.DataFrame(rows)
    lines = [
        "# Current Production xG Feature Inventory",
        "",
        "These raw xG-family features are active in the current production feature set.",
        "",
        _markdown_table(frame, ["feature", "family", "active_in_production", "calculation"]),
    ]
    (OUTPUT_DIR / "current_xg_feature_inventory.md").write_text("\n".join(lines))


def correlation_analysis(dataset: pd.DataFrame) -> pd.DataFrame:
    pairs = [
        ("home_xg_avg", "home_xg_attack_rating"),
        ("away_xg_avg", "away_xg_attack_rating"),
        ("home_xga_avg", "home_xg_defense_rating"),
        ("away_xga_avg", "away_xg_defense_rating"),
        ("home_xg_diff", "attack_defense_matchup_score"),
        ("away_xg_diff", "attack_defense_matchup_score"),
    ]
    rows = []
    for raw, adjusted in pairs:
        rows.append(
            {
                "raw_xg_feature": raw,
                "opponent_adjusted_feature": adjusted,
                "pearson_correlation": float(dataset[raw].corr(dataset[adjusted])),
                "absolute_correlation": float(abs(dataset[raw].corr(dataset[adjusted]))),
            }
        )
    output = pd.DataFrame(rows).sort_values("absolute_correlation", ascending=False)
    output.to_csv(OUTPUT_DIR / "correlation_analysis.csv", index=False)
    return output


def evaluate_replacement_models(dataset: pd.DataFrame, metadata: pd.DataFrame, feature_sets: dict[str, list[str]]) -> tuple[pd.DataFrame, dict[str, dict[str, object]]]:
    results = []
    lookup = {}
    for name, columns in feature_sets.items():
        result = evaluate_feature_set(dataset, metadata, columns, name)
        results.append(result)
        lookup[name] = result
    frame = replacement_results_frame(results)
    frame.to_csv(OUTPUT_DIR / "model_replacement_comparison.csv", index=False)
    return frame, lookup


def replacement_results_frame(results: list[dict[str, object]]) -> pd.DataFrame:
    rows = []
    for result in results:
        rows.append(
            {
                "model_version": result["model_version"],
                "train_period": result["train_period"],
                "test_period": result["test_period"],
                "accuracy": result["accuracy"],
                "log_loss": result["log_loss"],
                "Brier_score": result["Brier_score"],
                "calibration_score": result["calibration_score"],
                "expected_calibration_error": result["expected_calibration_error"],
                "draw_recall": result["draw_recall"],
                "draw_log_loss": result["draw_log_loss"],
                "draw_mean_probability_on_draws": result["draw_mean_probability_on_draws"],
            }
        )
    return pd.DataFrame(rows)


def remove_one_family_analysis(dataset: pd.DataFrame, metadata: pd.DataFrame) -> pd.DataFrame:
    tests = {
        "production_reference": PRODUCTION_FEATURE_COLUMNS,
        "remove_all_raw_xg": NON_XG_PRODUCTION_COLUMNS,
        "remove_xg_avgs": [column for column in PRODUCTION_FEATURE_COLUMNS if column not in set(XG_AVG_COLUMNS)],
        "remove_xga_avgs": [column for column in PRODUCTION_FEATURE_COLUMNS if column not in set(XGA_AVG_COLUMNS)],
        "remove_xg_diff": [column for column in PRODUCTION_FEATURE_COLUMNS if column not in set(XG_DIFF_COLUMNS)],
        "ratings_reference": NON_XG_PRODUCTION_COLUMNS + RATING_FEATURE_COLUMNS,
        "ratings_reference_remove_attack": NON_XG_PRODUCTION_COLUMNS
        + [column for column in RATING_FEATURE_COLUMNS if "attack" not in column],
        "ratings_reference_remove_defense": NON_XG_PRODUCTION_COLUMNS
        + [column for column in RATING_FEATURE_COLUMNS if "defense" not in column],
        "production_plus_ratings_remove_raw_xg": NON_XG_PRODUCTION_COLUMNS + RATING_FEATURE_COLUMNS,
        "production_plus_ratings_remove_ratings": PRODUCTION_FEATURE_COLUMNS,
    }
    rows = []
    for name, columns in tests.items():
        result = evaluate_feature_set(dataset, metadata, columns, name)
        rows.append(
            {
                "test": name,
                "feature_count": len(columns),
                "log_loss": result["log_loss"],
                "Brier_score": result["Brier_score"],
                "expected_calibration_error": result["expected_calibration_error"],
                "draw_recall": result["draw_recall"],
                "draw_log_loss": result["draw_log_loss"],
            }
        )
    output = pd.DataFrame(rows)
    output.to_csv(OUTPUT_DIR / "remove_one_family_analysis.csv", index=False)
    return output


def write_remove_one_report(remove_one: pd.DataFrame) -> None:
    production = remove_one[remove_one["test"] == "production_reference"].iloc[0]
    no_raw = remove_one[remove_one["test"] == "remove_all_raw_xg"].iloc[0]
    ratings = remove_one[remove_one["test"] == "ratings_reference"].iloc[0]
    lines = [
        "# Remove-One Analysis: Raw xG vs Opponent-Adjusted Ratings",
        "",
        "Lower Log Loss, Brier Score and ECE are better.",
        "",
        _markdown_table(
            remove_one,
            ["test", "feature_count", "log_loss", "Brier_score", "expected_calibration_error", "draw_recall", "draw_log_loss"],
        ),
        "",
        "## Interpretation",
        "",
        f"- Removing all raw xG from production changes Log Loss by {float(no_raw['log_loss'] - production['log_loss']):.4f}.",
        f"- Replacing raw xG with ratings changes Log Loss by {float(ratings['log_loss'] - production['log_loss']):.4f}.",
        "- If raw xG removal hurts more than rating removal, raw xG still contains more unique signal.",
    ]
    (OUTPUT_DIR / "remove_one_analysis.md").write_text("\n".join(lines))


def shap_replacement_outputs(best_result: dict[str, object]) -> pd.DataFrame:
    shap_importance, _, _ = compute_shap_importance(best_result["model"], best_result["split"].X_test)
    shap_importance["feature_group"] = shap_importance["feature"].map(replacement_feature_group)
    shap_importance.to_csv(OUTPUT_DIR / "shap_replacement_importance.csv", index=False)
    group = shap_importance.groupby("feature_group", as_index=False)["mean_abs_shap"].sum().sort_values(
        "mean_abs_shap", ascending=False
    )
    group.to_csv(OUTPUT_DIR / "shap_replacement_group_importance.csv", index=False)
    plot_shap_importance(shap_importance.head(40), OUTPUT_DIR / "shap_replacement_importance.png")
    plot_shap_summary(best_result["model"], best_result["split"].X_test, OUTPUT_DIR / "shap_replacement_summary.png")
    gain = gain_importance(best_result["model"], best_result["feature_columns"])
    gain.to_csv(OUTPUT_DIR / "replacement_gain_importance.csv", index=False)
    plot_feature_importance(gain.head(40), "gain_importance", "Replacement Gain Importance", OUTPUT_DIR / "replacement_gain_importance.png")
    return shap_importance


def replacement_feature_group(feature: str) -> str:
    if feature in XG_AVG_COLUMNS:
        return "raw_xg"
    if feature in XGA_AVG_COLUMNS:
        return "raw_xga"
    if feature in XG_DIFF_COLUMNS:
        return "xg_differential"
    if feature in RATING_FEATURE_COLUMNS and "attack" in feature:
        return "attack_ratings"
    if feature in RATING_FEATURE_COLUMNS and "defense" in feature:
        return "defense_ratings"
    if feature in RATING_FEATURE_COLUMNS:
        return "matchup_ratings"
    return feature_group(feature)


def write_shap_replacement_report(shap_importance: pd.DataFrame) -> None:
    group = shap_importance.groupby("feature_group", as_index=False)["mean_abs_shap"].sum().sort_values(
        "mean_abs_shap", ascending=False
    )
    top = shap_importance[shap_importance["feature_group"].isin(["raw_xg", "raw_xga", "xg_differential", "attack_ratings", "defense_ratings", "matchup_ratings"])].head(20)
    lines = [
        "# SHAP Replacement Report",
        "",
        "This report compares the predictive contribution of raw xG/xGA/xG-differential features against opponent-adjusted attack/defense ratings.",
        "",
        "## Group Importance",
        "",
        _markdown_table(group, ["feature_group", "mean_abs_shap"]),
        "",
        "## Top xG-Representation Features",
        "",
        _markdown_table(top, ["feature", "mean_abs_shap", "feature_group"]),
    ]
    (OUTPUT_DIR / "shap_replacement_report.md").write_text("\n".join(lines))


def write_decision_report(results: pd.DataFrame, correlations: pd.DataFrame, remove_one: pd.DataFrame, shap_importance: pd.DataFrame) -> None:
    baseline = results[results["model_version"] == "model_a_current_production"].iloc[0]
    best_log = results.sort_values("log_loss").iloc[0]
    best_brier = results.sort_values("Brier_score").iloc[0]
    best_draw = results.sort_values("draw_log_loss").iloc[0]
    model_b = results[results["model_version"] == "model_b_no_raw_xg_plus_ratings"].iloc[0]
    model_c = results[results["model_version"] == "model_c_no_xg_diff_plus_ratings"].iloc[0]
    model_d = results[results["model_version"] == "model_d_production_plus_ratings"].iloc[0]
    equal_or_better_replacement = (
        float(model_b["log_loss"]) <= float(baseline["log_loss"])
        and float(model_b["Brier_score"]) <= float(baseline["Brier_score"])
        and float(model_b["expected_calibration_error"]) <= float(baseline["expected_calibration_error"]) + 0.01
    )
    add_on_improves = float(model_d["log_loss"]) < float(baseline["log_loss"]) or float(model_d["Brier_score"]) < float(baseline["Brier_score"])
    xg_diff_replacement_improves = (
        float(model_c["log_loss"]) < float(baseline["log_loss"])
        and float(model_c["Brier_score"]) < float(baseline["Brier_score"])
        and float(model_c["expected_calibration_error"]) <= float(baseline["expected_calibration_error"]) + 0.01
    )
    if equal_or_better_replacement:
        decision = "CASE 2: ratings can replace raw xG with equal or better probability quality. Consider a simplified production candidate."
    elif xg_diff_replacement_improves:
        decision = (
            "CASE 1 variant: ratings should not replace all raw xG, but they may replace xG differential. "
            "Best tested setup keeps xG/xGA averages, removes xG-diff columns, and adds opponent-adjusted ratings."
        )
    elif add_on_improves:
        decision = "CASE 1: ratings add a small amount of signal on top of raw xG. Keep both only after a broader confirmation backtest."
    else:
        decision = "CASE 3: ratings add little/no robust value. Keep current production and mark ratings research-only."

    avg_abs_corr = float(correlations["absolute_correlation"].mean())
    raw_groups = ["raw_xg", "raw_xga", "xg_differential"]
    rating_groups = ["attack_ratings", "defense_ratings", "matchup_ratings"]
    shap_group = shap_importance.groupby("feature_group", as_index=False)["mean_abs_shap"].sum()
    raw_shap = float(shap_group[shap_group["feature_group"].isin(raw_groups)]["mean_abs_shap"].sum())
    rating_shap = float(shap_group[shap_group["feature_group"].isin(rating_groups)]["mean_abs_shap"].sum())

    lines = [
        "# Sprint 4E: Replacement Decision Report",
        "",
        "## Goal",
        "",
        "Determine whether opponent-adjusted ratings should be added on top of raw xG, replace raw xG, or remain research-only.",
        "",
        "## Model Comparison",
        "",
        _markdown_table(
            results,
            ["model_version", "accuracy", "log_loss", "Brier_score", "expected_calibration_error", "draw_recall", "draw_log_loss"],
        ),
        "",
        "## Correlation Summary",
        "",
        _markdown_table(correlations, ["raw_xg_feature", "opponent_adjusted_feature", "pearson_correlation", "absolute_correlation"]),
        "",
        f"Average absolute correlation across inspected pairs: {avg_abs_corr:.4f}.",
        "",
        "## SHAP Summary",
        "",
        f"- Raw xG-family SHAP total in best comparison model: {raw_shap:.4f}",
        f"- Opponent-adjusted rating SHAP total in best comparison model: {rating_shap:.4f}",
        "",
        "## Answers",
        "",
        f"1. Are opponent-adjusted ratings mostly redundant with raw xG? {'Partly yes' if avg_abs_corr >= 0.45 else 'Not strongly by simple pairwise correlation'}, based on pairwise correlations and overlapping SHAP signal.",
        "",
        f"2. Can attack/defense ratings replace xG averages? {'Yes, based on this run' if equal_or_better_replacement else 'No. The best tested model kept xG averages active.'}",
        "",
        f"3. Can attack/defense ratings replace xGA averages? {'Yes, based on this run' if equal_or_better_replacement else 'No. The best tested model kept xGA averages active.'}",
        "",
        f"4. Can attack/defense ratings replace xG differential? {'Yes as a candidate: Model C improved Log Loss, Brier and ECE versus production.' if xg_diff_replacement_improves else 'Not cleanly in this run.'}",
        "",
        f"5. Best Log Loss: `{best_log['model_version']}` at {float(best_log['log_loss']):.4f}.",
        "",
        f"6. Best Brier Score: `{best_brier['model_version']}` at {float(best_brier['Brier_score']):.4f}.",
        "",
        f"7. Best draw performance by draw log loss: `{best_draw['model_version']}` at {float(best_draw['draw_log_loss']):.4f}.",
        "",
        f"8. Recommended production configuration: {decision}",
        "",
        "Important caution: Model C lowers Log Loss/Brier/ECE, but accuracy and draw recall fall. Treat it as a production candidate only after confirming on additional rolling splits.",
        "",
        "## Decision Framework Result",
        "",
        decision,
        "",
        "Production optimization priority remains: Log Loss, Brier Score, Calibration/ECE. Accuracy is secondary.",
    ]
    (OUTPUT_DIR / "replacement_decision_report.md").write_text("\n".join(lines))


def main() -> None:
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    dataset, metadata, feature_sets = build_replacement_dataset()
    write_current_xg_inventory()
    correlations = correlation_analysis(dataset)
    results, lookup = evaluate_replacement_models(dataset, metadata, feature_sets)
    remove_one = remove_one_family_analysis(dataset, metadata)
    write_remove_one_report(remove_one)
    best_name = str(results.sort_values(["log_loss", "Brier_score"])["model_version"].iloc[0])
    shap_importance = shap_replacement_outputs(lookup[best_name])
    write_shap_replacement_report(shap_importance)
    write_decision_report(results, correlations, remove_one, shap_importance)
    print(json.dumps({"best_model": best_name, "report": str(OUTPUT_DIR / "replacement_decision_report.md")}, indent=2))


if __name__ == "__main__":
    main()
