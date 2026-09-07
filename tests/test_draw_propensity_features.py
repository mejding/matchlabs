from datetime import date

import pandas as pd

from draw_propensity_features import build_draw_propensity_features, draw_propensity_feature_columns


def test_draw_propensity_features_use_only_previous_matches() -> None:
    matches = pd.DataFrame(
        [
            {
                "Season": "2627",
                "Date": date(2026, 8, 21),
                "HomeTeam": "Team A",
                "AwayTeam": "Team B",
                "FTHG": 1,
                "FTAG": 1,
                "FTR": "D",
                "home_xg": 0.8,
                "away_xg": 0.7,
                "HST": 2,
                "AST": 2,
            },
            {
                "Season": "2627",
                "Date": date(2026, 8, 28),
                "HomeTeam": "Team A",
                "AwayTeam": "Team C",
                "FTHG": 2,
                "FTAG": 0,
                "FTR": "H",
                "home_xg": 1.8,
                "away_xg": 0.4,
                "HST": 5,
                "AST": 1,
            },
        ]
    )

    features = build_draw_propensity_features(matches)

    assert list(features.columns) == draw_propensity_feature_columns()
    assert features.loc[0, "combined_draw_rate_last10"] == 0.0
    assert features.loc[1, "home_draw_rate_last10"] == 1.0
    assert features.loc[1, "away_draw_rate_last10"] == 0.0
    assert 0.0 <= features.loc[1, "draw_propensity_score"] <= 1.0
