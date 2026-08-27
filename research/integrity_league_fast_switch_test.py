#!/usr/bin/env python3
"""Integrity contract for compact league snapshots and browser fast switching."""
from __future__ import annotations
import argparse, hashlib, importlib.util, json, tempfile
from pathlib import Path
R=Path(__file__).resolve().parents[1]

def load_builder():
 p=R/'research/build_league_app_snapshots.py';spec=importlib.util.spec_from_file_location('fastsnap',p);m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m);return m

def main():
 ap=argparse.ArgumentParser();ap.add_argument('--generated',action='store_true');a=ap.parse_args()
 dc=(R/'app/core/data-client.js').read_text(encoding='utf-8')
 wf=(R/'.github/workflows/build-fie-current.yml').read_text(encoding='utf-8')
 rel=(R/'tools/release_build.py').read_text(encoding='utf-8');sync=(R/'tools/sync_league_app_snapshots.py').read_text(encoding='utf-8')
 assert 'fie-league-core-v1' in dc
 assert 'prefetchLeagueSnapshots' in dc and 'requestIdleCallback' in dc
 assert 'liveRefresh(route,url,value' in dc and 'cache:\'no-store\'' in dc
 assert 'historical_transactions' not in dc, 'data client must not eagerly load transaction history'
 assert 'build_league_app_snapshots.py' in wf
 assert 'data/research/app' in wf
 assert 'sync_league_app_snapshots.py' in rel
 assert "'app/core.json'" in sync and "'app/manifest.json'" in sync
 assert "data/research/app/league-index.json" in sync
 m=load_builder();lid='123456789012345678';row={'league_name':'Fixture','format':'REDRAFT','priority':'HIGH','profile_fingerprint':'abc','scoring_signature':'def'}
 payloads={
  f'https://api.sleeper.app/v1/league/{lid}':{'league_id':lid,'name':'Fixture','season':'2026'},
  f'https://api.sleeper.app/v1/league/{lid}/rosters':[{'roster_id':1,'players':['1']}],
  f'https://api.sleeper.app/v1/league/{lid}/users':[{'user_id':'u1','display_name':'Test'}],
 }
 core=m.build_core(lid,row,lambda url:payloads[url]);m.validate_core(core,lid)
 raw=m.canonical_bytes(core);manifest=m.manifest_for(core,hashlib.sha256(raw).hexdigest(),len(raw))
 assert manifest['league_id']==lid and manifest['core']['bytes']==len(raw)
 assert core['live_overlay']['blocking'] is False and core['live_overlay']['historical_transactions']=='lazy-manual'
 if a.generated:
  index_path=R/'data/research/app/league-index.json';assert index_path.exists(),'generated league-index.json missing'
  idx=json.loads(index_path.read_text(encoding='utf-8'));assert idx.get('schema')=='fie-league-index-v1'
  for e in idx.get('leagues') or []:
   cp=R/e['core'];mp=R/e['manifest'];assert cp.exists() and mp.exists(),e['league_id']
   raw=cp.read_bytes();assert hashlib.sha256(raw).hexdigest()==e['core_sha256'],e['league_id']
   core=json.loads(raw);m.validate_core(core,str(e['league_id']))
 print('PASS league fast-switch integrity')
if __name__=='__main__':main()
