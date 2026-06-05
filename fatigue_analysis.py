from __future__ import annotations

from pathlib import Path

import matplotlib
import numpy as np
import pandas as pd
from matplotlib import pyplot as plt

from train_model import points_for_team

matplotlib.use("Agg")


def _team_match_rows(matches: pd.DataFrame, features: pd.DataFrame) -> pd.DataFrame:
    rows = []
    joined = pd.concat([matches.reset_index(drop=True), features.reset_index(drop=True)], axis=1)
    for _, row in joined.iterrows():
        for side, team_col, opponent_col in (
            ("home", "HomeTeam", "AwayTeam"),
            ("away", "AwayTeam", "HomeTeam"),
        ):
            rows.append(
                {
                    "Date": row["Date"],
                    "team": row[team_col],
                    "opponent": row[opponent_col],
                    "side": side,
                    "points": points_for_team(row, row[team_col]),
                    "had_midweek_match": float(row.get(f"{side}_had_midweek_match", 0.0)),
                    "days_rest": float(row.get(f"{side}_days_rest", 14.0)),
                    "fixture_congestion_score": float(row.get(f"{side}_fixture_congestion_score", 0.0)),
                    "played_europe_midweek": float(row.get(f"{side}_played_europe_midweek", 0.0)),
                }
            )
    return pd.DataFrame(rows)


def team_midweek_performance(matches: pd.DataFrame, features: pd.DataFrame) -> pd.DataFrame:
    team_rows = _team_match_rows(matches, features)
    grouped = []
    for team, group in team_rows.groupby("team"):
        midweek = group[group["had_midweek_match"] == 1]
        normal = group[group["had_midweek_match"] == 0]
        grouped.append(
            {
                "team": team,
                "matches_after_midweek": int(len(midweek)),
                "points_per_match_after_midweek": float(midweek["points"].mean()) if len(midweek) else np.nan,
                "points_per_match_normal": float(normal["points"].mean()) if len(normal) else np.nan,
                "midweek_points_delta": (
                    float(midweek["points"].mean() - normal["points"].mean())
                    if len(midweek) and len(normal)
                    else np.nan
                ),
            }
        )
    return pd.DataFrame(grouped).sort_values("midweek_points_delta", ascending=False, na_position="last")


def short_rest_performance(matches: pd.DataFrame, features: pd.DataFrame, short_rest_days: int = 4) -> pd.DataFrame:
    team_rows = _team_match_rows(matches, features)
    grouped = []
    for team, group in team_rows.groupby("team"):
        short = group[group["days_rest"] <= short_rest_days]
        rested = group[group["days_rest"] > short_rest_days]
        grouped.append(
            {
                "team": team,
                "short_rest_matches": int(len(short)),
                "points_per_match_short_rest": float(short["points"].mean()) if len(short) else np.nan,
                "points_per_match_rested": float(rested["points"].mean()) if len(rested) else np.nan,
                "short_rest_points_delta": (
                    float(short["points"].mean() - rested["points"].mean())
                    if len(short) and len(rested)
                    else np.nan
                ),
            }
        )
    return pd.DataFrame(grouped).sort_values("short_rest_points_delta", ascending=True, na_position="last")


def congestion_correlation(matches: pd.DataFrame, features: pd.DataFrame) -> pd.DataFrame:
    team_rows = _team_match_rows(matches, features)
    rows = []
    for team, group in team_rows.groupby("team"):
        if len(group) < 10 or group["fixture_congestion_score"].nunique() < 2:
            correlation = np.nan
        else:
            correlation = group["fixture_congestion_score"].corr(group["points"])
        rows.append({"team": team, "congestion_points_correlation": float(correlation) if pd.notna(correlation) else np.nan})
    return pd.DataFrame(rows).sort_values("congestion_points_correlation", ascending=False, na_position="last")


def plot_team_midweek_performance(performance: pd.DataFrame, output_path: Path, top_n: int = 12) -> None:
    plot_data = performance.dropna(subset=["midweek_points_delta"]).head(top_n).sort_values("midweek_points_delta")
    fig, ax = plt.subplots(figsize=(8, 6))
    ax.barh(plot_data["team"], plot_data["midweek_points_delta"])
    ax.axvline(0, color="black", linewidth=1)
    ax.set_title("Teams Overperforming After Midweek Matches")
    ax.set_xlabel("Points per match delta")
    fig.tight_layout()
    fig.savefig(output_path, dpi=160)
    plt.close(fig)


def plot_short_rest_performance(performance: pd.DataFrame, output_path: Path, top_n: int = 12) -> None:
    plot_data = performance.dropna(subset=["short_rest_points_delta"]).head(top_n).sort_values("short_rest_points_delta")
    fig, ax = plt.subplots(figsize=(8, 6))
    ax.barh(plot_data["team"], plot_data["short_rest_points_delta"])
    ax.axvline(0, color="black", linewidth=1)
    ax.set_title("Teams Underperforming With Short Rest")
    ax.set_xlabel("Points per match delta")
    fig.tight_layout()
    fig.savefig(output_path, dpi=160)
    plt.close(fig)


def write_discovery_outputs(matches: pd.DataFrame, features: pd.DataFrame, output_dir: Path) -> dict[str, pd.DataFrame]:
    output_dir.mkdir(parents=True, exist_ok=True)
    midweek = team_midweek_performance(matches, features)
    short_rest = short_rest_performance(matches, features)
    congestion = congestion_correlation(matches, features)

    midweek.to_csv(output_dir / "team_midweek_performance.csv", index=False)
    short_rest.to_csv(output_dir / "team_short_rest_performance.csv", index=False)
    congestion.to_csv(output_dir / "team_congestion_correlation.csv", index=False)
    plot_team_midweek_performance(midweek, output_dir / "team_midweek_performance.png")
    plot_short_rest_performance(short_rest, output_dir / "team_short_rest_performance.png")

    return {
        "midweek": midweek,
        "short_rest": short_rest,
        "congestion": congestion,
    }
