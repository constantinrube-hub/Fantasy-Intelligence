#!/usr/bin/env python3
"""Durable recommendation objects derived from unchanged decision-owner reports.

Observing a submitted roster is not proof that a user followed advice. Actions
and outcomes remain unknown until a separately bound observation exists.
"""
from __future__ import annotations
import argparse
import hashlib
import json
from datetime import datetime,timezone
from pathlib import Path
from point_in_time_capture import canonical_bytes
from weekly_report_bundle import load_owner
from weekly_pipeline_readiness import stamp,digest
from workflow_decision_context import operational_lifecycle


def decision(owner: str, source: dict, league: dict, kind: str, recommendation: dict, observed: str) -> dict:
    inputs={'owner':owner,'source_sha256':source['sha256'],'league_id':str(league['league_id']),
            'season':league['season'],'week':league['week'],'kind':kind,'recommendation':recommendation}
    identity=hashlib.sha256(canonical_bytes(inputs)).hexdigest()
    evidence=league.get('input_readiness') or league.get('evidence') or {}
    return {'schema':'fie-weekly-decision-v1','decision_id':identity,'owner':owner,'kind':kind,
        'league_id':str(league['league_id']),'season':league['season'],'week':league['week'],
        'recommendation_as_of':observed,'issued_at':source.get('generated_at'),
        'issued_at_status':'DECLARED_GENERATION_TIME' if source.get('generated_at') else 'NOT_DECLARED_BY_OWNER','source':source,'input_bindings':league.get('source_bindings') or {key:value for key,value in evidence.items() if key.endswith('_sha256') or 'fingerprint' in key or 'signature' in key or key in {'current_generated_at','current_season','current_week'}},
        'scoring_signature':evidence.get('current_scoring_signature') or evidence.get('scoring_signature'),
        'profile_fingerprint':evidence.get('current_profile_fingerprint') or evidence.get('profile_fingerprint'),
        'recommendation':recommendation,'alternatives':recommendation.get('alternatives'),
        'explanation':{'owner_rationale':recommendation.get('rationale'),'confidence':recommendation.get('confidence'),
                       'uncertainty':recommendation.get('projection_evidence'),'synthesized_drivers':False},
        'user_action':{'status':'NOT_OBSERVED'},'outcome':{'status':'NOT_OBSERVED'},'hindsight_optimum':None,
        'ex_ante_quality':'NOT_ASSESSED','ex_post_result':'NOT_OBSERVED',
        'governance':{'recommendation_owner_unchanged':True,'transaction_execution':False,'model_promotion':False}}


def build(root: Path,season: int,week: int,as_of: datetime) -> dict:
    if as_of.tzinfo is None or not 1<=week<=18:raise ValueError('LEDGER_TARGET_OR_TIME_INVALID')
    base=root/f'data/research/evaluation/{season}/weeks/week-{week}'
    paths={'WINDOW_1C':base/'weekly-actions-portfolio-v1.json','WINDOW_1D':base/'waivers/portfolio-latest.json'}
    schemas={'WINDOW_1C':'fie-window1c-weekly-actions-portfolio-v1','WINDOW_1D':'fie-window1d-optimal-waiver-portfolio-v1'}
    decisions=[];states=[];sources={}
    for owner,path in paths.items():
        report,binding=load_owner(root,path,season,week,as_of,expected_schema=schemas[owner]);sources[owner]=binding
        if report is None:continue
        for league in report['leagues']:
            lid=str(league['league_id']);lifecycle=operational_lifecycle(root,lid,season,week)
            states.append({'owner':owner,'league_id':lid,'status':league['status'],'lifecycle':lifecycle})
            if not lifecycle['operational']:continue
            kinds=([('LINEUP_CHANGE',(league.get('actions') or {}).get('lineup',[])),
                    ('STATUS_CHECK',(league.get('actions') or {}).get('injury_alerts',[]))] if owner=='WINDOW_1C'
                    else [('WAIVER_PLAN',league.get('recommendations') or [])])
            for kind,rows in kinds:
                for row in rows:
                    if not isinstance(row,dict):raise ValueError('LEDGER_RECOMMENDATION_NOT_OBJECT')
                    decisions.append(decision(owner,binding,league,kind,row,binding['observed_at']))
    # Identical owner rows are one decision, while conflicting source revisions
    # have distinct identities even if the player recommendation is unchanged.
    unique={row['decision_id']:row for row in decisions}
    return {'producer':{'module':'research/weekly_decision_ledger.py','version':'1.0.0','sha256':digest(Path(__file__))},'schema':'fie-weekly-decision-ledger-v1','season':season,'week':week,'as_of_utc':as_of.isoformat(),
            'status':'BOUND_OWNER_OUTPUTS' if all(row['status']=='AVAILABLE' for row in sources.values()) else 'PARTIAL_SOURCES',
            'decisions':sorted(unique.values(),key=lambda row:(row['league_id'],row['kind'],row['decision_id'])),
            'decision_count':len(unique),'league_states':states,'sources':sources,
            'note':'This ledger preserves owner recommendations, including low-confidence checks. It does not infer user adoption, outcome quality, a model improvement, or a transaction from current roster state.'}


def observe_action(root: Path,ledger: dict,observation: dict,as_of: datetime) -> dict:
    """Bind a separately captured action source; never execute or infer an action."""
    matches=[row for row in ledger['decisions'] if row['decision_id']==observation.get('decision_id')]
    if len(matches)!=1:raise ValueError('LEDGER_ACTION_DECISION_UNRESOLVED')
    chosen=matches[0];observed=stamp(observation['observed_at'])
    if not chosen.get('issued_at'):raise ValueError('LEDGER_ACTION_RECOMMENDATION_ISSUANCE_UNKNOWN')
    if observed>as_of or observed<stamp(chosen['issued_at']):raise ValueError('LEDGER_ACTION_TIME_INVALID')
    if (observation.get('league_id'),observation.get('season'),observation.get('week'))!=(chosen['league_id'],chosen['season'],chosen['week']):
        raise ValueError('LEDGER_ACTION_TARGET_MISMATCH')
    source=observation['source'];path=(root/source['path']).resolve()
    if not path.is_relative_to(root) or digest(path)!=source['sha256']:raise ValueError('LEDGER_ACTION_SOURCE_HASH_MISMATCH')
    if not isinstance(observation.get('actual_action'),dict):raise ValueError('LEDGER_ACTION_PAYLOAD_MISSING')
    source_value=json.loads(path.read_text(encoding='utf-8'))
    if source_value.get('schema')!='fie-user-action-source-v1' or any(source_value.get(key)!=observation.get(key) for key in ('decision_id','league_id','season','week','observed_at','actual_action')):
        raise ValueError('LEDGER_ACTION_SOURCE_PAYLOAD_MISMATCH')
    return {'schema':'fie-decision-action-observation-v1','decision_id':chosen['decision_id'],
            'decision_source_sha256':chosen['source']['sha256'],'observed_at':observed.isoformat(),
            'league_id':chosen['league_id'],'season':chosen['season'],'week':chosen['week'],
            'source':source,'actual_action':observation['actual_action'],'status':'SOURCE_BOUND_DECLARED_ACTION',
            'quality_classification':'NOT_ASSESSED','transaction_execution':False}


def markdown(report: dict) -> str:
    lines=[f"## Decision ledger — {report['season']} Week {report['week']}",f"{report['decision_count']} durable owner recommendations; **{report['status']}**.",'',report['note'],'',
           '| League | Kind | Decision ID | User action | Outcome |','|---|---|---|---|---|']
    for row in report['decisions']:
        lines.append(f"| {row['league_id']} | {row['kind']} | `{row['decision_id'][:12]}` | NOT_OBSERVED | NOT_OBSERVED |")
    return '\n'.join(lines)+'\n'


def main():
    parser=argparse.ArgumentParser();parser.add_argument('--root',default=str(Path(__file__).resolve().parents[1]))
    parser.add_argument('--season',type=int,required=True);parser.add_argument('--week',type=int,required=True)
    parser.add_argument('--output',type=Path,required=True);args=parser.parse_args();root=Path(args.root).resolve()
    output=args.output.resolve()
    if output.is_relative_to(root/'data/research'):raise ValueError('LEDGER_MUST_NOT_OVERWRITE_OWNER_EVIDENCE')
    report=build(root,args.season,args.week,datetime.now(timezone.utc));output.parent.mkdir(parents=True,exist_ok=True)
    with output.open('x',encoding='utf-8') as stream:stream.write(json.dumps(report,separators=(',',':'),sort_keys=True,allow_nan=False)+'\n')
    with output.with_suffix('.md').open('x',encoding='utf-8') as stream:stream.write(markdown(report))
    print(markdown(report))

if __name__=='__main__':main()
