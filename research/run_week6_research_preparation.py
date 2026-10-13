"""Coordinate additive research preparation with explicit partial/block states."""
from __future__ import annotations
import argparse
import json
from pathlib import Path
from prospective_research_io import binding, clock, encoded, gates, now, replay_response, write
from capture_week6_research_sources import capture, resolve_target, validate_manifest
from prepare_live_waiver_history import prepare
from capture_prospective_waiver import publish
from evaluate_prospective_waiver import evaluate
from waiver_v2_prospective import ROOT
from prepare_weekly_research_context import build as context
from prepare_league_research_evidence import build as league_evidence
from prepare_weekly_report_products import preparation, markdown


def run(root,season,week=None,mode='capture',envelope=None,completed_week=None):
    if completed_week is not None and (mode!='evaluate' or week!=18 or completed_week!=18):
        raise ValueError('LOCAL_CLOSEOUT_REQUIRES_EXPLICIT_WEEK18_COMPLETED18')
    stages=[];started=now()
    def stage(name,fn):
        try:
            value=fn();stages.append({'name':name,'status':'PRODUCED','result':str(value) if isinstance(value,Path) else value});return value
        except (ValueError,KeyError,TypeError,OSError,AssertionError) as error:
            stages.append({'name':name,'status':'BLOCKED','reason':type(error).__name__+':'+str(error)[:500]});return None
    if envelope:
        source=validate_manifest(root,envelope);week=source['week'];season=source['season']
    else:
        week=week or resolve_target(season)
        envelope=stage('raw_sources',lambda:capture(root,season,week))
        source=validate_manifest(root,envelope) if envelope else None
    stamp=clock(started).strftime('%Y%m%dT%H%M%S%fZ')
    base=root/f'data/research/prospective/weekly-preparation/{season}/week_{week:02d}/{stamp}'
    if source and source['responses']:
        from capture_retrospective_auction_history import capture as auction_history
        stage('auction_history',lambda:auction_history(root,season,week,source['league_ids']))
        from scenario_readiness import build as scenario_readiness
        from prepare_weekly_scenario_inputs import build as scenario_inputs
        for name,fn in [('scenario_readiness',lambda:scenario_readiness(root,season=season,week=week,as_of=now())),
                        ('scenario_inputs',lambda:scenario_inputs(root,envelope)),('football_context',lambda:context(root,envelope)),('league_evidence',lambda:league_evidence(root,envelope)),
                        ('seven_report_products',lambda:preparation(root,season,week,now()))]:
            value=stage(name,fn)
            if value is not None:
                write(base/(name+'.json'),value)
                if name=='league_evidence' and mode=='capture':
                    from freeze_specialist_strategy_choices import freeze as freeze_specialists
                    from window2d_context_foundation import parse_schedule_csv
                    schedule_ref=next(r for r in source['responses'] if r['name']=='schedule')
                    games=parse_schedule_csv(replay_response(root,schedule_ref,source['captured_at']),season)
                    target=[g for g in games if g['week']==week]
                    first=min(g['kickoff'] for g in target)
                    stage('specialist_choices',lambda:freeze_specialists(root,base/(name+'.json'),first))
                if name=='seven_report_products':
                    with (base/(name+'.md')).open('x',encoding='utf-8') as f:f.write(markdown(value))
        if mode=='capture' and week<=16:
            history=stage('exact_history',lambda:prepare(root,envelope,root/f'data/research/prospective/waiver-v2/history/{season}/week_{week:02d}/{stamp}'))
            if history:
                lock=root/f'data/research/prospective/waiver-v2/locks/{season}/revision-1/model-lock.json'
                stage('waiver_forecast',lambda:publish(root,envelope,history,lock))
        elif mode=='evaluate':
            history=stage('exact_outcome_history',lambda:prepare(root,envelope,root/f'data/research/prospective/waiver-v2/history/{season}/week_{week:02d}/{stamp}',completed_week=completed_week))
            if history:
                for path in sorted((root/f'data/research/prospective/waiver-v2/forecasts/{season}').glob('week_*/capture.json')):
                    stage('evaluate_'+path.parent.name,lambda p=path:evaluate(root,p,envelope,history))
        if mode=='evaluate':
            from prepare_weekly_model_outcomes import build as weekly_model_outcomes
            owner_review=stage('weekly_model_outcomes',lambda:weekly_model_outcomes(root,season,completed_week or week-1))
            if owner_review:write(base/'weekly_model_outcomes.json',owner_review)
        from prepare_research_readiness_ledger import build as readiness_ledger
        from publish_weekly_research_view import publish as research_view
        canonical=root/f'data/research/prospective/waiver-v2/forecasts/{season}/week_{week:02d}/capture.json'
        ledger=stage('readiness_ledger',lambda:readiness_ledger(root,season,week,canonical))
        if ledger:
            write(base/'readiness_ledger.json',ledger)
            stage('read_only_view',lambda:research_view(root,envelope,canonical,ledger))
    else:
        stages.append({'name':'normalized_research','status':'BLOCKED','reason':'NO_VALID_RAW_RESPONSES'})
    produced=sum(s['status']=='PRODUCED' for s in stages)
    # Reports, calibration and scientific eligibility remain incomplete even
    # when capture mechanics succeed. Do not report a complete research cycle.
    status='PARTIAL' if produced else 'BLOCKED'
    report={'schema':'fie-week6-research-preparation-cycle-v1','season':season,'week':week,'mode':mode,
            'started_at':started,'completed_at':now(),'stages':stages,
            'source_envelope':binding(root,envelope,source['captured_at']) if source else None,
            'operational_readiness':{'status':status,'counts':{'produced_stages':produced,'blocked_stages':len(stages)-produced}},
            **gates(['BLOCKED_PER_PRODUCT_AND_MODEL_VALIDATION_REQUIRED'])}
    path=base/'cycle.json';write(path,report)
    index=root/'.cache/week6-preparation-index.json';index.parent.mkdir(parents=True,exist_ok=True)
    index.write_bytes(encoded({'report_json':path.relative_to(root).as_posix()}))
    return report


def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--root',type=Path,default=ROOT)
    p.add_argument('--season',type=int,default=2026);p.add_argument('--week',type=int)
    p.add_argument('--mode',choices=['capture','evaluate'],default='capture');p.add_argument('--source-envelope',type=Path)
    p.add_argument('--completed-week',type=int,help='Explicit local Week18 closeout only; no scheduled override')
    a=p.parse_args();r=run(a.root,a.season,a.week,a.mode,a.source_envelope,a.completed_week)
    print(json.dumps({'status':r['operational_readiness']['status'],'season':r['season'],'week':r['week'],'stages':len(r['stages'])}))


if __name__=='__main__':main()
