# OddsPortal Opening Odds Feasibility Report

## Executive Summary

OddsPortal is a promising source for a future safe pre-match market layer because it explicitly distinguishes opening odds from closing odds. Opening odds are theoretically usable as production features because they exist before kickoff. Closing odds should remain benchmark-only because they can include late team news, lineup information, injuries, weather and market movement that may not be available at the time a user makes a prediction.

Current recommendation: do not activate OddsPortal odds in production yet. Run a small, permission-aware proof of concept first. If opening 1X2 odds can be exported or collected reproducibly with acceptable usage rights, then test them as `SAFE_PREMATCH_CANDIDATE` features.

## Sources Checked

- OddsPortal Premier League results page: https://www.oddsportal.com/football/england/premier-league/results/
- OddsPortal historical results and odds explainer: https://www.oddsportal.com/results/
- OddsPortal terms: https://www.oddsportal.com/terms/

Key observations:

- OddsPortal describes historical odds as prices from when lines opened on the site until the game began.
- OddsPortal says opening odds are the first prices offered by a sportsbook before a fixture, while closing odds are the final prices before the match starts.
- OddsPortal says archived odds are available by clicking an individual archived result and filtering market tabs.
- OddsPortal terms restrict automated extraction, database copying and scraping without express consent. This means a production pipeline should prefer an approved export/API/licensed feed, or at minimum avoid aggressive scraping.

## Timing Classification

| Odds Type | Definition | Leakage Risk | Recommended Usage |
| --- | --- | --- | --- |
| Opening odds | First available bookmaker price before kickoff | Low if timestamp/source are verified | Safe pre-match candidate |
| Pre-match snapshot odds | Odds captured at a fixed time before kickoff, e.g. 24h/6h/1h | Low to medium, depends on snapshot timing | Safe pre-match candidate if timestamped |
| Closing odds | Final price before kickoff | Medium/high for early predictions | Benchmark only |
| Average closing odds | Market average at close | High for live production | Benchmark only |
| Maximum closing odds | Best available closing price | High for live production | Benchmark only |
| Unknown listed odds | Price shown without collection timing | Unknown | Research only |

## What Would Make OddsPortal Usable?

For the model, the minimum safe schema is:

| Column | Purpose |
| --- | --- |
| `match_id` | Stable match key |
| `date` | Match date |
| `kickoff_time` | Needed to prove pre-match timing |
| `home_team` | Team mapping |
| `away_team` | Team mapping |
| `bookmaker` | Source bookmaker |
| `market` | Usually `1X2` for this project |
| `home_open_odds` | Opening home price |
| `draw_open_odds` | Opening draw price |
| `away_open_odds` | Opening away price |
| `home_close_odds` | Optional benchmark field |
| `draw_close_odds` | Optional benchmark field |
| `away_close_odds` | Optional benchmark field |
| `opening_collected_at` | Timestamp or source proof for opening price |
| `source_url` | Audit trail |

Without explicit opening/closing separation, the odds must remain out of production.

## Proposed Feature Mapping

If opening odds are available:

- `market_open_home_prob`
- `market_open_draw_prob`
- `market_open_away_prob`
- `market_open_margin`
- `market_open_favorite_class`
- `model_vs_open_market_home_edge`
- `model_vs_open_market_draw_edge`
- `model_vs_open_market_away_edge`

These should be separate from current benchmark fields:

- `market_home_prob`
- `market_draw_prob`
- `market_away_prob`

This separation prevents accidental mixing of opening odds with benchmark/closing odds.

## Model Experiment Plan

Use strict time-based validation.

Model A: current production model without odds.

Model B: opening-market-only model.

Model C: production model plus opening odds.

Model D: calibrated production model plus opening odds.

Evaluate:

- Accuracy
- Log Loss
- Brier Score
- ECE
- Calibration plots
- SHAP importance
- Model-vs-market edge profitability

Promotion rule:

- Opening odds must improve out-of-sample Log Loss or Brier.
- Calibration must not materially worsen.
- Timing must be documented as pre-match.
- The ingestion source must be legally and operationally acceptable.

## Legal and Operational Risk

OddsPortal appears useful for manual research and historical comparison, but its terms restrict scraping and database extraction without permission. A robust production setup should therefore use one of these approaches:

1. Obtain an approved export or permission from OddsPortal/Livesport.
2. Use a licensed odds-history API that includes opening odds.
3. Keep OddsPortal as a manual feasibility reference only.

Do not build an aggressive scraper as a production dependency.

## Recommendation

OddsPortal opening odds should be treated as `SAFE_PREMATCH_CANDIDATE`, not `SAFE_PREMATCH_ACTIVE`.

The next practical sprint should be:

1. Manually inspect 10-20 Premier League match pages and confirm whether opening 1X2 odds are visible and consistently separable from closing odds.
2. Determine whether an approved export, API, or licensed route is available.
3. If acceptable, collect one full historical season into `data/oddsportal_opening_odds.csv`.
4. Add `--market-mode opening` as a research mode.
5. Run the market comparison and betting validation using opening odds only.
6. Activate only if the experiment beats the current production model without leakage risk.

Bottom line: yes, opening odds could be very valuable for the odds layer. But they should not go into production until we can prove both timing and data-rights safety.
