# Market Intelligence Report

Market mode evaluated in this run: `opening`.

No usable market odds were available for this mode.

For `opening` mode, create `data/oddsportal_opening_odds.csv` with verified pre-match opening prices before rerunning the experiment.

## Model Comparison

| model | accuracy | log_loss | brier_score | calibration_score | ece |
| --- | --- | --- | --- | --- | --- |
| Model A: current production model | 0.4860 | 1.0488 | 0.6295 | 0.0528 | 0.0528 |
| Model B: market-only opening model | nan | nan | nan | nan | nan |
| Model C: current model + opening odds | nan | nan | nan | nan | nan |
| Model D: production + safe-prematch odds | nan | nan | nan | nan | nan |

## Production Decision

Do not move market odds into production. There is not enough verified opening/pre-match data in the project yet.
