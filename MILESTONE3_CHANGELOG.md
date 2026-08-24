# V8.5-M3 Changelog, Steps 16–18

## Baseline preservation

- V8.2.2 remains the frozen live decision model.
- M1 Steps 0–9 and M2 Steps 10–15 are preserved.
- New M3 outputs are diagnostic-only and browser-separated under `Lab → M3 Research`.

## Step 16, advanced position-specific models

- Added NGS weekly enrichment for QB, RB and WR/TE when available.
- Added PFR advanced weekly enrichment, including QB pressure/bad-throw, receiver drop and defensive hurry/hit/blitz fields when available.
- Added public participation aggregation from all offensive/defensive players on field.
- Participation metrics are explicitly labelled context/presence rather than true routes or individual pass rushes.
- All advanced features are lagged by player/season before forecast use.
- Added position-specific expanding-window validation against recent fantasy points and M2 opportunity xFP.
- Added a conservative `validated_candidate` gate: >=1% mean MAE improvement vs M2 xFP with positive improvement in at least 3 folds.

## Step 17, natural experiments

- Added QB-change studies for receiving target share and fantasy scoring.
- Added major-receiver absence studies.
- Added lead-back absence studies.
- Added lead LB/S absence studies.
- Added sustained role-jump studies.
- Every result carries `causal_claim: false`.
- Coordinator changes are explicitly blocked instead of guessed because no reliable time-stamped coaching feed is yet included.

## Step 18, Y1/Y2 opportunity model

- Added young-player player-season construction from draft year.
- Added public combine enrichment keyed primarily by PFR ID.
- Added position-specific meaningful-role and high-value-role outcome definitions.
- Added preseason role classifier using only pre-NFL priors.
- Added after-Week-3 role classifier using early NFL evidence plus priors.
- Validation reports Brier score, ROC AUC and accuracy on chronological holdouts.

## Workflow and QA

- Combined manual GitHub workflow now builds M1 → M2 → M3 in order.
- Added `integrity_m3_test.py` and `validate_m3_bundle.py`.
- Added placeholder `data/research/milestone3.json` that cannot be mistaken for empirical results.
- Added M3 derived tables for follow-on Steps 19+.
