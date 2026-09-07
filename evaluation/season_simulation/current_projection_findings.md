# Current Season Projection Findings

Refresh date: 2026-09-07

## Data State

- Completed Premier League 2026/27 matches included: `30`
- Latest local match date: `2026-09-06`
- Next default dashboard round: `4`
- Projection simulations: `10000`

Football-data.co.uk still served the 2026/27 CSV only through `2026-08-31` at refresh time. Understat had all 30 completed 2026/27 results through Matchweek 3, so Matchweek 3 was supplemented locally from Understat result/xG rows before retraining.

The supplemental Matchweek 3 rows include final score and xG. Football-data-only fields such as referee, cards, odds and shot counts are left blank; missing shot counts are ignored by the shot-volume history rather than treated as zero.

## Matchweek 4 Probabilities

| Date | Fixture | Home | Draw | Away |
| --- | --- | ---: | ---: | ---: |
| 2026-09-12 | Aston Villa v Nott'm Forest | 45.9% | 27.1% | 27.0% |
| 2026-09-12 | Bournemouth v Brentford | 39.9% | 25.3% | 34.8% |
| 2026-09-12 | Chelsea v Hull | 57.9% | 22.8% | 19.3% |
| 2026-09-12 | Coventry v Brighton | 25.7% | 28.9% | 45.4% |
| 2026-09-12 | Crystal Palace v Ipswich | 57.6% | 21.1% | 21.3% |
| 2026-09-12 | Leeds v Newcastle | 37.8% | 28.9% | 33.3% |
| 2026-09-12 | Liverpool v Fulham | 57.1% | 23.6% | 19.3% |
| 2026-09-12 | Man United v Man City | 43.7% | 23.7% | 32.7% |
| 2026-09-12 | Sunderland v Arsenal | 14.3% | 27.3% | 58.4% |
| 2026-09-12 | Tottenham v Everton | 25.7% | 29.8% | 44.5% |

## Updated Finish Outlook

| Team | Expected points | Avg finish | Title | Top 4 | Relegation |
| --- | ---: | ---: | ---: | ---: | ---: |
| Arsenal | 81.5 | 1.5 | 61.0% | 99.4% | 0.0% |
| Man City | 78.4 | 2.0 | 34.3% | 97.5% | 0.0% |
| Liverpool | 66.3 | 4.3 | 2.8% | 66.4% | 0.0% |
| Man United | 63.5 | 5.1 | 1.2% | 50.7% | 0.1% |
| Brighton | 57.8 | 7.1 | 0.4% | 24.0% | 0.4% |
| Chelsea | 55.3 | 8.3 | 0.1% | 14.8% | 0.8% |
| Brentford | 54.8 | 8.4 | 0.1% | 13.2% | 0.8% |
| Aston Villa | 52.3 | 9.5 | 0.0% | 8.1% | 2.5% |
| Everton | 52.0 | 9.9 | 0.0% | 6.6% | 2.4% |
| Bournemouth | 51.3 | 10.1 | 0.0% | 6.5% | 2.9% |
| Newcastle | 51.6 | 10.3 | 0.0% | 5.1% | 3.2% |
| Sunderland | 49.9 | 11.2 | 0.0% | 3.7% | 5.0% |
| Nott'm Forest | 46.7 | 12.8 | 0.0% | 1.3% | 11.5% |
| Leeds | 46.2 | 13.0 | 0.0% | 1.3% | 11.2% |
| Hull | 43.8 | 14.1 | 0.0% | 0.8% | 18.5% |
| Fulham | 41.8 | 15.0 | 0.0% | 0.3% | 27.0% |
| Crystal Palace | 40.4 | 15.6 | 0.0% | 0.1% | 33.1% |
| Coventry | 39.5 | 15.8 | 0.0% | 0.1% | 36.8% |
| Tottenham | 37.3 | 17.0 | 0.0% | 0.1% | 53.9% |
| Ipswich | 28.9 | 19.2 | 0.0% | 0.0% | 90.2% |

## Findings

- Arsenal move ahead of Man City in the season projection after beating Chelsea and opening 3-0-0 with strong xG control.
- Man City remain very close on expected points and top-four security, but their narrow 1-0 home win over Coventry was less dominant than Arsenal's Chelsea win in xG terms.
- Liverpool's win at Ipswich improves their top-four outlook, but the model still sees a clear gap to Arsenal and Man City.
- Hull remain third in the actual table with 7 points and no goals conceded, but the projection stays cautious: their average finish is 14.1 and relegation probability is 18.5% because promoted-team uncertainty and long-term strength priors still matter.
- Tottenham's 0-0 at Nott'm Forest stops the losing run but not the scoring concern; they remain a large relegation-tail outlier at 53.9%.
- Ipswich are now the clearest relegation-risk team after starting 1-0-2 with eight goals conceded.
