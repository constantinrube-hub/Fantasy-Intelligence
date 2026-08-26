#!/usr/bin/env python3
from pathlib import Path
import re
from statistical_guardrails import promotion_gate
from datetime import datetime, timezone
from fie_research import latest_completed_season
from build_current_snapshot import inferred_nfl_season

root=Path(__file__).resolve().parents[1]
html=(root/'index.html').read_text()
proxy=(root/'functions/api/data/[[path]].js').read_text()
health=(root/'functions/api/health.js').read_text(); release=(root/'config/release.json').read_text()

assert 'V8.9-RTS' in html
assert "window.FIE89_HASH_VERIFIED=false" in html
assert 'verifyGovernanceHashesV89' in html
assert "hashOk=window.FIE89_HASH_VERIFIED===true" in html
assert "runtime_enabled===true" in html
assert "function replacementIndex(effective,poolLength){const rank=Math.max(1,Math.round(Number(effective)||1));return Math.max(0,Math.min(poolLength-1,rank-1));}" in html
assert 'marginalStarterDemand' in html and "SUPER_FLEX:['QB','RB','WR','TE']" in html
assert 'expanding-window out-of-time' in html
assert 'temporalFeatureGate' in html
assert 'heuristic low/high, not calibrated P10/P90' in html
assert 'empirical historical survival frequency' in html
assert 'rankValueDifferenceV89' in html
assert 'generic rookie-slot prior + probabilistic owner slot' in html
assert 'optimal-lineup simulation across' in html
assert 'three-year discounted projected VOR utility' in html
assert 'weekly survival-strength proxy' in html
assert "['rec_te','bonus_rec_te','rec_rb','bonus_rec_rb','rec_wr','bonus_rec_wr']" in html
assert 'weeklyExact' in html and 'seasonExact' in html
# Multi-league production isolation: browser loaders must be League-ID scoped.
assert 'data/research/leagues/${id}' in html
assert 'FIE_RESEARCH_RUNTIME' in html and 'resetAll()' in html
assert 'artifact_paths' in html and 'league_id_match' in html and 'profile_fingerprint_match' in html
assert 'current_profile_live_match' in html and 'artifact_scope_match' in html
for legacy in ('data/research/milestone4.json','data/research/milestone5.json','data/research/milestone6.json','data/research/current/milestone5_current.json','data/research/governance/active_release.json'):
    assert legacy not in html, f'legacy global browser research path remains: {legacy}'

# Remove embedded curated data before rollover scan. Historical draft years in that dataset are legitimate.
scan=re.sub(r'const CURATED = \[.*?\];\nconst PFF', 'const CURATED=[];\nconst PFF', html, flags=re.S)
for bad in ('===2026','season=2026','end-2026','contractEnd<=2026'):
    assert bad not in scan, f'hard-coded live season remains: {bad}'

assert '/api/data/nflverse/weekly/${c.season}' in html
assert "if (parts.length === 3)" in proxy and "seasonalNflverse(parts[1], parts[2])" in proxy
assert "const y = String(season);" in proxy
assert 'FIE_RELEASE.release' in health and '"release": "9.3-decision-ux-reliability"' in release
assert latest_completed_season(datetime(2027,1,10,tzinfo=timezone.utc))==2025
assert latest_completed_season(datetime(2027,2,10,tzinfo=timezone.utc))==2026
assert inferred_nfl_season(datetime(2027,1,10,tzinfo=timezone.utc))==2026
assert inferred_nfl_season(datetime(2027,8,10,tzinfo=timezone.utc))==2027

# Promotion guardrails must reject inconsistent folds and accept a strong persistent improvement.
good=promotion_gate([.04,.03,.05,.02,.04], min_mean=.01, min_folds=4, require_positive_ci=True)
bad=promotion_gate([.10,-.08,.09,-.07,.01], min_mean=.01, min_folds=4, require_positive_ci=True)
assert good['robust'] is True, good
assert bad['robust'] is False, bad
print('OK: V8.9 runtime integrity, rollover, scoring, governance and statistical guardrails')
