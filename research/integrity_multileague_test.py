#!/usr/bin/env python3
"""Deterministic multi-league namespace/governance tests."""
import json, os, tempfile
from pathlib import Path
from types import SimpleNamespace
from datetime import datetime, timezone
from fie_governance import build
from league_profile import scoring_signature

A='111111111111111111';B='222222222222222222';SIG=scoring_signature({'rec':1,'pass_td':4})

def w(p,obj):
    p=Path(p);p.parent.mkdir(parents=True,exist_ok=True);p.write_text(json.dumps(obj))

def artifact(lid,fp,kind):
    d={'status':'complete','league_id':lid,'league_format':'REDRAFT','profile_fingerprint':fp,'profile_scoring_signature':SIG,'scoring_signature':SIG}
    if kind=='m5': d['activation']={'decision_gates':{}}
    return d

with tempfile.TemporaryDirectory() as td:
    old=os.getcwd();os.chdir(td)
    try:
        fp='f'*64; root=f'data/research/leagues/{A}'
        profile={'league_id':A,'format':'REDRAFT','profile_fingerprint':fp,'scoring_signature':SIG}
        w(f'{root}/profile.json',profile);w(f'{root}/milestone4.json',artifact(A,fp,'m4'));w(f'{root}/milestone5.json',artifact(A,fp,'m5'));w(f'{root}/milestone6.json',artifact(A,fp,'m6'))
        cur=artifact(A,fp,'cur');cur.update({'status':'complete','producer_build':'V8.8-M6','m5_build':'V8.7-M5','generated_at':datetime.now(timezone.utc).isoformat(),'snapshot_max_age_hours':18,'target_week_realised_stats_excluded':True,'live_profile_fingerprint':fp,'profile_current_match':True,'summary':{'activation_eligible':3}});w(f'{root}/current/milestone5_current.json',cur)
        w(f'{root}/governance/operator_override.json',{'mode':'AUTO'});w('data/research/governance/operator_override.json',{'mode':'AUTO'})
        args=SimpleNamespace(league_id=A,league_profile=f'{root}/profile.json',m4_bundle=f'{root}/milestone4.json',m5_bundle=f'{root}/milestone5.json',m6_bundle=f'{root}/milestone6.json',current_snapshot=f'{root}/current/milestone5_current.json',operator_override=f'{root}/governance/operator_override.json',global_operator_override='data/research/governance/operator_override.json',output=f'{root}/governance/active_release.json',mode='KEEP',max_age_hours=18)
        g=build(args); assert g['runtime_enabled'] is True, g['reason']; assert all(g['checks'].values()),g['checks']
        # Cross-league artifact must fail even with identical scoring.
        bad=artifact(B,fp,'m5');bad['activation']={'decision_gates':{}};w(f'{root}/milestone5.json',bad)
        g2=build(args);assert not g2['runtime_enabled'] and not g2['checks']['league_id_match']
        w(f'{root}/milestone5.json',artifact(A,fp,'m5'));d=json.loads(Path(f'{root}/milestone5.json').read_text());d['activation']={'decision_gates':{}};w(f'{root}/milestone5.json',d)
        # Global emergency CONTROL must disable an otherwise valid league.
        w('data/research/governance/operator_override.json',{'mode':'CONTROL'});g3=build(args);assert not g3['runtime_enabled'] and not g3['checks']['global_operator_auto']
    finally: os.chdir(old)
print('OK: multi-league namespace, profile, scoring and global rollback isolation')
