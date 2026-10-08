# Chopped provider not-eliminated field at PR2 capture

The Chopped matchup rows alone do not establish who is still eligible. At an
immutable PR2 capture, the producer may additionally bind those rows to the
manifest-verified app core for the same league and season. The source core must
precede the matchup observation by no more than six hours, and the league's
`last_chopped_leg` must equal the prior completed week. Each roster must have
unique ID and a settings object. An absent `settings.eliminated` is recorded as
`NOT_MARKED_ELIMINATED`; an integer elimination round in the completed range is
`ELIMINATED`. Null, boolean, unknown round, missing managed roster, missing
not-eliminated matchup roster, or mismatched source time/target fail closed.

This encoding is observed in the 2026 Chopped app-core snapshots; it is not
treated as a documented or stable Sleeper API guarantee. A future provider
shape change must block certification pending a new source review. The frozen
PR2 report carries the core SHA-256 and source observation time. The downstream
read-only portfolio joins submitted starters in two independent views: all raw
matchup rows, and only the source-bound not-eliminated roster subset. Both
retain unresolved player IDs and source hashes. Direct H2H counts remain
separate. No future survival, final Best Ball lineup, win probability, or
action recommendation follows from this observation. Older captures remain
immutable and retain their typed unverified/blocked states.
