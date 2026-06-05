# Data Quality Report

- Premier League 2024/25 results: Has rows (380 rows)
- Understat 2024 xG: Present (n/a rows)
- Injury data: Missing or template-only (0 rows)
- Lineup appearances: Missing or template-only (0 rows)
- Team match tactics: Has rows (4560 rows)
- FBref team match stats: Missing or template-only (0 rows)

## Tactical Field Availability

- Available fields: shots, shots_on_target
- Missing fields: possession, passes_attempted, passes_completed, pass_completion_pct, progressive_passes, progressive_carries, crosses, long_balls, tackles, interceptions, blocks

## Production Interpretation

Injuries and lineup stability are treated as template/research data unless their CSV files contain real historical rows.
Tactical pressure is only a candidate feature because current coverage is mostly shots-based, not full tactical event data.
