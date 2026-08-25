from __future__ import annotations

import base64
import html as html_lib
import json
import subprocess
from datetime import date, timedelta
from pathlib import Path
from textwrap import dedent

import joblib
import numpy as np
import pandas as pd
import streamlit as st

from data_quality import assess_prediction_data_quality
from help_text import (
    active_features_text,
    fair_odds_text,
    how_model_works_text,
    investigated_features_text,
    probability_confidence_text,
    raw_vs_displayed_probability_text,
    season_projection_text,
    validation_metrics,
    validation_text,
)
from model_feature_status import FEATURE_STATUS, active_feature_statuses, inactive_feature_statuses, status_tone
from official_fixtures import (
    OFFICIAL_FIXTURE_PATH,
    detect_fixture_mode,
    fixtures_for_model,
    load_official_fixtures,
    schedule_context_for_fixture,
)
from predict import MODEL_PATH, build_prediction_features
from season_simulation import (
    expected_points_from_probabilities,
    filter_unplayed_fixtures,
    load_completed_current_season_matches,
    monte_carlo_season,
    predict_fixture_probabilities,
    projection_feature_overrides,
    read_fixture_list,
    read_default_upcoming_fixtures,
    season_table_from_results,
    season_start_feature_audit,
    starting_points_from_completed,
    validate_projection_feature_inputs,
)
from scoreline_model import ScorelineProbability, estimate_scorelines
from squad_strength import (
    apply_squad_strength_prior,
    load_squad_strength,
    normalize_squad_strength,
    squad_strength_lookup,
)
from train_model import load_matches


st.set_page_config(page_title="Football Analytics Dashboard", layout="wide")


def app_version() -> str:
    try:
        result = subprocess.run(
            ["git", "rev-parse", "--short", "HEAD"],
            check=True,
            capture_output=True,
            text=True,
            timeout=2,
        )
    except (OSError, subprocess.SubprocessError):
        return "unknown"
    return result.stdout.strip() or "unknown"

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
    "Chelsea",
    "Coventry",
    "Crystal Palace",
    "Everton",
    "Fulham",
    "Hull",
    "Ipswich",
    "Leeds",
    "Liverpool",
    "Man City",
    "Man United",
    "Newcastle",
    "Nott'm Forest",
    "Sunderland",
    "Tottenham",
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
SEASON_PROJECTION_VERSION = "balanced_round_robin_long_term_prior_squad_strength_v5"
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
        .scoreline-section {
            border: 1px solid rgba(148, 163, 184, 0.16);
            border-radius: 8px;
            padding: 14px;
            background: rgba(15, 23, 42, 0.38);
            margin-top: 14px;
        }
        .scoreline-title-row {
            display: flex;
            justify-content: space-between;
            gap: 12px;
            align-items: flex-start;
            flex-wrap: wrap;
            margin-bottom: 10px;
        }
        .scoreline-grid {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(150px, 1fr));
            gap: 10px;
        }
        .scoreline-card {
            border: 1px solid rgba(148, 163, 184, 0.16);
            border-radius: 8px;
            padding: 10px;
            background: rgba(2, 6, 23, 0.28);
        }
        .scoreline-card.primary {
            border-color: rgba(34, 197, 94, 0.42);
            background: rgba(22, 101, 52, 0.16);
        }
        .scoreline-number {
            font-size: 1.28rem;
            font-weight: 900;
            margin-top: 3px;
        }
        .scoreline-prob {
            color: var(--muted);
            font-size: 0.82rem;
            font-weight: 800;
            margin-top: 2px;
        }
        .scoreline-list {
            margin: 8px 0 0;
            padding-left: 18px;
        }
        .scoreline-list li {
            display: flex;
            justify-content: space-between;
            gap: 12px;
            color: var(--text);
            font-size: 0.88rem;
            margin: 5px 0;
        }
        .scoreline-list strong {
            color: #86efac;
            white-space: nowrap;
        }
        div[data-testid="stTabs"] div[role="tablist"] {
            gap: 12px;
            border: 1px solid rgba(148, 163, 184, 0.18);
            border-radius: 8px;
            padding: 10px;
            margin-bottom: 18px;
            flex-wrap: wrap;
            background: rgba(2, 6, 23, 0.46);
            box-shadow: inset 0 1px 0 rgba(255, 255, 255, 0.04), 0 14px 34px rgba(0, 0, 0, 0.18);
        }
        div[data-testid="stTabs"] button[role="tab"],
        div[data-testid="stTabs"] div[role="tab"][data-testid="stTab"] {
            border: 2px solid rgba(34, 197, 94, 0.50) !important;
            border-radius: 8px !important;
            background: linear-gradient(180deg, #14532d 0%, #052e16 100%) !important;
            color: #f8fafc !important;
            padding: 12px 17px !important;
            min-height: 48px;
            min-width: 128px;
            display: inline-flex;
            align-items: center;
            justify-content: center;
            box-shadow: 0 10px 22px rgba(0, 0, 0, 0.30), inset 0 1px 0 rgba(255, 255, 255, 0.09);
            cursor: pointer;
            transition: transform 120ms ease, border-color 120ms ease, background 120ms ease, color 120ms ease, box-shadow 120ms ease;
        }
        div[data-testid="stTabs"] button[role="tab"]:hover,
        div[data-testid="stTabs"] div[role="tab"][data-testid="stTab"]:hover {
            transform: translateY(-2px);
            border-color: rgba(134, 239, 172, 0.95) !important;
            background: linear-gradient(180deg, #16a34a 0%, #166534 100%) !important;
            color: #ffffff !important;
            box-shadow: 0 13px 26px rgba(0, 0, 0, 0.34), 0 0 0 3px rgba(34, 197, 94, 0.14);
        }
        div[data-testid="stTabs"] button[role="tab"][aria-selected="true"],
        div[data-testid="stTabs"] div[role="tab"][data-testid="stTab"][aria-selected="true"] {
            border-color: rgba(187, 247, 208, 0.98) !important;
            background: linear-gradient(180deg, #22c55e 0%, #15803d 100%) !important;
            color: #ffffff !important;
            box-shadow: 0 0 0 3px rgba(34, 197, 94, 0.22), 0 14px 30px rgba(21, 128, 61, 0.34);
        }
        div[data-testid="stTabs"] button[role="tab"] p,
        div[data-testid="stTabs"] div[role="tab"][data-testid="stTab"] p {
            font-weight: 850;
            font-size: 0.92rem;
            line-height: 1.1;
            margin: 0;
        }
        div[data-testid="stTabs"] button[role="tab"] *,
        div[data-testid="stTabs"] div[role="tab"][data-testid="stTab"] * {
            color: inherit;
        }
        .dashboard-nav-title {
            color: #a7f3d0;
            font-size: 0.78rem;
            font-weight: 900;
            letter-spacing: 0.08em;
            margin: 8px 0 8px;
            text-transform: uppercase;
        }
        .dashboard-nav-spacer {
            height: 14px;
        }
        div[data-testid="stButton"] > button {
            border-radius: 8px;
            min-height: 44px;
            font-weight: 850;
        }
        div[data-testid="stSegmentedControl"] {
            margin-bottom: 14px;
        }
        div[data-testid="stSegmentedControl"] label {
            border-radius: 8px !important;
            min-height: 44px;
            font-weight: 850;
        }
        button[data-testid="stBaseButton-segmented_control"] {
            background: #09172a !important;
            border: 1px solid rgba(229, 231, 235, 0.22) !important;
            border-radius: 8px !important;
            color: #e5e7eb !important;
            min-height: 44px !important;
            font-weight: 850 !important;
        }
        button[data-testid="stBaseButton-segmented_controlActive"] {
            background: #2dd4bf !important;
            border: 1px solid #2dd4bf !important;
            border-radius: 8px !important;
            color: #052e2b !important;
            min-height: 44px !important;
            font-weight: 900 !important;
            box-shadow: 0 10px 22px rgba(45, 212, 191, 0.18) !important;
        }
        div[data-testid="stSelectbox"] [data-baseweb="select"],
        .stSelectbox [data-baseweb="select"],
        div[data-testid="stSelectbox"] [data-baseweb="select"] > div,
        .stSelectbox [data-baseweb="select"] > div,
        div[data-testid="stSelectbox"] .react-aria-ComboBox div[role="group"],
        .stSelectbox .react-aria-ComboBox div[role="group"] {
            background: #f8fafc !important;
            border: 1px solid rgba(34, 197, 94, 0.78) !important;
            border-radius: 8px !important;
            color: #0f172a !important;
            min-height: 48px !important;
            box-shadow: 0 8px 20px rgba(34, 197, 94, 0.14) !important;
        }
        div[data-testid="stSelectbox"] [data-baseweb="select"] span,
        div[data-testid="stSelectbox"] [data-baseweb="select"] div,
        div[data-testid="stSelectbox"] [data-baseweb="select"] input,
        .stSelectbox [data-baseweb="select"] span,
        .stSelectbox [data-baseweb="select"] div,
        .stSelectbox [data-baseweb="select"] input,
        div[data-testid="stSelectbox"] .react-aria-ComboBox div,
        div[data-testid="stSelectbox"] .react-aria-ComboBox input,
        .stSelectbox .react-aria-ComboBox div,
        .stSelectbox .react-aria-ComboBox input {
            color: #0f172a !important;
            -webkit-text-fill-color: #0f172a !important;
        }
        div[data-testid="stSelectbox"] [data-baseweb="select"] svg,
        .stSelectbox [data-baseweb="select"] svg,
        div[data-testid="stSelectbox"] .react-aria-ComboBox svg,
        .stSelectbox .react-aria-ComboBox svg {
            color: #166534 !important;
            fill: #166534 !important;
        }
        div[data-testid="stSelectbox"] label p {
            color: #e5e7eb;
            font-size: 0.93rem;
            font-weight: 850;
        }
        .compact-note-row {
            display: flex;
            flex-wrap: wrap;
            gap: 8px;
            margin: 10px 0 16px;
        }
        .info-card {
            border: 1px solid rgba(148, 163, 184, 0.18);
            border-radius: 8px;
            padding: 14px;
            background: rgba(15, 23, 42, 0.58);
            margin-bottom: 12px;
        }
        .info-card h4 {
            margin: 0 0 6px;
            font-size: 1rem;
        }
        .info-card p {
            margin: 0;
            color: var(--muted);
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
        .compact-status-grid {
            grid-template-columns: repeat(auto-fit, minmax(140px, 1fr));
        }
        .compact-status-grid .status-item {
            padding: 7px 8px;
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
            .scoreline-grid {
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


@st.cache_data(show_spinner=False)
def load_official_fixture_data() -> tuple[pd.DataFrame, object]:
    mode = detect_fixture_mode()
    if not mode.validation_ok:
        return pd.DataFrame(), mode
    frame = load_official_fixtures(OFFICIAL_FIXTURE_PATH)
    return frame, mode


def fixture_label(row: pd.Series) -> str:
    return (
        f"MW{int(row['matchweek'])}: {row['home_team']} v {row['away_team']} — "
        f"{row['date']} {row['kickoff_time_dk']} DK"
    )


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


def market_probabilities_from_odds(offered_odds: list[float]) -> tuple[list[float], float]:
    odds = np.asarray(offered_odds, dtype=float)
    implied = 1.0 / np.clip(odds, 1.01, None)
    total_implied = float(implied.sum())
    normalized = implied / total_implied if total_implied else np.array([1 / 3, 1 / 3, 1 / 3])
    margin = total_implied - 1.0
    return [float(value) for value in normalized], margin


def render_model_fair_odds(probabilities, home_team: str, away_team: str) -> None:
    labels = [f"{home_team} win", "Draw", f"{away_team} win"]
    fair_odds = fair_odds_from_probabilities(probabilities)
    st.markdown(
        "<span class='badge warn'>Market odds: Benchmark only</span>",
        unsafe_allow_html=True,
    )
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

    with st.expander("Manual bookmaker odds comparison", expanded=True):
        use_market_odds = st.checkbox(
            "Compare with bookmaker odds",
            value=False,
            key="use_manual_bookmaker_odds",
            help="Use this for live/manual comparison only. These odds are not used as production model inputs.",
        )
        if not use_market_odds:
            return

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

        market_probabilities, market_margin = market_probabilities_from_odds(offered_odds)
        market_favorite_index = int(np.argmax(market_probabilities))
        model_favorite_index = int(np.argmax(probabilities))
        market_html = "<div class='odds-card-grid'>"
        for index, (label, probability) in enumerate(zip(labels, market_probabilities)):
            highlight = " value" if index == market_favorite_index else ""
            market_html += dedent(
                f"""
            <div class="odds-card{highlight}">
                <div class="prob-label">{html_lib.escape(label)}</div>
                <div class="odds-number">{probability * 100:.1f}%</div>
                <div class="odds-detail">Market-implied probability</div>
            </div>
            """
            )
        market_html += "</div>"
        st.markdown("##### Market-implied probabilities")
        st.markdown(market_html, unsafe_allow_html=True)
        st.caption(
            f"Estimated bookmaker margin: {market_margin * 100:.1f}%. "
            "Market probabilities are normalized so Home/Draw/Away sum to 100%."
        )
        if market_favorite_index == model_favorite_index:
            st.info(f"Model and market agree that {labels[model_favorite_index]} is most likely.")
        else:
            st.warning(
                f"Model favorite: {labels[model_favorite_index]}. "
                f"Market favorite: {labels[market_favorite_index]}."
            )

        rows = []
        for label, probability, market_probability, fair, offered in zip(
            labels, probabilities, market_probabilities, fair_odds, offered_odds
        ):
            expected_return = (float(probability) * float(offered)) - 1.0
            edge_pct = expected_return * 100
            value_label = "Potential model value" if offered > fair else "No model value"
            rows.append(
                {
                    "Outcome": label,
                    "Model probability": f"{float(probability) * 100:.1f}%",
                    "Market probability": f"{float(market_probability) * 100:.1f}%",
                    "Model vs market": f"{(float(probability) - float(market_probability)) * 100:+.1f} pp",
                    "Model fair odds": f"{fair:.2f}",
                    "Bookmaker odds": f"{float(offered):.2f}",
                    "Model edge": f"{edge_pct:+.1f}%",
                    "Assessment": value_label,
                }
            )

        result = pd.DataFrame(rows)
        st.dataframe(result, width="stretch", hide_index=True)
        best_edge = max(rows, key=lambda row: float(row["Model edge"].replace("%", "")))
        best_edge_value = float(best_edge["Model edge"].replace("%", ""))
        if best_edge_value > 0:
            st.success(
                f"Highest model edge: {best_edge['Outcome']} at {best_edge['Model edge']}. "
                "Treat this as a comparison signal only."
            )
        else:
            st.info("No entered bookmaker odds are currently above the model fair odds.")

def _format_scoreline(scoreline: ScorelineProbability | None, home_team: str, away_team: str) -> tuple[str, str]:
    if scoreline is None:
        return "Unavailable", ""
    return (
        f"{html_lib.escape(home_team)} {scoreline.home_goals}-{scoreline.away_goals} {html_lib.escape(away_team)}",
        f"{scoreline.probability * 100:.1f}%",
    )


def _scoreline_list_html(scorelines: list[ScorelineProbability], home_team: str, away_team: str) -> str:
    items = []
    for scoreline in scorelines:
        items.append(
            "<li>"
            f"<span>{html_lib.escape(home_team)} {scoreline.home_goals}-{scoreline.away_goals} {html_lib.escape(away_team)}</span>"
            f"<strong>{scoreline.probability * 100:.1f}%</strong>"
            "</li>"
        )
    return "<ol class='scoreline-list'>" + "".join(items) + "</ol>"


def render_scoreline_section(row: dict[str, float], probabilities, home_team: str, away_team: str) -> None:
    try:
        scoreline_result = estimate_scorelines(row, probabilities)
    except Exception as exc:  # pragma: no cover - defensive Streamlit boundary
        print(f"Scoreline estimate failed: {exc}")
        st.info("Scoreline estimate unavailable for this fixture.")
        return

    predicted_outcome_index = int(scoreline_result["predicted_outcome_index"])
    predicted_outcome_label = ["home win", "draw", "away win"][predicted_outcome_index]
    predicted_outcome_lists = [
        scoreline_result["top_home_win_scorelines"],
        scoreline_result["top_draw_scorelines"],
        scoreline_result["top_away_win_scorelines"],
    ]
    predicted_outcome_scorelines = predicted_outcome_lists[predicted_outcome_index]
    most_likely = scoreline_result["most_likely"]
    home_win = scoreline_result["most_likely_home_win"]
    draw = scoreline_result["most_likely_draw"]
    away_win = scoreline_result["most_likely_away_win"]
    cards = [
        ("Highest individual scoreline", most_likely, ""),
        ("Most likely home-win scoreline", home_win, ""),
        ("Most likely draw scoreline", draw, ""),
        ("Most likely away-win scoreline", away_win, ""),
    ]

    html = dedent(
        f"""
            <div class="scoreline-section">
            <div class="scoreline-title-row">
                <div>
                    <div class="prob-label">Most likely scorelines</div>
                </div>
                <div class="odds-detail">
                    Estimated goals: <strong>{html_lib.escape(home_team)} {float(scoreline_result['expected_home_goals']):.2f}</strong>
                    -
                    <strong>{float(scoreline_result['expected_away_goals']):.2f} {html_lib.escape(away_team)}</strong>
                </div>
            </div>
            <div class="scoreline-card primary">
                <div class="prob-label">Top scorelines for model's most likely outcome: {html_lib.escape(predicted_outcome_label)}</div>
                {_scoreline_list_html(predicted_outcome_scorelines, home_team, away_team)}
            </div>
            <div class="scoreline-grid">
        """
    )
    for label, scoreline, tone in cards:
        text, probability = _format_scoreline(scoreline, home_team, away_team)
        html += dedent(
            f"""
            <div class="scoreline-card {tone}">
                <div class="prob-label">{html_lib.escape(label)}</div>
                <div class="scoreline-number">{text}</div>
                <div class="scoreline-prob">{probability}</div>
            </div>
            """
        )
    html += "</div></div>"
    st.markdown(html, unsafe_allow_html=True)

    with st.expander("Show scoreline details", expanded=False):
        top_rows = [
            {
                "Scoreline": f"{item.home_goals}-{item.away_goals}",
                "Probability": f"{item.probability * 100:.1f}%",
            }
            for item in scoreline_result["top_scorelines"]
        ]
        st.dataframe(pd.DataFrame(top_rows), width="stretch", hide_index=True)
        grouped_rows = []
        for group_name, items in (
            ("Home win", scoreline_result["top_home_win_scorelines"]),
            ("Draw", scoreline_result["top_draw_scorelines"]),
            ("Away win", scoreline_result["top_away_win_scorelines"]),
        ):
            for item in items:
                grouped_rows.append(
                    {
                        "Outcome group": group_name,
                        "Scoreline": item.scoreline,
                        "Probability": f"{item.probability * 100:.1f}%",
                    }
                )
        st.dataframe(pd.DataFrame(grouped_rows), width="stretch", hide_index=True)


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
    active = active_feature_statuses(feature_columns)
    inactive = inactive_feature_statuses()
    names_to_show = [
        "Recent form",
        "xG strength",
        "Schedule and fatigue",
        "Elo rating",
        "Shot volume",
        "Market odds",
        "Injuries and suspensions",
        "Lineup stability",
        "Tactical intelligence",
    ]
    statuses = []
    for name in names_to_show:
        entry = active.get(name) or inactive.get(name) or FEATURE_STATUS.get(name)
        if entry is None:
            continue
        statuses.append((name, entry.status, status_tone(entry.status), entry.evidence))
    html = '<div class="status-grid">'
    for name, state, tone, tooltip in statuses:
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


def render_tested_ideas_status() -> None:
    tested = [(name, entry) for name, entry in FEATURE_STATUS.items() if entry.status == "Tested - Not adopted"]
    if not tested:
        return
    html = '<div class="status-grid compact-status-grid">'
    for name, entry in tested:
        html += dedent(
            f"""
        <div class="status-item" title="{html_lib.escape(entry.evidence)}">
            <div class="status-name">{name}</div>
            <div class="status-value"><span class="badge bad">{entry.status}</span></div>
        </div>
        """
        )
    html += "</div>"
    st.markdown(html, unsafe_allow_html=True)


DASHBOARD_NAV_ITEMS = [
    "Prediction",
    "Why / Key Factors",
    "Data Quality",
    "Technical Details",
    "Season Projection",
    "Info",
]


def render_dashboard_navigation() -> str:
    active = st.session_state.get("dashboard_section", "Prediction")
    if active not in DASHBOARD_NAV_ITEMS:
        active = "Prediction"

    st.markdown("<div class='dashboard-nav-title'>Dashboard navigation</div>", unsafe_allow_html=True)
    selected = st.segmented_control(
        "Dashboard section",
        DASHBOARD_NAV_ITEMS,
        default=active,
        key="dashboard_section_control",
        label_visibility="collapsed",
        width="stretch",
    )
    if selected in DASHBOARD_NAV_ITEMS:
        active = str(selected)
    st.session_state["dashboard_section"] = active
    st.markdown("<div class='dashboard-nav-spacer'></div>", unsafe_allow_html=True)
    return active


def render_model_help(feature_columns: list[str], metrics: dict) -> None:
    with st.expander("About the model", expanded=False):
        st.write(how_model_works_text())
    with st.expander("Active model features", expanded=False):
        st.markdown(active_features_text(feature_columns))
    with st.expander("Tested but not adopted / research", expanded=False):
        st.markdown(investigated_features_text())
    with st.expander("Probability, confidence and fair odds", expanded=False):
        st.markdown(probability_confidence_text())
        st.markdown(raw_vs_displayed_probability_text())
        st.markdown(fair_odds_text())
    with st.expander("Season projections", expanded=False):
        st.write(season_projection_text())
    with st.expander("Model validation", expanded=False):
        st.markdown(validation_text(metrics, MODEL_PATH))


def render_validation_card(metrics: dict) -> None:
    row = validation_metrics(metrics)
    with st.container(border=True):
        st.markdown("#### Model Validation")
        if row is None:
            st.caption("Validation metrics are not available yet. Run `python evaluate_model.py`.")
            return
        cols = st.columns(4)
        cols[0].metric("Accuracy", f"{float(row.get('accuracy', 0.0)):.3f}")
        cols[1].metric("Log Loss", f"{float(row.get('log_loss', 0.0)):.3f}")
        cols[2].metric("Brier", f"{float(row.get('brier_score', 0.0)):.3f}")
        cols[3].metric("ECE", f"{float(row.get('mean_absolute_calibration_error', 0.0)):.3f}")
        st.caption(
            f"Trained on matches before {row.get('test_start_date', 'unknown')}. "
            f"Tested on {int(row.get('test_rows', 0))} later matches from {row.get('test_start_date', 'unknown')} onward."
        )


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
) -> None:
    top_index = int(max(range(len(probabilities)), key=lambda idx: probabilities[idx]))
    outcome = RESULT_COPY[top_index]
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


def render_low_history_prediction_notes(
    row: dict[str, float],
    home_team: str,
    away_team: str,
    team_history: dict[str, dict[str, list]],
) -> None:
    rows = []
    for side, team in [("home", home_team), ("away", away_team)]:
        if team in team_history:
            continue
        rows.append(
            {
                "Team": team,
                "Source": "Championship-adjusted / promoted baseline",
                "Points last 5": f"{value(row, f'{side}_team_points_last_5'):.2f}",
                "xG": f"{value(row, f'{side}_xg_avg'):.2f}",
                "xGA": f"{value(row, f'{side}_xga_avg'):.2f}",
                "xG diff": f"{value(row, f'{side}_xg_diff'):.2f}",
                "Shots last 5": f"{value(row, f'{side}_shots_avg_last5'):.2f}",
            }
        )
    if not rows:
        return
    st.info(
        "Low-history Premier League team adjustment: this team has limited or no local Premier League history, "
        "so the prediction uses transparent Championship-adjusted or promoted-team baseline values instead of zero-filled form."
    )
    st.dataframe(pd.DataFrame(rows), width="stretch", hide_index=True)


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


def render_prediction_info_tab(
    active_prediction: dict,
    selected_match_date: str | None,
    latest_data_date,
    is_calibrated: bool,
    calibration_method: str | None,
    version: str,
) -> None:
    st.subheader("Prediction Info")
    st.markdown(
        f"""
        <div class="info-card">
            <h4>App version</h4>
            <p>
                Running commit: <strong>{html_lib.escape(version)}</strong>. Use this to confirm whether Streamlit Cloud
                has deployed the latest GitHub version.
            </p>
        </div>
        """,
        unsafe_allow_html=True,
    )
    st.markdown(
        """
        <div class="info-card">
            <h4>Probabilities, not certainties</h4>
            <p>
                The model estimates probabilities. A 64% home win probability means the model rates the home win as
                the most likely outcome based on historical data, but football results remain uncertain.
            </p>
        </div>
        """,
        unsafe_allow_html=True,
    )
    if is_calibrated:
        st.markdown(
            f"""
            <div class="info-card">
                <h4>Calibration</h4>
                <p>
                    Primary probabilities are calibrated with <strong>{html_lib.escape(str(calibration_method))}</strong>.
                    Raw model output is available under Technical Details.
                </p>
            </div>
            """,
            unsafe_allow_html=True,
        )
    if selected_match_date:
        st.markdown(
            f"""
            <div class="info-card">
                <h4>Fixture</h4>
                <p>
                    Official fixture: Matchweek {html_lib.escape(str(active_prediction.get('matchweek')))} ·
                    {html_lib.escape(str(selected_match_date))} ·
                    {html_lib.escape(str(active_prediction.get('kickoff_time_uk')))} UK /
                    {html_lib.escape(str(active_prediction.get('kickoff_time_dk')))} DK.
                    Fixtures are scheduled subject to change.
                </p>
            </div>
            """,
            unsafe_allow_html=True,
        )
    if latest_data_date:
        st.markdown(
            f"""
            <div class="info-card">
                <h4>Data window</h4>
                <p>
                    Form and xG inputs use each team's latest 5 matches available through
                    {html_lib.escape(str(latest_data_date))}. Schedule and fatigue currently use Premier League fixtures only
                    unless European and cup fixture files are added.
                </p>
            </div>
            """,
            unsafe_allow_html=True,
        )
    st.markdown(
        """
        <div class="info-card">
            <h4>Scorelines</h4>
            <p>
                Scoreline estimates are derived from expected goals and aligned with the model's 1X2 probabilities.
                Correct-score probabilities are naturally low because each outcome is spread across many possible scorelines.
            </p>
        </div>
        <div class="info-card">
            <h4>Fair odds and bookmaker comparison</h4>
            <p>
                Model fair odds are calculated as 1 / displayed model probability. Manual bookmaker odds are converted into
                market-implied probabilities after removing bookmaker margin. Entered bookmaker odds are not used as model inputs.
            </p>
        </div>
        <div class="info-card">
            <h4>Model and data statuses</h4>
            <p>
                Active = used in production. Candidate = promising but not fully production. Tested - Not adopted = evaluated but
                not strong enough for production. Benchmark only = evaluated but not used directly. Research mode = data or
                validation insufficient. Missing = data unavailable.
            </p>
        </div>
        """,
        unsafe_allow_html=True,
    )


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
) -> tuple[pd.DataFrame, pd.DataFrame, str, str, pd.DataFrame, pd.DataFrame]:
    artifact = joblib.load(MODEL_PATH)
    fixture_path = OFFICIAL_FIXTURE_PATH
    if fixture_path.exists():
        official = load_official_fixtures(fixture_path)
        fixtures = fixtures_for_model(official)
        fixture_schedule_frame = official
        mode = detect_fixture_mode(fixture_path)
        source = mode.message
        completed_matches = load_completed_current_season_matches()
        starting_points = starting_points_from_completed(completed_matches)
        played_count = len(completed_matches)
        if played_count:
            fixtures = filter_unplayed_fixtures(fixtures, completed_matches)
            source = f"{source}; {played_count} completed fixtures included as actual table points"
    else:
        fixtures = build_fixture_skeleton(list(teams))
        fixture_schedule_frame = fixtures.rename(columns={"Season": "season", "Date": "date", "HomeTeam": "home_team", "AwayTeam": "away_team"})
        source = "Fixture skeleton: official upcoming fixture list not found locally"
        starting_points = {}

    calibrator = None
    calibration_path = Path("models") / "calibrated_probability_layer.joblib"
    if calibration_path.exists():
        layer = joblib.load(calibration_path)
        if list(layer.get("feature_columns", [])) == list(artifact["feature_columns"]) and layer.get("method") in {"sigmoid", "isotonic"}:
            calibrator = layer["calibrator"]

    feature_audit = season_start_feature_audit(teams, artifact["team_history"], artifact.get("elo_state", {}))
    squad_strength = normalize_squad_strength(load_squad_strength(), teams)
    if not squad_strength.empty:
        feature_audit = feature_audit.merge(
            squad_strength[
                [
                    "team",
                    "squad_market_value_eur",
                    "average_player_value_eur",
                    "squad_size",
                    "squad_strength_rank",
                    "squad_strength_percentile",
                    "squad_strength_score",
                    "squad_strength_bucket",
                    "squad_strength_used",
                    "source",
                    "source_url",
                    "last_updated",
                    "data_confidence",
                    "promoted_team_flag",
                ]
            ],
            on="team",
            how="left",
        )
    validation_status, validation = validate_projection_feature_inputs(feature_audit, artifact["feature_columns"])
    overrides = projection_feature_overrides(feature_audit)

    probabilities = predict_fixture_probabilities(
        fixtures,
        artifact["model"],
        artifact["feature_columns"],
        artifact["team_history"],
        artifact.get("elo_state", {}),
        calibrator=calibrator,
        team_feature_overrides=overrides,
        fixture_schedule_frame=fixture_schedule_frame,
    )
    long_term_strength = build_long_term_team_strength(teams, artifact.get("elo_state", {}))
    probabilities = blend_with_long_term_season_prior(probabilities, long_term_strength)
    probabilities_before_squad_strength = probabilities.copy()
    probabilities = apply_squad_strength_prior(probabilities, squad_strength_lookup(squad_strength))
    projection = monte_carlo_season(probabilities, n_simulations=simulations, starting_points=starting_points)
    expected = expected_points_from_probabilities(probabilities, starting_points=starting_points)
    projection = projection.merge(expected, on="team", how="left")
    projection_before_squad_strength = monte_carlo_season(
        probabilities_before_squad_strength,
        n_simulations=simulations,
        starting_points=starting_points,
    )
    projection_before_squad_strength = projection_before_squad_strength.merge(
        expected_points_from_probabilities(probabilities_before_squad_strength, starting_points=starting_points),
        on="team",
        how="left",
        suffixes=("", "_deterministic"),
    )
    projection = projection.merge(
        projection_before_squad_strength[
            ["team", "expected_points", "expected_position", "relegation_probability"]
        ].rename(
            columns={
                "expected_points": "expected_points_before_squad_strength",
                "expected_position": "expected_position_before_squad_strength",
                "relegation_probability": "relegation_probability_before_squad_strength",
            }
        ),
        on="team",
        how="left",
    )
    projection["projected_position"] = range(1, len(projection) + 1)
    return projection, probabilities, source, validation_status, validation, feature_audit


@st.cache_data(show_spinner=False)
def upcoming_season_start_feature_audit(
    teams: tuple[str, ...],
    model_mtime: float,
    projection_version: str,
) -> pd.DataFrame:
    artifact = joblib.load(MODEL_PATH)
    return season_start_feature_audit(teams, artifact["team_history"], artifact.get("elo_state", {}))


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


def format_season_projection_display(frame: pd.DataFrame) -> pd.DataFrame:
    base_columns = [
        "team",
        "expected_points",
        "expected_points_deterministic",
        "expected_position",
        "projected_position",
        "title_probability",
        "top_4_probability",
        "top_6_probability",
        "relegation_probability",
    ]
    display = probability_percent_columns(
        frame[[column for column in base_columns if column in frame.columns]],
        ["title_probability", "top_4_probability", "top_6_probability", "relegation_probability"],
    )
    display = display.rename(
        columns={
            "team": "Team",
            "expected_points": "Simulated points",
            "expected_points_deterministic": "Probability points",
            "expected_position": "Average simulated finish",
            "projected_position": "Ordered table rank",
            "title_probability": "Title",
            "top_4_probability": "Top 4",
            "top_6_probability": "Top 6",
            "relegation_probability": "Relegation",
        }
    )
    for column in ["Simulated points", "Probability points", "Average simulated finish"]:
        display[column] = display[column].map(lambda value: f"{float(value):.1f}")
    return display


def format_season_start_audit_display(frame: pd.DataFrame) -> pd.DataFrame:
    display = frame.copy()
    display = display.rename(
        columns={
            "team": "Team",
            "data_source_league": "Data source league",
            "premier_league_matches_available": "PL matches available",
            "latest_premier_league_match": "Latest PL match",
            "fallback_used": "Fallback used",
            "fallback_reason": "Fallback reason",
            "championship_data_available": "Championship data",
            "championship_match_count": "Championship matches",
            "promotion_adjustment_applied": "Promotion adjustment",
            "promoted_team_uncertainty_flag": "Higher uncertainty",
            "recent_form_points_last5": "Points last 5",
            "recent_goals_scored_avg_last5": "Goals avg last 5",
            "xg_strength_last5": "xG avg last 5",
            "xga_strength_last5": "xGA avg last 5",
            "xg_diff_last5": "xG diff last 5",
            "shots_avg_last5": "Shots avg last 5",
            "shots_on_target_avg_last5": "SOT avg last 5",
            "shots_avg_last10": "Shots avg last 10",
            "shots_on_target_avg_last10": "SOT avg last 10",
            "shots_avg_latest_season": "Shots avg latest season",
            "shots_on_target_avg_latest_season": "SOT avg latest season",
            "elo_rating": "Elo",
            "elo_recent_change": "Elo recent change",
            "squad_strength_rank": "Squad rank",
            "squad_strength_bucket": "Squad bucket",
            "squad_strength_score": "Squad score",
            "squad_market_value_eur": "Squad value EUR",
            "data_confidence": "Squad data confidence",
            "fallback_flags": "Fallback flags",
        }
    )
    columns = [
        "Team",
        "Data source league",
        "PL matches available",
        "Latest PL match",
        "Fallback used",
        "Fallback reason",
        "Championship data",
        "Championship matches",
        "Promotion adjustment",
        "Higher uncertainty",
        "Points last 5",
        "Goals avg last 5",
        "xG avg last 5",
        "xGA avg last 5",
        "xG diff last 5",
        "Shots avg last 5",
        "SOT avg last 5",
        "Shots avg last 10",
        "SOT avg last 10",
        "Shots avg latest season",
        "SOT avg latest season",
        "Elo",
        "Elo recent change",
        "Squad rank",
        "Squad bucket",
        "Squad score",
        "Squad value EUR",
        "Squad data confidence",
        "Fallback flags",
    ]
    display = display[[column for column in columns if column in display.columns]]
    numeric_columns = [
        "Goals avg last 5",
        "xG avg last 5",
        "xGA avg last 5",
        "xG diff last 5",
        "Shots avg last 5",
        "SOT avg last 5",
        "Shots avg last 10",
        "SOT avg last 10",
        "Shots avg latest season",
        "SOT avg latest season",
        "Elo",
        "Elo recent change",
        "Squad rank",
        "Squad score",
        "Squad value EUR",
    ]
    for column in numeric_columns:
        if column in display.columns:
            if column == "Elo":
                display[column] = display[column].map(lambda value: f"{float(value):.1f}")
            elif column == "Squad value EUR":
                display[column] = display[column].map(lambda value: "" if pd.isna(value) else f"€{float(value) / 1_000_000:.1f}m")
            else:
                display[column] = display[column].map(lambda value: "" if pd.isna(value) else f"{float(value):.2f}")
    return display


def render_season_projection_tab(home_team: str, away_team: str, teams: list[str]) -> None:
    st.subheader("Upcoming Season Projection")
    fixture_path = OFFICIAL_FIXTURE_PATH
    mode = detect_fixture_mode(fixture_path)
    projection_teams = tuple(teams)
    if mode.validation_ok:
        official = load_official_fixtures(fixture_path)
        projection_teams = tuple(sorted(set(official["home_team"]).union(official["away_team"])))
    projection, probabilities, source, validation_status, validation, feature_audit = upcoming_season_projection(
        projection_teams,
        10000,
        Path(MODEL_PATH).stat().st_mtime if Path(MODEL_PATH).exists() else 0.0,
        (Path("models") / "calibrated_probability_layer.joblib").stat().st_mtime
        if (Path("models") / "calibrated_probability_layer.joblib").exists()
        else 0.0,
        fixture_path.stat().st_mtime if fixture_path.exists() else 0.0,
        SEASON_PROJECTION_VERSION,
    )
    if mode.validation_ok:
        st.success(f"Fixture mode: {mode.mode}")
        st.caption(source)
    else:
        st.warning(
            "Official 2026/27 fixtures are not loaded. "
            "This projection uses a balanced 38-round home/away fixture skeleton, so exact fixture-order and fatigue effects remain illustrative."
        )
    st.caption("Premier League fixtures do not include European or domestic cup fixtures, so congestion from those competitions is not included.")
    st.info(
        "Season projection is intentionally more conservative than a single-match prediction. "
        "It blends the match model with a long-term team-strength prior from the last two completed seasons and Elo, "
        f"using a {SEASON_PROJECTION_PRIOR_WEIGHT:.0%} prior weight, then applies a mild squad-strength preseason prior when CSV values are available."
    )
    fallback_count = int(feature_audit["fallback_used"].sum()) if "fallback_used" in feature_audit else 0
    adjusted_count = int(feature_audit["promotion_adjustment_applied"].sum()) if "promotion_adjustment_applied" in feature_audit else 0
    squad_strength_count = int(feature_audit["squad_strength_used"].fillna(False).sum()) if "squad_strength_used" in feature_audit else 0
    zero_history = feature_audit.loc[feature_audit["premier_league_matches_available"].eq(0), "team"].tolist()
    cols = st.columns(5)
    cols[0].metric("Feature parity", validation_status)
    cols[1].metric("Official fixtures", "OK" if mode.validation_ok else "Fallback")
    cols[2].metric("Fallback teams", fallback_count)
    cols[3].metric("Promoted adjustment", f"Active ({adjusted_count})")
    cols[4].metric("Squad strength", f"Active ({squad_strength_count})" if squad_strength_count else "Missing")
    if validation_status == "Error":
        st.error("Season Projection feature validation found missing active production inputs. Check the audit table before using the projection.")
    elif validation_status == "Warning":
        st.warning(
            "Season Projection uses explicit fallback assumptions for low-history teams. "
            f"Teams with 0 local Premier League matches: {', '.join(zero_history) if zero_history else 'none'}."
        )
    else:
        st.success("Season Projection feature validation passed with no fallback warnings.")

    selected = projection[projection["team"].isin([home_team, away_team])].copy()
    st.markdown("#### Selected Teams")
    st.dataframe(format_season_projection_display(selected), width="stretch", hide_index=True)
    st.caption(
        "Average simulated finish is the main projection number. Ordered table rank is only the table order after sorting teams, "
        "so tightly grouped teams can look more separated than the simulation really says."
    )
    if not selected.empty:
        max_rank_gap = (selected["projected_position"] - selected["expected_position"]).abs().max()
        if max_rank_gap >= 3:
            largest_gap = selected.assign(rank_gap=(selected["projected_position"] - selected["expected_position"]).abs()).sort_values(
                "rank_gap", ascending=False
            ).iloc[0]
            st.warning(
                f"{largest_gap['team']} is a good example of why the two numbers differ: "
                f"its ordered table rank is {int(largest_gap['projected_position'])}, "
                f"but its average simulated finish is {float(largest_gap['expected_position']):.1f}. "
                "That means the model sees a wide range of season outcomes, not a fixed finishing position."
            )

    with st.expander("Full upcoming season projection", expanded=True):
        st.markdown(
            "The table is sorted by average simulated finish. Use the probability columns to judge uncertainty, "
            "especially for the lower-table cluster where a few expected points can move a team many places."
        )
        st.dataframe(format_season_projection_display(projection), width="stretch", hide_index=True)

    with st.expander("Season start feature audit", expanded=True):
        st.markdown(
            "These are the team-level feature values available before the 2026/27 season starts. "
            "For an individual fixture, the model maps the home team into the `home_*` columns and the away team into the `away_*` columns. "
            "Fallback flags show where the local Premier League dataset does not contain enough history."
        )
        selected_audit = feature_audit[feature_audit["team"].isin([home_team, away_team])]
        st.markdown("##### Selected teams")
        st.dataframe(format_season_start_audit_display(selected_audit), width="stretch", hide_index=True)
        with st.expander("Feature validation details", expanded=False):
            st.dataframe(validation, width="stretch", hide_index=True)
        st.markdown("##### All 2026/27 teams")
        st.dataframe(format_season_start_audit_display(feature_audit), width="stretch", hide_index=True)

    with st.expander("Promoted team adjustment", expanded=True):
        st.write(
            "Promoted teams with limited Premier League history are handled separately. "
            "If Championship data is available, it is converted into Premier League-equivalent values. "
            "If not, the model uses a conservative promoted-team baseline instead of treating missing Premier League form as zero."
        )
        promoted_display = feature_audit[
            feature_audit["promotion_adjustment_applied"] | feature_audit["fallback_used"] | feature_audit["premier_league_matches_available"].lt(5)
        ].merge(
            projection[["team", "expected_points", "relegation_probability"]],
            on="team",
            how="left",
        )
        if promoted_display.empty:
            st.success("No promoted-team adjustments are active.")
        else:
            promoted_display = probability_percent_columns(promoted_display, ["relegation_probability"])
            promoted_display = promoted_display.rename(
                columns={
                    "team": "Team",
                    "source_league": "Source league",
                    "premier_league_matches_available": "Local PL matches",
                    "promotion_adjustment_applied": "Adjustment applied",
                    "fallback_used": "Fallback used",
                    "expected_points": "Expected points",
                    "relegation_probability": "Relegation",
                }
            )
            promoted_display["Expected points"] = promoted_display["Expected points"].map(lambda value: f"{float(value):.1f}")
            st.dataframe(
                promoted_display[
                    [
                        "Team",
                        "Source league",
                        "Local PL matches",
                        "Adjustment applied",
                        "Fallback used",
                        "Expected points",
                        "Relegation",
                    ]
                ],
                width="stretch",
                hide_index=True,
            )

    with st.expander("Squad strength", expanded=True):
        st.write(
            "Squad strength is used as a preseason prior in Season Projection. "
            "It helps the model account for current roster quality when there is limited current-season Premier League evidence. "
            "Its influence decreases as the season produces new data."
        )
        if "squad_strength_used" not in feature_audit or not bool(feature_audit["squad_strength_used"].fillna(False).any()):
            st.warning("Squad strength CSV is missing or has no usable team values, so this prior is not active.")
        else:
            squad_display = feature_audit.merge(
                projection[
                    [
                        "team",
                        "expected_points",
                        "expected_points_before_squad_strength",
                        "relegation_probability",
                        "relegation_probability_before_squad_strength",
                        "projected_position",
                    ]
                ],
                on="team",
                how="left",
            )
            squad_display = squad_display.sort_values("squad_strength_rank", na_position="last").copy()
            for column in ["relegation_probability", "relegation_probability_before_squad_strength"]:
                squad_display[column] = squad_display[column].map(lambda value: "" if pd.isna(value) else f"{float(value) * 100:.1f}%")
            for column in ["expected_points", "expected_points_before_squad_strength"]:
                squad_display[column] = squad_display[column].map(lambda value: "" if pd.isna(value) else f"{float(value):.1f}")
            squad_display["squad_market_value_eur"] = squad_display["squad_market_value_eur"].map(
                lambda value: "" if pd.isna(value) else f"€{float(value) / 1_000_000:.1f}m"
            )
            st.dataframe(
                squad_display[
                    [
                        "team",
                        "projected_position",
                        "expected_points",
                        "expected_points_before_squad_strength",
                        "relegation_probability",
                        "relegation_probability_before_squad_strength",
                        "squad_strength_rank",
                        "squad_strength_bucket",
                        "squad_market_value_eur",
                        "data_confidence",
                        "last_updated",
                    ]
                ].rename(
                    columns={
                        "team": "Team",
                        "projected_position": "Projected rank",
                        "expected_points": "Expected points",
                        "expected_points_before_squad_strength": "Points before squad prior",
                        "relegation_probability": "Relegation",
                        "relegation_probability_before_squad_strength": "Relegation before squad prior",
                        "squad_strength_rank": "Squad rank",
                        "squad_strength_bucket": "Bucket",
                        "squad_market_value_eur": "Squad value",
                        "data_confidence": "Data confidence",
                        "last_updated": "Last updated",
                    }
                ),
                width="stretch",
                hide_index=True,
            )

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
    official_fixtures, fixture_mode = load_official_fixture_data()
    official_teams = sorted(set(official_fixtures["home_team"]).union(official_fixtures["away_team"])) if not official_fixtures.empty else []
    team_options = sorted(set(teams).union(official_teams))

    if not team_options:
        st.error("No current Premier League teams are available in the saved model history.")
        return

    st.markdown("<div class='input-card'>", unsafe_allow_html=True)
    st.subheader("Match Setup")
    predict_clicked = False
    selected_fixture = None
    if not official_fixtures.empty:
        selector_cols = st.columns([0.55, 1.45, 0.55])
        with selector_cols[0]:
            matchweeks = sorted(official_fixtures["matchweek"].unique())
            selected_matchweek = st.selectbox("Matchweek", matchweeks, format_func=lambda value: f"Matchweek {int(value)}")
        week_fixtures = official_fixtures[official_fixtures["matchweek"] == selected_matchweek].reset_index(drop=True)
        with selector_cols[1]:
            selected_index = st.selectbox(
                "Official fixture",
                list(range(len(week_fixtures))),
                format_func=lambda index: fixture_label(week_fixtures.iloc[int(index)]),
            )
            selected_fixture = week_fixtures.iloc[int(selected_index)]
        with selector_cols[2]:
            predict_clicked = st.button("Predict fixture", type="primary", width="stretch")
        home_team = str(selected_fixture["home_team"])
        away_team = str(selected_fixture["away_team"])
    else:
        home_team = "Arsenal" if "Arsenal" in team_options else team_options[0]
        away_team = "Brighton" if "Brighton" in team_options else team_options[min(1, len(team_options) - 1)]
        st.warning("Official 2026/27 fixtures are not loaded. Use manual team selection below.")

    with st.expander("Manual / custom fixture", expanded=official_fixtures.empty):
        input_cols = st.columns([1, 1, 0.7])
        with input_cols[0]:
            home_team = st.selectbox("Home team", team_options, index=team_options.index(home_team) if home_team in team_options else 0)
        with input_cols[1]:
            away_default = team_options.index(away_team) if away_team in team_options else min(1, len(team_options) - 1)
            away_team = st.selectbox("Away team", team_options, index=away_default)
        with input_cols[2]:
            manual_predict_clicked = st.button("Predict custom", type="secondary", width="stretch")
        if manual_predict_clicked:
            selected_fixture = None
            predict_clicked = True
    if predict_clicked:
        st.session_state["active_prediction_match"] = {
            "home_team": home_team,
            "away_team": away_team,
            "match_date": None if selected_fixture is None else str(selected_fixture["date"]),
            "matchweek": None if selected_fixture is None else int(selected_fixture["matchweek"]),
            "kickoff_time_uk": None if selected_fixture is None else str(selected_fixture["kickoff_time_uk"]),
            "kickoff_time_dk": None if selected_fixture is None else str(selected_fixture["kickoff_time_dk"]),
        }
    st.markdown("</div>", unsafe_allow_html=True)

    with st.sidebar:
        st.header("Model Notes")
        st.caption(f"App version: {app_version()}")
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
                st.caption(
                    f"Validation split: trained before {latest['test_start_date']}; "
                    f"tested on {int(latest.get('test_rows', 0))} later matches."
                )

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
    if {prediction_home_team, prediction_away_team} - set(team_options):
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
    selected_match_date = active_prediction.get("match_date")

    features = build_prediction_features(home_team, away_team, team_history, feature_columns, match_date=selected_match_date, elo_state=elo_state)
    if selected_match_date and not official_fixtures.empty:
        match_date_for_schedule = pd.to_datetime(selected_match_date, errors="coerce").date()
        schedule_context = schedule_context_for_fixture(official_fixtures, home_team, away_team, match_date_for_schedule)
        for column, context_value in schedule_context.items():
            if column in features.columns:
                features.loc[:, column] = float(context_value)
    row = features.iloc[0].to_dict()
    raw_probabilities = model.predict_proba(features)[0]
    probabilities, is_calibrated, calibration_method = apply_calibration(raw_probabilities, calibrated_layer, features)
    quality_result = assess_prediction_data_quality(
        row,
        home_team,
        away_team,
        team_history=team_history,
        match_date=pd.to_datetime(selected_match_date, errors="coerce").date() if selected_match_date else None,
        latest_data_date=latest_data_date,
    )
    warnings = quality_result.warnings

    active_section = render_dashboard_navigation()

    if active_section == "Prediction":
        summary_card(home_team, away_team, probabilities)
        render_probability_bar(probabilities, home_team, away_team)
        render_scoreline_section(row, probabilities, home_team, away_team)
        st.subheader("Model Fair Odds")
        render_model_fair_odds(probabilities, home_team, away_team)
        render_bookmaker_odds_comparison(probabilities, home_team, away_team)

    elif active_section == "Why / Key Factors":
        st.subheader("Why The Model Thinks This")
        insights = build_insights(row, home_team, away_team)
        st.markdown("<ul class='insight-list'>" + "".join(f"<li>{item}</li>" for item in insights) + "</ul>", unsafe_allow_html=True)
        st.subheader("Feature Groups")
        render_low_history_prediction_notes(row, home_team, away_team, team_history)
        grouped_feature_cards(row, home_team, away_team)
        render_recent_head_to_head(home_team, away_team)

    elif active_section == "Data Quality":
        left, right = st.columns([0.9, 1.1])
        with left:
            st.subheader("Confidence & Data Quality")
            render_confidence_badge(probabilities, warnings)
            st.write("")
            render_data_quality_card(quality_result)
        with right:
            st.subheader("Model & Data Status")
            render_model_status(feature_columns, quality_result.checks)
            st.markdown("#### Tested ideas")
            render_tested_ideas_status()
            render_validation_card(metrics)

    elif active_section == "Technical Details":
        st.subheader("Prediction Context")
        context_rows = [
            {"Item": "Calibration", "Value": str(calibration_method) if is_calibrated else "Not applied"},
            {
                "Item": "Fixture",
                "Value": f"MW{active_prediction.get('matchweek')}" if active_prediction.get("matchweek") else "Custom fixture",
            },
            {"Item": "Data through", "Value": str(latest_data_date) if latest_data_date else "Unknown"},
        ]
        st.dataframe(pd.DataFrame(context_rows), width="stretch", hide_index=True)
        st.divider()
        st.subheader("Model Help")
        render_model_help(feature_columns, metrics)
        st.divider()
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

    elif active_section == "Season Projection":
        render_season_projection_tab(home_team, away_team, teams)

    elif active_section == "Info":
        render_prediction_info_tab(
            active_prediction,
            selected_match_date,
            latest_data_date,
            is_calibrated,
            calibration_method,
            app_version(),
        )


if __name__ == "__main__":
    main()
