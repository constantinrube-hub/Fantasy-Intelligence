#!/usr/bin/env python3
"""Static integrity checks for V8.9-VF2 Draft Value Finder + Top-100 Pick Optimizer."""
from pathlib import Path
import re

ROOT=Path(__file__).resolve().parents[1]
html=(ROOT/'index.html').read_text(encoding='utf-8')
js=(ROOT/'app'/'value-finder.js').read_text(encoding='utf-8')

checks={
    'value finder panel exists':'id="valueFinderPanel"' in html,
    'draft nav route exists':"['valuefinder','Value Finder']" in html,
    'module loaded':'<script src="app/value-finder.js"></script>' in html,
    'm5 getters exposed':'getResearchBundle:()=>m5ResearchBundle' in html and 'getCurrentBundle:()=>m5CurrentBundle' in html,
    'hard eligible pool reused':'draftFullEligiblePool' in js and 'vfEligiblePool' in js,
    'same-position market rerank':'marketPosRank' in js and 'fiePosRank' in js and 'posEdge' in js,
    '200 plus snap-path guard':"f.band!=='200_PLUS'||x.snap.score>=60" in js,
    'snap path score exists':'function vfSnapPath' in js,
    'm5 policy score exists':'function vfPolicyScore' in js and 'profile?.draft_weights' in js,
    'missing weights renormalized':'function vfWeighted' in js and 'covered+=w' in js,
    'm6 not force enabled':'FIE_M6_GOVERNANCE_ALLOW=true' not in js and 'operator_override' not in js,
    'live target states':all(x in js for x in ['WATCH','WAIT','TARGET','TAKE NOW','DRAFTED']),
    'draft assistant augmented':"['Value Finder','Target plan']" in js and 'augmentDraftAssistant' in js,
    'existing recommendation preserved':'The original Draft Assistant recommendation remains visible separately.' in js,
    'target filters':all(x in js for x in ['vfBand','vfPosition','vfSnap','vfExperience','vfConfidence','vfUnder','vfAvailable']),
    'top100 optimizer route':"Top 100 · Pick Optimizer" in js and 'renderTop100Optimizer' in js,
    'overall eligible market rerank':all(x in js for x in ['marketOverallRank','fieOverallRank','fieLeagueRank','overallEdge']),
    'top100 wait economics':all(x in js for x in ['valueCapture','reachCost','waitCost','tierRisk','replacementDrop']),
    'opponent adjusted survival reused':'managerPressure' in js and 'opponentPressure' in js,
    'three pick path proxy':all(x in js for x in ['pathTake','pathWait','pathDelta','thirdPick']),
    'top100 draft assistant integration':"TOP100" in js and 'top100Map' in js,
}
failed=[k for k,v in checks.items() if not v]
if failed:
    raise SystemExit('FAIL: '+', '.join(failed))
print('OK: V8.9-VF2 Value Finder + Top-100 Pick Optimizer static integrity')
