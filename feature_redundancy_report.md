# Feature Redundancy Analysis

## Scope

This analysis tests whether the current model is approaching feature saturation across these groups:

- Form
- xG
- xGA
- xG differential
- Fatigue
- Tactical pressure
- Venue-specific features

Tactical pressure status: `available`.

All evaluations use a strict time-based split. Lower is better for log loss, Brier score, calibration score and ECE.

## 1. Marginal Improvement When Added Individually

Reference model: Form features only.

| feature_group | features | accuracy | log_loss | brier_score | calibration_score | ece | log_loss_delta_vs_form | brier_delta_vs_form |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| Form | 5 | 0.4523 | 1.0707 | 0.6460 | 0.0376 | 0.0376 | 0.0000 | 0.0000 |
| xG | 2 | 0.4766 | 1.0609 | 0.6391 | 0.0344 | 0.0344 | -0.0098 | -0.0069 |
| xGA | 2 | 0.4860 | 1.0545 | 0.6337 | 0.0416 | 0.0416 | -0.0162 | -0.0123 |
| xG differential | 2 | 0.4897 | 1.0576 | 0.6358 | 0.0402 | 0.0402 | -0.0131 | -0.0102 |
| Fatigue | 8 | 0.4467 | 1.0800 | 0.6531 | 0.0484 | 0.0484 | 0.0093 | 0.0071 |
| Tactical pressure | 6 | 0.4411 | 1.0894 | 0.6564 | 0.0543 | 0.0543 | 0.0187 | 0.0104 |
| Venue-specific features | 8 | 0.4505 | 1.0566 | 0.6358 | 0.0482 | 0.0482 | -0.0141 | -0.0102 |

Negative delta means the group improved over form-only.

## 2. Marginal Impact When Removed

Reference model: full research model with all available groups.

| feature_group | features_removed | accuracy | log_loss | brier_score | calibration_score | ece | log_loss_delta_vs_full | brier_delta_vs_full |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| Full model | 0 | 0.4748 | 1.0718 | 0.6438 | 0.0523 | 0.0523 | 0.0000 | 0.0000 |
| Form | 5 | 0.4636 | 1.0713 | 0.6436 | 0.0615 | 0.0615 | -0.0006 | -0.0002 |
| xG | 2 | 0.4804 | 1.0678 | 0.6418 | 0.0523 | 0.0523 | -0.0041 | -0.0020 |
| xGA | 2 | 0.4598 | 1.0682 | 0.6422 | 0.0532 | 0.0532 | -0.0037 | -0.0016 |
| xG differential | 2 | 0.4804 | 1.0609 | 0.6368 | 0.0528 | 0.0528 | -0.0109 | -0.0070 |
| Fatigue | 8 | 0.4692 | 1.0681 | 0.6420 | 0.0542 | 0.0542 | -0.0037 | -0.0019 |
| Tactical pressure | 6 | 0.4542 | 1.0623 | 0.6392 | 0.0447 | 0.0447 | -0.0095 | -0.0047 |
| Venue-specific features | 8 | 0.4879 | 1.0725 | 0.6429 | 0.0633 | 0.0633 | 0.0006 | -0.0010 |

Positive delta means removing the group made performance worse, so the group contains useful information. Negative delta means removing the group improved performance, suggesting noise or redundancy.

## 3. Correlation With Existing Features

| feature_group | features | mean_abs_corr_with_other_features | max_abs_corr_with_other_features | high_corr_pairs_ge_0_80 |
| --- | --- | --- | --- | --- |
| Form | 5 | 0.1795 | 0.7481 | 0 |
| xG | 2 | 0.2068 | 0.8298 | 2 |
| xGA | 2 | 0.1626 | 0.8093 | 2 |
| xG differential | 2 | 0.2208 | 0.8298 | 4 |
| Fatigue | 8 | 0.0219 | 0.0918 | 0 |
| Tactical pressure | 6 | 0.1077 | 0.4136 | 0 |
| Venue-specific features | 8 | 0.1531 | 0.7609 | 0 |

High-correlation pairs at `abs(correlation) >= 0.80`: `8`.

## 4. SHAP Importance

| feature_group | mean_abs_shap |
| --- | --- |
| Venue-specific features | 0.3126 |
| Tactical pressure | 0.1716 |
| xG differential | 0.1334 |
| Form | 0.1008 |
| Fatigue | 0.0675 |
| xG | 0.0615 |
| xGA | 0.0599 |

Dominant SHAP group: `Venue-specific features`.

## 5. Permutation Importance

| feature_group | permutation_importance |
| --- | --- |
| Venue-specific features | 0.0135 |
| Form | 0.0085 |
| xGA | 0.0030 |
| xG | -0.0004 |
| xG differential | -0.0005 |
| Fatigue | -0.0043 |
| Tactical pressure | -0.0090 |

Dominant permutation group: `Venue-specific features`.

## Answers

### 1. Which features provide unique information?

The strongest candidates for unique information are the groups where removing them increases both log loss and Brier score. In this run:

No feature group cleanly worsened both log loss and Brier score when removed from the full research model.

Mixed-signal groups, where one metric improves and another worsens:

| feature_group | log_loss_delta_vs_full | brier_delta_vs_full |
| --- | --- | --- |
| Venue-specific features | 0.0006 | -0.0010 |

### 2. Which features are largely redundant?

Groups where removal improves or barely changes log loss are likely redundant or noisy in the current model:

| feature_group | log_loss_delta_vs_full | brier_delta_vs_full |
| --- | --- | --- |
| xG differential | -0.0109 | -0.0070 |
| Tactical pressure | -0.0095 | -0.0047 |
| xG | -0.0041 | -0.0020 |
| Fatigue | -0.0037 | -0.0019 |
| xGA | -0.0037 | -0.0016 |

### 3. Which feature groups dominate model performance?

SHAP dominance: `Venue-specific features`.  
Permutation dominance: `Venue-specific features`.

Use SHAP as contribution attribution and permutation importance as performance sensitivity. If they disagree, trust permutation more for redundancy decisions.

### 4. Is the model becoming saturated with highly correlated features?

Answer: Yes, there are signs of saturation: multiple groups are correlated and some removals improve or barely hurt log loss.

The most important warning sign is not just correlation, but that adding more rolling variants does not reliably improve out-of-sample log loss.

### 5. Which future feature families are most likely to add genuinely new information?

- verified pre-match market odds or opening odds, because market prices summarize broad public and private information
- reliable player availability/lineup data, because it is orthogonal to team-level rolling xG
- team strength ratings such as Elo/SPI-style priors, because they add long-horizon quality separate from last-5 form
- true event-data tactical metrics if coverage is complete, because current tactical pressure is limited by data availability

## Production Guidance

Do not add future features merely because they have SHAP signal. Promote only if they improve out-of-sample log loss or Brier score and do not materially worsen calibration.

## Artifacts

- `evaluation/feature_redundancy/add_one_group_results.csv`
- `evaluation/feature_redundancy/remove_one_group_results.csv`
- `evaluation/feature_redundancy/correlation_summary.csv`
- `evaluation/feature_redundancy/feature_correlation_matrix.csv`
- `evaluation/feature_redundancy/shap_feature_rankings.csv`
- `evaluation/feature_redundancy/shap_group_importance.csv`
- `evaluation/feature_redundancy/permutation_feature_importance.csv`
- `evaluation/feature_redundancy/permutation_group_importance.csv`
- `evaluation/feature_redundancy/shap_group_importance.png`
- `evaluation/feature_redundancy/permutation_group_importance.png`
