#!/usr/bin/env python3
"""V9.3.1+ completion contract against the current modular V9.3.x runtime."""
from pathlib import Path
import json

R=Path(__file__).resolve().parents[1]
read=lambda p:(R/p).read_text(encoding='utf-8')

rel=json.loads(read('config/release.json'))
core=read('app/core/core-services.js')
client=read('app/core/data-client.js')
rt=read('app/runtime-foundation.js')
ui=read('app/decision-ui.js')
store=read('app/current-snapshot-store.js')
d=read('app/v9.3.4d-starter-economics.js')

assert str(rel.get('release','')).startswith('9.3.'), rel
assert str(rel.get('runtime','')).startswith('9.3.'), rel
assert rel.get('built_at'), 'release build timestamp must be explicit'

# Progressive load/enrichment architecture remains present.
assert 'loadEnhancements' in rt
assert 'Promise.allSettled' in rt
assert 'league-season-projections' in rt
assert 'league-enrichment' in rt

# Persistent shared-data cache is still observable and usable.
assert 'persistentHits' in client and 'persistentStores' in client
assert 'PERSISTENT_CACHE' in client

# Canonical structural replacement is implemented in core services and the
# current universal starter-economics layer, rather than asserted through old
# duplicated literals in index.html.
assert 'const LeagueDemandService=' in core
assert 'const ReplacementService=' in core
assert 'canonical structural starter-slot demand' in core
replacement=core[core.index('const ReplacementService='):core.index('const RosterValueService=')]
assert 'projectedReplacementLevels' not in replacement
assert 'universal-starter-slot-economics' in d
assert "SUPER_FLEX:['QB','RB','WR','TE']" in d
assert 'replacementContext' in d and 'starterProbability' in d

# Best Ball remains format-specific without replacing the governed score.
for token in ['Ceiling / Profile','bestBallDraftProfile','Best Ball portfolio fit *',
              'bestBallPortfolioFit','Contribution Profile']:
    assert token in ui, f'missing Best Ball completion contract: {token}'
assert 'does not silently replace the governed decision score' in ui

# Current runtime layering remains explicit.
for token in ['bootA3','bootC','bootD','bootE']:
    assert token in store

print('PASS V9.3.1+ completion contract on current modular runtime')
