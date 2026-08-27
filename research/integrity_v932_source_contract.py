#!/usr/bin/env python3
"""Bounded V9.3.2 Browser QA & Ranking Integrity source contract."""
from pathlib import Path
import json,re
R=Path(__file__).resolve().parents[1]
rel=json.loads((R/'config/release.json').read_text())
idx=(R/'index.html').read_text();ui=(R/'app/decision-ui.js').read_text();vf=(R/'app/value-finder.js').read_text();dst=(R/'app/dst-intelligence.js').read_text();kick=(R/'app/kicker-intelligence.js').read_text();cur=(R/'research/build_current_snapshot.py').read_text();port=(R/'app/portfolio-config.js').read_text();core=(R/'app/core/core-services.js').read_text();rt=(R/'app/runtime-foundation.js').read_text()
for f in ['season-context.js','numeric.js','projection-service.js','draft-state-service.js','surface-router.js','special-teams-series.js','draft-value-service.js']:
    assert f'app/core/{f}' in idx,f'{f} not loaded by browser shell'
assert rel['release'].startswith('9.3.2-') and rel['runtime'].startswith('9.3.2-') and rel['value_finder']=='9.3.2-VF4'
# Season 0 and nullable semantics.
assert "String(raw).trim()===''" in idx and 'a>0?a:' in idx
assert 'FIESeasonBootstrapResolver' in idx and 'window.activeSeason=activeSeason' in idx and 'FIE_SEASON_BOOTSTRAP_FALLBACK' in idx
assert 'window.FIESeasonContext.resolve({' not in idx
assert 'window.FIECore?.SeasonResolver?.resolve' in idx
assert 'window.FIESeasonContext=SeasonContext' in rt and 'resolve({league=window.state?.league' in rt
assert "Number.isInteger(n)&&n>1900" in (R/'app/core/season-context.js').read_text()
assert '/app/core/season-context.js?v=932-season-namespace-fix' in idx
assert 'window.FIESeasonBootstrapResolver=API' in (R/'app/core/season-context.js').read_text()
assert 'window.FIESeasonContext=API' not in (R/'app/core/season-context.js').read_text()
assert 'state.weekly.season=activeSeason();syncSeasonSelectV89();' in idx
assert 'Season ${activeSeason()} · Week ${currentWeek()}' in idx
assert "value===null||value===undefined" in (R/'app/core/numeric.js').read_text()
# Shared canonical semantics.
assert 'FIEProjectionResolver' in ui and 'FIEDraftBaseValueService' in ui and 'FIEDraftBaseValueService' in vf
assert 'marketIndependent:true' in (R/'app/core/draft-value-service.js').read_text()
assert 'FIEDraftStateService' in vf and 'FIEDraftStateService' in ui
assert 'FIESurfaceRouter' in idx and 'matchupSimPanel' in (R/'app/core/surface-router.js').read_text()
# Structural contract must have one implementation.
assert 'structural_contract' in cur and 'live_contract = structural_contract(' in cur
assert '"settings": pf.get("settings")' not in cur
assert 'profile_diff' in cur
# Caps/League Intel/Weekly orchestration.
assert 'optionalCap' in port and 'optionalCap' in idx
assert 'playerPosBySleeperId(' not in idx
assert 'PlayerIdentity?.positionForId' in idx
assert 'Optional context loading in background' in idx and 'const deadline=' in idx
# K/DST full week support and drawers.
for txt in (dst,kick):
    assert ('Weeks 1–18' in txt or 'Week 1–18' in txt) and 'FIESpecialTeamsSeries' in txt and 'openDrawer' in txt
# UI corrections from initial browser review.
assert 'Player</th><th>Asset Rank' in ui or "label:'Asset Rank'" in ui
assert 'Best pick' in ui and 'Alternative' in ui and 'Value play' in ui
assert 'Board → Decision' in ui
assert 'Low-data' in ui and 'Canonical FIE player quality excludes market price' in ui
assert 'Evaluates the selected roster’s starting strength, depth, positional strengths and weaknesses using the loaded league’s exact rules.' in idx
# Runtime/cache release lineage updated.
assert '9.3.2' in rt and "fie-data-v932" in (R/'app/core/data-client.js').read_text()
print('PASS V9.3.2 Browser QA source contract')
