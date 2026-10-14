"""Append exact mature three-week outcomes to immutable research forecasts."""
from __future__ import annotations
import argparse
from datetime import timedelta
import io
import json
from pathlib import Path
import pandas as pd
from prospective_research_io import binding, clock, gates, now, replay_response, sha, verified, write
from capture_week6_research_sources import validate_manifest
from prepare_live_waiver_history import prepare
from waiver_v2_prospective import ROOT, evaluate_rows


def paired_metrics(rows):
    from collections import defaultdict
    from paired_forecast_metrics import metrics
    groups=defaultdict(list)
    for row in rows:groups[(row['scoring_signature'],row['position'])].append(row)
    result=[]
    for (signature,position),cohort in sorted(groups.items()):
        pairs=[{'fie_mean':r['forecast_mean'],'sleeper_mean':r['baseline_mean'],'realized_points':r['realized_mean']} for r in cohort if all(r.get(k) is not None for k in ['forecast_mean','baseline_mean','realized_mean'])]
        raw=metrics(pairs)
        result.append({'scoring_signature':signature,'position':position,'cutoff_rows':len(cohort),
                      'paired_rows':len(pairs),'abstained_rows':sum(r['forecast_mean'] is None for r in cohort),
                      'incomplete_outcome_rows':sum(r['realized_mean'] is None for r in cohort),
                      'model':raw['fie'],'recent_production_baseline':raw['sleeper'],
                      'paired_mae_delta_model_minus_recent_production':raw['paired_mae_delta_fie_minus_sleeper'],
                      'baseline_id':'SAME_CUTOFF_FP_PRIOR_4','sleeper_comparison':False})
    return result


def evaluate(root,capture_path,envelope,history_path,namespace="waiver-v2"):
    if namespace not in {"waiver-v2","waiver-expanded"}:raise ValueError("WAIVER_OUTCOME_NAMESPACE")
    capture=json.loads(capture_path.read_text());source=validate_manifest(root,envelope)
    history=json.loads(history_path.read_text());at=now()
    if capture.get('schema')!='fie-waiver-v2-prospective-capture-v1' or capture['status']!='CAPTURED_RESEARCH':
        raise ValueError('WAIVER_EVALUATE_NOT_FROZEN_FORECAST')
    if source['season']!=capture['season'] or history['season']!=capture['season']:
        raise ValueError('WAIVER_EVALUATE_SEASON_DRIFT')
    for ref in capture['bindings'].values():verified(root,ref,capture['captured_at'])
    expanded=capture.get('scope')=='ADDITIONAL_COMPONENT_SCOPED'
    if expanded!=(namespace=='waiver-expanded') or (history.get('scope')=='ADDITIONAL_COMPONENT_SCOPED')!=expanded:raise ValueError('WAIVER_OUTCOME_SCOPE_DRIFT')
    owner='waiver_v2_expanded_runtime.py' if expanded else 'prepare_live_waiver_history.py'
    if history['builder_sha256']!=sha(Path(__file__).with_name(owner)):
        raise ValueError('WAIVER_OUTCOME_HISTORY_OWNER_DRIFT')
    if verified(root,history['source_envelope'],history['prepared_at']).resolve()!=envelope.resolve():
        raise ValueError('WAIVER_OUTCOME_SOURCE_DRIFT')
    schedule_ref=next(r for r in source['responses'] if r['name']=='schedule')
    games=pd.read_csv(io.BytesIO(replay_response(root,schedule_ref,at)))
    final_week=capture['target_weeks'][-1]
    final_games=games[(games.season==capture['season'])&(games.week==final_week)&games.game_type.eq('REG')]
    if final_games.empty or history['completed_week']<final_week:
        return {'status':'NOT_DUE_FULL_HORIZON','target_weeks':capture['target_weeks']}
    from build_current_snapshot import first_kickoff_utc
    # Six hours is only a minimum elapsed-time guard, never source finality.
    # Actual scoring and the complete PBP game proof remain mandatory below.
    from zoneinfo import ZoneInfo
    starts=[pd.Timestamp(str(r.gameday)+' '+str(r.gametime)).to_pydatetime().replace(tzinfo=ZoneInfo('America/New_York'))
            for r in final_games.itertuples()]
    horizon_end=(max(starts)+timedelta(hours=6)).isoformat()
    if clock(at)<=clock(horizon_end):
        return {'status':'NOT_DUE_LAST_GAME_WINDOW','horizon_end':horizon_end}
    frames=[];coverage=[]
    for profile in history['profiles']:
        rows=pd.read_csv(verified(root,profile['outcomes'],at),low_memory=False)
        ready=set(capture['target_weeks'])<=set(profile['whole_nfl_ready_weeks'])
        coverage.append({'scoring_signature':profile['scoring_signature'],'complete_game_proof':ready,
                         'source_blockers':profile['zero_proof_blockers']})
        if ready:
            rows['scoring_signature']=profile['scoring_signature'];frames.append(rows)
    outcomes=pd.concat(frames,ignore_index=True) if frames else pd.DataFrame(columns=[
        'canonical_player_id','season','week','scoring_signature','fantasy_points_exact','outcome_complete','exact_scoring'])
    evaluated=evaluate_rows(capture['forecasts'],outcomes,observed_at=at,horizon_end=horizon_end)
    complete=sum(r['realized_mean'] is not None for r in evaluated)
    metrics=paired_metrics(evaluated)
    report={'schema':'fie-waiver-v2-prospective-evaluation-v1','season':capture['season'],'week':capture['week'],
            'target_weeks':capture['target_weeks'],'outcome_observed_at':at,'rows':evaluated,'coverage':coverage,
            'complete_rows':complete,'total_cutoff_rows':len(evaluated),'total_forecast_rows':len(evaluated),'paired_metrics':metrics,
            'status':('EVALUATED_EXACT_COHORT' if complete==len(evaluated) and complete else 'PARTIAL_EXACT_OUTCOME_COVERAGE' if complete else 'BLOCKED_EXACT_OUTCOME_COVERAGE'),
            'bindings':{'capture':binding(root,capture_path,capture['captured_at']),
                        'outcome_source':binding(root,envelope,source['captured_at']),
                        'history':binding(root,history_path,history['prepared_at'])},
            'independent_temporal_unit':'same-season three-week horizon; overlapping starts share outcomes',
            **gates(['BLOCKED_SAMPLE_AND_TEMPORAL_REVIEW','BLOCKED_PROMOTION_REVIEW_REQUIRED'])}
    revision=clock(at).strftime('%Y%m%dT%H%M%S%fZ')
    path=root/f"data/research/prospective/{namespace}/outcomes/{capture['season']}/week_{capture['week']:02d}/{revision}/evaluation.json"
    write(path,report)
    return {'status':report['status'],'path':str(path),'complete_rows':complete}


def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--root',type=Path,default=ROOT)
    p.add_argument('--source-envelope',type=Path,required=True);p.add_argument('--completed-week',type=int);a=p.parse_args()
    source=validate_manifest(a.root,a.source_envelope)
    stamp=clock(now()).strftime('%Y%m%dT%H%M%S%fZ')
    path=a.root/f"data/research/prospective/waiver-v2/history/{source['season']}/week_{source['week']:02d}/{stamp}"
    history=prepare(a.root,a.source_envelope,path,a.completed_week)
    results=[]
    for capture in sorted((a.root/f"data/research/prospective/waiver-v2/forecasts/{source['season']}").glob('week_*/capture.json')):
        results.append(evaluate(a.root,capture,a.source_envelope,history))
    print(json.dumps({'evaluations':results,'research_only':True}))


if __name__=='__main__':main()
