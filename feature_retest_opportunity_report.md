# Feature Retest Opportunity Report

## Question

Which tested-but-not-adopted feature families may still improve the model if tested differently or with better data?

## Short Answer

Several families should not be treated as permanently rejected. The most plausible issue is that the first tests often added a whole feature group to XGBoost, while the true football signal may need better historical coverage, replacement tests, segment-specific tests, or a transparent overlay rather than direct model columns.

## Priority Retest List

| feature_family | current_status | retest_priority | why_retest | recommended_next_test |
| --- | --- | --- | --- | --- |
| Injuries and suspensions | Tested - Not adopted | High | Historical injuries have broad rows, but suspension signal had zero training matches and only 71 test matches. A trained model could not learn suspension impact from that setup. | Separate injuries from suspensions, add more timestamped historical suspension rows, and test a capped post-calibration overlay for missing expected starters. |
| Non-PL match context | Tested - Not adopted | High | Current evaluation had zero Premier League train/test rows with usable non-PL context, so the test mostly proves missing coverage rather than no football signal. | Backfill dated cup, European and selected pre-season rows across multiple seasons; retest early-season and congested-fixture segments separately. |
| Opponent-adjusted xG | Tested - Not adopted | Medium-High | Full ratings did not beat production on rolling splits, but earlier replacement tests suggested raw xG differential may be redundant. | Latest focused rolling retest found defense-only ratings improved average Log Loss/Brier, but only in 2 of 5 seasons. Keep research-only. |
| Draw propensity | Tested - Not adopted | Medium-High | Static draw features increased double-chance hit rate but hurt log loss/Brier. Draws may be better handled through calibration or match-state-informed priors than direct features. | Latest overlay retest improved holdout Log Loss by only 0.0002 but worsened Brier by 0.0002. Keep research-only. |
| Venue-specific form | Tested - Not adopted | Medium | Venue features have SHAP signal, but last-5 home/away samples are noisy and can overreact. | Retest with shrinkage toward all-venue team strength and larger windows, especially for teams with few venue-specific matches. |
| Lineup stability | Research | Medium | Only one full season of lineup data exists locally. That is thin for squad continuity and rotation effects. | Ingest more seasons before retesting, and segment by heavy rotation, European congestion and unchanged XI. |
| Manager consistency | Tested - Not adopted | Medium | General manager features worsened probability quality, but the plausible effect is short-lived after a change. | Keep as research-only. The new first-5/first-10 segment test did not improve log loss/Brier, and sample size is only 18 first-10 test matches. |
| Market odds | Benchmark only | Special | Market-only probabilities beat the football model, but live timing and data availability decide whether this can be used safely. | Keep as separate benchmark/overlay; only promote a blend if live pre-match odds timing is verified and calibration does not deteriorate. |
| Head-to-head | Tested - Not adopted | Low-Medium | H2H improved some draw-specific metrics but worsened overall probability quality. | Use as display/context or narrow draw-subsignal only; avoid broad model adoption unless a segment test improves total log loss/Brier. |
| Shot efficiency | Tested - Not adopted | Low-Medium | Finishing features are noisy and remove-one tests improved when goals-minus-xG was removed. | Keep shot volume active; retest only defensive shot-prevention or shot-quality variants with shrinkage, not raw goals-minus-xG. |
| Decayed Elo | Tested - Not adopted | Low | Simple season-boundary decay lost to full Elo carryover. | Revisit Elo through promoted-team and league-strength priors, not generic season decay. |

## Manager Short-Window Result

The manager experiment was extended with segment metrics for matches where at least one team is within the first 5 or first 10 matches under a new manager.

| segment | matches | production_log_loss | best_manager_log_loss | production_brier | best_manager_brier | interpretation |
| --- | --- | --- | --- | --- | --- | --- |
| any_new_manager_first_5 | 5 | 1.0574 | 1.2299 | 0.6503 | 0.7244 | Too small and worse than production. |
| any_new_manager_first_10 | 18 | 1.1241 | 1.1401 | 0.6659 | 0.6673 | Manager features do not improve probability quality on the short-window segment. |
| no_new_manager_first_10 | 520 | 1.0558 | 1.0621 | 0.6320 | 0.6352 | Manager features also do not help normal fixtures. |

Best manager model above means the lowest log loss among the manager-feature variants on that segment.

## Opponent-Adjusted xG Retest Result

The rolling validation now includes focused replacement variants after removing raw xG differential:

- attack-only opponent-adjusted ratings
- defense-only opponent-adjusted ratings
- matchup-only opponent-adjusted ratings
- full opponent-adjusted ratings

| model | mean_log_loss_delta | mean_brier_delta | seasons_log_loss_improved | seasons_brier_improved | decision |
| --- | --- | --- | --- | --- | --- |
| candidate_minus_xg_diff_plus_defense_ratings | -0.0027 | -0.0020 | 2/5 | 2/5 | Best average result, but not stable enough. |
| candidate_minus_xg_diff_plus_ratings | -0.0016 | 0.0001 | 2/5 | 2/5 | Mixed; Brier does not improve on average. |
| candidate_minus_xg_diff_plus_matchup_ratings | -0.0003 | 0.0003 | 4/5 | 3/5 | Stable-ish log loss, but tiny and Brier worsens. |

Do not activate opponent-adjusted xG yet. The best new clue is that defensive ratings may carry useful information, but they need a simpler or more stable formulation before production.

## Draw Overlay Retest Result

The draw retest added a post-calibration overlay. Candidate parameters were selected on an internal calibration slice and then tested on the holdout period.

Selected overlay:

- strategy: `draw_score_and_low_spread`
- draw score threshold: `0.4177`
- home/away probability spread threshold: `0.20`
- draw boost: `0.06`
- holdout matches adjusted: `108`

Holdout result versus no overlay:

| metric | delta |
| --- | --- |
| Log Loss | -0.0002 |
| Brier score | +0.0002 |
| ECE | +0.0014 |

Do not activate the draw overlay. The result is very close to neutral: it nudges draw probability closer to actual draw rate, but does not improve the full probability distribution enough.

## Recommendation

Do not activate manager features now. The short-window theory is reasonable, but current local evidence does not support it. The biggest limitation is sample size: only 18 first-10 manager-change fixtures appear in the current test split.

The next best use of engineering time is:

1. Backfill better injury/suspension and non-PL context data.
2. Simplify opponent-adjusted defensive ratings and rerun rolling validation before considering production.
3. Keep draw calibration research-only unless a future overlay improves both Log Loss and Brier.
4. Expand manager and lineup data to more seasons before retesting manager-bounce or squad-stability effects.
