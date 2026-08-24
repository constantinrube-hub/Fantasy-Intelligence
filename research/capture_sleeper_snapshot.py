#!/usr/bin/env python3
"""Capture an immutable Sleeper weekly projection snapshot for future M4 benchmarking.

The file is first-write only by default. `pregame_eligible` is never inferred from an
old endpoint response: it must be explicitly asserted by a capture process that ran
before the week's first kickoff. M4 ignores rows where this flag is false.
"""
from __future__ import annotations
import argparse, gzip, json
from datetime import datetime, timezone
from pathlib import Path
import pandas as pd
import requests

UA="Fantasy-Intelligence-Engine-V8.6-M4/1.0"

def now(): return datetime.now(timezone.utc).isoformat()

def get_json(url):
    r=requests.get(url,timeout=30,headers={"User-Agent":UA,"Accept":"application/json"});r.raise_for_status();return r.json()

def parse_args():
    p=argparse.ArgumentParser()
    p.add_argument('--season',type=int)
    p.add_argument('--week',type=int)
    p.add_argument('--derived-dir',default='data/research/derived')
    p.add_argument('--output-root',default='data/research/market/sleeper')
    p.add_argument('--pregame-eligible',action='store_true',help='Assert this capture occurred before the first kickoff of the week.')
    p.add_argument('--force',action='store_true')
    return p.parse_args()

def main():
    a=parse_args(); state={}
    if not a.season or not a.week:
        state=get_json('https://api.sleeper.app/v1/state/nfl')
    season=a.season or int(state.get('season'))
    week=a.week or int(state.get('week'))
    out=Path(a.output_root)/str(season)/f'week_{week:02d}.jsonl.gz'
    if out.exists() and not a.force:
        print(f'Immutable snapshot already exists: {out}');return
    ident_path=Path(a.derived_dir)/'player_identity.csv.gz'
    ident=pd.read_csv(ident_path,low_memory=False) if ident_path.exists() else pd.DataFrame()
    mapping={}
    if not ident.empty and {'sleeper_id','canonical_player_id'}.issubset(ident.columns):
        for r in ident.dropna(subset=['sleeper_id','canonical_player_id']).itertuples(index=False):
            mapping[str(getattr(r,'sleeper_id'))]=str(getattr(r,'canonical_player_id'))
    posmap={}
    if not ident.empty and 'position' in ident:
        for r in ident.dropna(subset=['sleeper_id']).itertuples(index=False):posmap[str(getattr(r,'sleeper_id'))]=str(getattr(r,'position') or '')
    rows=get_json(f'https://api.sleeper.com/projections/nfl/{season}/{week}?season_type=regular')
    captured=now();out.parent.mkdir(parents=True,exist_ok=True)
    with gzip.open(out,'wt',encoding='utf-8') as h:
        for r in rows or []:
            sid=str(r.get('player_id') or (r.get('player') or {}).get('player_id') or '')
            if not sid:continue
            rec={'season':season,'week':week,'captured_at':captured,'pregame_eligible':bool(a.pregame_eligible),'sleeper_id':sid,
                 'canonical_player_id':mapping.get(sid),'position_model':posmap.get(sid) or (r.get('player') or {}).get('position'),'stats':r.get('stats') or r}
            h.write(json.dumps(rec,separators=(',',':'))+'\n')
    meta=out.with_suffix(out.suffix+'.meta.json')
    meta.write_text(json.dumps({'season':season,'week':week,'captured_at':captured,'pregame_eligible':bool(a.pregame_eligible),'rows':len(rows or []),'first_write_policy':not a.force,'source':'Sleeper projection endpoint'},indent=2))
    print(f'Wrote {out} rows={len(rows or [])} pregame_eligible={a.pregame_eligible}')
if __name__=='__main__':main()
