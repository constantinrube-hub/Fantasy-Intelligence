#!/usr/bin/env python3
from __future__ import annotations
from pathlib import Path

from league_profile import build_profile
from portfolio_rules import load_portfolio_config, entry_for

ROOT=Path(__file__).resolve().parents[1]
CFG=ROOT/'config'/'league-portfolio.json'
cfg=load_portfolio_config(CFG)
assert cfg['sleeper_username']=='C0nstant1n'
assert len(cfg['leagues'])==19
formats={}
for e in cfg['leagues']: formats[e['format']]=formats.get(e['format'],0)+1
assert formats=={'CHOPPED':4,'REDRAFT':3,'REDRAFT_BESTBALL':2,'DYNASTY':7,'DYNASTY_BESTBALL':3},formats

legacy=entry_for(cfg,'1316165875291668480')
assert legacy and legacy['priority']=='VERY_HIGH'
c=legacy['research_constraints'][0]
assert c['type']=='cohort_floor_with_legacy_cap'
assert c['unlimited_entry_season_min']==2025 and c['legacy_entry_season_max']==2024
assert c['legacy_cap_by_season']=={'2026':15,'2027':10,'2028':7,'2029':4,'2030':1}
assert c['legacy_cap_after_2030']==1

cohort=entry_for(cfg,'1342896584593018880')
assert cohort['research_constraints']==[{'type':'nfl_entry_cohort_floor','minimum_entry_season':2025}]

fixture={'league_id':'1316165875291668480','name':'Fixture','season':'2026','season_type':'regular','total_rosters':12,
         'roster_positions':['QB','RB','WR','TE','FLEX','BN'],'settings':{'type':2},
         'scoring_settings':{'rec':1,'pass_td':4}}
managed=build_profile(fixture['league_id'],'DYNASTY',league_json=fixture,portfolio_entry=legacy)
plain=build_profile(fixture['league_id'],'DYNASTY',league_json=fixture)
assert managed['research_constraints']==legacy['research_constraints']
assert managed['profile_fingerprint']!=plain['profile_fingerprint'],'custom research rules must be fingerprinted'
assert managed['portfolio']['priority']=='VERY_HIGH'

# Browser-side implementation is now a dedicated module. Validate its public
# rule contract directly rather than requiring old inline index.html hooks.
js=(ROOT/'app'/'portfolio-config.js').read_text(encoding='utf-8')
for token in [
    'nfl_entry_cohort_floor',
    'cohort_floor_with_legacy_cap',
    'Legacy veteran cap',
    'managedLeagues',
    'isPlayerEligible',
    'acquisitionConstraint',
    'rosterRuleViolations',
    'dropSatisfiesAcquisition',
    'poolViolations',
    'window.FIEPortfolioConfig=API',
]:
    assert token in js,token

print('PASS: 19-league portfolio + fixed-cohort custom rules are valid, research-fingerprinted and exposed through modular browser rules')
