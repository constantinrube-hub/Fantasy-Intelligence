#!/usr/bin/env python3
"""Aggregate completed/blocked/failed per-league research without pooling validation."""
from __future__ import annotations
import argparse, csv, json, math, statistics
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any
from fie_research_pipeline_contract import (
    PORTFOLIO_SCHEMA, ROOT, enabled_league_rows, load_json, pipeline_dir, write_json,
)

def finite(v):
    try:
        x=float(v); return x if math.isfinite(x) else None
    except Exception:return None

def _status(lid:str, season:int, readiness:dict, summary:dict, matrix:dict)->tuple[str,str]:
    if matrix and str(matrix.get('outcome') or '').lower() not in {'success','complete','completed','pass','passed'}:
        return 'failed',str(matrix.get('reason') or matrix.get('outcome') or 'matrix_job_failed')
    if not readiness or not summary:
        return 'blocked','readiness_or_report_summary_missing'
    ps=str((readiness.get('pipeline') or {}).get('status') or '')
    if ps.startswith('blocked') or ps=='failed_integrity': return 'blocked',ps
    return 'completed',''

def _audit_row(lid,row,season,readiness,summary,matrix):
    status,reason=_status(lid,season,readiness,summary,matrix); league=readiness.get('league') or {}; pos=readiness.get('positions') or {}; lv=readiness.get('league_value') or {}; repl=lv.get('replacement') or {}; head=summary.get('headline') or {}
    return {
      'league_id':lid,'league_name':row.get('league_name') or league.get('name'),'format':row.get('research_format') or row.get('format') or league.get('format'),'teams':league.get('teams'),'scoring_signature':league.get('scoring_signature') or row.get('scoring_signature'),'roster_signature':league.get('roster_signature'),'adp_key':(readiness.get('market') or {}).get('adp_key'),
      'pipeline_status':status,'M1_M9_status':((matrix.get('stages') or {}).get('m1_m9') if matrix else None),'V971_status':(pos.get('QB') or {}).get('evidence',{}).get('v974',{}).get('v972_prior_gate_status') if isinstance((pos.get('QB') or {}).get('evidence'),dict) else None,'V974_exact_comparator_status':(pos.get('QB') or {}).get('exact_scoring'),'V975_QB_status':(((pos.get('QB') or {}).get('evidence') or {}).get('v975') or {}).get('status'),
      'QB_selected_model':(pos.get('QB') or {}).get('selected_production_model'),'RB_selected_model':(pos.get('RB') or {}).get('selected_production_model'),'WR_selected_model':(pos.get('WR') or {}).get('selected_production_model'),'TE_selected_model':(pos.get('TE') or {}).get('selected_production_model'),'DST_selected_model':(pos.get('DST') or {}).get('selected_production_model'),'K_selected_model':(pos.get('K') or {}).get('selected_production_model'),
      'QB_decision':(pos.get('QB') or {}).get('decision'),'RB_decision':(pos.get('RB') or {}).get('decision'),'WR_decision':(pos.get('WR') or {}).get('decision'),'TE_decision':(pos.get('TE') or {}).get('decision'),'DST_decision':(pos.get('DST') or {}).get('decision'),'K_decision':(pos.get('K') or {}).get('decision'),
      'QB_replacement':repl.get('QB'),'RB_replacement':repl.get('RB'),'WR_replacement':repl.get('WR'),'TE_replacement':repl.get('TE'),
      'top100_positive_count':head.get('actionable_top100_positive',0),'top100_negative_count':head.get('actionable_top100_negative',0),'sleepers_gt100_count':head.get('positive_sleepers_gt100',0),'report_complete':bool(summary),'app_publish_complete':bool(matrix.get('app_publish_complete')) if matrix else False,'blocker_reason':reason,
    }

def _write_csv(path:Path,rows:list[dict]):
    path.parent.mkdir(parents=True,exist_ok=True)
    fields=[]
    for r in rows:
        for k in r:
            if k not in fields: fields.append(k)
    with path.open('w',newline='',encoding='utf-8') as f:
        w=csv.DictWriter(f,fieldnames=fields); w.writeheader(); w.writerows(rows)

def _consensus(records:list[tuple[str,dict,dict]],kind:str)->list[dict]:
    # records: (league_id, registry_row, report_summary)
    by=defaultdict(list)
    for lid,row,s in records:
        if kind=='outlier':
            for direction in ('positive','negative'):
                for p in (s.get('outliers_top100') or {}).get(direction,[]) or []:
                    key=str(p.get('player_id') or p.get('sleeper_id') or p.get('name') or '')
                    if key: by[(key,direction)].append((lid,row,p))
        else:
            for pos,players in (s.get('sleepers_gt100') or {}).items():
                for p in players or []:
                    key=str(p.get('player_id') or p.get('sleeper_id') or p.get('name') or '')
                    if key: by[(key,pos)].append((lid,row,p))
    out=[]; applicable=max(1,len(records))
    for (key,group),vals in by.items():
        first=vals[0][2]; edges=[finite(v[2].get('rank_edge_position')) for v in vals]; edges=[x for x in edges if x is not None]; vorps=[finite(v[2].get('vorp')) for v in vals]; vorps=[x for x in vorps if x is not None]; formats=sorted({str(v[1].get('research_format') or v[1].get('format') or '') for v in vals})
        count=len(vals)
        if kind=='outlier':
            category=('PORTFOLIO_CONSENSUS_VALUE' if group=='positive' and count==applicable else 'PORTFOLIO_CONSENSUS_FADE' if group=='negative' and count==applicable else 'FORMAT_DEPENDENT_VALUE')
            out.append({'player_id':key,'player':first.get('name'),'position':first.get('position'),'direction':group,'applicable_leagues':applicable,'signal_leagues':count,'median_rank_edge':statistics.median(edges) if edges else None,'min_rank_edge':min(edges) if edges else None,'max_rank_edge':max(edges) if edges else None,'formats':'|'.join(formats),'classification':category})
        else:
            out.append({'player_id':key,'player':first.get('name'),'position':group,'applicable_leagues':applicable,'sleeper_leagues':count,'strong_sleeper_leagues':sum(str(v[2].get('sleeper_strength'))=='STRONG' for v in vals),'median_vorp':statistics.median(vorps) if vorps else None,'median_rank_edge':statistics.median(edges) if edges else None,'formats':'|'.join(formats),'reason_codes':'|'.join(sorted({c for v in vals for c in (v[2].get('why') or [])})),'classification':'PORTFOLIO_CONSENSUS_VALUE' if count==applicable else 'FORMAT_DEPENDENT_VALUE'})
    countkey='signal_leagues' if kind=='outlier' else 'sleeper_leagues'; out.sort(key=lambda r:(-int(r.get(countkey) or 0),-(abs(float(r.get('median_rank_edge') or 0))),str(r.get('player') or ''))); return out

def _markdown(overview:dict)->str:
    lines=['# FIE Portfolio Research Overview','',f"Season: **{overview['season']}**  ",f"Enabled leagues: **{overview['coverage']['enabled']}** · Completed: **{overview['coverage']['completed']}** · Blocked: **{overview['coverage']['blocked']}** · Failed: **{overview['coverage']['failed']}**",'', '## Run coverage','', '| League | Format | Status | QB | RB | WR | TE | DST | K |','|---|---|---|---|---|---|---|---|---|']
    for r in overview['leagues']:
        lines.append('| '+' | '.join(str(x or '—') for x in [r.get('league_name') or r['league_id'],r.get('format'),r.get('pipeline_status'),r.get('QB_decision'),r.get('RB_decision'),r.get('WR_decision'),r.get('TE_decision'),r.get('DST_decision'),r.get('K_decision')])+' |')
    lines += ['', '## Position model outcomes across leagues','']
    for pos,counts in overview['position_model_outcomes'].items(): lines.append(f"- **{pos}:** "+', '.join(f"{k}={v}" for k,v in sorted(counts.items())))
    lines += ['', 'Cross-league consensus is descriptive only and never changes an individual league validation or promotion decision.','']
    return '\n'.join(lines)

def build(season:int,output:Path):
    rows=enabled_league_rows(); audits=[]; completed_records=[]
    for lid,row in sorted(rows.items()):
        pdir=pipeline_dir(lid,season); readiness=load_json(pdir/'readiness.json',{}); summary=load_json(pdir/'report-summary.json',{}); matrix=load_json(pdir/'matrix-job-status.json',{})
        audit=_audit_row(lid,row,season,readiness,summary,matrix); audits.append(audit)
        if audit['pipeline_status']=='completed': completed_records.append((lid,row,summary))
    counts=Counter(r['pipeline_status'] for r in audits); enabled=len(rows); assert counts['completed']+counts['blocked']+counts['failed']==enabled
    model_outcomes={}
    for pos in ('QB','RB','WR','TE','DST','K'):
        model_outcomes[pos]=dict(Counter(str(r.get(f'{pos}_decision') or 'MISSING') for r in audits))
    overview={'schema':PORTFOLIO_SCHEMA,'schema_version':1,'season':int(season),'coverage':{'enabled':enabled,'completed':counts['completed'],'blocked':counts['blocked'],'failed':counts['failed']},'position_model_outcomes':model_outcomes,'leagues':audits,'governance':{'cross_league_validation_pooling':False,'automatic_promotion':False,'league_specific_decisions_preserved':True}}
    output.mkdir(parents=True,exist_ok=True); write_json(output/'research-overview.json',overview); (output/'research-overview.md').write_text(_markdown(overview),encoding='utf-8'); _write_csv(output/'model-readiness.csv',audits); _write_csv(output/'outlier-consensus.csv',_consensus(completed_records,'outlier')); _write_csv(output/'sleeper-consensus.csv',_consensus(completed_records,'sleeper'))
    return overview

def main(argv=None):
    ap=argparse.ArgumentParser(); ap.add_argument('--season',type=int,required=True); ap.add_argument('--output-dir',default=''); a=ap.parse_args(argv); out=Path(a.output_dir) if a.output_dir else ROOT/'data/research/portfolio'/str(a.season); overview=build(a.season,out); print(json.dumps(overview['coverage'],indent=2)); return 0
if __name__=='__main__': raise SystemExit(main())
