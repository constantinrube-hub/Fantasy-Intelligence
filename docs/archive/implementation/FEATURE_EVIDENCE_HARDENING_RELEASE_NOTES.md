# FIE Feature Evidence Hardening Release Notes

## Added

- Evidence-only extended M4 OOS backfill to unlock genuine multi-season second-stage residual/challenger validation.
- Training-only feature selection for backfilled M4 folds.
- Calibrated next-season baseline: Ridge prior-PPG versus Ridge prior-PPG plus feature.
- De-duplicated position/feature hypotheses before validation and BH-FDR.
- Preserved semantic family memberships through the new `families` field.
- `hypothesis_id` for stable audit identity.
- Research-only consumer-routing table that routes signals only to the mechanism/horizon they validated.
- Tier 1 temporal-gate versus Tier 2 multiplicity-supported evidence labels.
- Hardening validator requiring four second-stage residual folds for QB/RB/WR/TE.
- Evidence OOS cache in GitHub Actions.
- `consumer_routing.csv` and `hardening_audit.json` outputs.

## Unchanged

- No runtime auto-activation.
- No change to the production M7/M8/M9 gate.
- No overwrite of canonical M4 OOS predictions.
- All promoted research evidence still requires separate consumer integration and revalidation.
