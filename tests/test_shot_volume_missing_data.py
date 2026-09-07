from __future__ import annotations

import pandas as pd

from train_model import build_features


def test_missing_shot_volume_rows_are_not_added_as_zeroes() -> None:
    matches = pd.DataFrame(
        [
            {
                "Season": "2526",
                "Date": pd.Timestamp("2026-05-01").date(),
                "HomeTeam": "Team A",
                "AwayTeam": "Team B",
                "FTHG": 2,
                "FTAG": 0,
                "FTR": "H",
                "home_xg": 1.8,
                "away_xg": 0.4,
                "HS": 14,
                "AS": 7,
                "HST": 5,
                "AST": 2,
            },
            {
                "Season": "2627",
                "Date": pd.Timestamp("2026-09-05").date(),
                "HomeTeam": "Team A",
                "AwayTeam": "Team B",
                "FTHG": 1,
                "FTAG": 1,
                "FTR": "D",
                "home_xg": 1.1,
                "away_xg": 0.9,
                "HS": pd.NA,
                "AS": pd.NA,
                "HST": pd.NA,
                "AST": pd.NA,
            },
        ]
    )

    _, history = build_features(matches, include_xg=True, include_schedule=True, include_shot_volume=True)

    assert history["Team A"]["shots"] == [14.0]
    assert history["Team B"]["shots"] == [7.0]
    assert history["Team A"]["shots_on_target"] == [5.0]
    assert history["Team B"]["shots_on_target"] == [2.0]
