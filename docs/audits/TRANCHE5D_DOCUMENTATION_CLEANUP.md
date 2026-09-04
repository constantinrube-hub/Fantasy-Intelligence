# Tranche 5D Target — Evidence-Backed Documentation Cleanup

## Target scope

The validated 5D preflight authorizes this location-only cleanup. The target relocates twenty-nine historical records intact to `docs/archive/implementation/` or `docs/archive/releases/`; it does not edit or delete historical content.

The archive index separates historical evidence from current operational documentation. `docs/current/` contains canonical topic guides, with one documented path-bound exception. Root-level historical-location exceptions are retained only where preserved patch or checksum manifests require their exact paths.

## Preserved exceptions

- `APPLY_INSTRUCTIONS.md`
- `APPLY_V975.md`
- `RELEASE_NOTES_V9.3.4A3.md`
- `docs/current/V9.3.4A3-SCORE-FIX.md`

## Validation

`research/integrity_tranche5d_documentation_cleanup.py --mode target` requires an exact Git `R100` rename from the validated preflight head for every relocated record, unchanged path-bound exceptions, the archive index, and the redirected changelog link. The target also retains the 5C lifecycle contract and runs the complete deterministic release gate.
