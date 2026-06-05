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
    "BW": "Bet&Win/Bwin",
    "IW": "Interwetten",
    "PS": "Pinnacle",
    "WH": "William Hill",
    "VC": "VC Bet",
    "BF": "Betfair sportsbook",
    "BFE": "Betfair Exchange",
    "1XB": "1xBet",
    "Max": "Market maximum",
    "Avg": "Market average",
}


@dataclass(frozen=True)
class OddsColumnClassification:
    column: str
    source: str
    outcome: str
    odds_type: str
    timing_classification: str
    usage_category: str


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
        odds_type = "average closing" if closing else "average listed"
        timing = "BENCHMARK_ONLY"
        usage = "Benchmark only"
    elif prefix == "Max":
        odds_type = "maximum closing" if closing else "maximum listed"
        timing = "BENCHMARK_ONLY"
        usage = "Benchmark only"
    elif closing:
        odds_type = "single-bookmaker closing"
        timing = "BENCHMARK_ONLY"
        usage = "Benchmark only"
    else:
        odds_type = "single-bookmaker listed"
        timing = "UNKNOWN_TIMING"
        usage = "Research only until collection time is verified"

    return OddsColumnClassification(
        column=column,
        source=source,
        outcome=outcome,
        odds_type=odds_type,
        timing_classification=timing,
        usage_category=usage,
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
                "seasons_covered": ", ".join(seasons),
                "non_missing_values": sum(season_values[column].values()),
                "missing_values": sum(season_missing[column].values()),
            }
        )
    return pd.DataFrame(rows)


def safe_prematch_columns() -> list[str]:
    inventory = odds_column_inventory()
    return inventory.loc[inventory["timing_classification"] == "SAFE_PREMATCH", "column"].tolist()


def benchmark_columns() -> list[str]:
    inventory = odds_column_inventory()
    return inventory.loc[inventory["timing_classification"] == "BENCHMARK_ONLY", "column"].tolist()


def write_odds_column_inventory(output_path: Path = Path("odds_column_inventory.md")) -> pd.DataFrame:
    inventory = odds_column_inventory()
    safe = inventory[inventory["timing_classification"] == "SAFE_PREMATCH"]
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

Conservative timing rule: odds are not production-safe unless their pre-match availability is explicitly verified. Closing, average and maximum market prices are treated as benchmark-only because they may represent late or closing prices.

## Summary

- Total match-result odds columns: {len(inventory)}
- SAFE_PREMATCH columns: {len(safe)}
- BENCHMARK_ONLY columns: {len(benchmark)}
- UNKNOWN_TIMING columns: {len(unknown)}

## Inventory

{markdown_table(inventory)}

## Recommended Usage

- SAFE_PREMATCH: may be used in production only if the live data feed guarantees values are known before kickoff.
- BENCHMARK_ONLY: useful for model-vs-market evaluation, not production training.
- RESEARCH_ONLY / UNKNOWN_TIMING: can be tested offline, but must not be used in production.
"""
    )
    inventory.to_csv(Path("evaluation") / "market_intelligence" / "odds_column_inventory.csv", index=False)
    return inventory


def main() -> None:
    Path("evaluation/market_intelligence").mkdir(parents=True, exist_ok=True)
    inventory = write_odds_column_inventory()
    print(f"Wrote odds_column_inventory.md with {len(inventory)} odds columns.")


if __name__ == "__main__":
    main()
