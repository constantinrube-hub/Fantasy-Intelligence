# P1 Sleeper baseline source binding

The current-season refresh records the Sleeper projection stats used for its
weekly means and compares that per-player stats map with the verified, immutable
pregame market archive for the same season and week. The receipt is frozen in
each later PR2 lineup capture. Postgame review checks the archive bytes, row
identity and timing, receipt hashes, league scoring signature and observation
time before reporting `REFRESH_PROJECTION_STATS_BOUND_TO_ARCHIVE`.

When the endpoint has changed since the first-write archive, the refresh
reports `ARCHIVED_PROJECTION_STATS_DIFFER`. A missing or invalid archive is
also typed. In all these cases the current snapshot retains its normal Sleeper
means; the receipt cannot rewrite history or imply that the old archived
numbers were used in a later refresh. Older immutable PR2 captures have no
receipt and stay `SOURCE_RECEIPT_MISSING`.

An exact stats match establishes source equivalence for this refresh at the
captured per-player stats level. It does not establish byte equality of the
whole HTTP response, complete support for every league scoring rule, calibrated
forecast performance, or independent paired observations. The P1 paired
forecast validation gate therefore retains `SLEEPER_BASELINE_SCORING_UNVERIFIED`
even when every league has a source-bound receipt. No model is promoted.
