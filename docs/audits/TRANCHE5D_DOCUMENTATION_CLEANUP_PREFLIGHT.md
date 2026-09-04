# Tranche 5D Preflight — Evidence-Backed Documentation Cleanup

## Decision boundary

Tranche 5C made current documentation authority explicit but deliberately retained historical records in their original locations. This preflight determines whether a later archival relocation is warranted. It does not move, rename, delete, or edit any historical record.

## Evidence

The lifecycle contract identifies 21 root-level historical patch, apply, upload, and release documents plus 12 versioned implementation records under `docs/current/`. Twenty-nine are archive-safe candidates. Their tracked references are limited to this preflight inventory, generated 5C release evidence, co-relocated historical records in the same archive directory, or one redirectable `CHANGELOG.md` link. The canonical index and nine canonical guides remain present, and the repository already has implementation and release archive directories.

Four records are deliberately excluded from relocation: `APPLY_INSTRUCTIONS.md`, `APPLY_V975.md`, `RELEASE_NOTES_V9.3.4A3.md`, and `docs/current/V9.3.4A3-SCORE-FIX.md`. Historical patch/checksum manifests record their exact paths, so moving any of them would modify or invalidate a preserved historical package. They are documented location exceptions, not current operational guidance.

Leaving these records at the root or inside `docs/current/` conflicts with the current-location meaning established by `docs/current/README.md`: canonical topic guides are current authority, while version-specific material is historical evidence. The cleanup problem is therefore document lifecycle clarity, not content quality or application behavior.

## Proposed later target

If this preflight validates independently, relocate only the 29 enumerated candidates to their specified `docs/archive/implementation/` or `docs/archive/releases/` destinations. Preserve content byte-for-byte, add a durable archive index, redirect the one `CHANGELOG.md` link, and regenerate lifecycle/release evidence. Do not retire workflows and do not alter application, generated, research, governance, or data artifacts.

## Preconditions for any relocation

- The candidate inventory and proposed destinations remain collision-free.
- Every current canonical guide and the canonical index remain intact.
- No tracked inbound reference is left unresolved.
- The Tranche 5C lifecycle contract and scheduled operational workflows remain preserved.
- The target has focused relocation/identity checks before one full release gate at closure.

## Preflight outcome

Cleanup is justified narrowly because location currently obscures the authoritative documentation boundary. This is not authorization to execute cleanup until the dedicated preflight workflow has passed.
