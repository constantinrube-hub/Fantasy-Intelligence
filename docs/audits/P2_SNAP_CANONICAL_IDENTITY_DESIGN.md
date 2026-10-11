# Source-bound PFR snap identity join

The captured snap source has PFR player identifiers. The nflverse master
player source provides PFR and GSIS identifiers. Join only those exact source
identifiers; names, position and team similarity cannot resolve missing rows.
Duplicate PFR bindings fail before dictionary construction, including repeated
identical bindings. A GSIS identifier must match its canonical source syntax.

The adapter validates immutable raw source receipts and observation cutoffs
before producing a prior-week research table. A newly observed master cannot
be represented as available at an older pregame cutoff. Both input hashes and
observation receipts travel with the derived report. Unmatched IDs retain a
typed reason and a null canonical identity. Snap counts retain their raw
values; percentage scale, routes and production authority remain unavailable.

This supplies identity plumbing only. It does not authorize new forecast
features, model training, rankings or promotion. Percentage semantics require
their own source contract; field ranges alone do not prove the unit.
