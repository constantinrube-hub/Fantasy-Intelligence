#!/usr/bin/env python3
"""Extend existing fast-switch league core with compact research endpoints.

This is a postprocessor on the existing app snapshot architecture.  It never
builds a second league shell and preserves manifest/index hash binding.
"""
from __future__ import annotations
import argparse,hashlib,json
from pathlib import Path
from fie_research_pipeline_contract import ROOT, enabled_league_rows, pipeline_dir

def bytes_(obj):return (json.dumps(obj,ensure_ascii=False,sort_keys=True,separators=(',',':'))+'\n').encode('utf-8')
def write(path,obj):path.parent.mkdir(parents=True,exist_ok=True);data=bytes_(obj);path.write_bytes(data);return hashlib.sha256(data).hexdigest(),len(data)
def publish(lid,season,strict=False):
    app=ROOT/'data/research/leagues'/lid/'app';cp=app/'core.json';mp=app/'manifest.json';pdir=pipeline_dir(lid,season)
    if not cp.is_file() or not mp.is_file():
        if strict: raise RuntimeError(f'existing app core/manifest required for {lid}')
        return False
    matrix=json.loads((pdir/'matrix-job-status.json').read_text()) if (pdir/'matrix-job-status.json').is_file() else {}
    if matrix and str(matrix.get('outcome') or '').lower() not in {'success','complete','completed','pass','passed'}:
        if strict: raise RuntimeError(f'current matrix run failed for {lid}; refusing stale research publish')
        return False
    refs={'readiness':pdir/'readiness.json','rankings':pdir/'rankings.json','report_summary':pdir/'report-summary.json'}
    missing=[k for k,p in refs.items() if not p.is_file()]
    if missing:
        if strict: raise RuntimeError(f'research files missing for {lid}: {missing}')
        return False
    core=json.loads(cp.read_text());assert str(core.get('league_id'))==str(lid)
    research=core.setdefault('research',{})
    for key,path in refs.items(): research[key]=path.relative_to(ROOT).as_posix()
    for key in refs:
        assert f'/leagues/{lid}/performance/{season}/research_pipeline/' in '/'+research[key]
    sha,size=write(cp,core);manifest=json.loads(mp.read_text());manifest['core']={'path':f'data/research/leagues/{lid}/app/core.json','sha256':sha,'bytes':size};write(mp,manifest)
    indexp=ROOT/'data/research/app/league-index.json'
    if indexp.is_file():
        idx=json.loads(indexp.read_text());found=False
        for entry in idx.get('leagues') or []:
            if str(entry.get('league_id'))==str(lid):entry['core_sha256']=sha;entry['core_bytes']=size;found=True
        if strict and not found:raise RuntimeError(f'league-index entry missing for {lid}')
        write(indexp,idx)
    return True
def main(argv=None):
    ap=argparse.ArgumentParser();ap.add_argument('--league-id',action='append',default=[]);ap.add_argument('--season',type=int,required=True);ap.add_argument('--strict',action='store_true');a=ap.parse_args(argv)
    ids=list(map(str,a.league_id)) if a.league_id else sorted(enabled_league_rows());done=[];skipped=[]
    for lid in ids:
        if publish(lid,a.season,a.strict):done.append(lid)
        else:skipped.append(lid)
    print(json.dumps({'published':done,'skipped':skipped},indent=2));return 0
if __name__=='__main__':raise SystemExit(main())
