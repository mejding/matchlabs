import json

import pandas as pd

import refresh_data


def test_extract_understat_match_info_reads_shot_columns() -> None:
    payload = json.dumps(
        {
            "h_shot": "16",
            "a_shot": "13",
            "h_shotOnTarget": "9",
            "a_shotOnTarget": "5",
        }
    ).replace('"', '\\"')
    html = f"var match_info = JSON.parse('{payload}')"

    info = refresh_data._extract_understat_match_info(html)

    assert info["h_shot"] == "16"
    assert info["a_shot"] == "13"
    assert info["h_shotOnTarget"] == "9"
    assert info["a_shotOnTarget"] == "5"


def test_backfill_understat_shots_for_missing_football_data_rows(tmp_path, monkeypatch) -> None:
    data_dir = tmp_path / "data"
    data_dir.mkdir()
    csv_path = data_dir / "premier_league_2627.csv"
    understat_path = data_dir / "understat_epl_2026.json"

    pd.DataFrame(
        [
            {
                "Date": "06/09/2026",
                "HomeTeam": "Arsenal",
                "AwayTeam": "Chelsea",
                "FTHG": 2,
                "FTAG": 1,
                "FTR": "H",
                "HS": pd.NA,
                "AS": pd.NA,
                "HST": pd.NA,
                "AST": pd.NA,
            }
        ]
    ).to_csv(csv_path, index=False)
    understat_path.write_text(
        json.dumps(
            {
                "dates": [
                    {
                        "id": "31209",
                        "isResult": True,
                        "datetime": "2026-09-06 15:30:00",
                        "h": {"title": "Arsenal"},
                        "a": {"title": "Chelsea"},
                    }
                ]
            }
        ),
        encoding="utf-8",
    )

    monkeypatch.setattr(refresh_data, "DATA_DIR", data_dir)
    monkeypatch.setattr(
        refresh_data,
        "_download_understat_match_info",
        lambda match_id: {
            "h_shot": "16",
            "a_shot": "13",
            "h_shotOnTarget": "9",
            "a_shotOnTarget": "5",
        },
    )

    result = refresh_data.backfill_understat_shots_for_season("2627", 2026, dry_run=False)

    updated = pd.read_csv(csv_path)
    assert result.status == "updated"
    assert result.rows == 1
    assert updated.loc[0, "HS"] == 16
    assert updated.loc[0, "AS"] == 13
    assert updated.loc[0, "HST"] == 9
    assert updated.loc[0, "AST"] == 5
