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

from evaluation.model_evaluation import time_based_split
from feature_experiments import _markdown_table, train_xgb
from market_intelligence_experiments import MARKET_PROB_COLUMNS, normalize_probabilities
from market_odds_features import add_market_features
from train_model import SCHEDULE_FEATURE_COLUMNS, build_features, load_matches_with_xg

matplotlib.use("Agg")

OUTPUT_DIR = Path("evaluation") / "betting_validation"
OUTCOME_LABELS = ["home", "draw", "away"]
RESULT_LABELS = {0: "home", 1: "draw", 2: "away"}
THRESHOLDS = [0.0, 0.03, 0.05, 0.08, 0.10]
STAKE = 1.0


def fair_odds_from_probabilities(probabilities: np.ndarray) -> np.ndarray:
    clipped = np.clip(probabilities, 1e-9, 1.0)
    normalized = clipped / clipped.sum(axis=1, keepdims=True)
    return 1.0 / normalized


def max_drawdown(cumulative_profit: pd.Series) -> float:
    if cumulative_profit.empty:
        return 0.0
    running_peak = cumulative_profit.cummax().clip(lower=0.0)
    drawdown = running_peak - cumulative_profit
    return float(drawdown.max())


def profit_for_bet(actual: str, outcome: str, bookmaker_odds: float) -> float:
    return float(bookmaker_odds - STAKE) if actual == outcome else -STAKE


def build_validation_dataset(market_mode: str = "benchmark") -> pd.DataFrame:
    matches = add_market_features(load_matches_with_xg().sort_values("Date").reset_index(drop=True), market_mode=market_mode)
    required_columns = MARKET_PROB_COLUMNS + ["home_odds", "draw_odds", "away_odds"]
    missing = [column for column in required_columns if column not in matches.columns]
    if missing:
        raise ValueError(f"Historical bookmaker odds are unavailable for market_mode={market_mode}: {missing}")

    matches = matches.dropna(subset=required_columns).reset_index(drop=True)
    odds_dataset, _ = build_features(matches, include_xg=True, include_schedule=True)
    for column in required_columns + ["odds_source", "market_mode"]:
        if column in matches.columns:
            odds_dataset[column] = matches[column].values
    odds_metadata = matches[["Season", "Date", "HomeTeam", "AwayTeam", "FTR", "odds_source", "market_mode"]].reset_index(drop=True)

    split = time_based_split(odds_dataset[SCHEDULE_FEATURE_COLUMNS], odds_dataset["target"], odds_metadata)
    model = train_xgb(split.X_train, split.y_train)
    model_probs = normalize_probabilities(model.predict_proba(split.X_test))
    market_probs = odds_dataset.loc[split.X_test.index, MARKET_PROB_COLUMNS].to_numpy(dtype=float)
    market_probs = normalize_probabilities(market_probs)
    fair_odds = fair_odds_from_probabilities(model_probs)

    rows = split.test_metadata.reset_index(drop=True).copy()
    y_test = split.y_test.reset_index(drop=True)
    rows["actual"] = y_test.map(RESULT_LABELS)
    rows["match"] = rows["HomeTeam"].astype(str) + " vs " + rows["AwayTeam"].astype(str)
    rows["model_pick"] = pd.Series(model_probs.argmax(axis=1)).map(RESULT_LABELS)
    rows["market_pick"] = pd.Series(market_probs.argmax(axis=1)).map(RESULT_LABELS)
    rows["model_confidence"] = model_probs.max(axis=1)
    rows["market_confidence"] = market_probs.max(axis=1)

    source_rows = odds_dataset.loc[split.X_test.index].reset_index(drop=True)
    for index, outcome in enumerate(OUTCOME_LABELS):
        rows[f"model_{outcome}_prob"] = model_probs[:, index]
        rows[f"market_{outcome}_prob"] = market_probs[:, index]
        rows[f"model_{outcome}_fair_odds"] = fair_odds[:, index]
        rows[f"bookmaker_{outcome}_odds"] = source_rows[f"{outcome}_odds"].astype(float).to_numpy()
        rows[f"{outcome}_edge"] = (rows[f"bookmaker_{outcome}_odds"] / rows[f"model_{outcome}_fair_odds"]) - 1.0

    if "odds_source" in source_rows.columns:
        rows["odds_source"] = source_rows["odds_source"].values
    if "market_mode" in source_rows.columns:
        rows["market_mode"] = source_rows["market_mode"].values

    rows["cutoff_date"] = split.cutoff_date
    return rows


def strategy_bets(validation: pd.DataFrame, threshold: float) -> pd.DataFrame:
    bets = []
    for _, row in validation.iterrows():
        for outcome in OUTCOME_LABELS:
            edge = float(row[f"{outcome}_edge"])
            if edge <= threshold:
                continue
            bookmaker_odds = float(row[f"bookmaker_{outcome}_odds"])
            profit = profit_for_bet(str(row["actual"]), outcome, bookmaker_odds)
            bets.append(
                {
                    "Date": row["Date"],
                    "match": row["match"],
                    "HomeTeam": row["HomeTeam"],
                    "AwayTeam": row["AwayTeam"],
                    "actual": row["actual"],
                    "bet_type": outcome,
                    "threshold": threshold,
                    "model_probability": row[f"model_{outcome}_prob"],
                    "market_probability": row[f"market_{outcome}_prob"],
                    "model_fair_odds": row[f"model_{outcome}_fair_odds"],
                    "bookmaker_odds": bookmaker_odds,
                    "edge": edge,
                    "model_confidence": row["model_confidence"],
                    "profit": profit,
                    "won": int(profit > 0),
                    "stake": STAKE,
                    "odds_source": row.get("odds_source", ""),
                }
            )
    bets_frame = pd.DataFrame(bets)
    if bets_frame.empty:
        return bets_frame
    return bets_frame.sort_values(["Date", "match", "bet_type"]).reset_index(drop=True)


def pick_strategy(validation: pd.DataFrame, picker: str) -> pd.DataFrame:
    bets = []
    for _, row in validation.iterrows():
        outcome = str(row[f"{picker}_pick"])
        bookmaker_odds = float(row[f"bookmaker_{outcome}_odds"])
        profit = profit_for_bet(str(row["actual"]), outcome, bookmaker_odds)
        bets.append(
            {
                "Date": row["Date"],
                "match": row["match"],
                "HomeTeam": row["HomeTeam"],
                "AwayTeam": row["AwayTeam"],
                "actual": row["actual"],
                "bet_type": outcome,
                "threshold": np.nan,
                "model_probability": row[f"model_{outcome}_prob"],
                "market_probability": row[f"market_{outcome}_prob"],
                "model_fair_odds": row[f"model_{outcome}_fair_odds"],
                "bookmaker_odds": bookmaker_odds,
                "edge": row[f"{outcome}_edge"],
                "model_confidence": row["model_confidence"],
                "profit": profit,
                "won": int(profit > 0),
                "stake": STAKE,
                "odds_source": row.get("odds_source", ""),
            }
        )
    return pd.DataFrame(bets).sort_values(["Date", "match"]).reset_index(drop=True)


def summarize_bets(name: str, bets: pd.DataFrame) -> dict[str, float | str | int]:
    if bets.empty:
        return {
            "strategy": name,
            "bets": 0,
            "hit_rate": 0.0,
            "profit": 0.0,
            "stake": 0.0,
            "roi": 0.0,
            "yield": 0.0,
            "maximum_drawdown": 0.0,
            "average_edge": 0.0,
            "average_odds": 0.0,
        }

    cumulative = bets["profit"].cumsum()
    stake = float(bets["stake"].sum())
    profit = float(bets["profit"].sum())
    return {
        "strategy": name,
        "bets": int(len(bets)),
        "hit_rate": float(bets["won"].mean()),
        "profit": profit,
        "stake": stake,
        "roi": profit / stake if stake else 0.0,
        "yield": profit / len(bets) if len(bets) else 0.0,
        "maximum_drawdown": max_drawdown(cumulative),
        "average_edge": float(bets["edge"].mean()),
        "average_odds": float(bets["bookmaker_odds"].mean()),
    }


def summarize_by_group(bets: pd.DataFrame, group_column: str) -> pd.DataFrame:
    rows = []
    for group, frame in bets.groupby(group_column, dropna=False):
        summary = summarize_bets(str(group), frame.reset_index(drop=True))
        summary[group_column] = group
        rows.append(summary)
    if not rows:
        return pd.DataFrame()
    return pd.DataFrame(rows).drop(columns=["strategy"]).sort_values("roi", ascending=False)


def confidence_bucket(confidence: float) -> str:
    if confidence >= 0.62:
        return "high_confidence"
    if confidence >= 0.48:
        return "medium_confidence"
    return "low_confidence"


def plot_equity_curves(curves: dict[str, pd.DataFrame], output_path: Path, title: str) -> None:
    fig, ax = plt.subplots(figsize=(12, 6))
    for name, bets in curves.items():
        if bets.empty:
            continue
        ordered = bets.sort_values("Date").reset_index(drop=True)
        ax.plot(range(1, len(ordered) + 1), ordered["profit"].cumsum(), label=name)
    ax.axhline(0, color="#111827", linewidth=1)
    ax.set_title(title)
    ax.set_xlabel("Bet number")
    ax.set_ylabel("Cumulative profit, 1 unit stakes")
    ax.grid(alpha=0.25)
    ax.legend()
    fig.tight_layout()
    fig.savefig(output_path, dpi=160)
    plt.close(fig)


def plot_roi_table(summary: pd.DataFrame, output_path: Path) -> None:
    frame = summary.copy()
    fig, ax = plt.subplots(figsize=(11, 5))
    colors = ["#16a34a" if value >= 0 else "#dc2626" for value in frame["roi"]]
    ax.bar(frame["strategy"], frame["roi"] * 100, color=colors)
    ax.axhline(0, color="#111827", linewidth=1)
    ax.set_title("Betting Validation ROI by Strategy")
    ax.set_ylabel("ROI (%)")
    ax.tick_params(axis="x", rotation=25)
    ax.grid(axis="y", alpha=0.25)
    fig.tight_layout()
    fig.savefig(output_path, dpi=160)
    plt.close(fig)


def write_report(
    validation: pd.DataFrame,
    strategy_summary: pd.DataFrame,
    bet_type_summary: pd.DataFrame,
    confidence_summary: pd.DataFrame,
    market_mode: str,
) -> None:
    edge_rows = strategy_summary[strategy_summary["strategy"].str.startswith("edge_")].copy()
    best_edge = edge_rows.sort_values(["roi", "profit"], ascending=False).iloc[0] if not edge_rows.empty else None
    model_only = strategy_summary[strategy_summary["strategy"] == "model_only_top_pick"].iloc[0]
    market_only = strategy_summary[strategy_summary["strategy"] == "market_only_favorite"].iloc[0]
    profitable_edges = edge_rows[edge_rows["profit"] > 0]

    best_threshold_text = "None"
    if best_edge is not None:
        best_threshold_text = f"{best_edge['strategy']} with ROI {float(best_edge['roi']) * 100:.2f}%"

    genuine_value = best_edge is not None and float(best_edge["roi"]) > 0 and float(best_edge["bets"]) >= 25
    model_beats_market = float(model_only["roi"]) > float(market_only["roi"])
    best_bet_type = bet_type_summary.iloc[0]["bet_type"] if not bet_type_summary.empty else "N/A"

    Path("market_validation_report.md").write_text(
        f"""# Historical Betting Validation Report

This report tests whether model edges versus bookmaker odds would have produced profitable historical selections.

Important timing policy: this is a research backtest using `market_mode={market_mode}`. football-data non-C 1X2 odds are documented as pre-closing, while C-suffixed odds are closing. These odds do not use match results, but production use still requires an equivalent live/reproducible odds feed with controlled timing.

Test period starts: `{validation['Date'].min()}`  
Test period ends: `{validation['Date'].max()}`  
Matches evaluated: `{len(validation)}`

Edge formula:

```text
edge = bookmaker_odds / model_fair_odds - 1
model_fair_odds = 1 / model_probability
```

All simulations use 1 unit flat stakes.

## Strategy Summary

{_markdown_table(strategy_summary, ['strategy', 'bets', 'hit_rate', 'profit', 'roi', 'yield', 'maximum_drawdown', 'average_edge', 'average_odds'])}

## Bet Type Summary

{_markdown_table(bet_type_summary, ['bet_type', 'bets', 'hit_rate', 'profit', 'roi', 'yield', 'maximum_drawdown', 'average_edge', 'average_odds']) if not bet_type_summary.empty else 'No edge bets were selected.'}

## Confidence Summary

{_markdown_table(confidence_summary, ['confidence_bucket', 'bets', 'hit_rate', 'profit', 'roi', 'yield', 'maximum_drawdown', 'average_edge', 'average_odds']) if not confidence_summary.empty else 'No confidence-bucket edge bets were selected.'}

## 1. Do positive-edge bets outperform the market?

Model-only top picks ROI: `{float(model_only['roi']) * 100:.2f}%`  
Market-only favorite ROI: `{float(market_only['roi']) * 100:.2f}%`

Answer: {'Yes, model top picks outperform the market favorite baseline in this run.' if model_beats_market else 'No, model top picks do not outperform the market favorite baseline in this run.'}

For edge selections, profitable threshold rows: `{len(profitable_edges)}` out of `{len(edge_rows)}` tested thresholds.

## 2. Which edge threshold performs best?

Best threshold by ROI and profit: `{best_threshold_text}`.

## 3. Is the model finding genuine value?

Answer: {'Potentially yes, but treat it as research-only because odds timing is not verified and sample size should be stress-tested.' if genuine_value else 'Not convincingly in this run. Either ROI is negative, sample size is thin, or profitability is not robust across thresholds.'}

## 4. Which bet types work best?

Best edge bet type by ROI: `{best_bet_type}`.

Review `evaluation/betting_validation/bet_type_summary.csv` before trusting this, because draw and away bets can have smaller samples and higher variance.

## 5. Does model confidence improve betting performance?

Use `evaluation/betting_validation/confidence_summary.csv`. A useful confidence signal should show higher ROI or lower drawdown in medium/high confidence buckets. If confidence buckets are inconsistent, edge size is more informative than raw model confidence.

## Artifacts

- `evaluation/betting_validation/test_match_edges.csv`
- `evaluation/betting_validation/all_edge_bets.csv`
- `evaluation/betting_validation/strategy_summary.csv`
- `evaluation/betting_validation/bet_type_summary.csv`
- `evaluation/betting_validation/confidence_summary.csv`
- `evaluation/betting_validation/equity_curves.png`
- `evaluation/betting_validation/edge_threshold_equity_curves.png`
- `evaluation/betting_validation/strategy_roi.png`
"""
    )


def run_validation(market_mode: str = "benchmark") -> pd.DataFrame:
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    validation = build_validation_dataset(market_mode=market_mode)
    validation.to_csv(OUTPUT_DIR / "test_match_edges.csv", index=False)

    model_only = pick_strategy(validation, "model")
    market_only = pick_strategy(validation, "market")

    all_edge_bets = []
    strategy_rows = [
        summarize_bets("model_only_top_pick", model_only),
        summarize_bets("market_only_favorite", market_only),
    ]
    edge_curves: dict[str, pd.DataFrame] = {}
    for threshold in THRESHOLDS:
        bets = strategy_bets(validation, threshold)
        strategy_name = f"edge_gt_{int(threshold * 100)}pct"
        if not bets.empty:
            bets["strategy"] = strategy_name
            all_edge_bets.append(bets)
        edge_curves[strategy_name] = bets
        strategy_rows.append(summarize_bets(strategy_name, bets))

    edge_bets = pd.concat(all_edge_bets, ignore_index=True) if all_edge_bets else pd.DataFrame()
    edge_bets.to_csv(OUTPUT_DIR / "all_edge_bets.csv", index=False)
    model_only.to_csv(OUTPUT_DIR / "model_only_bets.csv", index=False)
    market_only.to_csv(OUTPUT_DIR / "market_only_bets.csv", index=False)

    strategy_summary = pd.DataFrame(strategy_rows)
    strategy_summary.to_csv(OUTPUT_DIR / "strategy_summary.csv", index=False)

    if not edge_bets.empty:
        threshold_5 = edge_bets[edge_bets["strategy"] == "edge_gt_5pct"].copy()
        if threshold_5.empty:
            threshold_5 = edge_bets.copy()
        threshold_5["confidence_bucket"] = threshold_5["model_confidence"].map(confidence_bucket)
        bet_type_summary = summarize_by_group(threshold_5, "bet_type")
        confidence_summary = summarize_by_group(threshold_5, "confidence_bucket")
    else:
        bet_type_summary = pd.DataFrame()
        confidence_summary = pd.DataFrame()

    bet_type_summary.to_csv(OUTPUT_DIR / "bet_type_summary.csv", index=False)
    confidence_summary.to_csv(OUTPUT_DIR / "confidence_summary.csv", index=False)

    plot_equity_curves(
        {
            "model_only_top_pick": model_only,
            "market_only_favorite": market_only,
            **edge_curves,
        },
        OUTPUT_DIR / "equity_curves.png",
        "Historical Betting Validation Equity Curves",
    )
    plot_equity_curves(edge_curves, OUTPUT_DIR / "edge_threshold_equity_curves.png", "Edge Threshold Equity Curves")
    plot_roi_table(strategy_summary, OUTPUT_DIR / "strategy_roi.png")

    write_report(validation, strategy_summary, bet_type_summary, confidence_summary, market_mode)
    return strategy_summary


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Validate model betting edges against historical bookmaker odds.")
    parser.add_argument(
        "--market-mode",
        choices=["benchmark", "research", "preclosing", "safe-prematch"],
        default="benchmark",
        help="Odds mode. preclosing uses football-data non-C 1X2 odds; benchmark uses closing/aggregate odds.",
    )
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    summary = run_validation(market_mode=args.market_mode)
    best = summary.sort_values(["roi", "profit"], ascending=False).iloc[0]
    print(json.dumps({"market_mode": args.market_mode, "best_strategy": str(best["strategy"])}, indent=2))


if __name__ == "__main__":
    main()
