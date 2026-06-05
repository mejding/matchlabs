# Historical Betting Validation Report

This report tests whether model edges versus bookmaker odds would have produced profitable historical selections.

Important timing policy: this is a research backtest using `market_mode=benchmark`. The football-data odds may be closing or average market prices. They do not use match results, but their exact pre-kickoff availability is not fully verified, so these results should not be treated as live production betting evidence without a verified odds feed.

Test period starts: `2025-01-26`  
Test period ends: `2026-05-24`  
Matches evaluated: `535`

Edge formula:

```text
edge = bookmaker_odds / model_fair_odds - 1
model_fair_odds = 1 / model_probability
```

All simulations use 1 unit flat stakes.

## Strategy Summary

| strategy | bets | hit_rate | profit | roi | yield | maximum_drawdown | average_edge | average_odds |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| model_only_top_pick | 535 | 0.4822 | -16.9000 | -0.0316 | -0.0316 | 31.9400 | 0.1240 | 2.2617 |
| market_only_favorite | 535 | 0.5178 | -28.7200 | -0.0537 | -0.0537 | 45.0100 | -0.1222 | 1.8994 |
| edge_gt_0pct | 684 | 0.2749 | -33.0100 | -0.0483 | -0.0483 | 70.1600 | 0.3854 | 4.4948 |
| edge_gt_3pct | 627 | 0.2727 | -29.8100 | -0.0475 | -0.0475 | 70.5000 | 0.4191 | 4.5799 |
| edge_gt_5pct | 586 | 0.2645 | -36.0900 | -0.0616 | -0.0616 | 69.1600 | 0.4457 | 4.6829 |
| edge_gt_8pct | 543 | 0.2560 | -30.3500 | -0.0559 | -0.0559 | 64.6300 | 0.4758 | 4.7738 |
| edge_gt_10pct | 514 | 0.2510 | -34.2000 | -0.0665 | -0.0665 | 61.0700 | 0.4976 | 4.8484 |

## Bet Type Summary

| bet_type | bets | hit_rate | profit | roi | yield | maximum_drawdown | average_edge | average_odds |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| away | 247 | 0.2429 | -0.1000 | -0.0004 | -0.0004 | 39.4100 | 0.5673 | 5.4726 |
| draw | 140 | 0.2214 | -1.7300 | -0.0124 | -0.0124 | 22.5800 | 0.2668 | 4.7216 |
| home | 199 | 0.3216 | -34.2600 | -0.1722 | -0.1722 | 37.6300 | 0.4205 | 3.6755 |

## Confidence Summary

| confidence_bucket | bets | hit_rate | profit | roi | yield | maximum_drawdown | average_edge | average_odds |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| low_confidence | 252 | 0.2698 | -2.7900 | -0.0111 | -0.0111 | 31.8300 | 0.4118 | 4.0058 |
| high_confidence | 97 | 0.2887 | -5.2600 | -0.0542 | -0.0542 | 26.2700 | 0.5287 | 6.5069 |
| medium_confidence | 237 | 0.2489 | -28.0400 | -0.1183 | -0.1183 | 53.1200 | 0.4477 | 4.6563 |

## 1. Do positive-edge bets outperform the market?

Model-only top picks ROI: `-3.16%`  
Market-only favorite ROI: `-5.37%`

Answer: Yes, model top picks outperform the market favorite baseline in this run.

For edge selections, profitable threshold rows: `0` out of `5` tested thresholds.

## 2. Which edge threshold performs best?

Best threshold by ROI and profit: `edge_gt_3pct with ROI -4.75%`.

## 3. Is the model finding genuine value?

Answer: Not convincingly in this run. Either ROI is negative, sample size is thin, or profitability is not robust across thresholds.

## 4. Which bet types work best?

Best edge bet type by ROI: `away`.

Review `evaluation/betting_validation/bet_type_summary.csv` before trusting this, because draw and away bets can have smaller samples and higher variance.

## 5. Does model confidence improve betting performance?

Use `evaluation/betting_validation/confidence_summary.csv`. A useful confidence signal should show higher ROI or lower drawdown in medium/high confidence buckets. If confidence buckets are inconsistent, edge size is more informative than raw model confidence.

## Artifacts

- `evaluation/betting_validation/test_match_edges.csv`
- `evaluation/betting_validation/all_edge_bets.csv`
- `evaluation/betting_validation/strategy_summary.csv`
- `evaluation/betting_validation/bet_type_summary.csv`
- `evaluation/betting_validation/confidence_summary.csv`
- `evaluation/betting_validation/equity_curves.png`
- `evaluation/betting_validation/edge_threshold_equity_curves.png`
- `evaluation/betting_validation/strategy_roi.png`
