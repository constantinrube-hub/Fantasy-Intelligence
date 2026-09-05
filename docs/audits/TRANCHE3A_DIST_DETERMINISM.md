# Tranche 3A Dist Determinism Closure

## Root cause

The Tranche 3A football-economics tests and the canonical release gate were
green, but repeated release builds on different GitHub runners produced
different content-addressed compact current bases.

`tools/build_dist.py` iterated league directories with `Path.iterdir()` and fed
that filesystem-dependent order into a greedy compatibility partition. The
partition is logically valid for any order, but its grouping can differ by
order. That changes content hashes, per-league compact current references, and
served governance hashes even when source data is identical.

## Fix

- `partition_compatible()` canonicalizes entries by league ID internally.
- the main league traversal is also sorted by league directory name.
- the existing permanent V9.3.2 build determinism test now permutes a
  conflict/compatibility fixture and requires identical grouping for every
  permutation.

No football model, replacement, VOR, scarcity, ADP, research promotion, or
league-profile semantics change.

## One-time dist reconciliation

Because previously committed `dist` may embody a noncanonical runner ordering,
the first canonical build may legitimately modify compact current manifests,
served governance hashes, and content-addressed runtime bases.

The controlled 3A workflow allows only those deterministic derivative paths,
copies changed/new files into its artifact, and records deleted obsolete
content-addressed files in `DELETE_PATHS.txt`. Any other source or dist drift
still fails.
