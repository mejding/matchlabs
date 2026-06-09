# Market Odds Timing Discovery Report

## Scope

This report audits the 1X2 bookmaker odds columns in the local football-data.co.uk Premier League CSV files from 2019/20 through 2025/26.

Official football-data notes used for timing classification: https://www.football-data.co.uk/notes.txt

## Timing Finding

football-data.co.uk notes classify non-C 1X2 odds as pre-closing odds and C-suffixed odds as closing odds. Weekend odds are collected Friday afternoons; midweek odds are collected Tuesday afternoons.

Interpretation:

- Non-`C` 1X2 columns such as `B365H/B365D/B365A`, `PSH/PSD/PSA`, `AvgH/AvgD/AvgA` are **pre-closing odds**.
- `C` columns such as `B365CH/B365CD/B365CA`, `PSCH/PSCD/PSCA`, `AvgCH/AvgCD/AvgCA` are **closing odds**.
- None of the local football-data columns are documented as opening odds.

## Leakage Assessment

Pre-closing odds do not leak the final result because they are collected before kickoff. They can still create **timestamp leakage** if the production app predicts earlier than the Friday/Tuesday collection point or cannot access an equivalent pre-closing feed.

Closing odds should not be used as production model inputs because they can contain late injury, lineup, weather and market information that would not be available at earlier prediction time.

## Summary

- Total 1X2 odds columns: 96
- Pre-closing conditional columns: 48
- Closing / benchmark-only columns: 48
- Opening odds columns: 0
- Safe production columns today: 0

## Timing Groups

| timing_classification | odds_type | column_count | non_missing_values | missing_values | columns |
| --- | --- | --- | --- | --- | --- |
| BENCHMARK_ONLY | average closing | 3 | 7980 | 0 | AvgCA, AvgCD, AvgCH |
| BENCHMARK_ONLY | maximum closing | 3 | 7980 | 0 | MaxCA, MaxCD, MaxCH |
| BENCHMARK_ONLY | single-bookmaker closing | 42 | 49872 | 2568 | 1XBCA, 1XBCD, 1XBCH, B365CA, B365CD, B365CH, BFCA, BFCD, BFCH, BFDCA, BFDCD, BFDCH, BFECA, BFECD, BFECH, BMGMCA, BMGMCD, BMGMCH, BVCA, BVCD, BVCH, BWCA, BWCD, BWCH, CLCA, CLCD, CLCH, IWCA, IWCD, IWCH, LBCA, LBCD, LBCH, PSCA, PSCD, PSCH, VCCA, VCCD, VCCH, WHCA, WHCD, WHCH |
| PREMATCH_CONDITIONAL | average pre-closing | 3 | 7980 | 0 | AvgA, AvgD, AvgH |
| PREMATCH_CONDITIONAL | maximum pre-closing | 3 | 7980 | 0 | MaxA, MaxD, MaxH |
| PREMATCH_CONDITIONAL | single-bookmaker pre-closing | 42 | 50001 | 2439 | 1XBA, 1XBD, 1XBH, B365A, B365D, B365H, BFA, BFD, BFDA, BFDD, BFDH, BFEA, BFED, BFEH, BFH, BMGMA, BMGMD, BMGMH, BVA, BVD, BVH, BWA, BWD, BWH, CLA, CLD, CLH, IWA, IWD, IWH, LBA, LBD, LBH, PSA, PSD, PSH, VCA, VCD, VCH, WHA, WHD, WHH |

## Source Coverage

| bookmaker_or_source | timing_classification | columns | seasons | non_missing_values | missing_values |
| --- | --- | --- | --- | --- | --- |
| 1xBet | BENCHMARK_ONLY | 1XBCA, 1XBCD, 1XBCH | 2425 | 1140 | 0 |
| 1xBet | PREMATCH_CONDITIONAL | 1XBA, 1XBD, 1XBH | 2425 | 1113 | 27 |
| Bet&Win/Bwin | BENCHMARK_ONLY | BWCA, BWCD, BWCH | 1920, 2021, 2122, 2223, 2324, 2425, 2526 | 7521 | 459 |
| Bet&Win/Bwin | PREMATCH_CONDITIONAL | BWA, BWD, BWH | 1920, 2021, 2122, 2223, 2324, 2425, 2526 | 7551 | 429 |
| Bet365 | BENCHMARK_ONLY | B365CA, B365CD, B365CH | 1920, 2021, 2122, 2223, 2324, 2425, 2526 | 7980 | 0 |
| Bet365 | PREMATCH_CONDITIONAL | B365A, B365D, B365H | 1920, 2021, 2122, 2223, 2324, 2425, 2526 | 7980 | 0 |
| BetMGM | BENCHMARK_ONLY | BMGMCA, BMGMCD, BMGMCH | 2526 | 1140 | 0 |
| BetMGM | PREMATCH_CONDITIONAL | BMGMA, BMGMD, BMGMH | 2526 | 1134 | 6 |
| BetVictor | BENCHMARK_ONLY | BVCA, BVCD, BVCH | 2526 | 1116 | 24 |
| BetVictor | PREMATCH_CONDITIONAL | BVA, BVD, BVH | 2526 | 1134 | 6 |
| Betfair Exchange | BENCHMARK_ONLY | BFECA, BFECD, BFECH | 2425, 2526 | 2214 | 66 |
| Betfair Exchange | PREMATCH_CONDITIONAL | BFEA, BFED, BFEH | 2425, 2526 | 2220 | 60 |
| Betfair sportsbook | BENCHMARK_ONLY | BFCA, BFCD, BFCH | 2425 | 1140 | 0 |
| Betfair sportsbook | PREMATCH_CONDITIONAL | BFA, BFD, BFH | 2425 | 1137 | 3 |
| Betfred | BENCHMARK_ONLY | BFDCA, BFDCD, BFDCH | 2526 | 1116 | 24 |
| Betfred | PREMATCH_CONDITIONAL | BFDA, BFDD, BFDH | 2526 | 1137 | 3 |
| Coral | BENCHMARK_ONLY | CLCA, CLCD, CLCH | 2526 | 780 | 360 |
| Coral | PREMATCH_CONDITIONAL | CLA, CLD, CLH | 2526 | 846 | 294 |
| Interwetten | BENCHMARK_ONLY | IWCA, IWCD, IWCH | 1920, 2021, 2122, 2223, 2324 | 5145 | 555 |
| Interwetten | PREMATCH_CONDITIONAL | IWA, IWD, IWH | 1920, 2021, 2122, 2223, 2324 | 5154 | 546 |
| Ladbrokes | BENCHMARK_ONLY | LBCA, LBCD, LBCH | 2526 | 843 | 297 |
| Ladbrokes | PREMATCH_CONDITIONAL | LBA, LBD, LBH | 2526 | 858 | 282 |
| Market average | BENCHMARK_ONLY | AvgCA, AvgCD, AvgCH | 1920, 2021, 2122, 2223, 2324, 2425, 2526 | 7980 | 0 |
| Market average | PREMATCH_CONDITIONAL | AvgA, AvgD, AvgH | 1920, 2021, 2122, 2223, 2324, 2425, 2526 | 7980 | 0 |
| Market maximum | BENCHMARK_ONLY | MaxCA, MaxCD, MaxCH | 1920, 2021, 2122, 2223, 2324, 2425, 2526 | 7980 | 0 |
| Market maximum | PREMATCH_CONDITIONAL | MaxA, MaxD, MaxH | 1920, 2021, 2122, 2223, 2324, 2425, 2526 | 7980 | 0 |
| Pinnacle | BENCHMARK_ONLY | PSCA, PSCD, PSCH | 1920, 2021, 2122, 2223, 2324, 2425, 2526 | 7470 | 510 |
| Pinnacle | PREMATCH_CONDITIONAL | PSA, PSD, PSH | 1920, 2021, 2122, 2223, 2324, 2425, 2526 | 7470 | 510 |
| VC Bet | BENCHMARK_ONLY | VCCA, VCCD, VCCH | 1920, 2021, 2122, 2223, 2324 | 5700 | 0 |
| VC Bet | PREMATCH_CONDITIONAL | VCA, VCD, VCH | 1920, 2021, 2122, 2223, 2324 | 5700 | 0 |
| William Hill | BENCHMARK_ONLY | WHCA, WHCD, WHCH | 1920, 2021, 2122, 2223, 2324, 2425 | 6567 | 273 |
| William Hill | PREMATCH_CONDITIONAL | WHA, WHD, WHH | 1920, 2021, 2122, 2223, 2324, 2425 | 6567 | 273 |

## Recommendation

Treat football-data non-`C` 1X2 odds as a high-priority production candidate, not as active production yet.

They can move into production only if:

1. We define the product as a pre-match prediction made after the equivalent odds collection point.
2. The app has a live/reproducible odds feed with the same timing as the historical pre-closing columns.
3. A time-based model comparison shows improved Log Loss or Brier Score.
4. Calibration does not materially worsen.

Until those requirements are met:

- Use closing odds as benchmark only.
- Use non-`C` pre-closing odds for the next market feature experiment.
- Do not describe the football-data odds as opening odds.
