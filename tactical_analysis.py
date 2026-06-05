from __future__ import annotations

from pathlib import Path

import matplotlib
import numpy as np
import pandas as pd
from matplotlib import pyplot as plt

from tactical_features import ARCHETYPE_NAMES
from train_model import points_for_team

matplotlib.use("Agg")


def _team_style_rows(matches: pd.DataFrame, tactical_features: pd.DataFrame) -> pd.DataFrame:
    joined = pd.concat([matches.reset_index(drop=True), tactical_features.reset_index(drop=True)], axis=1)
    rows = []
    for _, row in joined.iterrows():
        rows.append(
            {
                "Date": row["Date"],
                "team": row["HomeTeam"],
                "opponent": row["AwayTeam"],
                "style_cluster": int(row.get("home_team_style_cluster", 0)),
                "opponent_style_cluster": int(row.get("away_team_style_cluster", 0)),
                "style_distance_score": float(row.get("style_distance_score", 0.0)),
                "points": points_for_team(row, row["HomeTeam"]),
            }
        )
        rows.append(
            {
                "Date": row["Date"],
                "team": row["AwayTeam"],
                "opponent": row["HomeTeam"],
                "style_cluster": int(row.get("away_team_style_cluster", 0)),
                "opponent_style_cluster": int(row.get("home_team_style_cluster", 0)),
                "style_distance_score": float(row.get("style_distance_score", 0.0)),
                "points": points_for_team(row, row["AwayTeam"]),
            }
        )
    return pd.DataFrame(rows)


def style_performance(matches: pd.DataFrame, tactical_features: pd.DataFrame) -> pd.DataFrame:
    rows = _team_style_rows(matches, tactical_features)
    summary = rows.groupby("style_cluster", as_index=False).agg(
        matches=("points", "size"),
        points_per_match=("points", "mean"),
        avg_style_distance=("style_distance_score", "mean"),
    )
    summary["style_archetype"] = summary["style_cluster"].map(lambda value: ARCHETYPE_NAMES.get(value, "Balanced"))
    return summary.sort_values("points_per_match", ascending=False)


def team_vs_style_performance(matches: pd.DataFrame, tactical_features: pd.DataFrame) -> pd.DataFrame:
    rows = _team_style_rows(matches, tactical_features)
    summary = rows.groupby(["team", "opponent_style_cluster"], as_index=False).agg(
        matches=("points", "size"),
        points_per_match=("points", "mean"),
    )
    summary["opponent_style_archetype"] = summary["opponent_style_cluster"].map(
        lambda value: ARCHETYPE_NAMES.get(value, "Balanced")
    )
    return summary.sort_values(["points_per_match", "matches"], ascending=[False, False])


def matchup_edges(matches: pd.DataFrame, tactical_features: pd.DataFrame) -> pd.DataFrame:
    rows = _team_style_rows(matches, tactical_features)
    if rows.empty:
        return pd.DataFrame(columns=["style_cluster", "opponent_style_cluster", "matches", "points_per_match"])
    summary = rows.groupby(["style_cluster", "opponent_style_cluster"], as_index=False).agg(
        matches=("points", "size"),
        points_per_match=("points", "mean"),
    )
    summary["style_archetype"] = summary["style_cluster"].map(lambda value: ARCHETYPE_NAMES.get(value, "Balanced"))
    summary["opponent_style_archetype"] = summary["opponent_style_cluster"].map(
        lambda value: ARCHETYPE_NAMES.get(value, "Balanced")
    )
    return summary.sort_values("points_per_match", ascending=False)


def plot_style_performance(performance: pd.DataFrame, output_path: Path) -> None:
    fig, ax = plt.subplots(figsize=(8, 5))
    ax.bar(performance["style_archetype"], performance["points_per_match"])
    ax.set_title("Tactical Style Performance")
    ax.set_ylabel("Points per match")
    ax.tick_params(axis="x", rotation=25)
    ax.grid(axis="y", alpha=0.25)
    fig.tight_layout()
    fig.savefig(output_path, dpi=160)
    plt.close(fig)


def write_tactical_discovery_outputs(
    matches: pd.DataFrame,
    tactical_features: pd.DataFrame,
    output_dir: Path,
) -> dict[str, pd.DataFrame]:
    output_dir.mkdir(parents=True, exist_ok=True)
    styles = style_performance(matches, tactical_features)
    team_styles = team_vs_style_performance(matches, tactical_features)
    edges = matchup_edges(matches, tactical_features)
    styles.to_csv(output_dir / "style_performance.csv", index=False)
    team_styles.to_csv(output_dir / "team_vs_style_performance.csv", index=False)
    edges.to_csv(output_dir / "style_matchup_edges.csv", index=False)
    plot_style_performance(styles, output_dir / "style_performance.png")
    return {"styles": styles, "team_styles": team_styles, "edges": edges}
