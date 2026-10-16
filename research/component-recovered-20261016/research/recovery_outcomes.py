"""Rebuild source-bound C1 outcomes and the C2 target view for any completed week."""
import argparse,collections,gzip,json
from pathlib import Path
import numpy as np
import pandas as pd
from recovery_common import *
from issue_component_forecasts import snapshot
from component_registry import build
from build_component_outcomes import normalize_population,apply_components,identity_bridge,provider_frame,regular,csv,KEYS,CALENDAR_EXCEPTIONS
from component_training_view import build_year,EXTRA
from component_source_contract import PLAYER_FIELDS,position,team
from waiver_v2_event_ledger import build_e5_event_ledger
from waiver_v2_source_adapter import normalize_player_stats
from waiver_v2_scoped_sources import component_sources
def csv(frame,path):
    import io
    stream=io.StringIO(newline='');frame.to_csv(stream,index=False,float_format='%.10g');atomic_bytes(path,gzip.compress(stream.getvalue().encode(),mtime=0))

def build_actual(output,week,bundle_path=None,provider_ref=None,root=ROOT):
    if not 1<=week<=18:raise ValueError('INVALID_ACTUAL_WEEK')
    out=root/output
    if out.exists() and any(out.iterdir()):raise ValueError('NEW_ACTUAL_REVISION_REQUIRED')
    out.mkdir(parents=True,exist_ok=True)
    bundle_path=Path(bundle_path or JOINT/'observations/observation-bundle.json');bundle=read(root/bundle_path);refs={r['name']:r for r in bundle['responses']}
    data={n:snapshot(root,refs[n],bundle['observation_cutoff']) for n in ['players','ff_playerids','weekly_rosters','player_week','schedule','pbp','sleeper_players']}
    raw=regular(data['player_week'],week);pbp=regular(data['pbp'],week);games=data['schedule']
    selected=games[games.season.eq(2026)&games.game_type.eq('REG')&games.week.eq(week)]
    if selected.empty or selected[['home_score','away_score']].isna().any().any():raise ValueError('WEEK_NOT_COMPLETE')
    if provider_ref is None:
        if 'sleeper_actual' in refs:
            r=refs['sleeper_actual']
            if r.get('actual_week',bundle.get('actual_week'))!=week:raise ValueError('ACTUAL_PROVIDER_WEEK_MISMATCH')
            provider_ref={**r,'season':2026,'week':week}
        else:
            manifest=read(root/'data/research/components/2026-10-14/c0-c1-v1/sources/manifest.json')
            provider_ref=next((r for r in manifest['sources'] if r['season']==2026 and r['week']==week),None)
            if provider_ref is None:raise ValueError('CAPTURE_ACTUAL_PROVIDER_WEEK_FIRST')
    verified(root,provider_ref)
    bridge=identity_bridge(data['players'],data['ff_playerids'],data['sleeper_players'],[data['weekly_rosters']])
    provider,_=provider_frame(root,[provider_ref],bridge)
    demand=build(root);scratch=out/'events';scratch.mkdir()
    ids=sorted(set(raw.player_id.dropna().astype(str)));identity=pd.DataFrame({'gsis_id':[i for i in ids if __import__('re').fullmatch(r'00-\d{7}',i)]});identity['canonical_player_id']=identity.gsis_id
    allstats,_=normalize_player_stats(raw,identity,offensive_only=False);stats=allstats[allstats.position_model.isin(['QB','RB','WR','TE'])]
    for name,frame in [('identity',identity),('all-stats',allstats),('offense-stats',stats),('pbp',pbp)]:csv(frame,scratch/(name+'.csv.gz'))
    report=build_e5_event_ledger(raw_pbp_path=scratch/'pbp.csv.gz',identity_path=scratch/'identity.csv.gz',canonical_player_stats_path=scratch/'offense-stats.csv.gz',canonical_return_stats_path=scratch/'all-stats.csv.gz',requested_seasons=[2026],pbp_source_items=[{**refs['pbp'],'season':2026,'url':refs['pbp']['endpoint']}],output_path=scratch/'events.csv.gz',weekly_stats_output_path=scratch/'weekly.csv.gz',report_path=scratch/'report.json')
    blockers=[json.loads(s) for s in (scratch/Path(report['blockers']['path']).name).read_text().splitlines() if s]
    event_weekly,support,excluded=component_sources(pbp,stats,pd.read_csv(scratch/'events.csv.gz',low_memory=False),report,blockers,allstats)
    population,cal,audit=normalize_population(raw,data['weekly_rosters'],games,2026,week)
    clubs=sorted(set(cal.team));dense=pd.DataFrame([(2026,w,club) for w in range(1,week+1) for club in clubs],columns=['season','week','team']);teams=dense.merge(cal,on=['season','week','team'],how='left',validate='one_to_one')
    teams['canonical_player_id']='TEAM:'+teams.team;teams['position_model']='DEF';teams['game_id']=teams.pop('calendar_game_id');complete=set(cal.groupby('week').game_complete.all().loc[lambda s:s].index)
    teams['week_state']=np.select([teams.game_complete.eq(True),teams.game_id.isna()&teams.week.isin(complete)],['COMPLETED_GAME','PROVEN_BYE'],default='UNKNOWN_GAME_OR_TEAM');teams['published_stat_row']=False
    population=pd.concat([population,teams],ignore_index=True,sort=False)
    c1,coverage,mismatch=apply_components(population,demand,event_weekly,provider)
    c1=c1.sort_values(['season','week','canonical_player_id']).reset_index(drop=True)
    components=sorted({c['component'] for c in demand['required_components']}|set(EXTRA)|set(PLAYER_FIELDS));rulekeys=collections.defaultdict(list)
    for r in demand['rules']:
        if r['scoring_key'] not in rulekeys[r['component']]:rulekeys[r['component']].append(r['scoring_key'])
    frame,game_audit,certificates,target_support=build_year(c1,raw,pbp,games[games.season.eq(2026)&games.game_type.eq('REG')&games.week.le(week)],provider,components,rulekeys)
    for name,f in [('c1-outcomes',c1),('training-2026',frame),('game-audit',game_audit),('absence-certificates',certificates),('target-support',target_support)]:csv(f,out/(name+'.csv.gz'))
    target=frame[frame.week.eq(week)]
    actual=[]
    for x in target.to_dict('records'):
        values={k:float(x[k]) for k in components if k in x and pd.notna(x[k]) and np.isfinite(x[k])};basis={k:str(x.get(k+'__basis','UNKNOWN')) for k in values}
        actual.append({'canonical_player_id':x['canonical_player_id'],'season':2026,'week':week,'position_model':x['position_model'],'game_id':x.get('game_id') if pd.notna(x.get('game_id')) else None,'components':values,'basis':basis,'week_state':x['week_state']})
    lines(out/'actual-components.jsonl.gz',actual)
    receipt={'schema':'fie-component-actual-revision-v2','built_at':now(),'season':2026,'week':week,'rows':len(actual),'bundle_path':bundle_path.as_posix(),'bundle_sha256':sha(root/bundle_path),'provider_source':provider_ref,'artifacts':closure(out,root),'unknowns_preserved':True,'provider_exact_certified':False,'population_audit':audit,'source_mismatches':len(mismatch),'research_only':True}
    write(out/'actual-receipt.json',receipt);print('ACTUAL_READY',week,len(actual),flush=True);return receipt
def update_training(actual_dir,output,previous=TRAINING,root=ROOT):
    actual=root/actual_dir;receipt=read(actual/'actual-receipt.json')
    for rel,h in receipt['artifacts'].items():
        if sha(root/rel)!=h:raise ValueError('ACTUAL_ARTIFACT_DRIFT')
    target=pd.read_csv(actual/'training-2026.csv.gz',low_memory=False);old=pd.read_csv(root/previous/'training-2026.csv.gz',low_memory=False)
    # The new complete source reconstruction replaces only its covered weeks.
    limit=receipt['week'];merged=pd.concat([old[old.week.gt(limit)],target],ignore_index=True).sort_values(KEYS)
    if merged.duplicated(KEYS).any() or merged.week.max()>limit:raise ValueError('TRAINING_DUPLICATE_OR_FUTURE_ROWS')
    out=root/output
    if out.exists() and any(out.iterdir()):raise ValueError('NEW_TRAINING_REVISION_REQUIRED')
    out.mkdir(parents=True,exist_ok=True);csv(merged,out/'training-2026.csv.gz')
    write(out/'training-view.json',{'through_week':limit,'actual_receipt_sha256':sha(actual/'actual-receipt.json'),'training_sha256':sha(out/'training-2026.csv.gz'),'rows':len(merged),'historical_training_preserved':True});return out
if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--output',type=Path,required=True);p.add_argument('--week',type=int,required=True);p.add_argument('--bundle',type=Path);p.add_argument('--training-output',type=Path);a=p.parse_args();build_actual(a.output,a.week,a.bundle)
    if a.training_output:update_training(a.output,a.training_output)
