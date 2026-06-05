from __future__ import annotations

from pathlib import Path

import numpy as np
import pandas as pd

from odds_timing_audit import safe_prematch_columns
from train_model import DATA_DIR, SEASONS


ODDS_PRIORITY = [
    ("AvgCH", "AvgCD", "AvgCA", "average closing odds"),
    ("MaxCH", "MaxCD", "MaxCA", "maximum closing odds"),
    ("B365CH", "B365CD", "B365CA", "Bet365 closing odds"),
    ("BWCH", "BWCD", "BWCA", "Bwin closing odds"),
    ("IWCH", "IWCD", "IWCA", "Interwetten closing odds"),
    ("PSCH", "PSCD", "PSCA", "Pinnacle closing odds"),
    ("WHCH", "WHCD", "WHCA", "William Hill closing odds"),
    ("VCCH", "VCCD", "VCCA", "VC Bet closing odds"),
    ("BFCH", "BFCD", "BFCA", "Betfair closing odds"),
    ("BFECH", "BFECD", "BFECA", "Betfair Exchange closing odds"),
    ("1XBCH", "1XBCD", "1XBCA", "1xBet closing odds"),
    ("AvgH", "AvgD", "AvgA", "average listed odds"),
    ("MaxH", "MaxD", "MaxA", "maximum listed odds"),
]
SINGLE_BOOKMAKER_LISTED_PRIORITY = [
    ("B365H", "B365D", "B365A", "Bet365 listed odds"),
    ("BWH", "BWD", "BWA", "Bwin listed odds"),
    ("IWH", "IWD", "IWA", "Interwetten listed odds"),
    ("PSH", "PSD", "PSA", "Pinnacle listed odds"),
    ("WHH", "WHD", "WHA", "William Hill listed odds"),
    ("VCH", "VCD", "VCA", "VC Bet listed odds"),
    ("BFH", "BFD", "BFA", "Betfair listed odds"),
    ("1XBH", "1XBD", "1XBA", "1xBet listed odds"),
]


def decimal_odds_to_probabilities(home_odds: float, draw_odds: float, away_odds: float) -> dict[str, float]:
    raw_home = 1.0 / home_odds
    raw_draw = 1.0 / draw_odds
    raw_away = 1.0 / away_odds
    total = raw_home + raw_draw + raw_away
    return {
        "market_home_prob": raw_home / total,
        "market_draw_prob": raw_draw / total,
        "market_away_prob": raw_away / total,
        "market_margin": total - 1.0,
    }


def odds_priority_for_mode(market_mode: str) -> list[tuple[str, str, str, str]]:
    if market_mode == "none":
        return []
    if market_mode == "safe-prematch":
        safe_columns = set(safe_prematch_columns())
        return [
            (home, draw, away, source)
            for home, draw, away, source in SINGLE_BOOKMAKER_LISTED_PRIORITY
            if {home, draw, away} <= safe_columns
        ]
    if market_mode == "research":
        return SINGLE_BOOKMAKER_LISTED_PRIORITY + ODDS_PRIORITY
    if market_mode == "benchmark":
        return ODDS_PRIORITY
    raise ValueError("market_mode must be one of: none, benchmark, research, safe-prematch")


def load_market_odds(market_mode: str = "benchmark") -> pd.DataFrame:
    priority = odds_priority_for_mode(market_mode)
    if not priority:
        return pd.DataFrame()

    rows = []
    for season in SEASONS:
        path = DATA_DIR / f"premier_league_{season}.csv"
        if not path.exists():
            continue
        frame = pd.read_csv(path)
        frame["Date"] = pd.to_datetime(frame["Date"], dayfirst=True, errors="coerce").dt.date
        for _, row in frame.iterrows():
            odds_source = None
            selected = None
            for home_col, draw_col, away_col, source in priority:
                if all(col in frame.columns for col in [home_col, draw_col, away_col]):
                    values = [row.get(home_col), row.get(draw_col), row.get(away_col)]
                    if all(pd.notna(value) and float(value) > 1.0 for value in values):
                        odds_source = source
                        selected = values
                        break
            if selected is None:
                continue
            probs = decimal_odds_to_probabilities(float(selected[0]), float(selected[1]), float(selected[2]))
            favorite_class = int(np.argmax([probs["market_home_prob"], probs["market_draw_prob"], probs["market_away_prob"]]))
            rows.append(
                {
                    "Season": season,
                    "Date": row["Date"],
                    "HomeTeam": row["HomeTeam"],
                    "AwayTeam": row["AwayTeam"],
                    "odds_source": odds_source,
                    "market_mode": market_mode,
                    "home_odds": float(selected[0]),
                    "draw_odds": float(selected[1]),
                    "away_odds": float(selected[2]),
                    **probs,
                    "market_favorite_prob": max(probs["market_home_prob"], probs["market_draw_prob"], probs["market_away_prob"]),
                    "market_favorite_class": favorite_class,
                }
            )
    return pd.DataFrame(rows)


def add_market_features(matches: pd.DataFrame, market_mode: str = "benchmark") -> pd.DataFrame:
    odds = load_market_odds(market_mode=market_mode)
    if odds.empty:
        return matches.copy()
    merged = matches.merge(odds, on=["Season", "Date", "HomeTeam", "AwayTeam"], how="left", validate="one_to_one")
    return merged


def add_model_market_edges(dataset: pd.DataFrame, model_probabilities: np.ndarray) -> pd.DataFrame:
    enriched = dataset.copy()
    enriched["model_vs_market_home_edge"] = model_probabilities[:, 0] - enriched["market_home_prob"]
    enriched["model_vs_market_draw_edge"] = model_probabilities[:, 1] - enriched["market_draw_prob"]
    enriched["model_vs_market_away_edge"] = model_probabilities[:, 2] - enriched["market_away_prob"]
    return enriched
