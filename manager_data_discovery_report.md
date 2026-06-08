# Manager Data Discovery Report

## Sources Checked

| Source | Local availability | Fields available | Historical reliability | Implementation notes |
| --- | --- | --- | --- | --- |
| Existing `data/manager_history.csv` | Empty before this sprint | Team, manager, start/end dates | Low before ingestion | Used as the normalized output target. |
| FBref match pages via soccerdata cache | Available for 2024/25 | Match date, teams, manager per team | Medium | Historically reproducible from cached match reports. Does not provide official appointment dates, so periods are inferred from first seen match. |
| football-data.co.uk | Available | Match results, odds, cards, shots | Not applicable | Does not include manager identity. |
| Understat | Available | xG and match data | Not applicable | Does not include manager identity in the local project data. |
| Transfermarkt | Not locally ingested | Manager appointments, departures, caretaker periods | Potentially high | Good candidate for future official tenure dates, but requires a separate ingestion policy and terms review. |
| Kaggle/manual CSV | Not locally available | Depends on dataset | Unknown | Useful fallback if source and timestamps are documented. |

## Recommendation

Use FBref cached match managers for research-only experiments. For production manager features, add a Transfermarkt or manually verified manager-change feed with official appointment dates and caretaker flags.
