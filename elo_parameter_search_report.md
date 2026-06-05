# Elo Parameter Search Report

Best configuration by Elo-only out-of-sample log loss: `k30_ha75_nomov`.

## Top Configurations

| elo_config | k_factor | home_advantage | margin_of_victory | accuracy | log_loss | brier_score | calibration_score | ece |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| k30_ha75_nomov | 30.0000 | 75.0000 | False | 0.4542 | 1.0776 | 0.6498 | 0.0471 | 0.0471 |
| k30_ha100_nomov | 30.0000 | 100.0000 | False | 0.4598 | 1.0778 | 0.6509 | 0.0501 | 0.0501 |
| k30_ha100_mov | 30.0000 | 100.0000 | True | 0.4654 | 1.0800 | 0.6513 | 0.0480 | 0.0480 |
| k40_ha75_mov | 40.0000 | 75.0000 | True | 0.4449 | 1.0817 | 0.6509 | 0.0416 | 0.0416 |
| k30_ha50_mov | 30.0000 | 50.0000 | True | 0.4598 | 1.0819 | 0.6513 | 0.0480 | 0.0480 |
| k40_ha100_nomov | 40.0000 | 100.0000 | False | 0.4505 | 1.0823 | 0.6524 | 0.0506 | 0.0506 |
| k30_ha75_mov | 30.0000 | 75.0000 | True | 0.4654 | 1.0825 | 0.6520 | 0.0433 | 0.0433 |
| k30_ha50_nomov | 30.0000 | 50.0000 | False | 0.4561 | 1.0827 | 0.6525 | 0.0453 | 0.0453 |
| k40_ha50_nomov | 40.0000 | 50.0000 | False | 0.4336 | 1.0849 | 0.6547 | 0.0478 | 0.0478 |
| k40_ha75_nomov | 40.0000 | 75.0000 | False | 0.4523 | 1.0851 | 0.6539 | 0.0422 | 0.0422 |
| k40_ha50_mov | 40.0000 | 50.0000 | True | 0.4467 | 1.0852 | 0.6541 | 0.0539 | 0.0539 |
| k40_ha100_mov | 40.0000 | 100.0000 | True | 0.4523 | 1.0858 | 0.6542 | 0.0439 | 0.0439 |

The search tests K-factor, fixed home Elo bonus, and margin-of-victory update multiplier. Ratings are calculated chronologically before each match, then updated after the match result.
