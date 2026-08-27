#!/usr/bin/env python3
"""V9.3.1 completion-patch source contract."""
from pathlib import Path
import json,re
R=Path(__file__).resolve().parents[1]
rel=json.loads((R/'config/release.json').read_text())
core=(R/'app/core/core-services.js').read_text()
client=(R/'app/core/data-client.js').read_text()
rt=(R/'app/runtime-foundation.js').read_text()
ui=(R/'app/decision-ui.js').read_text()
idx=(R/'index.html').read_text()
assert rel['release'].startswith(('9.3.1-','9.3.2-'))
assert rel['runtime'].startswith(('9.3.1-','9.3.2-'))
assert rel.get('built_at'), 'release build timestamp must be explicit'
# Progressive core load: background work is started but not awaited by switchLeague.
assert 'this.background=this.loadEnhancements' in rt
switch=rt[rt.index('async switchLeague'):rt.index('async loadEnhancements')]
assert 'await this.loadEnhancements' not in switch
assert 'await Promise.allSettled([trend,enrich,proj,research])' in rt
# Persistent stable shared-data cache is reachable from the legacy JSON/CSV call sites.
assert "PERSISTENT_CACHE='fie-data-v931'" in client or "PERSISTENT_CACHE='fie-data-v932'" in client
assert 'persistentHits' in client and 'persistentStores' in client
assert 'Data().json(url' in rt and 'Data().text(url' in rt
assert 'BROWSER_PERSISTENT' in rt
# One authoritative replacement path, no feedback from the old projected cutoff.
replacement=core[core.index('const ReplacementService='):core.index('const RosterValueService=')]
assert 'projectedReplacementLevels' not in replacement
assert "method:'canonical structural starter-slot demand'" in replacement
assert idx.count('FIECore ReplacementService structural cutoff')>=2
assert 'profile=service?.profile?.' in idx
# Best Ball is format-specific without violating roster-neutral Draft Board semantics.
assert 'Ceiling / Profile' in ui and 'bestBallDraftProfile' in ui
assert 'Best Ball portfolio fit *' in ui and 'bestBallPortfolioFit' in ui
assert 'does not silently replace the governed decision score' in ui
assert 'Contribution Profile' in ui
print('PASS V9.3.1+ completion source contract')
