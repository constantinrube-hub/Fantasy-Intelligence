#!/usr/bin/env python3
"""Bounded source integrity checks for V9.3 Decision UX & Reliability."""
from pathlib import Path
import json,re
ROOT=Path(__file__).resolve().parents[1]
idx=(ROOT/'index.html').read_text(encoding='utf-8')
ui=(ROOT/'app/decision-ui.js').read_text(encoding='utf-8')
lc=(ROOT/'app/league-context.js').read_text(encoding='utf-8')
vf=(ROOT/'app/value-finder.js').read_text(encoding='utf-8')
dst=(ROOT/'app/dst-intelligence.js').read_text(encoding='utf-8')
k=(ROOT/'app/kicker-intelligence.js').read_text(encoding='utf-8')
dc=(ROOT/'app/core/data-client.js').read_text(encoding='utf-8')
rt=(ROOT/'app/runtime-foundation.js').read_text(encoding='utf-8')
release=json.loads((ROOT/'config/release.json').read_text())
assert release['release']=='9.3.1-completion'
assert release['runtime']=='9.3.1-foundation'
assert release['value_finder']=='9.3-VF3'
assert 'app/league-context.js' in idx and 'app/decision-ui.js' in idx and 'app/decision-ui.css' in idx
assert "window.state=state" in idx and 'populateTradePicks' in idx
assert 'C0nstant1n' in lc
assert 'function syncRelease()' in ui
assert 'function renderScarcityAudit()' in ui
assert 'function renderLeagueIntel()' in ui
assert 'document.title=`Fantasy Intelligence Engine · ${release}`' in ui
assert 'roster_slots||{},seen=new Set()' in vf and '?.positions||[]' in vf
assert '?.eligible||[]' not in vf
assert "tabs=tabs.filter(x=>x[0]!=='targets')" in idx
assert 'Roster Contribution' in ui and 'Est. Available Next Pick' in ui and 'Market Pos' in ui
assert 'Add → Drop transaction' in ui
assert "S().activeTab==='waivers'" in ui and "fieFaabStrategy" in ui
assert 'Legality is checked only on final post-trade player rosters' in ui
assert "contract[slot]?.positions" in ui
assert 'Opponent-aware max-win lineup' in ui
assert 'Starter slots and legal FLEX/SF eligibility set replacement scarcity' in ui or 'starter slots' in ui.lower()
assert 'renderValueFinderInner' in vf and 'researchError' in vf and 'Retry' in vf
assert '.catch(()=>renderValueFinder())' not in vf.replace(' ','')
assert 'FIELeagueContext' in dst and 'FIELeagueContext' in k
assert 'inflight' in dc and 'coalesced' in dc and 'cacheStats' in dc
# Projections must no longer be serialized behind public enrichment.
assert "const proj=enrich.then" not in rt
assert "league-season-projections" in rt and "league-enrichment" in rt
# No stale hardcoded shell title/release badge.
head=idx[:30000]
assert 'Fantasy Intelligence Engine 9.1' not in head
assert 'Release 9.1' not in head
print('V9.3.1 Decision UX source integrity OK')
