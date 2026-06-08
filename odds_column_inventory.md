# Odds Column Inventory

This audit inspects football-data.co.uk CSV files currently downloaded in `data/`.

Conservative timing rule: odds are not production-safe unless their pre-match availability is explicitly verified. Closing, average and maximum market prices are treated as benchmark-only because they may represent late or closing prices.

## Summary

- Total match-result odds columns: 96
- SAFE_PREMATCH columns: 0
- BENCHMARK_ONLY columns: 54
- UNKNOWN_TIMING columns: 42

## Inventory

| column | bookmaker_or_source | outcome | odds_type | timing_classification | recommended_usage_category | seasons_covered | non_missing_values | missing_values |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 1XBA | 1xBet | away | single-bookmaker listed | UNKNOWN_TIMING | Research only until collection time is verified | 2425 | 371 | 9 |
| 1XBCA | 1xBet | away | single-bookmaker closing | BENCHMARK_ONLY | Benchmark only | 2425 | 380 | 0 |
| 1XBCD | 1xBet | draw | single-bookmaker closing | BENCHMARK_ONLY | Benchmark only | 2425 | 380 | 0 |
| 1XBCH | 1xBet | home | single-bookmaker closing | BENCHMARK_ONLY | Benchmark only | 2425 | 380 | 0 |
| 1XBD | 1xBet | draw | single-bookmaker listed | UNKNOWN_TIMING | Research only until collection time is verified | 2425 | 371 | 9 |
| 1XBH | 1xBet | home | single-bookmaker listed | UNKNOWN_TIMING | Research only until collection time is verified | 2425 | 371 | 9 |
| AvgA | Market average | away | average listed | BENCHMARK_ONLY | Benchmark only | 1920, 2021, 2122, 2223, 2324, 2425, 2526 | 2660 | 0 |
| AvgCA | Market average | away | average closing | BENCHMARK_ONLY | Benchmark only | 1920, 2021, 2122, 2223, 2324, 2425, 2526 | 2660 | 0 |
| AvgCD | Market average | draw | average closing | BENCHMARK_ONLY | Benchmark only | 1920, 2021, 2122, 2223, 2324, 2425, 2526 | 2660 | 0 |
| AvgCH | Market average | home | average closing | BENCHMARK_ONLY | Benchmark only | 1920, 2021, 2122, 2223, 2324, 2425, 2526 | 2660 | 0 |
| AvgD | Market average | draw | average listed | BENCHMARK_ONLY | Benchmark only | 1920, 2021, 2122, 2223, 2324, 2425, 2526 | 2660 | 0 |
| AvgH | Market average | home | average listed | BENCHMARK_ONLY | Benchmark only | 1920, 2021, 2122, 2223, 2324, 2425, 2526 | 2660 | 0 |
| B365A | Bet365 | away | single-bookmaker listed | UNKNOWN_TIMING | Research only until collection time is verified | 1920, 2021, 2122, 2223, 2324, 2425, 2526 | 2660 | 0 |
| B365CA | Bet365 | away | single-bookmaker closing | BENCHMARK_ONLY | Benchmark only | 1920, 2021, 2122, 2223, 2324, 2425, 2526 | 2660 | 0 |
| B365CD | Bet365 | draw | single-bookmaker closing | BENCHMARK_ONLY | Benchmark only | 1920, 2021, 2122, 2223, 2324, 2425, 2526 | 2660 | 0 |
| B365CH | Bet365 | home | single-bookmaker closing | BENCHMARK_ONLY | Benchmark only | 1920, 2021, 2122, 2223, 2324, 2425, 2526 | 2660 | 0 |
| B365D | Bet365 | draw | single-bookmaker listed | UNKNOWN_TIMING | Research only until collection time is verified | 1920, 2021, 2122, 2223, 2324, 2425, 2526 | 2660 | 0 |
| B365H | Bet365 | home | single-bookmaker listed | UNKNOWN_TIMING | Research only until collection time is verified | 1920, 2021, 2122, 2223, 2324, 2425, 2526 | 2660 | 0 |
| BFA | Betfair sportsbook | away | single-bookmaker listed | UNKNOWN_TIMING | Research only until collection time is verified | 2425 | 379 | 1 |
| BFCA | Betfair sportsbook | away | single-bookmaker closing | BENCHMARK_ONLY | Benchmark only | 2425 | 380 | 0 |
| BFCD | Betfair sportsbook | draw | single-bookmaker closing | BENCHMARK_ONLY | Benchmark only | 2425 | 380 | 0 |
| BFCH | Betfair sportsbook | home | single-bookmaker closing | BENCHMARK_ONLY | Benchmark only | 2425 | 380 | 0 |
| BFD | Betfair sportsbook | draw | single-bookmaker listed | UNKNOWN_TIMING | Research only until collection time is verified | 2425 | 379 | 1 |
| BFDA | BFD | away | single-bookmaker listed | UNKNOWN_TIMING | Research only until collection time is verified | 2526 | 379 | 1 |
| BFDCA | BFD | away | single-bookmaker closing | BENCHMARK_ONLY | Benchmark only | 2526 | 372 | 8 |
| BFDCD | BFD | draw | single-bookmaker closing | BENCHMARK_ONLY | Benchmark only | 2526 | 372 | 8 |
| BFDCH | BFD | home | single-bookmaker closing | BENCHMARK_ONLY | Benchmark only | 2526 | 372 | 8 |
| BFDD | BFD | draw | single-bookmaker listed | UNKNOWN_TIMING | Research only until collection time is verified | 2526 | 379 | 1 |
| BFDH | BFD | home | single-bookmaker listed | UNKNOWN_TIMING | Research only until collection time is verified | 2526 | 379 | 1 |
| BFEA | Betfair Exchange | away | single-bookmaker listed | UNKNOWN_TIMING | Research only until collection time is verified | 2425, 2526 | 740 | 20 |
| BFECA | Betfair Exchange | away | single-bookmaker closing | BENCHMARK_ONLY | Benchmark only | 2425, 2526 | 738 | 22 |
| BFECD | Betfair Exchange | draw | single-bookmaker closing | BENCHMARK_ONLY | Benchmark only | 2425, 2526 | 738 | 22 |
| BFECH | Betfair Exchange | home | single-bookmaker closing | BENCHMARK_ONLY | Benchmark only | 2425, 2526 | 738 | 22 |
| BFED | Betfair Exchange | draw | single-bookmaker listed | UNKNOWN_TIMING | Research only until collection time is verified | 2425, 2526 | 740 | 20 |
| BFEH | Betfair Exchange | home | single-bookmaker listed | UNKNOWN_TIMING | Research only until collection time is verified | 2425, 2526 | 740 | 20 |
| BFH | Betfair sportsbook | home | single-bookmaker listed | UNKNOWN_TIMING | Research only until collection time is verified | 2425 | 379 | 1 |
| BMGMA | BMGM | away | single-bookmaker listed | UNKNOWN_TIMING | Research only until collection time is verified | 2526 | 378 | 2 |
| BMGMCA | BMGM | away | single-bookmaker closing | BENCHMARK_ONLY | Benchmark only | 2526 | 380 | 0 |
| BMGMCD | BMGM | draw | single-bookmaker closing | BENCHMARK_ONLY | Benchmark only | 2526 | 380 | 0 |
| BMGMCH | BMGM | home | single-bookmaker closing | BENCHMARK_ONLY | Benchmark only | 2526 | 380 | 0 |
| BMGMD | BMGM | draw | single-bookmaker listed | UNKNOWN_TIMING | Research only until collection time is verified | 2526 | 378 | 2 |
| BMGMH | BMGM | home | single-bookmaker listed | UNKNOWN_TIMING | Research only until collection time is verified | 2526 | 378 | 2 |
| BVA | BV | away | single-bookmaker listed | UNKNOWN_TIMING | Research only until collection time is verified | 2526 | 378 | 2 |
| BVCA | BV | away | single-bookmaker closing | BENCHMARK_ONLY | Benchmark only | 2526 | 372 | 8 |
| BVCD | BV | draw | single-bookmaker closing | BENCHMARK_ONLY | Benchmark only | 2526 | 372 | 8 |
| BVCH | BV | home | single-bookmaker closing | BENCHMARK_ONLY | Benchmark only | 2526 | 372 | 8 |
| BVD | BV | draw | single-bookmaker listed | UNKNOWN_TIMING | Research only until collection time is verified | 2526 | 378 | 2 |
| BVH | BV | home | single-bookmaker listed | UNKNOWN_TIMING | Research only until collection time is verified | 2526 | 378 | 2 |
| BWA | Bet&Win/Bwin | away | single-bookmaker listed | UNKNOWN_TIMING | Research only until collection time is verified | 1920, 2021, 2122, 2223, 2324, 2425, 2526 | 2517 | 143 |
| BWCA | Bet&Win/Bwin | away | single-bookmaker closing | BENCHMARK_ONLY | Benchmark only | 1920, 2021, 2122, 2223, 2324, 2425, 2526 | 2507 | 153 |
| BWCD | Bet&Win/Bwin | draw | single-bookmaker closing | BENCHMARK_ONLY | Benchmark only | 1920, 2021, 2122, 2223, 2324, 2425, 2526 | 2507 | 153 |
| BWCH | Bet&Win/Bwin | home | single-bookmaker closing | BENCHMARK_ONLY | Benchmark only | 1920, 2021, 2122, 2223, 2324, 2425, 2526 | 2507 | 153 |
| BWD | Bet&Win/Bwin | draw | single-bookmaker listed | UNKNOWN_TIMING | Research only until collection time is verified | 1920, 2021, 2122, 2223, 2324, 2425, 2526 | 2517 | 143 |
| BWH | Bet&Win/Bwin | home | single-bookmaker listed | UNKNOWN_TIMING | Research only until collection time is verified | 1920, 2021, 2122, 2223, 2324, 2425, 2526 | 2517 | 143 |
| CLA | CL | away | single-bookmaker listed | UNKNOWN_TIMING | Research only until collection time is verified | 2526 | 282 | 98 |
| CLCA | CL | away | single-bookmaker closing | BENCHMARK_ONLY | Benchmark only | 2526 | 260 | 120 |
| CLCD | CL | draw | single-bookmaker closing | BENCHMARK_ONLY | Benchmark only | 2526 | 260 | 120 |
| CLCH | CL | home | single-bookmaker closing | BENCHMARK_ONLY | Benchmark only | 2526 | 260 | 120 |
| CLD | CL | draw | single-bookmaker listed | UNKNOWN_TIMING | Research only until collection time is verified | 2526 | 282 | 98 |
| CLH | CL | home | single-bookmaker listed | UNKNOWN_TIMING | Research only until collection time is verified | 2526 | 282 | 98 |
| IWA | Interwetten | away | single-bookmaker listed | UNKNOWN_TIMING | Research only until collection time is verified | 1920, 2021, 2122, 2223, 2324 | 1718 | 182 |
| IWCA | Interwetten | away | single-bookmaker closing | BENCHMARK_ONLY | Benchmark only | 1920, 2021, 2122, 2223, 2324 | 1715 | 185 |
| IWCD | Interwetten | draw | single-bookmaker closing | BENCHMARK_ONLY | Benchmark only | 1920, 2021, 2122, 2223, 2324 | 1715 | 185 |
| IWCH | Interwetten | home | single-bookmaker closing | BENCHMARK_ONLY | Benchmark only | 1920, 2021, 2122, 2223, 2324 | 1715 | 185 |
| IWD | Interwetten | draw | single-bookmaker listed | UNKNOWN_TIMING | Research only until collection time is verified | 1920, 2021, 2122, 2223, 2324 | 1718 | 182 |
| IWH | Interwetten | home | single-bookmaker listed | UNKNOWN_TIMING | Research only until collection time is verified | 1920, 2021, 2122, 2223, 2324 | 1718 | 182 |
| LBA | LB | away | single-bookmaker listed | UNKNOWN_TIMING | Research only until collection time is verified | 2526 | 286 | 94 |
| LBCA | LB | away | single-bookmaker closing | BENCHMARK_ONLY | Benchmark only | 2526 | 281 | 99 |
| LBCD | LB | draw | single-bookmaker closing | BENCHMARK_ONLY | Benchmark only | 2526 | 281 | 99 |
| LBCH | LB | home | single-bookmaker closing | BENCHMARK_ONLY | Benchmark only | 2526 | 281 | 99 |
| LBD | LB | draw | single-bookmaker listed | UNKNOWN_TIMING | Research only until collection time is verified | 2526 | 286 | 94 |
| LBH | LB | home | single-bookmaker listed | UNKNOWN_TIMING | Research only until collection time is verified | 2526 | 286 | 94 |
| MaxA | Market maximum | away | maximum listed | BENCHMARK_ONLY | Benchmark only | 1920, 2021, 2122, 2223, 2324, 2425, 2526 | 2660 | 0 |
| MaxCA | Market maximum | away | maximum closing | BENCHMARK_ONLY | Benchmark only | 1920, 2021, 2122, 2223, 2324, 2425, 2526 | 2660 | 0 |
| MaxCD | Market maximum | draw | maximum closing | BENCHMARK_ONLY | Benchmark only | 1920, 2021, 2122, 2223, 2324, 2425, 2526 | 2660 | 0 |
| MaxCH | Market maximum | home | maximum closing | BENCHMARK_ONLY | Benchmark only | 1920, 2021, 2122, 2223, 2324, 2425, 2526 | 2660 | 0 |
| MaxD | Market maximum | draw | maximum listed | BENCHMARK_ONLY | Benchmark only | 1920, 2021, 2122, 2223, 2324, 2425, 2526 | 2660 | 0 |
| MaxH | Market maximum | home | maximum listed | BENCHMARK_ONLY | Benchmark only | 1920, 2021, 2122, 2223, 2324, 2425, 2526 | 2660 | 0 |
| PSA | Pinnacle | away | single-bookmaker listed | UNKNOWN_TIMING | Research only until collection time is verified | 1920, 2021, 2122, 2223, 2324, 2425, 2526 | 2490 | 170 |
| PSCA | Pinnacle | away | single-bookmaker closing | BENCHMARK_ONLY | Benchmark only | 1920, 2021, 2122, 2223, 2324, 2425, 2526 | 2490 | 170 |
| PSCD | Pinnacle | draw | single-bookmaker closing | BENCHMARK_ONLY | Benchmark only | 1920, 2021, 2122, 2223, 2324, 2425, 2526 | 2490 | 170 |
| PSCH | Pinnacle | home | single-bookmaker closing | BENCHMARK_ONLY | Benchmark only | 1920, 2021, 2122, 2223, 2324, 2425, 2526 | 2490 | 170 |
| PSD | Pinnacle | draw | single-bookmaker listed | UNKNOWN_TIMING | Research only until collection time is verified | 1920, 2021, 2122, 2223, 2324, 2425, 2526 | 2490 | 170 |
| PSH | Pinnacle | home | single-bookmaker listed | UNKNOWN_TIMING | Research only until collection time is verified | 1920, 2021, 2122, 2223, 2324, 2425, 2526 | 2490 | 170 |
| VCA | VC Bet | away | single-bookmaker listed | UNKNOWN_TIMING | Research only until collection time is verified | 1920, 2021, 2122, 2223, 2324 | 1900 | 0 |
| VCCA | VC Bet | away | single-bookmaker closing | BENCHMARK_ONLY | Benchmark only | 1920, 2021, 2122, 2223, 2324 | 1900 | 0 |
| VCCD | VC Bet | draw | single-bookmaker closing | BENCHMARK_ONLY | Benchmark only | 1920, 2021, 2122, 2223, 2324 | 1900 | 0 |
| VCCH | VC Bet | home | single-bookmaker closing | BENCHMARK_ONLY | Benchmark only | 1920, 2021, 2122, 2223, 2324 | 1900 | 0 |
| VCD | VC Bet | draw | single-bookmaker listed | UNKNOWN_TIMING | Research only until collection time is verified | 1920, 2021, 2122, 2223, 2324 | 1900 | 0 |
| VCH | VC Bet | home | single-bookmaker listed | UNKNOWN_TIMING | Research only until collection time is verified | 1920, 2021, 2122, 2223, 2324 | 1900 | 0 |
| WHA | William Hill | away | single-bookmaker listed | UNKNOWN_TIMING | Research only until collection time is verified | 1920, 2021, 2122, 2223, 2324, 2425 | 2189 | 91 |
| WHCA | William Hill | away | single-bookmaker closing | BENCHMARK_ONLY | Benchmark only | 1920, 2021, 2122, 2223, 2324, 2425 | 2189 | 91 |
| WHCD | William Hill | draw | single-bookmaker closing | BENCHMARK_ONLY | Benchmark only | 1920, 2021, 2122, 2223, 2324, 2425 | 2189 | 91 |
| WHCH | William Hill | home | single-bookmaker closing | BENCHMARK_ONLY | Benchmark only | 1920, 2021, 2122, 2223, 2324, 2425 | 2189 | 91 |
| WHD | William Hill | draw | single-bookmaker listed | UNKNOWN_TIMING | Research only until collection time is verified | 1920, 2021, 2122, 2223, 2324, 2425 | 2189 | 91 |
| WHH | William Hill | home | single-bookmaker listed | UNKNOWN_TIMING | Research only until collection time is verified | 1920, 2021, 2122, 2223, 2324, 2425 | 2189 | 91 |

## Recommended Usage

- SAFE_PREMATCH: may be used in production only if the live data feed guarantees values are known before kickoff.
- BENCHMARK_ONLY: useful for model-vs-market evaluation, not production training.
- RESEARCH_ONLY / UNKNOWN_TIMING: can be tested offline, but must not be used in production.
