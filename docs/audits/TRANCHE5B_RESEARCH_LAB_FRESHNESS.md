# Tranche 5B — Research/Lab Navigation and Freshness

## Outcome

Research/Lab now opens on one evidence-oriented overview instead of presenting nine unrelated peer tabs. The overview groups validation and historical research, decision evidence, and production/data governance while preserving every existing milestone, Features, and Model & Data route.

The League Research Report is now entered from the Lab overview. Its overlay remains league-scoped and evidence-only; it does not own or alter League Rank or Decision Rank.

## Shared freshness language

`FIEFreshness` presents five explicit display states: Current, Aging, Needs refresh, Unavailable, and Freshness unknown. M5 current-snapshot context, M6 governance, the League Research Report, the Lab overview, and Runtime & Data Quality use the same presenter.

The presenter derives age only from an existing trustworthy timestamp. Explicit unavailability wins over a timestamp, invalid or future timestamps are unknown, and stale evidence is never relabeled current. The presenter returns no score, rank, recommendation, activation, or promotion fields.

## Preserved behavior

- Projection, ranking, recommendation, roster, and promotion calculations are unchanged.
- M1–M6 route IDs and their panels remain available.
- Features, Model & Data, and Validation remain available.
- M6 retains its existing 18-hour governance freshness threshold and all fail-closed checks.
- Research evidence remains unable to change canonical ranks without formal promotion.
