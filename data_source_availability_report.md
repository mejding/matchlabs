# Data Source Availability Report

Date: 2026-06-08

## Scope

This report checks whether injuries, lineups and head-to-head data are available from sources already used or already considered by the project.

## Current Local Status

| Data family | Local file(s) | Current rows | Status |
| --- | --- | ---: | --- |
| Injuries | `data/injuries.csv` | 0 | Template only |
| Lineups | `data/match_lineups.csv`, `data/player_appearances.csv`, `data/match_substitutions.csv`, `data/formation_history.csv` | 0 | Template only |
| Head-to-head | `data/premier_league_*.csv`, Understat JSON | Available | Already reproducible |

## Source Findings

### football-data.co.uk

Source checked:

- https://www.football-data.co.uk/data

Useful for:

- Match results.
- Home/away teams.
- Dates.
- Goals.
- Basic match stats such as shots, shots on target, cards and corners.
- Bookmaker odds.

Not useful for:

- Injuries.
- Starting lineups.
- Substitutions.
- Formations.

Interpretation:

- H2H can be built completely from football-data results.
- Injury and lineup features cannot be built from football-data alone.

### Understat

Sources checked:

- https://understat.readthedocs.io/en/latest/classes/understat.html
- https://soccerdata.readthedocs.io/en/latest/datasources/Understat.html

Useful for:

- Match xG.
- Player match-level minutes, goals, xG, xA, shots and xGChain/xGBuildup through available scrapers/libraries.
- Shot events.

Limitations:

- It does not provide injury availability.
- It does not reliably provide full starting XI, bench, captain, substitutions or formations as primary lineup tables.

Interpretation:

- Understat can support missing xG contribution *if* an external injury list identifies unavailable players.
- It can help estimate player contribution and expected-starter strength, but it is not an injury source by itself.

### FBref

Sources checked:

- https://soccerdata.readthedocs.io/en/latest/reference/fbref.html
- https://soccerdata.readthedocs.io/en/latest/datasources/FBref.html

Useful for:

- Historical team match logs.
- Formation and captain in schedule/team match logs.
- Player match stats.
- Match lineups through scraper libraries such as `soccerdata.FBref.read_lineup`.
- Match events, including goals, cards and substitutions.

Limitations:

- Direct scraping can be blocked/rate-limited.
- Some advanced data availability has changed over time.
- Actual lineups are post-match facts. They are safe for historical previous-match continuity features, but current-match actual XI should only be used for predictions after lineups are officially released.

Interpretation:

- Best candidate for lineup stability ingestion.
- Should be built as a reproducible ingestion pipeline with caching, not live scraping inside the Streamlit app.

### Transfermarkt

Sources checked:

- https://www.transfermarkt.co.uk/premier-league/verletztespieler/wettbewerb/GB1/plus/1
- https://www.rdocumentation.org/packages/worldfootballR/versions/0.6.2

Useful for:

- Current injured-player lists by competition.
- Player injury history pages.
- Injury type, since/until dates and market value.
- Transfermarkt tooling in `worldfootballR` includes league injuries and player injury history functions.

Limitations:

- Historical reproducibility is the hard part: a current page is not the same as a timestamped pre-kickoff snapshot.
- Expected return dates and status can be revised after the fact.
- To avoid leakage, source rows need `source_collected_at` or a historically archived snapshot.

Interpretation:

- Promising for injury research.
- Not production-safe unless we build or obtain timestamped historical snapshots.

## H2H Decision

H2H data is available now and already implemented historically without leakage. The model experiment showed:

- H2H has non-zero SHAP signal.
- H2H improved some draw diagnostics.
- H2H did not improve overall out-of-sample log loss or Brier enough versus the production baseline.

Decision:

- Keep H2H as frontend context and research-only model features.
- Do not promote H2H into production until a later model comparison improves log loss or Brier.

## Lineup Decision

Lineup data is not locally populated, but a feasible path exists:

1. Use FBref through `soccerdata` or a user-provided FBref export.
2. Ingest `read_schedule`, `read_lineup`, player match stats and events.
3. Populate:
   - `match_lineups`
   - `player_appearances`
   - `formation_history`
   - `match_substitutions`
4. Generate only historical continuity features from matches before the prediction date.

Decision:

- Good candidate for a later sprint.
- Do not activate until at least one full season is ingested and validated.

## Injury Decision

Injury data is not locally populated. Transfermarkt is the best available public source already considered by the project, but it needs careful historical reconstruction.

Practical path:

1. Use Transfermarkt injury histories to create player unavailability intervals.
2. Use Understat/player minutes to estimate missing minutes and missing xG/xA contribution.
3. Use Transfermarkt market values for missing market value.
4. Mark every row with source URL and collection timestamp.
5. Treat the result as research-only unless historical snapshots prove the data was known before kickoff.

Decision:

- Potentially valuable, but higher leakage risk than lineups.
- Defer until lineup or market odds timing work is complete.

## Recommended Priority

1. **H2H**: no new data needed; keep as context/research.
2. **Lineups via FBref/soccerdata**: best next data-engineering sprint if we want a new football-specific signal.
3. **Injuries via Transfermarkt + Understat contribution mapping**: useful, but more complex and harder to make leakage-safe.

## Production Rule

Do not activate any new feature family unless:

- It has real historical rows.
- It is generated only from information available before the prediction date.
- It improves out-of-sample log loss or Brier.
- It does not materially worsen calibration.
