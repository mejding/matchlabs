# Official 2026/27 Fixtures Integration Report

## Fixture Source

- Source: Premier League official fixtures
- Source URL: https://www.premierleague.com/fixtures?co=1&se=841
- API source: `https://footballapi.pulselive.com/football/fixtures?comps=1&compSeasons=841&page=0&pageSize=380&sort=asc`
- Local file: `data/upcoming_fixtures_2026_27.csv`
- Status: scheduled subject to change

## Number Of Fixtures Loaded

- Fixtures: 380
- Teams: 20
- Matchweeks: 38

## Team Validation

Validation confirms:

- every team has 38 matches
- every team has 19 home matches
- every team has 19 away matches
- no duplicate fixtures
- dates and kickoff times are valid

See `evaluation/fixtures_2026_27/fixture_import_validation_report.md`.

## Prediction Tab Impact

The Prediction tab now supports official fixture selection:

- Season: 2026/27
- Matchweek selector
- Fixture selector with date and Danish kickoff time
- Selected fixture automatically sets home team, away team and fixture date

Manual/custom team selection remains available.

## Season Projection Impact

The Season Projection tab now uses `data/upcoming_fixtures_2026_27.csv` by default when it validates successfully.

If the official file is missing or invalid, the app falls back to the neutral fixture skeleton and shows a warning.

## Neutral Skeleton Usage

The neutral skeleton is still used only as a fallback when official fixtures are unavailable or invalid.

## Schedule And Fatigue

Official fixture dates are used to calculate Premier League-only schedule context:

- rest days since previous Premier League match
- Premier League matches in the previous 7 and 14 days
- Premier League matches in the next 7 and 14 days
- short-rest flag
- midweek fixture flag
- festive congestion flag

Only the existing production schedule columns are passed into the model. Extra next-fixture context is available for reporting/UI, not as newly trained model features.

## Known Limitations

- Fixtures are subject to broadcast and competition-related changes.
- Premier League fixtures do not include European fixtures.
- Premier League fixtures do not include FA Cup or EFL Cup fixtures.
- Promoted or returning teams can have limited recent Premier League model history; predictions use fallback assumptions where necessary.

## Next Recommended Improvement

Add optional European and domestic cup fixture files so fatigue and congestion can account for non-league matches.
