#!/usr/bin/env python3
"""Aggregate per-league FIE research, including official M9.1c challenger coverage.

Cross-league outputs remain descriptive only. M9.1c validation/projection evidence is
never pooled to change an individual league's model decision.
"""
from __future__ import annotations
import argparse, csv, json, math, statistics
from collections import Counter, defaultdict
from pathlib import Path
from fie_research_pipeline_contract import (
    PORTFOLIO_SCHEMA, ROOT, enabled_league_rows, load_json, pipeline_dir, write_json,
)

def finite(v):
    try:
        x=float(v); return x if math.isfinite(x) else None
    except Exception:return None

def _m91c(readiness:dict)->dict:
    x=readiness.get('preseason_projection_challenger') or {}
    return x if isinstance(x,dict) else {}

def _status(lid:str, season:int, readiness:dict, summary:dict, matrix:dict)->tuple[str,str]:
    if matrix and str(matrix.get('outcome') or '').lower() not in {'success','complete','completed','pass','passed'}:
        return 'failed',str(matrix.get('reason') or matrix.get('outcome') or 'matrix_job_failed')
    if not readiness or not summary:
        return 'blocked','readiness_or_report_summary_missing'
    ps=str((readiness.get('pipeline') or {}).get('status') or '')
    if ps.startswith('blocked') or ps=='failed_integrity':
        return 'blocked',ps

    challenger=_m91c(readiness)
    if challenger.get('model')!='M9.1c':
        return 'blocked','official_m91c_preseason_challenger_missing'
    if challenger.get('production_eligible') is not False or challenger.get('automatic_promotion') is not False:
        return 'blocked','m91c_governance_contract_invalid'
    matrix_status=str(matrix.get('m91c_integration_status') or '') if matrix else ''
    if matrix and matrix_status!='complete_research_only':
        return 'blocked','m91c_matrix_integration_incomplete'
    return 'completed',''

def _position_challenger(posmeta:dict)->dict:
    x=posmeta.get('preseason_projection_challenger') or {}
    return x if isinstance(x,dict) else {}

def _audit_row(lid,row,season,readiness,summary,matrix):
    status,reason=_status(lid,season,readiness,summary,matrix)
    league=readiness.get('league') or {}
    pos=readiness.get('positions') or {}
    lv=readiness.get('league_value') or {}
    repl=lv.get('replacement') or {}
    head=summary.get('headline') or {}
    m91c=_m91c(readiness)
    residual=m91c.get('residual_model_gate') or {}
    out={
      'league_id':lid,
      'league_name':row.get('league_name') or league.get('name'),
      'format':row.get('research_format') or row.get('format') or league.get('format'),
      'teams':league.get('teams'),
      'scoring_signature':league.get('scoring_signature') or row.get('scoring_signature'),
      'roster_signature':league.get('roster_signature'),
      'adp_key':(readiness.get('market') or {}).get('adp_key'),
      'pipeline_status':status,
      'M1_M9_status':((matrix.get('stages') or {}).get('m1_m9') if matrix else None),
      'V971_status':(pos.get('QB') or {}).get('evidence',{}).get('v974',{}).get('v972_prior_gate_status') if isinstance((pos.get('QB') or {}).get('evidence'),dict) else None,
      'V974_exact_comparator_status':(pos.get('QB') or {}).get('exact_scoring'),
      'V975_QB_status':(((pos.get('QB') or {}).get('evidence') or {}).get('v975') or {}).get('status'),
      'M91c_model':m91c.get('model'),
      'M91c_status':m91c.get('status'),
      'M91c_production_eligible':m91c.get('production_eligible'),
      'M91c_automatic_promotion':m91c.get('automatic_promotion'),
      'M91c_residual_gate_status':residual.get('status'),
      'M91c_matrix_integration_status':matrix.get('m91c_integration_status') if matrix else None,
      'QB_selected_model':(pos.get('QB') or {}).get('selected_production_model'),
      'RB_selected_model':(pos.get('RB') or {}).get('selected_production_model'),
      'WR_selected_model':(pos.get('WR') or {}).get('selected_production_model'),
      'TE_selected_model':(pos.get('TE') or {}).get('selected_production_model'),
      'DST_selected_model':(pos.get('DST') or {}).get('selected_production_model'),
      'K_selected_model':(pos.get('K') or {}).get('selected_production_model'),
      'QB_decision':(pos.get('QB') or {}).get('decision'),
      'RB_decision':(pos.get('RB') or {}).get('decision'),
      'WR_decision':(pos.get('WR') or {}).get('decision'),
      'TE_decision':(pos.get('TE') or {}).get('decision'),
      'DST_decision':(pos.get('DST') or {}).get('decision'),
      'K_decision':(pos.get('K') or {}).get('decision'),
      'QB_replacement':repl.get('QB'),
      'RB_replacement':repl.get('RB'),
      'WR_replacement':repl.get('WR'),
      'TE_replacement':repl.get('TE'),
      'top100_positive_count':head.get('actionable_top100_positive',0),
      'top100_negative_count':head.get('actionable_top100_negative',0),
      'sleepers_gt100_count':head.get('positive_sleepers_gt100',0),
      'report_complete':bool(summary),
      'app_publish_complete':bool(matrix.get('app_publish_complete')) if matrix else False,
      'blocker_reason':reason,
    }
    for p in ('QB','RB','WR','TE'):
        ch=_position_challenger(pos.get(p) or {})
        out[f'{p}_M91c_exact_rows']=ch.get('exact_rows')
        out[f'{p}_M91c_adjusted_rows']=ch.get('adjusted_rows')
        out[f'{p}_M91c_median_abs_adjustment']=ch.get('median_abs_adjustment')
        out[f'{p}_M91c_p90_abs_adjustment']=ch.get('p90_abs_adjustment')
        out[f'{p}_M91c_max_abs_adjustment']=ch.get('max_abs_adjustment')
        out[f'{p}_M91c_median_reliability']=ch.get('median_total_reliability')
    return out

def _write_csv(path:Path,rows:list[dict]):
    path.parent.mkdir(parents=True,exist_ok=True)
    fields=[]
    for r in rows:
        for k in r:
            if k not in fields: fields.append(k)
    with path.open('w',newline='',encoding='utf-8') as f:
        w=csv.DictWriter(f,fieldnames=fields); w.writeheader(); w.writerows(rows)

def _consensus(records:list[tuple[str,dict,dict]],kind:str)->list[dict]:
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
        first=vals[0][2]
        edges=[finite(v[2].get('rank_edge_position')) for v in vals]; edges=[x for x in edges if x is not None]
        vorps=[finite(v[2].get('vorp')) for v in vals]; vorps=[x for x in vorps if x is not None]
        formats=sorted({str(v[1].get('research_format') or v[1].get('format') or '') for v in vals})
        count=len(vals)
        if kind=='outlier':
            category=('PORTFOLIO_CONSENSUS_VALUE' if group=='positive' and count==applicable else 'PORTFOLIO_CONSENSUS_FADE' if group=='negative' and count==applicable else 'FORMAT_DEPENDENT_VALUE')
            out.append({'player_id':key,'player':first.get('name'),'position':first.get('position'),'direction':group,'applicable_leagues':applicable,'signal_leagues':count,'median_rank_edge':statistics.median(edges) if edges else None,'min_rank_edge':min(edges) if edges else None,'max_rank_edge':max(edges) if edges else None,'formats':'|'.join(formats),'classification':category})
        else:
            out.append({'player_id':key,'player':first.get('name'),'position':group,'applicable_leagues':applicable,'sleeper_leagues':count,'strong_sleeper_leagues':sum(str(v[2].get('sleeper_strength'))=='STRONG' for v in vals),'median_vorp':statistics.median(vorps) if vorps else None,'median_rank_edge':statistics.median(edges) if edges else None,'formats':'|'.join(formats),'reason_codes':'|'.join(sorted({c for v in vals for c in (v[2].get('why') or [])})),'classification':'PORTFOLIO_CONSENSUS_VALUE' if count==applicable else 'FORMAT_DEPENDENT_VALUE'})
    countkey='signal_leagues' if kind=='outlier' else 'sleeper_leagues'
    out.sort(key=lambda r:(-int(r.get(countkey) or 0),-(abs(float(r.get('median_rank_edge') or 0))),str(r.get('player') or '')))
    return out

def _markdown(overview:dict)->str:
    c=overview['coverage']
    m=overview.get('m91c_challenger_coverage') or {}
    lines=[
        '# FIE Portfolio Research Overview','',
        f"Season: **{overview['season']}**  ",
        f"Enabled leagues: **{c['enabled']}** · Completed: **{c['completed']}** · Blocked: **{c['blocked']}** · Failed: **{c['failed']}**",
        '',
        '## Official preseason projection challenger','',
        f"- Model: **M9.1c**",
        f"- Integrated leagues: **{m.get('integrated',0)}/{c['enabled']}**",
        f"- Production activations: **{m.get('production_eligible',0)}**",
        f"- Historical residual gates: {', '.join(f'{k}={v}' for k,v in sorted((m.get('residual_gate_status') or {}).items())) or '—'}",
        '- M9 remains the governed production preseason model. M9.1c evidence is not pooled across leagues for promotion.',
        '',
        '## Run coverage','',
        '| League | Format | Status | M9.1c | Residual Gate | QB | RB | WR | TE | DST | K |',
        '|---|---|---|---|---|---|---|---|---|---|---|'
    ]
    for r in overview['leagues']:
        lines.append('| '+' | '.join(str(x if x not in (None,'') else '—') for x in [
            r.get('league_name') or r['league_id'],r.get('format'),r.get('pipeline_status'),
            r.get('M91c_status'),r.get('M91c_residual_gate_status'),
            r.get('QB_decision'),r.get('RB_decision'),r.get('WR_decision'),r.get('TE_decision'),
            r.get('DST_decision'),r.get('K_decision')
        ])+' |')
    lines += ['', '## Position model outcomes across leagues','']
    for pos,counts in overview['position_model_outcomes'].items():
        lines.append(f"- **{pos}:** "+', '.join(f"{k}={v}" for k,v in sorted(counts.items())))
    lines += ['', 'Cross-league consensus is descriptive only and never changes an individual league validation or promotion decision.','']
    return '\n'.join(lines)

def build(season:int,output:Path):
    rows=enabled_league_rows(); audits=[]; completed_records=[]
    for lid,row in sorted(rows.items()):
        pdir=pipeline_dir(lid,season)
        readiness=load_json(pdir/'readiness.json',{})
        summary=load_json(pdir/'report-summary.json',{})
        matrix=load_json(pdir/'matrix-job-status.json',{})
        audit=_audit_row(lid,row,season,readiness,summary,matrix); audits.append(audit)
        if audit['pipeline_status']=='completed':
            completed_records.append((lid,row,summary))

    counts=Counter(r['pipeline_status'] for r in audits)
    enabled=len(rows)
    assert counts['completed']+counts['blocked']+counts['failed']==enabled

    model_outcomes={}
    for pos in ('QB','RB','WR','TE','DST','K'):
        model_outcomes[pos]=dict(Counter(str(r.get(f'{pos}_decision') or 'MISSING') for r in audits))

    integrated=sum(
        r.get('M91c_model')=='M9.1c'
        and r.get('M91c_matrix_integration_status')=='complete_research_only'
        for r in audits
    )
    prod_eligible=sum(r.get('M91c_production_eligible') is True for r in audits)
    gate_counts=dict(Counter(str(r.get('M91c_residual_gate_status') or 'MISSING') for r in audits))

    overview={
        'schema':PORTFOLIO_SCHEMA,'schema_version':1,'season':int(season),
        'coverage':{
            'enabled':enabled,'completed':counts['completed'],
            'blocked':counts['blocked'],'failed':counts['failed']
        },
        'm91c_challenger_coverage':{
            'official_model':'M9.1c',
            'integrated':integrated,
            'production_eligible':prod_eligible,
            'residual_gate_status':gate_counts,
        },
        'position_model_outcomes':model_outcomes,
        'leagues':audits,
        'governance':{
            'cross_league_validation_pooling':False,
            'automatic_promotion':False,
            'league_specific_decisions_preserved':True,
            'm91c_production_activation':False,
            'm91c_historical_residual_gate_required':True,
        }
    }
    output.mkdir(parents=True,exist_ok=True)
    write_json(output/'research-overview.json',overview)
    (output/'research-overview.md').write_text(_markdown(overview),encoding='utf-8')
    _write_csv(output/'model-readiness.csv',audits)
    _write_csv(output/'outlier-consensus.csv',_consensus(completed_records,'outlier'))
    _write_csv(output/'sleeper-consensus.csv',_consensus(completed_records,'sleeper'))
    return overview

def main(argv=None):
    ap=argparse.ArgumentParser()
    ap.add_argument('--season',type=int,required=True)
    ap.add_argument('--output-dir',default='')
    a=ap.parse_args(argv)
    out=Path(a.output_dir) if a.output_dir else ROOT/'data/research/portfolio'/str(a.season)
    overview=build(a.season,out)
    print(json.dumps({
        'coverage':overview['coverage'],
        'm91c_challenger_coverage':overview['m91c_challenger_coverage'],
    },indent=2))
    return 0

if __name__=='__main__':
    raise SystemExit(main())
