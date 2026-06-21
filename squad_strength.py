from __future__ import annotations

from pathlib import Path

import numpy as np
import pandas as pd


SQUAD_STRENGTH_PATH = Path("data") / "squad_strength_2026_27.csv"
SQUAD_PRIOR_MAX_WEIGHT = 0.08


REQUIRED_COLUMNS = {
    "season",
    "team",
    "squad_market_value_eur",
    "average_player_value_eur",
    "squad_size",
    "source",
    "source_url",
    "last_updated",
    "data_confidence",
}


def load_squad_strength(path: Path = SQUAD_STRENGTH_PATH) -> pd.DataFrame:
    if not path.exists():
        return pd.DataFrame()
    frame = pd.read_csv(path)
    missing = REQUIRED_COLUMNS - set(frame.columns)
    if missing:
        raise ValueError(f"Missing squad strength columns in {path}: {sorted(missing)}")
    frame = frame.copy()
    frame["team"] = frame["team"].astype(str)
    for column in ["squad_market_value_eur", "average_player_value_eur", "squad_size"]:
        frame[column] = pd.to_numeric(frame[column], errors="coerce")
    if "promoted_team_flag" not in frame.columns:
        frame["promoted_team_flag"] = False
    frame["promoted_team_flag"] = frame["promoted_team_flag"].fillna(False).astype(bool)
    return frame


def normalize_squad_strength(frame: pd.DataFrame, teams: tuple[str, ...] | list[str] | None = None) -> pd.DataFrame:
    if frame.empty:
        return pd.DataFrame(
            columns=[
                "team",
                "squad_strength_rank",
                "squad_strength_percentile",
                "squad_strength_score",
                "squad_strength_bucket",
                "squad_strength_used",
            ]
        )
    output = frame.copy()
    if teams is not None:
        output = pd.DataFrame({"team": list(teams)}).merge(output, on="team", how="left")
    output["squad_strength_used"] = output["squad_market_value_eur"].notna()
    valid = output["squad_market_value_eur"].dropna()
    if valid.empty:
        output["squad_strength_rank"] = np.nan
        output["squad_strength_percentile"] = np.nan
        output["squad_strength_score"] = np.nan
        output["squad_strength_bucket"] = "Missing"
        return output

    output["log_market_value"] = np.log(output["squad_market_value_eur"].clip(lower=1.0))
    min_log = float(output.loc[output["squad_strength_used"], "log_market_value"].min())
    max_log = float(output.loc[output["squad_strength_used"], "log_market_value"].max())
    denominator = max(max_log - min_log, 1e-9)
    output["squad_strength_score"] = (output["log_market_value"] - min_log) / denominator
    output["squad_strength_rank"] = output["squad_market_value_eur"].rank(method="min", ascending=False)
    team_count = int(output["squad_strength_used"].sum())
    output["squad_strength_percentile"] = 1.0 - (output["squad_strength_rank"] - 1.0) / max(team_count - 1, 1)

    def bucket(row: pd.Series) -> str:
        if not bool(row.get("squad_strength_used", False)):
            return "Missing"
        if bool(row.get("promoted_team_flag", False)) and float(row["squad_strength_rank"]) > 12:
            return "Promoted / uncertain"
        rank = float(row["squad_strength_rank"])
        if rank <= 4:
            return "Elite"
        if rank <= 8:
            return "Strong"
        if rank <= 14:
            return "Mid-table"
        return "Lower-table"

    output["squad_strength_bucket"] = output.apply(bucket, axis=1)
    return output


def squad_strength_lookup(normalized: pd.DataFrame) -> dict[str, float]:
    if normalized.empty or "squad_strength_score" not in normalized.columns:
        return {}
    usable = normalized.dropna(subset=["squad_strength_score"])
    return dict(zip(usable["team"], usable["squad_strength_score"].astype(float)))


def _fixture_squad_weight(match_index: int) -> float:
    if match_index <= 5:
        return SQUAD_PRIOR_MAX_WEIGHT
    if match_index <= 12:
        return 0.05
    return 0.025


def apply_squad_strength_prior(
    probabilities: pd.DataFrame,
    squad_scores: dict[str, float],
    max_weight: float = SQUAD_PRIOR_MAX_WEIGHT,
) -> pd.DataFrame:
    if probabilities.empty or not squad_scores:
        return probabilities.copy()
    adjusted = probabilities.sort_values("Date").copy()
    team_match_counts: dict[str, int] = {}
    rows = []
    for _, match in adjusted.iterrows():
        home = str(match["HomeTeam"])
        away = str(match["AwayTeam"])
        home_count = team_match_counts.get(home, 0) + 1
        away_count = team_match_counts.get(away, 0) + 1
        fixture_phase = min(home_count, away_count)
        weight = min(max_weight, _fixture_squad_weight(fixture_phase))
        home_score = squad_scores.get(home)
        away_score = squad_scores.get(away)
        model_probs = match[["home_win_probability", "draw_probability", "away_win_probability"]].to_numpy(dtype=float)
        if home_score is None or away_score is None:
            blended = model_probs
        else:
            strength_gap = float(home_score) - float(away_score)
            prior_logits = np.array([0.18 + 0.65 * strength_gap, -0.05 - 0.04 * abs(strength_gap), -0.18 - 0.65 * strength_gap])
            prior = np.exp(prior_logits - prior_logits.max())
            prior = prior / prior.sum()
            blended = (1.0 - weight) * model_probs + weight * prior
            blended = blended / blended.sum()
        row = match.copy()
        row["home_win_probability"] = float(blended[0])
        row["draw_probability"] = float(blended[1])
        row["away_win_probability"] = float(blended[2])
        row["squad_strength_prior_weight"] = weight
        row["home_squad_strength_score"] = np.nan if home_score is None else float(home_score)
        row["away_squad_strength_score"] = np.nan if away_score is None else float(away_score)
        row["squad_strength_diff"] = np.nan if home_score is None or away_score is None else float(home_score) - float(away_score)
        rows.append(row)
        team_match_counts[home] = home_count
        team_match_counts[away] = away_count
    return pd.DataFrame(rows).sort_index()
