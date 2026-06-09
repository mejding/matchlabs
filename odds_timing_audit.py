from __future__ import annotations

from collections import defaultdict
from dataclasses import dataclass
from pathlib import Path

import pandas as pd

from train_model import DATA_DIR, SEASONS


OUTCOME_SUFFIXES = {
    "H": "home",
    "D": "draw",
    "A": "away",
    "CH": "home",
    "CD": "draw",
    "CA": "away",
}
BOOKMAKER_NAMES = {
    "B365": "Bet365",
    "BFD": "Betfred",
    "BW": "Bet&Win/Bwin",
    "BMGM": "BetMGM",
    "BV": "BetVictor",
    "CL": "Coral",
    "IW": "Interwetten",
    "LB": "Ladbrokes",
    "PS": "Pinnacle",
    "WH": "William Hill",
    "VC": "VC Bet",
    "BF": "Betfair sportsbook",
    "BFE": "Betfair Exchange",
    "1XB": "1xBet",
    "Max": "Market maximum",
    "Avg": "Market average",
}
SOURCE_NOTE = (
    "football-data.co.uk notes classify non-C 1X2 odds as pre-closing odds and C-suffixed odds "
    "as closing odds. Weekend odds are collected Friday afternoons; midweek odds are collected Tuesday afternoons."
)


@dataclass(frozen=True)
class OddsColumnClassification:
    column: str
    source: str
    outcome: str
    odds_type: str
    timing_classification: str
    usage_category: str
    leakage_assessment: str


def is_match_result_odds_column(column: str) -> bool:
    if any(token in column for token in [">2.5", "<2.5", "AHH", "AHA", "AHCh", "AHCA", "AHh"]):
        return False
    return column.endswith(("H", "D", "A", "CH", "CD", "CA"))


def split_odds_column(column: str) -> tuple[str, str]:
    for prefix in sorted(BOOKMAKER_NAMES, key=len, reverse=True):
        if not column.startswith(prefix):
            continue
        suffix = column[len(prefix) :]
        if suffix in OUTCOME_SUFFIXES:
            return prefix, suffix
    suffix = next((candidate for candidate in ["CH", "CD", "CA", "H", "D", "A"] if column.endswith(candidate)), "")
    prefix = column[: -len(suffix)] if suffix else column
    return prefix, suffix


def classify_column(column: str) -> OddsColumnClassification:
    prefix, suffix = split_odds_column(column)
    closing = suffix in {"CH", "CD", "CA"}
    source = BOOKMAKER_NAMES.get(prefix, prefix)
    outcome = OUTCOME_SUFFIXES.get(suffix, "unknown")

    if prefix == "Avg":
        odds_type = "average closing" if closing else "average pre-closing"
        timing = "BENCHMARK_ONLY" if closing else "PREMATCH_CONDITIONAL"
        usage = "Benchmark only" if closing else "Production candidate only with matching live pre-closing feed"
    elif prefix == "Max":
        odds_type = "maximum closing" if closing else "maximum pre-closing"
        timing = "BENCHMARK_ONLY" if closing else "PREMATCH_CONDITIONAL"
        usage = "Benchmark only" if closing else "Production candidate only with matching live pre-closing feed"
    elif closing:
        odds_type = "single-bookmaker closing"
        timing = "BENCHMARK_ONLY"
        usage = "Benchmark only"
    else:
        odds_type = "single-bookmaker pre-closing"
        timing = "PREMATCH_CONDITIONAL"
        usage = "Production candidate only with matching live pre-closing feed"

    if timing == "PREMATCH_CONDITIONAL":
        leakage = (
            "No result leakage, but timestamp leakage is possible if the production prediction is made earlier "
            "than football-data's Friday/Tuesday collection window or if no equivalent live feed exists."
        )
    else:
        leakage = "Closing or market aggregate price may include late pre-kickoff information; keep out of production features."

    return OddsColumnClassification(
        column=column,
        source=source,
        outcome=outcome,
        odds_type=odds_type,
        timing_classification=timing,
        usage_category=usage,
        leakage_assessment=leakage,
    )


def odds_column_inventory() -> pd.DataFrame:
    rows = []
    season_values: dict[str, dict[str, int]] = defaultdict(dict)
    season_missing: dict[str, dict[str, int]] = defaultdict(dict)

    all_columns: set[str] = set()
    for season in SEASONS:
        path = DATA_DIR / f"premier_league_{season}.csv"
        if not path.exists():
            continue
        frame = pd.read_csv(path)
        odds_columns = [column for column in frame.columns if is_match_result_odds_column(column)]
        all_columns.update(odds_columns)
        for column in odds_columns:
            values = pd.to_numeric(frame[column], errors="coerce")
            season_values[column][season] = int(values.notna().sum())
            season_missing[column][season] = int(values.isna().sum())

    for column in sorted(all_columns):
        classification = classify_column(column)
        seasons = sorted(season_values[column])
        rows.append(
            {
                "column": classification.column,
                "bookmaker_or_source": classification.source,
                "outcome": classification.outcome,
                "odds_type": classification.odds_type,
                "timing_classification": classification.timing_classification,
                "recommended_usage_category": classification.usage_category,
                "leakage_assessment": classification.leakage_assessment,
                "seasons_covered": ", ".join(seasons),
                "non_missing_values": sum(season_values[column].values()),
                "missing_values": sum(season_missing[column].values()),
            }
        )
    return pd.DataFrame(rows)


def safe_prematch_columns() -> list[str]:
    inventory = odds_column_inventory()
    return inventory.loc[inventory["timing_classification"] == "SAFE_PREMATCH", "column"].tolist()


def prematch_conditional_columns() -> list[str]:
    inventory = odds_column_inventory()
    return inventory.loc[inventory["timing_classification"] == "PREMATCH_CONDITIONAL", "column"].tolist()


def benchmark_columns() -> list[str]:
    inventory = odds_column_inventory()
    return inventory.loc[inventory["timing_classification"] == "BENCHMARK_ONLY", "column"].tolist()


def write_odds_column_inventory(output_path: Path = Path("odds_column_inventory.md")) -> pd.DataFrame:
    inventory = odds_column_inventory()
    safe = inventory[inventory["timing_classification"] == "SAFE_PREMATCH"]
    conditional = inventory[inventory["timing_classification"] == "PREMATCH_CONDITIONAL"]
    benchmark = inventory[inventory["timing_classification"] == "BENCHMARK_ONLY"]
    unknown = inventory[inventory["timing_classification"] == "UNKNOWN_TIMING"]

    def markdown_table(frame: pd.DataFrame) -> str:
        columns = list(frame.columns)
        lines = ["| " + " | ".join(columns) + " |", "| " + " | ".join(["---"] * len(columns)) + " |"]
        for _, row in frame.iterrows():
            lines.append("| " + " | ".join(str(row[column]) for column in columns) + " |")
        return "\n".join(lines)

    output_path.write_text(
        f"""# Odds Column Inventory

This audit inspects football-data.co.uk CSV files currently downloaded in `data/`.

Conservative timing rule: odds are not production-safe unless the live prediction path can reproduce the historical timing. Football-data documents non-C odds as pre-closing prices and C-suffixed odds as closing prices. Pre-closing is not the same as opening.

Source note: {SOURCE_NOTE}

## Summary

- Total match-result odds columns: {len(inventory)}
- SAFE_PREMATCH columns: {len(safe)}
- PREMATCH_CONDITIONAL columns: {len(conditional)}
- BENCHMARK_ONLY columns: {len(benchmark)}
- UNKNOWN_TIMING columns: {len(unknown)}

## Inventory

{markdown_table(inventory)}

## Recommended Usage

- SAFE_PREMATCH: may be used in production only if the live data feed guarantees values are known before kickoff and the historical timing matches production timing.
- PREMATCH_CONDITIONAL: no result leakage, but only safe for production if the app obtains equivalent pre-closing odds before kickoff at the same point in the betting lifecycle.
- BENCHMARK_ONLY: useful for model-vs-market evaluation, not production training.
- RESEARCH_ONLY / UNKNOWN_TIMING: can be tested offline, but must not be used in production.
"""
    )
    inventory.to_csv(Path("evaluation") / "market_intelligence" / "odds_column_inventory.csv", index=False)
    return inventory


def write_market_odds_timing_discovery_report(
    inventory: pd.DataFrame,
    output_path: Path = Path("market_odds_timing_discovery_report.md"),
) -> None:
    group = (
        inventory.groupby(["timing_classification", "odds_type"], as_index=False)
        .agg(
            column_count=("column", "count"),
            non_missing_values=("non_missing_values", "sum"),
            missing_values=("missing_values", "sum"),
            columns=("column", lambda values: ", ".join(values)),
        )
        .sort_values(["timing_classification", "odds_type"])
    )
    source_group = (
        inventory.groupby(["bookmaker_or_source", "timing_classification"], as_index=False)
        .agg(
            columns=("column", lambda values: ", ".join(values)),
            seasons=("seasons_covered", lambda values: " | ".join(sorted(set(values)))),
            non_missing_values=("non_missing_values", "sum"),
            missing_values=("missing_values", "sum"),
        )
        .sort_values(["bookmaker_or_source", "timing_classification"])
    )

    def markdown_table(frame: pd.DataFrame) -> str:
        columns = list(frame.columns)
        lines = ["| " + " | ".join(columns) + " |", "| " + " | ".join(["---"] * len(columns)) + " |"]
        for _, row in frame.iterrows():
            lines.append("| " + " | ".join(str(row[column]) for column in columns) + " |")
        return "\n".join(lines)

    preclosing = inventory[inventory["timing_classification"] == "PREMATCH_CONDITIONAL"]
    closing = inventory[inventory["timing_classification"] == "BENCHMARK_ONLY"]
    output_path.write_text(
        f"""# Market Odds Timing Discovery Report

## Scope

This report audits the 1X2 bookmaker odds columns in the local football-data.co.uk Premier League CSV files from 2019/20 through 2025/26.

Official football-data notes used for timing classification: https://www.football-data.co.uk/notes.txt

## Timing Finding

{SOURCE_NOTE}

Interpretation:

- Non-`C` 1X2 columns such as `B365H/B365D/B365A`, `PSH/PSD/PSA`, `AvgH/AvgD/AvgA` are **pre-closing odds**.
- `C` columns such as `B365CH/B365CD/B365CA`, `PSCH/PSCD/PSCA`, `AvgCH/AvgCD/AvgCA` are **closing odds**.
- None of the local football-data columns are documented as opening odds.

## Leakage Assessment

Pre-closing odds do not leak the final result because they are collected before kickoff. They can still create **timestamp leakage** if the production app predicts earlier than the Friday/Tuesday collection point or cannot access an equivalent pre-closing feed.

Closing odds should not be used as production model inputs because they can contain late injury, lineup, weather and market information that would not be available at earlier prediction time.

## Summary

- Total 1X2 odds columns: {len(inventory)}
- Pre-closing conditional columns: {len(preclosing)}
- Closing / benchmark-only columns: {len(closing)}
- Opening odds columns: 0
- Safe production columns today: 0

## Timing Groups

{markdown_table(group)}

## Source Coverage

{markdown_table(source_group)}

## Recommendation

Treat football-data non-`C` 1X2 odds as a high-priority production candidate, not as active production yet.

They can move into production only if:

1. We define the product as a pre-match prediction made after the equivalent odds collection point.
2. The app has a live/reproducible odds feed with the same timing as the historical pre-closing columns.
3. A time-based model comparison shows improved Log Loss or Brier Score.
4. Calibration does not materially worsen.

Until those requirements are met:

- Use closing odds as benchmark only.
- Use non-`C` pre-closing odds for the next market feature experiment.
- Do not describe the football-data odds as opening odds.
"""
    )


def main() -> None:
    Path("evaluation/market_intelligence").mkdir(parents=True, exist_ok=True)
    inventory = write_odds_column_inventory()
    write_market_odds_timing_discovery_report(inventory)
    print(f"Wrote odds_column_inventory.md with {len(inventory)} odds columns.")


if __name__ == "__main__":
    main()
