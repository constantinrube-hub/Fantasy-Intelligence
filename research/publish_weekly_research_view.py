"""Replaceable compact pointer; immutable source observations remain first-write."""
import json
from prospective_research_io import binding,clock,encoded,gates,now,replay_response,verified
from capture_week6_research_sources import validate_manifest
from build_waiver_v2_outcome_ledger import scoring_signature


def validate(value,root=None):
    if value.get('schema')!='fie-weekly-research-view-v1' or value.get('pointer_replaceable') is not True:raise ValueError('RESEARCH_VIEW_SCHEMA')
    season,week=value['season'],value['week']
    if not 2<=week<=16 or value['target_weeks']!=list(range(week,week+3)):raise ValueError('RESEARCH_VIEW_HORIZON')
    if any(value.get(k) is not False for k in gates([]) if k.endswith('_eligible')):raise ValueError('RESEARCH_VIEW_AUTHORITY')
    at=clock(value['generated_at']);seen=set()
    for ref in value['bindings'].values():
        if clock(ref['observed_at'])>at:raise ValueError('RESEARCH_VIEW_FUTURE_SOURCE')
        if root:verified(root,ref,value['generated_at'])
    for league in value['leagues']:
        if league['league_id'] in seen or not str(league['league_id']).isdigit():raise ValueError('RESEARCH_VIEW_LEAGUE_DUPLICATE')
        seen.add(league['league_id'])
        if (league['season'],league['week'])!=(season,week) or any(league.get(k) is not False for k in gates([]) if k.endswith('_eligible')):raise ValueError('RESEARCH_VIEW_CONTEXT_OR_AUTHORITY')
        if clock(league['observed_at'])>at:raise ValueError('RESEARCH_VIEW_FUTURE_LEAGUE')
        ids=set()
        for row in league['forecasts']:
            key=(row['canonical_player_id'],row['position'])
            if key in ids:raise ValueError('RESEARCH_VIEW_FORECAST_DUPLICATE')
            ids.add(key)
            from strict_sleeper_baseline import finite
            if any(row[k] is not None and finite(row[k]) is None for k in ['forecast_mean','baseline_mean']):raise ValueError('RESEARCH_VIEW_NONFINITE')
            if row.get('confidence') is not None:raise ValueError('RESEARCH_VIEW_SYNTHETIC_CONFIDENCE')
    return value


def publish(root,envelope,capture_path=None,readiness=None):
    source=validate_manifest(root,envelope);at=now();capture=None
    refs={'source_envelope':binding(root,envelope,source['captured_at'])}
    if capture_path and capture_path.is_file():
        capture=json.loads(capture_path.read_text())
        if capture.get('schema')!='fie-waiver-v2-prospective-capture-v1' or (capture['season'],capture['week'])!=(source['season'],source['week']):raise ValueError('RESEARCH_VIEW_CAPTURE_CONTEXT')
        if any(capture.get(k) is not False for k in gates([]) if k.endswith('_eligible')):raise ValueError('RESEARCH_VIEW_CAPTURE_AUTHORITY')
        for ref in capture['bindings'].values():verified(root,ref,capture['captured_at'])
        refs['capture']=binding(root,capture_path,capture['captured_at'])
    leagues=[]
    for lid in source['league_ids']:
        items=[r for r in source['responses'] if r.get('league_id')==lid and r.get('role')=='profile']
        if len(items)!=1:continue
        profile=json.loads(replay_response(root,items[0],source['captured_at']))
        if str(profile.get('season'))!=str(source['season']):continue
        signature=scoring_signature(profile['scoring_settings'])
        rows=[{'canonical_player_id':r['canonical_player_id'],'position':r['position'],
               'forecast_mean':r['forecast_mean'],'baseline_mean':r['baseline_mean'],'confidence':None,
               'status':r['status']} for r in (capture or {}).get('forecasts',[]) if r['scoring_signature']==signature]
        units=[u for u in (readiness or {}).get('units',[]) if u['scoring_signature']==signature]
        leagues.append({'league_id':lid,'scoring_signature':signature,'season':source['season'],'week':source['week'],
                        'observed_at':items[0]['observed_at'],'status':capture['status'] if rows else 'BLOCKED_NO_SUPPORTED_CAPTURE',
                        'forecast_observed_at':capture['captured_at'] if capture else None,
                        'first_kickoff':capture['first_kickoff'] if capture else None,
                        'forecasts':rows,'readiness_units':units,'baseline_id':'SAME_CUTOFF_FP_PRIOR_4',
                        'sleeper_comparison':False,'actual_adoption':'UNKNOWN',
                        **gates(['BLOCKED_PROSPECTIVE_CONFIRMATION_AND_PROMOTION'])})
    value={'schema':'fie-weekly-research-view-v1','season':source['season'],'week':source['week'],
           'target_weeks':list(range(source['week'],source['week']+3)),'generated_at':at,'pointer_replaceable':True,
           'bindings':refs,'leagues':leagues,**gates(['BLOCKED_RESEARCH_ONLY_VIEW'])}
    validate(value,root)
    path=root/f"data/research/prospective/weekly-research-view/{source['season']}/week_{source['week']:02d}.json"
    path.parent.mkdir(parents=True,exist_ok=True);path.write_bytes(encoded(value))
    return {'path':str(path),'league_count':len(leagues),'forecast_rows':sum(len(l['forecasts']) for l in leagues)}
