#!/usr/bin/env python3
"""Static guards for current Draft/Decision rank and sortable-table consistency."""
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
ui=(ROOT/'app'/'decision-ui.js').read_text(encoding='utf-8')
tsort=(ROOT/'app'/'table-sort.js').read_text(encoding='utf-8')
engine=(ROOT/'app'/'decision-engines.js').read_text(encoding='utf-8')

# Current Decision UX owns ranking and table sorting. Do not require the old
# inline draftFullEligiblePool implementation from index.html.
for token in [
    'function rankMap(',
    'function marketRanks(',
    'function sortRows(',
    'function renderTable(',
    'data-fie93-sort',
    'UI.sort',
    'marketADP',
    'FIEDraftBaseValueService',
]:
    assert token in ui, token

# Draft simulation must still consume a full draft candidate pool and preserve
# market/ranking context rather than reducing everything to current table rows.
for token in [
    'draftCandidatePool()',
    'marketRankMap(',
    'staticDecisionMap(',
    'simulationContext(',
]:
    assert token in engine, token

# Generic sorter must not double-bind model-aware tables.
assert 'th.dataset.sort||th.dataset.daSort' in tsort
assert 'MutationObserver' in tsort
assert 'sortDomTable' in tsort
assert 'window.FIE_TABLE_SORT' in tsort

print('OK current Draft/Decision rank + sortable-table integration')
