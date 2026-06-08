from __future__ import annotations

import base64
import html as html_lib
import json
from datetime import date, timedelta
from pathlib import Path
from textwrap import dedent

import joblib
import numpy as np
import pandas as pd
import streamlit as st

from data_quality import assess_prediction_data_quality
from predict import MODEL_PATH, build_prediction_features
from season_simulation import (
    expected_points_from_probabilities,
    monte_carlo_season,
    predict_fixture_probabilities,
    read_fixture_list,
    season_table_from_results,
)
from train_model import load_matches


st.set_page_config(page_title="Football Analytics Dashboard", layout="wide")

CLASS_LABELS = ["Home win", "Draw", "Away win"]
RESULT_COPY = {
    0: "Home win",
    1: "Draw",
    2: "Away win",
}
CURRENT_PREMIER_LEAGUE_TEAMS = [
    "Arsenal",
    "Aston Villa",
    "Bournemouth",
    "Brentford",
    "Brighton",
    "Burnley",
    "Chelsea",
    "Crystal Palace",
    "Everton",
    "Fulham",
    "Leeds",
    "Liverpool",
    "Man City",
    "Man United",
    "Newcastle",
    "Nott'm Forest",
    "Sunderland",
    "Tottenham",
    "West Ham",
    "Wolves",
]
LOGO_DIR = Path("assets") / "logos"
team_logo_map = {
    "Arsenal": "assets/logos/Arsenal.png",
    "Aston Villa": "assets/logos/Aston Villa.png",
    "Bournemouth": "assets/logos/Bournemouth.png",
    "Brentford": "assets/logos/Brentford.png",
    "Brighton": "assets/logos/Brighton.png",
    "Burnley": "assets/logos/Burnley.png",
    "Chelsea": "assets/logos/Chelsea.png",
    "Crystal Palace": "assets/logos/Crystal Palace.png",
    "Everton": "assets/logos/Everton.png",
    "Fulham": "assets/logos/Fulham.png",
    "Leeds": "assets/logos/Leeds.png",
    "Liverpool": "assets/logos/Liverpool.png",
    "Man City": "assets/logos/Man City.png",
    "Man United": "assets/logos/Man United.png",
    "Newcastle": "assets/logos/Newcastle.png",
    "Nott'm Forest": "assets/logos/Nott'm Forest.png",
    "Sunderland": "assets/logos/Sunderland.png",
    "Tottenham": "assets/logos/Tottenham.png",
    "West Ham": "assets/logos/West Ham.png",
    "Wolves": "assets/logos/Wolves.png",
}
STATUS_EXPLANATIONS = {
    "Active": "Used directly by the production model.",
    "Candidate": "Tested and promising, but not fully promoted to production.",
    "Benchmark only": "Evaluated for comparison, not used directly in production predictions.",
    "Research mode": "Code exists, but data or validation is not strong enough for production.",
    "Missing": "Required data is not available locally.",
    "Stale": "The local dataset should be refreshed before relying heavily on this input.",
}
SEASON_PROJECTION_VERSION = "balanced_round_robin_long_term_prior_v1"
SEASON_PROJECTION_PRIOR_WEIGHT = 0.35


@st.cache_resource
def load_model_artifact():
    return joblib.load(MODEL_PATH)


@st.cache_data
def load_metrics() -> dict:
    metrics_path = Path("models") / "metrics.json"
    if not metrics_path.exists():
        return {}
    return json.loads(metrics_path.read_text())


@st.cache_resource
def load_calibrated_layer():
    path = Path("models") / "calibrated_probability_layer.joblib"
    if not path.exists():
        return None
    return joblib.load(path)


@st.cache_data
def file_has_rows(path: str) -> bool:
    file_path = Path(path)
    if not file_path.exists():
        return False
    try:
        return len(pd.read_csv(file_path)) > 0
    except pd.errors.EmptyDataError:
        return False


def inject_styles() -> None:
    st.markdown(
        dedent(
            """
        <style>
        .stApp {
            background: #07111f;
            color: #e5e7eb;
        }
        [data-testid="stHeader"] {
            background: rgba(7, 17, 31, 0.82);
        }
        :root {
            --panel: rgba(255, 255, 255, 0.055);
            --panel-strong: rgba(255, 255, 255, 0.09);
            --border: rgba(148, 163, 184, 0.24);
            --muted: #94a3b8;
            --text: #e5e7eb;
            --good: #22c55e;
            --warn: #f59e0b;
            --bad: #ef4444;
            --accent: #2dd4bf;
            --pitch: #16a34a;
        }
        .block-container {
            max-width: 1180px;
            padding-top: 1.3rem;
        }
        .hero {
            border: 1px solid var(--border);
            border-radius: 8px;
            padding: 18px;
            background:
                linear-gradient(135deg, rgba(15, 23, 42, 0.94), rgba(17, 24, 39, 0.82)),
                repeating-linear-gradient(90deg, rgba(34, 197, 94, 0.05) 0 48px, transparent 48px 96px);
            box-shadow: 0 18px 45px rgba(2, 6, 23, 0.18);
        }
        .input-card {
            border: 1px solid var(--border);
            border-radius: 8px;
            padding: 16px 18px 10px 18px;
            background: rgba(15, 23, 42, 0.72);
            margin: 16px 0;
        }
        div.stButton > button {
            min-height: 42px;
            margin-top: 28px;
            border-radius: 8px;
            font-weight: 900;
        }
        button[data-baseweb="tab"] {
            background: rgba(15, 23, 42, 0.88);
            border: 1px solid rgba(148, 163, 184, 0.30);
            border-radius: 8px 8px 0 0;
            color: #dbeafe;
            font-weight: 850;
            padding: 8px 14px;
            margin-right: 6px;
        }
        button[data-baseweb="tab"] p {
            color: #dbeafe;
            font-weight: 850;
        }
        button[data-baseweb="tab"][aria-selected="true"] {
            background: linear-gradient(135deg, rgba(22, 101, 52, 0.92), rgba(15, 118, 110, 0.82));
            border-color: rgba(45, 212, 191, 0.72);
            color: #ffffff;
        }
        button[data-baseweb="tab"][aria-selected="true"] p {
            color: #ffffff;
        }
        div[data-baseweb="tab-list"] {
            gap: 2px;
            border-bottom: 1px solid rgba(45, 212, 191, 0.28);
        }
        .hero h1 {
            font-size: 1.9rem;
            line-height: 1.1;
            margin: 0 0 8px 0;
            letter-spacing: 0;
        }
        .muted {
            color: var(--muted);
            font-size: 0.92rem;
        }
        .badge-row {
            display: flex;
            flex-wrap: wrap;
            gap: 8px;
            margin-top: 14px;
        }
        .badge {
            display: inline-flex;
            align-items: center;
            border-radius: 999px;
            padding: 4px 9px;
            min-height: 24px;
            font-size: 0.75rem;
            font-weight: 700;
            border: 1px solid var(--border);
            background: rgba(15, 23, 42, 0.46);
            color: var(--text);
        }
        .badge.good { border-color: rgba(34, 197, 94, 0.45); color: #86efac; }
        .badge.warn { border-color: rgba(245, 158, 11, 0.50); color: #fcd34d; }
        .badge.bad { border-color: rgba(239, 68, 68, 0.50); color: #fca5a5; }
        .panel {
            border: 1px solid var(--border);
            border-radius: 8px;
            padding: 14px;
            background: var(--panel);
            height: 100%;
        }
        .feature-card {
            border: 1px solid var(--border);
            border-radius: 8px;
            padding: 14px;
            background: var(--panel);
            height: 100%;
            margin-bottom: 12px;
        }
        .feature-card h3, .panel h3 {
            font-size: 1.02rem;
            margin: 0 0 8px 0;
            letter-spacing: 0;
        }
        .mini-grid {
            display: grid;
            grid-template-columns: repeat(2, minmax(0, 1fr));
            gap: 10px;
            margin: 14px 0;
        }
        .mini-stat {
            border-radius: 8px;
            padding: 10px;
            background: var(--panel-strong);
            border: 1px solid rgba(148, 163, 184, 0.14);
        }
        .mini-label {
            color: var(--muted);
            font-size: 0.76rem;
            margin-bottom: 3px;
        }
        .mini-value {
            font-size: 1.15rem;
            font-weight: 800;
        }
        .prob-row {
            margin-bottom: 13px;
        }
        .match-card {
            border: 1px solid rgba(45, 212, 191, 0.28);
            border-radius: 8px;
            padding: 18px;
            background:
                radial-gradient(circle at 50% -20%, rgba(34, 197, 94, 0.18), transparent 38%),
                linear-gradient(135deg, rgba(15, 23, 42, 0.98), rgba(6, 78, 59, 0.36));
        }
        .match-teams {
            display: grid;
            grid-template-columns: minmax(0, 1fr) auto minmax(0, 1fr);
            gap: 14px;
            align-items: center;
        }
        .team-side {
            display: flex;
            align-items: center;
            gap: 12px;
            min-width: 0;
        }
        .team-side.away {
            justify-content: flex-end;
            text-align: right;
        }
        .team-name {
            font-size: 1.35rem;
            font-weight: 900;
            overflow-wrap: anywhere;
        }
        .versus {
            color: var(--muted);
            font-weight: 900;
            letter-spacing: 0;
        }
        .logo {
            width: 72px;
            height: 72px;
            border-radius: 50%;
            border: 1px solid rgba(148, 163, 184, 0.34);
            background: rgba(15, 23, 42, 0.72);
            display: inline-flex;
            align-items: center;
            justify-content: center;
            flex: 0 0 auto;
            overflow: hidden;
            font-weight: 900;
            font-size: 1rem;
            color: #bbf7d0;
        }
        .logo img {
            width: 82%;
            height: 82%;
            object-fit: contain;
        }
        .match-meta {
            display: flex;
            flex-wrap: wrap;
            gap: 8px;
            margin-top: 16px;
        }
        .outcome-line {
            margin-top: 14px;
            font-size: 1rem;
            color: var(--muted);
        }
        .outcome-line strong {
            color: var(--text);
        }
        .prob-card-grid {
            display: grid;
            grid-template-columns: repeat(3, minmax(0, 1fr));
            gap: 12px;
        }
        .prob-card {
            border: 1px solid rgba(148, 163, 184, 0.18);
            border-radius: 8px;
            padding: 12px;
            background: rgba(15, 23, 42, 0.62);
        }
        .prob-card.top {
            border-color: rgba(34, 197, 94, 0.56);
            background: rgba(22, 101, 52, 0.24);
        }
        .prob-label {
            color: var(--muted);
            font-size: 0.82rem;
            font-weight: 800;
        }
        .prob-value {
            font-size: 1.45rem;
            font-weight: 900;
            margin: 3px 0 8px;
        }
        .prob-top {
            display: flex;
            justify-content: space-between;
            gap: 14px;
            font-weight: 750;
            margin-bottom: 5px;
        }
        .odds-card-grid {
            display: grid;
            grid-template-columns: repeat(3, minmax(0, 1fr));
            gap: 12px;
            margin-top: 12px;
        }
        .odds-card {
            border: 1px solid rgba(148, 163, 184, 0.18);
            border-radius: 8px;
            padding: 12px;
            background: rgba(15, 23, 42, 0.52);
        }
        .odds-card.value {
            border-color: rgba(34, 197, 94, 0.52);
            background: rgba(22, 101, 52, 0.18);
        }
        .odds-card.no-value {
            border-color: rgba(239, 68, 68, 0.32);
        }
        .odds-number {
            font-size: 1.34rem;
            font-weight: 900;
            margin-top: 3px;
        }
        .odds-detail {
            color: var(--muted);
            font-size: 0.78rem;
            margin-top: 4px;
        }
        .bar-shell {
            height: 11px;
            border-radius: 999px;
            background: rgba(148, 163, 184, 0.18);
            overflow: hidden;
            border: 1px solid rgba(148, 163, 184, 0.14);
        }
        .bar-fill {
            height: 100%;
            border-radius: 999px;
            background: var(--muted);
        }
        .bar-fill.top {
            background: linear-gradient(90deg, #22c55e, #2dd4bf);
        }
        .comparison-table {
            display: grid;
            gap: 6px;
            margin-top: 12px;
        }
        .comparison-header,
        .comparison-row {
            display: grid;
            grid-template-columns: minmax(100px, 1.2fr) minmax(70px, 0.8fr) minmax(70px, 0.8fr);
            gap: 8px;
            align-items: center;
        }
        .comparison-header {
            color: var(--muted);
            font-size: 0.75rem;
            font-weight: 800;
        }
        .comparison-row {
            padding: 8px;
            border-radius: 8px;
            background: rgba(255, 255, 255, 0.045);
            border: 1px solid rgba(148, 163, 184, 0.10);
        }
        .metric-label {
            color: var(--muted);
            font-size: 0.8rem;
        }
        .metric-cell {
            font-weight: 900;
        }
        .metric-cell.good { color: #86efac; }
        .metric-cell.warn { color: #fde68a; }
        .metric-cell.bad { color: #fca5a5; }
        .insight-list {
            margin: 0;
            padding-left: 1.1rem;
        }
        .insight-list li {
            margin: 7px 0;
        }
        .status-grid {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(155px, 1fr));
            gap: 8px;
        }
        .status-item {
            border: 1px solid rgba(148, 163, 184, 0.16);
            border-radius: 8px;
            padding: 9px;
            background: var(--panel);
        }
        .status-name {
            font-size: 0.78rem;
            color: var(--muted);
        }
        .status-value {
            margin-top: 3px;
            font-weight: 800;
        }
        div[data-testid="stAlert"] {
            border-radius: 8px;
        }
        section[data-testid="stSidebar"] {
            background: #081425;
        }
        @media (max-width: 760px) {
            .match-teams {
                grid-template-columns: 1fr;
                text-align: center;
            }
            .team-side,
            .team-side.away {
                justify-content: center;
                text-align: center;
            }
            .prob-card-grid {
                grid-template-columns: 1fr;
            }
            .odds-card-grid {
                grid-template-columns: 1fr;
            }
        }
        </style>
        """
        ),
        unsafe_allow_html=True,
    )


def value(row: dict[str, float], key: str) -> float:
    return float(row.get(key, 0.0))


def fmt(value_: float, decimals: int = 1) -> str:
    return f"{value_:.{decimals}f}"


def team_initials(team: str) -> str:
    parts = team.replace("'", "").split()
    if len(parts) == 1:
        return parts[0][:3].upper()
    return "".join(part[0] for part in parts[:3]).upper()


def get_team_logo(team_name: str) -> str | None:
    configured = Path(team_logo_map.get(team_name, str(LOGO_DIR / f"{team_name}.png")))
    candidates = [configured]
    if configured.suffix.lower() != ".svg":
        candidates.append(configured.with_suffix(".svg"))
    if configured.suffix.lower() != ".png":
        candidates.append(configured.with_suffix(".png"))
    for path in candidates:
        if path.exists():
            return str(path)
    return None


def _logo_mime_type(path: Path) -> str:
    if path.suffix.lower() == ".svg":
        return "image/svg+xml"
    return "image/png"


def render_team_badge(team_name: str) -> str:
    logo_path = get_team_logo(team_name)
    if logo_path is None:
        return f"<span class='logo'>{html_lib.escape(team_initials(team_name))}</span>"

    path = Path(logo_path)
    if path.exists():
        encoded = base64.b64encode(path.read_bytes()).decode("ascii")
        alt = html_lib.escape(f"{team_name} badge")
        mime = _logo_mime_type(path)
        return f"<span class='logo'><img src='data:{mime};base64,{encoded}' alt='{alt}'></span>"
    return f"<span class='logo'>{html_lib.escape(team_initials(team_name))}</span>"


def latest_dataset_date(team_history: dict) -> object:
    known_dates = [
        match_date
        for history in team_history.values()
        for match_date in history.get("match_dates", [])
    ]
    if not known_dates:
        return None
    return max(known_dates)


def latest_team_date(team_history: dict, team: str) -> object:
    dates = team_history.get(team, {}).get("match_dates", [])
    return max(dates) if dates else None


def has_recent_team_history(team_history: dict, team: str, max_stale_days: int = 370) -> bool:
    latest_date = latest_dataset_date(team_history)
    team_date = latest_team_date(team_history, team)
    if latest_date is None or team_date is None:
        return False
    return (latest_date - team_date).days <= max_stale_days


def selectable_current_teams(team_history: dict) -> list[str]:
    return [team for team in CURRENT_PREMIER_LEAGUE_TEAMS if has_recent_team_history(team_history, team)]


def unavailable_current_teams(team_history: dict) -> list[str]:
    return [team for team in CURRENT_PREMIER_LEAGUE_TEAMS if team not in team_history]


def stale_current_teams(team_history: dict) -> list[str]:
    return [
        team
        for team in CURRENT_PREMIER_LEAGUE_TEAMS
        if team in team_history and not has_recent_team_history(team_history, team)
    ]


@st.cache_data
def load_recent_head_to_head(home_team: str, away_team: str, limit: int = 5) -> pd.DataFrame:
    matches = load_matches()
    h2h = matches[
        ((matches["HomeTeam"] == home_team) & (matches["AwayTeam"] == away_team))
        | ((matches["HomeTeam"] == away_team) & (matches["AwayTeam"] == home_team))
    ].sort_values("Date", ascending=False)

    rows = []
    for _, match in h2h.head(limit).iterrows():
        result = "Draw"
        if match["FTR"] == "H":
            result = f"{match['HomeTeam']} win"
        elif match["FTR"] == "A":
            result = f"{match['AwayTeam']} win"
        rows.append(
            {
                "Date": match["Date"],
                "Match": f"{match['HomeTeam']} vs {match['AwayTeam']}",
                "Score": f"{int(match['FTHG'])}-{int(match['FTAG'])}",
                "Result": result,
            }
        )
    return pd.DataFrame(rows)


def confidence_label(probabilities, warnings: list[str]) -> tuple[str, str]:
    top_prob = float(max(probabilities))
    if len(warnings) >= 2:
        return "Low", "warn"
    if top_prob >= 0.62 and not warnings:
        return "High", "good"
    if top_prob >= 0.48:
        return "Medium", "warn" if warnings else "good"
    return "Low", "warn"


def data_quality_label(warnings: list[str]) -> tuple[str, str]:
    if not warnings:
        return "Good", "good"
    if len(warnings) <= 2:
        return "Warning", "warn"
    return "Poor", "bad"


def apply_calibration(raw_probabilities, calibrated_layer, features: pd.DataFrame):
    if calibrated_layer is None:
        return raw_probabilities, False, "raw"
    method = calibrated_layer.get("method")
    if method in {"sigmoid", "isotonic"}:
        probabilities = calibrated_layer["calibrator"].predict_proba(features)[0]
    elif method == "temperature":
        temperature = float(calibrated_layer["temperature"])
        clipped = np.clip(raw_probabilities, 1e-15, 1.0)
        logits = np.log(clipped) / temperature
        logits = logits - logits.max()
        exp_values = np.exp(logits)
        probabilities = exp_values / exp_values.sum()
    else:
        return raw_probabilities, False, "raw"
    return probabilities, True, str(method)


def fair_odds_from_probabilities(probabilities) -> list[float]:
    clipped = np.clip(np.asarray(probabilities, dtype=float), 1e-9, 1.0)
    normalized = clipped / clipped.sum()
    return [float(1.0 / probability) for probability in normalized]


def render_model_fair_odds(probabilities, home_team: str, away_team: str) -> None:
    labels = [f"{home_team} win", "Draw", f"{away_team} win"]
    fair_odds = fair_odds_from_probabilities(probabilities)
    html = "<div class='odds-card-grid'>"
    for label, odds in zip(labels, fair_odds):
        html += dedent(
            f"""
        <div class="odds-card">
            <div class="prob-label">{html_lib.escape(label)}</div>
            <div class="odds-number">{odds:.2f}</div>
            <div class="odds-detail">Model fair odds</div>
        </div>
        """
        )
    html += "</div>"
    st.markdown(html, unsafe_allow_html=True)


def render_bookmaker_odds_comparison(probabilities, home_team: str, away_team: str) -> None:
    labels = [f"{home_team} win", "Draw", f"{away_team} win"]
    fair_odds = fair_odds_from_probabilities(probabilities)

    with st.expander("Compare with bookmaker odds", expanded=False):
        st.caption(
            "Enter decimal bookmaker odds manually. If bookmaker odds are higher than model fair odds, "
            "the model rates that outcome as better value. This is only a comparison tool, not betting advice."
        )
        columns = st.columns(3)
        offered_odds = []
        for column, label in zip(columns, labels):
            with column:
                offered_odds.append(
                    st.number_input(
                        label,
                        min_value=1.01,
                        max_value=100.0,
                        value=2.00,
                        step=0.01,
                        format="%.2f",
                        key=f"bookmaker_odds_{label}",
                    )
                )

        rows = []
        for label, probability, fair, offered in zip(labels, probabilities, fair_odds, offered_odds):
            expected_return = (float(probability) * float(offered)) - 1.0
            edge_pct = expected_return * 100
            value_label = "Better than fair odds" if offered > fair else "Worse than fair odds"
            rows.append(
                {
                    "Outcome": label,
                    "Model probability": f"{float(probability) * 100:.1f}%",
                    "Model fair odds": f"{fair:.2f}",
                    "Bookmaker odds": f"{float(offered):.2f}",
                    "Model edge": f"{edge_pct:+.1f}%",
                    "Assessment": value_label,
                }
            )

        result = pd.DataFrame(rows)
        st.dataframe(result, width="stretch", hide_index=True)
        st.caption(
            "Formula: model fair odds = 1 / model probability. Model edge = probability * bookmaker odds - 1."
        )


def build_warnings(row: dict[str, float]) -> list[str]:
    warnings = []
    for side, team_label in (("home", "Home team"), ("away", "Away team")):
        days_rest = value(row, f"{side}_days_rest")
        if days_rest > 30:
            warnings.append(
                f"{team_label} has a very large gap since its last match in the dataset. Prediction reliability may be reduced."
            )
    return warnings


def render_probability_bar(probabilities, home_team: str, away_team: str) -> None:
    labels = [f"{home_team} win", "Draw", f"{away_team} win"]
    top_index = int(max(range(len(probabilities)), key=lambda idx: probabilities[idx]))
    html = "<div class='prob-card-grid'>"
    for index, probability in enumerate(probabilities):
        percent = float(probability) * 100
        is_top = index == top_index
        html += dedent(
            f"""
        <div class="prob-card {'top' if is_top else ''}">
            <div class="prob-label">{labels[index]}{" - most likely" if is_top else ""}</div>
            <div class="prob-value">{percent:.1f}%</div>
            <div class="bar-shell">
                <div class="bar-fill {'top' if is_top else ''}" style="width: {percent:.1f}%"></div>
            </div>
        </div>
        """
        )
    html += "</div>"
    st.markdown(html, unsafe_allow_html=True)


def render_confidence_badge(probabilities, warnings: list[str]) -> None:
    label, tone = confidence_label(probabilities, warnings)
    st.markdown(f"<span class='badge {tone}'>Model confidence: {label}</span>", unsafe_allow_html=True)


def render_model_status(feature_columns: list[str], checks: dict[str, str] | None = None) -> None:
    checks = checks or {}
    statuses = [
        ("Match results data", checks.get("Match results data", "Active"), "good"),
        ("xG data", checks.get("xG data", "Active"), "good" if any("xg" in feature for feature in feature_columns) else "warn"),
        ("Fatigue features", checks.get("Fatigue features", "Active"), "good" if any("days_rest" in feature for feature in feature_columns) else "warn"),
        ("Elo rating", checks.get("Elo rating", "Active"), "good" if any("elo" in feature for feature in feature_columns) else "warn"),
        ("Shot volume", checks.get("Shot volume", "Active"), "good" if any("shots_avg" in feature for feature in feature_columns) else "warn"),
        ("Market odds", checks.get("Market odds", "Benchmark only"), "warn"),
    ]
    if checks.get("Injury data") == "Available":
        statuses.append(("Injury data", "Available", "good"))
    if checks.get("Lineup stability") == "Available":
        statuses.append(("Lineup stability", "Available", "good"))
    if checks.get("Tactical pressure") in {"Active", "Candidate"} or any("attacking_pressure" in feature for feature in feature_columns):
        statuses.append(("Tactical pressure", checks.get("Tactical pressure", "Active"), "good"))
    html = '<div class="status-grid">'
    for name, state, tone in statuses:
        tooltip = STATUS_EXPLANATIONS.get(state, f"{name}: {state}")
        html += dedent(
            f"""
        <div class="status-item" title="{html_lib.escape(tooltip)}">
            <div class="status-name">{name}</div>
            <div class="status-value"><span class="badge {tone}">{state}</span></div>
        </div>
        """
        )
    html += "</div>"
    st.markdown(html, unsafe_allow_html=True)


def render_data_quality_card(quality_result) -> None:
    tone = "good" if quality_result.status == "Good" else "warn" if quality_result.status == "Warning" else "bad"
    st.markdown(f"<span class='badge {tone}'>Data quality: {quality_result.status}</span>", unsafe_allow_html=True)
    if quality_result.warnings:
        for warning in quality_result.warnings:
            st.warning(warning)
    else:
        st.success("No major data-quality warnings detected for this prediction.")
    for explanation in quality_result.explanations:
        st.caption(explanation)


def summary_card(
    home_team: str,
    away_team: str,
    probabilities,
    warnings: list[str],
) -> None:
    top_index = int(max(range(len(probabilities)), key=lambda idx: probabilities[idx]))
    outcome = RESULT_COPY[top_index]
    confidence, confidence_tone = confidence_label(probabilities, warnings)
    quality, quality_tone = data_quality_label(warnings)
    st.markdown(
        dedent(
            f"""
        <div class="match-card">
            <div class="muted">Match prediction</div>
            <div class="match-teams">
                <div class="team-side">{render_team_badge(home_team)}<div class="team-name">{html_lib.escape(home_team)}</div></div>
                <div class="versus">vs</div>
                <div class="team-side away"><div class="team-name">{html_lib.escape(away_team)}</div>{render_team_badge(away_team)}</div>
            </div>
            <div class="outcome-line">Most likely outcome: <strong>{outcome}</strong></div>
            <div class="match-meta">
                <span class="badge {confidence_tone}">Model confidence: {confidence}</span>
                <span class="badge {quality_tone}">Data quality: {quality}</span>
                <span class="badge">Home {probabilities[0] * 100:.1f}%</span>
                <span class="badge">Draw {probabilities[1] * 100:.1f}%</span>
                <span class="badge">Away {probabilities[2] * 100:.1f}%</span>
            </div>
        </div>
        """,
        ),
        unsafe_allow_html=True,
    )


def comparison_tones(home_value: float, away_value: float, higher_is_better: bool = True, close_threshold: float = 0.05) -> tuple[str, str]:
    diff = home_value - away_value
    if not higher_is_better:
        diff = -diff
    scale = max(abs(home_value), abs(away_value), 1.0)
    if abs(diff) <= close_threshold * scale:
        return "warn", "warn"
    return ("good", "bad") if diff > 0 else ("bad", "good")


def formatted_feature_value(raw_value: float, decimals: int, value_type: str = "number") -> str:
    if value_type == "bool_bad_when_true":
        return "Yes" if bool(raw_value) else "No"
    return fmt(raw_value, decimals)


def feature_style_frame(frame: pd.DataFrame, tone_rows: list[tuple[str, str]], home_team: str, away_team: str) -> pd.DataFrame:
    styles = pd.DataFrame("", index=frame.index, columns=frame.columns)
    tone_css = {
        "good": "color: #86efac; font-weight: 800;",
        "warn": "color: #fde68a; font-weight: 800;",
        "bad": "color: #fca5a5; font-weight: 800;",
    }
    styles["Metric"] = "color: #94a3b8;"
    for index, (home_tone, away_tone) in enumerate(tone_rows):
        styles.loc[index, home_team] = tone_css[home_tone]
        styles.loc[index, away_team] = tone_css[away_tone]
    return styles


def render_feature_group(
    title: str,
    explanation: str,
    rows: list[tuple[str, float, float, int, bool, str]],
    home_team: str,
    away_team: str,
) -> None:
    display_rows = []
    tone_rows = []
    for label, home_value, away_value, decimals, higher_is_better, value_type in rows:
        if value_type == "bool_bad_when_true":
            home_tone = "bad" if bool(home_value) else "good"
            away_tone = "bad" if bool(away_value) else "good"
        else:
            home_tone, away_tone = comparison_tones(home_value, away_value, higher_is_better)
        tone_rows.append((home_tone, away_tone))
        display_rows.append(
            {
                "Metric": label,
                home_team: formatted_feature_value(home_value, decimals, value_type),
                away_team: formatted_feature_value(away_value, decimals, value_type),
            }
        )

    frame = pd.DataFrame(display_rows)
    with st.container(border=True):
        st.markdown(f"#### {title}")
        st.caption(explanation)
        styled = frame.style.apply(lambda _: feature_style_frame(frame, tone_rows, home_team, away_team), axis=None)
        st.dataframe(styled, width="stretch", hide_index=True)


def grouped_feature_cards(row: dict[str, float], home_team: str, away_team: str) -> None:
    cards = [
        (
            "Recent Form",
            "Points and scoring form from each team's latest 5 matches in the saved dataset.",
            [
                ("Points last 5", value(row, "home_team_points_last_5"), value(row, "away_team_points_last_5"), 0, True, "number"),
                ("Goals avg", value(row, "home_goals_scored_avg"), value(row, "away_goals_scored_avg"), 1, True, "number"),
            ],
        ),
        (
            "xG Strength",
            "Expected-goals form from each team's latest 5 matches: xG created, xG conceded and xG differential.",
            [
                ("xG", value(row, "home_xg_avg"), value(row, "away_xg_avg"), 2, True, "number"),
                ("xGA", value(row, "home_xga_avg"), value(row, "away_xga_avg"), 2, False, "number"),
                ("xG diff", value(row, "home_xg_diff"), value(row, "away_xg_diff"), 2, True, "number"),
            ],
        ),
        (
            "Schedule & Fatigue",
            "Rest and fixture congestion from matches already present in the historical dataset. Congestion counts use the last 14 days.",
            [
                ("Days rest", value(row, "home_days_rest"), value(row, "away_days_rest"), 0, True, "number"),
                ("Matches last 14 days", value(row, "home_matches_last_14_days"), value(row, "away_matches_last_14_days"), 0, False, "number"),
                ("Midweek match", value(row, "home_had_midweek_match"), value(row, "away_had_midweek_match"), 0, False, "bool_bad_when_true"),
            ],
        ),
        (
            "Elo Team Strength",
            "Longer-term team strength rating updated chronologically after each known match. Elo is available before the prediction.",
            [
                ("Elo rating", value(row, "home_elo"), value(row, "away_elo"), 0, True, "number"),
                ("Elo trend", value(row, "home_elo_trend"), value(row, "away_elo_trend"), 1, True, "number"),
                ("Elo advantage", value(row, "elo_difference"), -value(row, "elo_difference"), 0, True, "number"),
            ],
        ),
    ]
    if "home_shots_avg_last5" in row or "away_shots_avg_last5" in row:
        cards.append(
            (
                "Shot Volume",
                "Shooting pressure from each team's latest matches. These production features use shots and shots on target before the prediction.",
                [
                    ("Shots avg last 5", value(row, "home_shots_avg_last5"), value(row, "away_shots_avg_last5"), 1, True, "number"),
                    (
                        "Shots on target last 5",
                        value(row, "home_shots_on_target_avg_last5"),
                        value(row, "away_shots_on_target_avg_last5"),
                        1,
                        True,
                        "number",
                    ),
                    ("Shots avg season", value(row, "home_shots_avg_season"), value(row, "away_shots_avg_season"), 1, True, "number"),
                ],
            )
        )

    for start in range(0, len(cards), 2):
        columns = st.columns(2)
        for column, card in zip(columns, cards[start : start + 2]):
            with column:
                render_feature_group(*card, home_team, away_team)


def render_recent_head_to_head(home_team: str, away_team: str) -> None:
    h2h = load_recent_head_to_head(home_team, away_team)
    st.markdown(
        dedent(
            """
        <div class="feature-card">
            <div class="badge-row" style="margin-top:0;margin-bottom:8px;">
                <span class="badge warn">Research / Not active</span>
            </div>
            <h3>Recent meetings</h3>
            <div class="muted">
                Shown as historical context. Only used in the model if H2H features are active.
            </div>
        </div>
        """
        ),
        unsafe_allow_html=True,
    )
    if h2h.empty:
        st.info("No recent Premier League head-to-head meetings found in the local dataset for these teams.")
        return
    st.dataframe(h2h, width="stretch", hide_index=True)


def generate_plain_english_explanation(row: dict[str, float], home_team: str, away_team: str) -> list[str]:
    insights = []
    home_xg_diff = value(row, "home_xg_diff")
    away_xg_diff = value(row, "away_xg_diff")
    home_points = value(row, "home_team_points_last_5")
    away_points = value(row, "away_team_points_last_5")
    home_rest = value(row, "home_days_rest")
    away_rest = value(row, "away_days_rest")

    insights.append(f"{home_team} gets the built-in home advantage signal, which is one of the model's baseline inputs.")

    if abs(home_xg_diff - away_xg_diff) >= 0.15:
        stronger = home_team if home_xg_diff > away_xg_diff else away_team
        insights.append(f"{stronger} has the stronger recent xG differential in the available data.")
    else:
        insights.append("The recent xG differential is close, so chance quality does not create a clear separation by itself.")

    if abs(home_points - away_points) >= 4:
        stronger = home_team if home_points > away_points else away_team
        insights.append(f"{stronger} has the stronger recent points trend.")
    else:
        insights.append("Recent points form is fairly close, which increases uncertainty.")

    if value(row, "home_xga_avg") >= 1.8:
        insights.append(f"{home_team}'s recent xGA is high, suggesting defensive chances conceded in the available data.")
    if value(row, "away_xga_avg") >= 1.8:
        insights.append(f"{away_team}'s recent xGA is high, suggesting defensive chances conceded in the available data.")

    for side, team in (("home", home_team), ("away", away_team)):
        days_rest = value(row, f"{side}_days_rest")
        if days_rest <= 4:
            insights.append(f"{team} has short rest due to recent match activity.")
        elif days_rest > 30:
            insights.append(f"{team} has a suspiciously large rest gap, suggesting incomplete recent data for this match date.")

    if abs(home_rest - away_rest) >= 3 and max(home_rest, away_rest) <= 30:
        fresher = home_team if home_rest > away_rest else away_team
        insights.append(f"{fresher} has the rest advantage in the latest available schedule data.")

    return insights[:5]


def build_insights(row: dict[str, float], home_team: str, away_team: str) -> list[str]:
    return generate_plain_english_explanation(row, home_team, away_team)


def warning_panel(warnings: list[str]) -> None:
    if not warnings:
        st.success("No major data-quality warnings detected for this prediction.")
        return
    for warning in warnings:
        st.warning(warning)


def technical_details(features: pd.DataFrame) -> None:
    display = features.T.reset_index()
    display.columns = ["Feature", "Value"]
    display["Value"] = display["Value"].map(lambda item: round(float(item), 4))
    st.dataframe(display, width="stretch", hide_index=True)


def zscore(series: pd.Series) -> pd.Series:
    std = float(series.std(ddof=0))
    if std == 0.0 or np.isnan(std):
        return pd.Series(np.zeros(len(series)), index=series.index)
    return (series - float(series.mean())) / std


def build_long_term_team_strength(teams: tuple[str, ...], elo_state: dict[str, dict[str, object]]) -> dict[str, float]:
    matches = load_matches()
    seasons = sorted(matches["Season"].dropna().unique())
    recent_seasons = seasons[-2:]
    rows = []
    for season in recent_seasons:
        season_matches = matches[matches["Season"] == season].copy()
        if season_matches.empty:
            continue
        table = season_table_from_results(season_matches)
        played = pd.concat([season_matches["HomeTeam"], season_matches["AwayTeam"]]).value_counts()
        table["played"] = table["team"].map(played).fillna(0)
        table["ppg"] = table["points"] / table["played"].replace(0, np.nan)
        table["gd_per_match"] = table["gd"] / table["played"].replace(0, np.nan)
        rows.append(table[["team", "points", "played", "gd", "ppg", "gd_per_match"]])

    if not rows:
        return {team: 0.0 for team in teams}

    recent = pd.concat(rows, ignore_index=True)
    summary = (
        recent.groupby("team", as_index=False)
        .agg(points=("points", "sum"), played=("played", "sum"), gd=("gd", "sum"))
        .query("played > 0")
    )
    summary["ppg"] = summary["points"] / summary["played"]
    summary["gd_per_match"] = summary["gd"] / summary["played"]
    summary = pd.DataFrame({"team": list(teams)}).merge(summary, on="team", how="left")
    summary["ppg"] = summary["ppg"].fillna(summary["ppg"].median()).fillna(1.0)
    summary["gd_per_match"] = summary["gd_per_match"].fillna(summary["gd_per_match"].median()).fillna(0.0)
    summary["elo"] = summary["team"].map(lambda team: float(elo_state.get(team, {}).get("rating", 1500.0)))
    summary["strength"] = 0.55 * zscore(summary["ppg"]) + 0.30 * zscore(summary["gd_per_match"]) + 0.15 * zscore(summary["elo"])
    return dict(zip(summary["team"], summary["strength"]))


def blend_with_long_term_season_prior(
    probabilities: pd.DataFrame,
    team_strength: dict[str, float],
    prior_weight: float = SEASON_PROJECTION_PRIOR_WEIGHT,
) -> pd.DataFrame:
    adjusted = probabilities.copy()
    adjusted_values = []
    for _, match in adjusted.iterrows():
        home_strength = team_strength.get(match["HomeTeam"], 0.0)
        away_strength = team_strength.get(match["AwayTeam"], 0.0)
        strength_gap = home_strength - away_strength
        prior_logits = np.array(
            [
                0.22 + 0.52 * strength_gap,
                -0.06 - 0.05 * abs(strength_gap),
                -0.22 - 0.52 * strength_gap,
            ]
        )
        prior = np.exp(prior_logits - prior_logits.max())
        prior = prior / prior.sum()
        model_probs = match[["home_win_probability", "draw_probability", "away_win_probability"]].to_numpy(dtype=float)
        blended = (1.0 - prior_weight) * model_probs + prior_weight * prior
        adjusted_values.append(blended / blended.sum())

    adjusted[["home_win_probability", "draw_probability", "away_win_probability"]] = np.vstack(adjusted_values)
    return adjusted


def build_fixture_skeleton(teams: list[str]) -> pd.DataFrame:
    start = date(2026, 8, 15)
    rows = []
    ordered_teams = sorted(teams)
    if len(ordered_teams) % 2:
        ordered_teams.append("BYE")

    fixed_team = ordered_teams[0]
    rotating = ordered_teams[1:]
    first_half_rounds: list[list[tuple[str, str]]] = []
    teams_per_round = len(ordered_teams) // 2

    for round_index in range(len(ordered_teams) - 1):
        current = [fixed_team] + rotating
        pairings = []
        for pairing_index in range(teams_per_round):
            team_a = current[pairing_index]
            team_b = current[-(pairing_index + 1)]
            if "BYE" in {team_a, team_b}:
                continue
            if (round_index + pairing_index) % 2 == 0:
                pairings.append((team_a, team_b))
            else:
                pairings.append((team_b, team_a))
        first_half_rounds.append(pairings)
        rotating = [rotating[-1]] + rotating[:-1]

    all_rounds = first_half_rounds + [[(away, home) for home, away in round_pairings] for round_pairings in first_half_rounds]
    for round_index, round_pairings in enumerate(all_rounds):
        for home_team, away_team in round_pairings:
            rows.append(
                {
                    "Season": "2627_skeleton",
                    "Date": start + timedelta(days=7 * round_index),
                    "HomeTeam": home_team,
                    "AwayTeam": away_team,
                }
            )
    return pd.DataFrame(rows)


@st.cache_data(show_spinner=False)
def upcoming_season_projection(
    teams: tuple[str, ...],
    simulations: int,
    model_mtime: float,
    calibration_mtime: float,
    fixture_mtime: float,
    projection_version: str,
) -> tuple[pd.DataFrame, pd.DataFrame, str]:
    artifact = joblib.load(MODEL_PATH)
    fixture_path = Path("data") / "upcoming_fixtures.csv"
    if fixture_path.exists():
        fixtures = read_fixture_list(fixture_path)
        source = "Loaded from data/upcoming_fixtures.csv"
    else:
        fixtures = build_fixture_skeleton(list(teams))
        source = "Fixture skeleton: official upcoming fixture list not found locally"

    calibrator = None
    calibration_path = Path("models") / "calibrated_probability_layer.joblib"
    if calibration_path.exists():
        layer = joblib.load(calibration_path)
        if list(layer.get("feature_columns", [])) == list(artifact["feature_columns"]) and layer.get("method") in {"sigmoid", "isotonic"}:
            calibrator = layer["calibrator"]

    probabilities = predict_fixture_probabilities(
        fixtures,
        artifact["model"],
        artifact["feature_columns"],
        artifact["team_history"],
        artifact.get("elo_state", {}),
        calibrator=calibrator,
    )
    long_term_strength = build_long_term_team_strength(teams, artifact.get("elo_state", {}))
    probabilities = blend_with_long_term_season_prior(probabilities, long_term_strength)
    projection = monte_carlo_season(probabilities, n_simulations=simulations)
    expected = expected_points_from_probabilities(probabilities)
    projection = projection.merge(expected, on="team", how="left")
    projection["projected_position"] = range(1, len(projection) + 1)
    return projection, probabilities, source


@st.cache_data(show_spinner=False)
def load_historical_season_outputs() -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    base = Path("evaluation") / "season_simulation"
    comparison_path = base / "historical_season_comparison.csv"
    summary_path = base / "historical_validation_summary.csv"
    by_season_path = base / "historical_validation_by_season.csv"
    comparison = pd.read_csv(comparison_path) if comparison_path.exists() else pd.DataFrame()
    summary = pd.read_csv(summary_path) if summary_path.exists() else pd.DataFrame()
    by_season = pd.read_csv(by_season_path) if by_season_path.exists() else pd.DataFrame()
    return comparison, summary, by_season


def probability_percent_columns(frame: pd.DataFrame, columns: list[str]) -> pd.DataFrame:
    output = frame.copy()
    for column in columns:
        if column in output.columns:
            output[column] = output[column].map(lambda value: f"{float(value) * 100:.1f}%")
    return output


def render_season_projection_tab(home_team: str, away_team: str, teams: list[str]) -> None:
    st.subheader("Upcoming Season Projection")
    fixture_path = Path("data") / "upcoming_fixtures.csv"
    projection, probabilities, source = upcoming_season_projection(
        tuple(teams),
        10000,
        Path(MODEL_PATH).stat().st_mtime if Path(MODEL_PATH).exists() else 0.0,
        (Path("models") / "calibrated_probability_layer.joblib").stat().st_mtime
        if (Path("models") / "calibrated_probability_layer.joblib").exists()
        else 0.0,
        fixture_path.stat().st_mtime if fixture_path.exists() else 0.0,
        SEASON_PROJECTION_VERSION,
    )
    if fixture_path.exists():
        st.success(source)
    else:
        st.warning(
            "No official upcoming fixture list found at data/upcoming_fixtures.csv. "
            "This projection uses a balanced 38-round home/away fixture skeleton, so exact fixture-order and fatigue effects remain illustrative."
        )
    st.info(
        "Season projection is intentionally more conservative than a single-match prediction. "
        "It blends the match model with a long-term team-strength prior from the last two completed seasons and Elo, "
        f"using a {SEASON_PROJECTION_PRIOR_WEIGHT:.0%} prior weight."
    )

    selected = projection[projection["team"].isin([home_team, away_team])].copy()
    selected_display = probability_percent_columns(
        selected[
            [
                "team",
                "expected_position",
                "projected_position",
                "expected_points",
                "title_probability",
                "top_4_probability",
                "top_6_probability",
                "relegation_probability",
            ]
        ],
        ["title_probability", "top_4_probability", "top_6_probability", "relegation_probability"],
    )
    selected_display = selected_display.rename(
        columns={
            "expected_position": "monte_carlo_expected_position",
            "projected_position": "rank_by_expected_position",
        }
    )
    selected_display["monte_carlo_expected_position"] = selected_display["monte_carlo_expected_position"].map(lambda value: f"{float(value):.1f}")
    selected_display["expected_points"] = selected_display["expected_points"].map(lambda value: f"{float(value):.1f}")
    st.markdown("#### Selected Teams")
    st.dataframe(selected_display, width="stretch", hide_index=True)
    st.caption(
        "Monte Carlo expected position is the average finishing position across simulations. "
        "Rank by expected position is the ordered table rank, so close teams can look more decisive than the simulation really is."
    )

    with st.expander("Full upcoming season projection", expanded=True):
        full_display = probability_percent_columns(
            projection[
                [
                    "team",
                    "expected_position",
                    "projected_position",
                    "expected_points",
                    "title_probability",
                    "top_4_probability",
                    "top_6_probability",
                    "relegation_probability",
                ]
            ],
            ["title_probability", "top_4_probability", "top_6_probability", "relegation_probability"],
        )
        full_display = full_display.rename(
            columns={
                "expected_position": "monte_carlo_expected_position",
                "projected_position": "rank_by_expected_position",
            }
        )
        for column in ["expected_points", "monte_carlo_expected_position"]:
            full_display[column] = full_display[column].map(lambda value: f"{float(value):.1f}")
        st.dataframe(full_display, width="stretch", hide_index=True)

    st.subheader("Previous Seasons: Forecast vs Result")
    comparison, summary, by_season = load_historical_season_outputs()
    if comparison.empty:
        st.info("Historical season simulation outputs are not available yet. Run `python season_simulation.py --historical-validation --simulations 10000`.")
        return

    variant_options = sorted(comparison["model_variant"].dropna().unique())
    default_variant = "current_plus_elo_calibrated" if "current_plus_elo_calibrated" in variant_options else variant_options[0]
    selected_variant = st.selectbox("Historical forecast variant", variant_options, index=variant_options.index(default_variant))
    historical_selected = comparison[
        (comparison["model_variant"] == selected_variant) & (comparison["team"].isin([home_team, away_team]))
    ].copy()
    historical_selected = historical_selected.sort_values(["season", "expected_position"])
    historical_display = historical_selected[
        ["season", "team", "expected_position", "actual_position", "expected_points", "points", "position_error", "points_error"]
    ].copy()
    for column in ["expected_position", "expected_points", "position_error", "points_error"]:
        historical_display[column] = historical_display[column].map(lambda value: f"{float(value):.1f}")
    st.markdown("#### Selected Teams In Historical Backtests")
    st.dataframe(historical_display, width="stretch", hide_index=True)

    with st.expander("Validation summary", expanded=False):
        st.dataframe(summary, width="stretch", hide_index=True)
        st.dataframe(by_season, width="stretch", hide_index=True)


def show_missing_model_message() -> None:
    st.warning("No trained model found yet.")
    st.write("Train the model first, then refresh this page:")
    st.code("python train_model.py", language="bash")


def main() -> None:
    inject_styles()
    st.markdown(
        dedent(
            """
        <div class="hero">
            <div class="muted">Premier League Prediction Model</div>
            <h1>Football analytics dashboard</h1>
            <div class="muted">
                Machine learning model estimating home win, draw and away win probabilities using historical
                Premier League results, xG, recent form, Elo team strength and fatigue signals.
            </div>
            <div class="badge-row">
                <span class="badge">Predictions are probabilities, not guarantees</span>
                <span class="badge good">Time-based validation</span>
                <span class="badge good">Only active inputs shown</span>
            </div>
        </div>
        """
        ),
        unsafe_allow_html=True,
    )

    if not Path(MODEL_PATH).exists():
        show_missing_model_message()
        return

    artifact = load_model_artifact()
    model = artifact["model"]
    feature_columns = artifact["feature_columns"]
    team_history = artifact["team_history"]
    elo_state = artifact.get("elo_state", {})
    metrics = load_metrics()
    calibrated_layer = load_calibrated_layer()
    teams = selectable_current_teams(team_history)
    missing_current_teams = unavailable_current_teams(team_history)
    stale_teams = stale_current_teams(team_history)
    latest_data_date = latest_dataset_date(team_history)

    if not teams:
        st.error("No current Premier League teams are available in the saved model history.")
        return

    st.markdown("<div class='input-card'>", unsafe_allow_html=True)
    st.subheader("Match Setup")
    input_cols = st.columns([1, 1, 0.7])
    with input_cols[0]:
        home_team = st.selectbox("Home team", teams, index=teams.index("Arsenal") if "Arsenal" in teams else 0)
    with input_cols[1]:
        away_default = teams.index("Brighton") if "Brighton" in teams else min(1, len(teams) - 1)
        away_team = st.selectbox("Away team", teams, index=away_default)
    with input_cols[2]:
        predict_clicked = st.button("Predict", type="primary", width="stretch")
    if predict_clicked:
        st.session_state["active_prediction_match"] = {
            "home_team": home_team,
            "away_team": away_team,
        }
    if latest_data_date:
        st.caption(
            f"Prediction uses the latest available form data through {latest_data_date}. "
            "Update/retrain the model after new matches to refresh the form curve."
        )
    st.markdown("</div>", unsafe_allow_html=True)

    with st.sidebar:
        st.header("Model Notes")
        st.caption("Training data currently loaded locally: Premier League 2019/20 to 2025/26.")
        if latest_data_date:
            st.caption(f"Latest match in model history: {latest_data_date}")
        st.caption("Team selectors show current Premier League teams that also exist in the model history.")
        if missing_current_teams:
            st.caption(f"Current PL teams unavailable in model history: {', '.join(missing_current_teams)}")
        if stale_teams:
            st.caption(
                "Current PL teams hidden because their latest local EPL history is stale: "
                f"{', '.join(stale_teams)}"
            )
        if calibrated_layer is not None:
            st.caption(f"Calibrated probability layer: {calibrated_layer.get('method', 'available')}")
        if metrics:
            latest = (
                metrics.get("xg_schedule_elo_shot_volume_model")
                or metrics.get("xg_schedule_elo_model")
                or metrics.get("xg_schedule_model")
                or {}
            )
            if latest.get("test_start_date"):
                st.caption(f"Saved model test period starts: {latest['test_start_date']}")

    if home_team == away_team:
        st.error("Choose two different teams.")
        return

    active_prediction = st.session_state.get("active_prediction_match")
    if active_prediction is None:
        st.info("Choose a fixture and run a prediction.")
        render_model_status(feature_columns)
        return

    prediction_home_team = str(active_prediction["home_team"])
    prediction_away_team = str(active_prediction["away_team"])
    if {prediction_home_team, prediction_away_team} - set(teams):
        st.session_state.pop("active_prediction_match", None)
        st.info("Choose a fixture and run a prediction.")
        render_model_status(feature_columns)
        return

    if (prediction_home_team, prediction_away_team) != (home_team, away_team):
        st.info(
            f"Showing last prediction: {prediction_home_team} vs {prediction_away_team}. "
            "Click Predict to update to the selected teams."
        )

    home_team = prediction_home_team
    away_team = prediction_away_team

    features = build_prediction_features(home_team, away_team, team_history, feature_columns, elo_state=elo_state)
    row = features.iloc[0].to_dict()
    raw_probabilities = model.predict_proba(features)[0]
    probabilities, is_calibrated, calibration_method = apply_calibration(raw_probabilities, calibrated_layer, features)
    quality_result = assess_prediction_data_quality(
        row,
        home_team,
        away_team,
        team_history=team_history,
        latest_data_date=latest_data_date,
    )
    warnings = quality_result.warnings

    prediction_tab, why_tab, quality_tab, technical_tab, season_tab = st.tabs(
        ["Prediction", "Why / Key Factors", "Data Quality", "Technical Details", "Season Projection"]
    )

    with prediction_tab:
        summary_card(home_team, away_team, probabilities, warnings)
        st.markdown("")
        st.markdown(
            """
            This model estimates probabilities, not certainties. A 64% home win probability means the model rates
            home win as the most likely outcome based on historical data, but football results remain uncertain.
            """
        )
        if is_calibrated:
            st.caption(f"Primary probabilities are calibrated with `{calibration_method}`. Raw model output is available under technical details.")
        if latest_data_date:
            st.caption(
                f"Form and xG inputs use each team's latest 5 matches available through {latest_data_date}. "
                "Fatigue inputs use the latest match date plus recent 14-day schedule activity."
            )
        render_probability_bar(probabilities, home_team, away_team)
        st.subheader("Model Fair Odds")
        st.caption("Fair odds are calculated directly from the displayed model probabilities, before bookmaker margin.")
        render_model_fair_odds(probabilities, home_team, away_team)
        render_bookmaker_odds_comparison(probabilities, home_team, away_team)

    with why_tab:
        st.subheader("Why The Model Thinks This")
        insights = build_insights(row, home_team, away_team)
        st.markdown("<ul class='insight-list'>" + "".join(f"<li>{item}</li>" for item in insights) + "</ul>", unsafe_allow_html=True)
        st.subheader("Feature Groups")
        grouped_feature_cards(row, home_team, away_team)
        render_recent_head_to_head(home_team, away_team)

    with quality_tab:
        left, right = st.columns([0.9, 1.1])
        with left:
            st.subheader("Confidence & Data Quality")
            render_confidence_badge(probabilities, warnings)
            st.write("")
            render_data_quality_card(quality_result)
        with right:
            st.subheader("Model & Data Status")
            render_model_status(feature_columns, quality_result.checks)
            st.caption(
                "Status guide: Active = used in production, Candidate = promising but not fully production, "
                "Benchmark only = evaluated but not used directly, Research mode = data or validation insufficient, "
                "Missing = data unavailable."
            )
            st.caption(
                "Market odds are currently used as a benchmark only because the available historical odds may represent "
                "closing prices. They are not used in production predictions until pre-match timing is verified."
            )

    with technical_tab:
        if is_calibrated:
            st.write("Raw model probabilities")
            raw_display = pd.DataFrame(
                {
                    "Outcome": [f"{home_team} win", "Draw", f"{away_team} win"],
                    "Raw probability": raw_probabilities,
                    "Displayed probability": probabilities,
                    "Displayed fair odds": fair_odds_from_probabilities(probabilities),
                }
            )
            st.dataframe(raw_display, width="stretch", hide_index=True)
        st.write("Feature values used by the saved model artifact")
        technical_details(features)

    with season_tab:
        render_season_projection_tab(home_team, away_team, teams)


if __name__ == "__main__":
    main()
