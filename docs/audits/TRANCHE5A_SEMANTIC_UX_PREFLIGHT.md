# Tranche 5A Preflight — Semantic UX Reconciliation

## Purpose

This characterization-only package begins the audit plan's semantic UX tranche. It does not redesign the interface and does not change any model value, ranking calculation, recommendation, or promotion gate.

## Current gap

The app already separates several important concepts in code, but its labels do not provide one stable vocabulary. Active surfaces use Draft Rank, FIE Pos, Asset Rank, League Rank, FIE League Rank, Board Rank, Decision Rank, and Market Rank. Some are true semantic distinctions; others are synonyms whose meaning depends on the current screen.

Research/Lab also has six routed panels while the newer League Research Report appears through a separate overlay. The report correctly declares that it does not calculate canonical app ranking, but the navigation does not yet communicate that boundary consistently.

## Target to freeze before implementation

The later target must define one machine-readable semantic contract for:

- roster-neutral league draft rank;
- position rank derived from the same canonical board value;
- roster/timing-aware decision rank;
- dynasty asset rank where multi-year value is genuinely distinct;
- market rank and ADP as market context, not football-model input;
- research ranks and evidence as non-canonical unless formally promoted;
- the role of Draft Board, Draft Assistant, Value Finder, Research/Lab, and League Research Report.

The implementation may rename or clarify labels, navigation, help text, and metadata adapters. It may not silently make two different calculations equivalent or change their numeric results.

## Preflight success condition

The dedicated workflow must reproduce the known-gap marker, preserve Tranches 2A through 4, pass all 22 league/six-format contracts, and finish with `DEPLOYABLE_SOURCE` without runtime or generated drift.
