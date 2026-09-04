# Tranche 5A Target — Semantic UX Reconciliation

## Outcome

The app now has one machine-readable vocabulary for rankings and one explicit role for each decision or research surface. This is a semantic-only change: ranking values, projections, recommendation calculations, promotion controls, and league-format behavior are unchanged.

## Canonical vocabulary

- **League Rank** is the roster-neutral overall ordering on the canonical Draft Board.
- **Position Rank** is the position view of the same canonical board value.
- **Decision Rank** adds current roster marginal value and pick timing in Draft Assistant.
- **Asset Rank** is the distinct multi-year dynasty ordering.
- **Asset Position Rank** is its position-specific dynasty view.
- **Market Rank**, **Market Position Rank**, and ADP are external context, not football-model inputs.
- **Weekly Position Rank** belongs to the active weekly projection context.
- **Research Position Rank** is evidence-only and cannot become canonical without formal promotion.

## Surface roles

Draft Board owns the canonical league ordering. Draft Assistant supports the current pick. Value Finder discovers market disagreement and timing opportunities. Research / Lab and League Research Report expose diagnostics and evidence under fail-closed promotion rules.

## Verification

The target workflow validates the JSON/browser contract mirror, canonical labels, source-to-dist parity, completed tranche protections, the 22-league/six-format matrix, and the complete deterministic release gate.

The deploy writers also pin LF output so source-to-dist verification and governed artifact hashes remain byte-identical on Windows and Linux.
