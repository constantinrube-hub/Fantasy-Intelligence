from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
C = (ROOT / 'app/v9.3.4c-weekly-context.js').read_text(encoding='utf-8')
D = (ROOT / 'app/v9.3.4d-starter-economics.js').read_text(encoding='utf-8')
E = (ROOT / 'app/v9.3.4e-return-scoring.js').read_text(encoding='utf-8')
LOADER = (ROOT / 'app/current-snapshot-store.js').read_text(encoding='utf-8')

# C: lightweight selected-week matchup context, additive to full simulation.
assert "const VERSION='9.3.4C'" in C
assert '/matchups/${Number(week)}' in C
assert 'normalWinProbability' in C and 'projectedLineup' in C
assert 'fullSimulationRequired:false' in C
assert 'FIEWeeklyMatchupContext' in C
assert 'FIEDecisionEngines.weeklyContext=out' in C
assert 'runLeagueSimulation(' not in C, 'C must not trigger the full league simulation'
assert 'leagueSim.data.current=' not in C, 'C must not masquerade as a full simulation result'
assert 'stillCurrent(ctx)' in C, 'C requires league/generation stale-result protection'
assert 'Opponent projected total' in C and 'Modeled win probability' in C
assert "'#matchupSimPanel'" in C, 'C must target the current Matchup & Playoffs panel' 
assert 's?.selectedRoster??fromEl??s?.selectedRosterId' in C, 'C must prioritize the current decision-ui selectedRoster state'
assert 'FIEDataClient?.response' in C, 'C should use the shared data client when available'

# D: starter-slot economics is universal and eligibility-aware.
assert "const VERSION='9.3.4D'" in D
assert 'universal-starter-slot-economics' in D
assert "SUPER_FLEX:['QB','RB','WR','TE']" in D
assert "OP:['QB','RB','WR','TE']" in D
assert "FLEX:['RB','WR','TE']" in D
assert "WRRB_FLEX:['RB','WR']" in D
assert "IDP_FLEX:['DL','LB','DB']" in D
assert "EDGE:['DL']" in D and "FS:['DB']" in D, 'D must normalize common Sleeper IDP aliases'
assert "'EDGE','IDL'" in C and "'FS','SS'" in C, 'C must normalize common IDP aliases'
for term in ['effectiveStarterDemand','replacementAdjustedValue','starterProbability','scarcityMultiplier','floorDownside','marginalLineupUtility']:
    assert term in D, term
assert 'economicsAwareRerank' in D, 'D must influence live decision ranking, not remain diagnostic only'
assert 'const w=weeklyProjection(p)' in D and 'season/17' in D, 'D FLEX allocation must compare players on a common weekly-points scale'
assert 'finite(p?.seasonScore)' in D, 'D must preserve a season-score fallback if FIE89 is temporarily unavailable'
assert 'fie:score-published' in D
assert 'chopped' not in D.lower(), 'starter economics must not contain a Chopped special case'

# E: verified return keys/fields and explicit double-count protection.
assert "const VERSION='9.3.4E'" in E
for term in ["'kr_yd'", "'pr_yd'", "'kr_td'", "'pr_td'", "'st_td'", "'def_kr_td'", "'def_pr_td'", "'def_st_td'"]:
    assert term in E, term
for term in ['special_teams_tds','kickoff_returns','kickoff_return_yards','punt_returns','punt_return_yards']:
    assert term in E, term
assert 'completionDecision' in E and 'zeroReturnRow' in E
assert "mode:'already-complete'" in E
assert "mode:'missing-completed'" in E
assert "mode:'partial-completed'" in E
assert "mode:'ambiguous-fail-closed'" in E
assert 'returnYardScoring:null' in E, 'do not invent unverified DST return-yard keys'
assert 'returnProjectionPoints=null' in E, 'missing return projections must remain null'
assert 'weeklyProjectionWithReturns' in E
assert 'Deliberately expose the adjusted projection rather than mutate an opaque baseline' in E

# Loader: preserve A3 baseline and then chain C -> D -> E.
assert "const VERSION='9.3.4C-E'" in LOADER
for asset in ['v9.3.4a3-score-performance.js','v9.3.4c-weekly-context.js','v9.3.4d-starter-economics.js','v9.3.4e-return-scoring.js']:
    assert asset in LOADER, asset
assert LOADER.index('function bootE') < LOADER.index('function bootD') < LOADER.index('function bootC') < LOADER.index('function bootA3')
assert 'c.onload=bootD' in LOADER
assert 'd.onload=bootE' in LOADER
assert 'b.onload=bootC' in LOADER

print('V9.3.4C-E integrity: PASS')
