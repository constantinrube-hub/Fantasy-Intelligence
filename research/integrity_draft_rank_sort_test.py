#!/usr/bin/env python3
"""Static guards for Draft Assistant rank-sample consistency and table sorting."""
from pathlib import Path

root=Path(__file__).resolve().parents[1]
idx=(root/'index.html').read_text(encoding='utf-8')
tsort=(root/'app'/'table-sort.js').read_text(encoding='utf-8')

assert 'function draftFullEligiblePool()' in idx
assert 'const marketRanks=draftMarketRanks(fullPool)' in idx
assert 'leagueRank:leagueRanks.get(id)' in idx
assert 'marketSampleRank=marketRanks.get(id)' in idx
assert 'Number(x.marketSampleRank)-Number(x.leagueComparableRank)' in idx
assert 'leagueRows.filter(x=>marketRanks.has(x.id))' in idx
assert 'including players already selected' in idx
assert 'available decision #' in idx
assert 'data-da-sort="market"' in idx
assert 'data-da-sort="leagueRank"' in idx
assert 'draftAssistantSortRows(buildDraftValueRows(rosterId))' in idx
assert '<script src="app/table-sort.js"></script>' in idx
assert 'th.dataset.sort||th.dataset.daSort' in tsort  # avoid double-binding model-aware tables
assert 'MutationObserver' in tsort
print('OK Draft Assistant stable rank sample + sortable-table integration')
