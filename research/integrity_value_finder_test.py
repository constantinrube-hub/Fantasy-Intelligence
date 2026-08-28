#!/usr/bin/env python3
"""Static integrity checks for the current V9.3 Value Finder + Top-100 optimizer.

The old test required literal panel/nav/script wiring in index.html. Value Finder
is now a self-registering modular surface, so this test validates the module's
actual public API, navigation registration, M5 access and ranking/timing logic.
"""
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
js=(ROOT/'app'/'value-finder.js').read_text(encoding='utf-8')
ui=(ROOT/'app'/'decision-ui.js').read_text(encoding='utf-8')

checks={
    # Current modular surface + public export
    'value finder module exists':'window.FIE_VALUE_FINDER=' in js,
    'value finder render exposed':'window.renderValueFinder=renderValueFinder' in js,
    'draft nav route self-registers':"SECTION_CONFIG.draft.tabs.splice(1,0,['valuefinder','Value Finder'])" in js,
    'decision UI knows value finder panel':'valueFinderPanel' in ui,

    # M5 access is consumed through the public runtime API rather than old
    # inline getters in index.html.
    'm5 research getter consumed':'window.FIE_M5?.getResearchBundle?.()' in js,
    'm5 current getter consumed':'window.FIE_M5?.getCurrentBundle?.()' in js,

    # Eligibility and canonical ranking
    'hard eligible pool reused':'draftFullEligiblePool' in js and 'vfEligiblePool' in js,
    'canonical draft value service':'FIEDraftBaseValueService' in js,
    'same-position market rerank':'marketPosRank' in js and 'fiePosRank' in js and 'posEdge' in js,
    'overall eligible market rerank':all(x in js for x in ['marketOverallRank','fieOverallRank','fieLeagueRank','overallEdge']),

    # Role / M5 policy semantics
    '200 plus snap-path guard':"f.band!=='200_PLUS'||x.snap.score>=60" in js,
    'snap path score exists':'function vfSnapPath' in js,
    'm5 policy score exists':'function vfPolicyScore' in js and 'profile?.draft_weights' in js,
    'missing weights renormalized':'function vfWeighted' in js and 'covered+=w' in js,
    'm6 not force enabled':'FIE_M6_GOVERNANCE_ALLOW=true' not in js and 'operator_override' not in js,

    # Live target states and Draft Assistant augmentation
    'live target states':all(x in js for x in ['WATCH','WAIT','TARGET','TAKE NOW','DRAFTED']),
    'draft assistant augmented':'augmentDraftAssistant' in js and 'window.renderDraftAssistant=function()' in js,

    # Filters
    'target filters':all(x in js for x in ['vfBand','vfPosition','vfSnap','vfExperience','vfConfidence','vfUnder','vfAvailable']),

    # Top-100 optimizer
    'top100 optimizer route':"Top 100 · Pick Optimizer" in js and 'renderTop100Optimizer' in js,
    'top100 wait economics':all(x in js for x in ['valueCapture','reachCost','waitCost','tierRisk','replacementDrop']),
    'opponent adjusted survival reused':'managerPressure' in js and 'opponentPressure' in js,
    'three pick path proxy':all(x in js for x in ['pathTake','pathWait','pathDelta','thirdPick']),
    'top100 draft assistant integration':'TOP100' in js and 'top100Map' in js,

    # Cache + invalidation architecture
    'split base/live cache':'vfBaseCacheKey' in js and 'vfLiveCacheKey' in js,
    'league invalidation':"fie:league-changing" in js and "fie:league-loaded" in js,
}

failed=[k for k,v in checks.items() if not v]
if failed:
    raise SystemExit('FAIL: '+', '.join(failed))

print('OK: V9.3 Value Finder + Top-100 Pick Optimizer modular integrity')
