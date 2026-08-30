# Patch Manifest

Build: `V10.4-STRATEGY-STACK-SHADOW-2`

This is an additive research/action patch. It does not replace canonical M1-M9, V9.6, current snapshot, app, dist, scoring, identity, league-profile, or release files.

## New files

- research/preseason_projection_v2.py
- research/fie_strategy_stack.py
- research/build_fie_strategy_stack.py
- research/validate_fie_strategy_stack.py
- research/integrity_fie_strategy_stack_test.py
- research/capture_fie_availability.py
- research/verified_market_index.example.json
- .github/workflows/build-fie-strategy-stack.yml
- .github/workflows/capture-fie-season-market.yml
- .github/workflows/capture-fie-availability.yml
- docs/STRATEGY_STACK_V97_V104.md
- APPLY_STRATEGY_STACK.md

## Preflight additions in shadow-2

- committed-state protection around broad cache restoration
- profile-derived `AUTO` ADP market selection
- split current-snapshot hydration
- provenance hashes and phase-readiness metadata
- immutable daily prospective availability/injury archive
