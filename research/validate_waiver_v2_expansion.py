"""Read-only replay of additional source scope, scoring, models and captures."""
from __future__ import annotations
import argparse,gzip,hashlib,json,re
from pathlib import Path
import numpy as np,pandas as pd
from prospective_research_io import verified,sha,clock,gates
from archive_waiver_expansion_sources import BASE
from build_waiver_v2_expansion import methodology
from build_waiver_v2_label_batch import label_frame
from waiver_v2_validation import features,evaluate,select,fit,KEYS,TARGET,FULL
from validate_waiver_v2_validation import equivalent

ROOT=Path(__file__).resolve().parents[1]
def validate(root,full=True,unit_key=None,replay_models=True):
    from waiver_v2_expanded_runtime import load_lock,validate_capture
    lock,_=load_lock(root);contract=methodology(root);at=lock['frozen_at']
    receipts=json.loads(verified(root,lock['inputs']['source_receipts'],at).read_text())
    for ref in receipts['pbp_sources']+receipts['raw_player_stats']+receipts['scoring_scope']+[receipts['games'],receipts['field_goal_return_audit']]:
        path=verified(root,ref,at)
        if path.suffix=='.gz':
            with gzip.open(path,'rb') as check:
                while check.read(1024*1024):pass
        if 'raw_sha256' in ref and hashlib.sha256(gzip.decompress(path.read_bytes())).hexdigest()!=ref['raw_sha256']:raise ValueError('EXPANDED_RAW_HASH')
    for ref in receipts['scoring_scope']:
        payload=json.loads(gzip.decompress((root/ref['path']).read_bytes()))
        detected=[{'player_id':row['player_id'],'fg_ret_yd':float(row['stats']['fg_ret_yd'])} for row in payload if row.get('stats',{}).get('fg_ret_yd')]
        equivalent(detected,ref['nonzero_fg_ret_yd'])
        if any(not re.fullmatch('[A-Z]{2,3}',x['player_id']) for x in detected):raise ValueError('EXPANDED_FG_OFFENSIVE_COUNTEREXAMPLE')
    stats=pd.read_csv(verified(root,lock['inputs']['stats'],at),low_memory=False);source_args=None;published=None;profile_data={}
    if full and unit_key is None:
        from waiver_v2_scoped_sources import component_sources,profile_outcomes
        read=lambda key:pd.read_csv(verified(root,lock['inputs'][key],at),low_memory=False)
        pbp=pd.concat([read(k) for k in sorted(lock['inputs']) if k.startswith('pbp_')],ignore_index=True,sort=False)
        scope=json.loads(verified(root,lock['inputs']['scope'],at).read_text());report=json.loads(verified(root,lock['inputs']['event_report'],at).read_text())
        weekly,support,excluded=component_sources(pbp,stats,read('events'),report,scope['raw_blockers'],read('reconciliation_stats'))
        pd.testing.assert_frame_equal(weekly,read('scoped_weekly'),check_dtype=False,check_exact=False,rtol=1e-10,atol=1e-10)
        equivalent(support,scope['effective_support']);equivalent(excluded,scope['exclusions'])
        games=read('games');games=games[games.season.isin(contract['seasons'])&games.game_type.eq('REG')]
        source_args=(pbp,stats,read('roster'),games,read('identity'),weekly,support,excluded)
        published=stats.drop(columns='position_model').merge(weekly,on=KEYS,how='left',validate='one_to_one')
        fg=[];mask=pbp.season_type.eq('REG')&pbp.desc.str.contains('field goal',case=False,na=False)&pbp.desc.str.contains('No Good',case=False,na=False)&pbp.desc.str.contains('for [0-9]+ yards',case=False,na=False)&~pbp.desc.str.contains('BLOCKED',case=False,na=False)
        for r in pbp[mask].itertuples(index=False):fg.append({'season':int(r.season),'week':int(r.week),'game_id':r.game_id,'play_id':r.play_id,'description':r.desc,'description_yards':int(re.findall(r'for (\d+) yards',r.desc,re.I)[-1]),'structured_return_yards':r.return_yards})
        audit=json.loads(verified(root,receipts['field_goal_return_audit'],at).read_text());equivalent(fg,audit['events'])
        if audit['event_count']!=len(fg) or audit['description_yards']!=sum(r['description_yards'] for r in fg):raise ValueError('EXPANDED_FG_COUNT_DRIFT')
    game_last=pd.read_csv(verified(root,lock['inputs']['games'],at),low_memory=False);game_last=game_last[game_last.game_type.eq('REG')].groupby('season').week.max()
    for p in lock['profiles']:
        if unit_key and p['scoring_signature']!=unit_key.split(':')[0]:continue
        art=p['artifacts'];outcomes=pd.read_csv(verified(root,art['outcomes'],at),low_memory=False);labels=pd.read_csv(verified(root,art['labels'],at),low_memory=False)
        expected=label_frame(outcomes,p['scoring_signature'],contract['seasons'])
        pd.testing.assert_frame_equal(labels,expected,check_dtype=False,check_exact=False,rtol=1e-10,atol=1e-10)
        if source_args is not None:
            from waiver_v2_scoped_sources import profile_outcomes
            from waiver_v2_outcomes import _score_exact_row
            scoring=json.loads(verified(root,art['scoring'],at).read_text())['scoring_settings'];rebuilt,_,_=profile_outcomes(*source_args,scoring)
            cols=KEYS+['position_model','team','outcome_complete','exact_scoring','fantasy_points_exact','target_only_row']
            pd.testing.assert_frame_equal(outcomes[cols],rebuilt[cols],check_dtype=False,check_exact=False,rtol=1e-10,atol=1e-10)
            complete=rebuilt[rebuilt.outcome_complete&rebuilt.outcome_status.isin(['COMPLETE_EXACT','COMPLETE_PUBLISHED_SOURCE_WITHOUT_ROSTER'])]
            check=complete[KEYS+['position_model','fantasy_points_exact']].merge(published,on=KEYS,how='left',validate='one_to_one')
            scalar=check.apply(lambda r:_score_exact_row(r,scoring,str(r.position_model)),axis=1).to_numpy(float)
            if not np.allclose(scalar,check.fantasy_points_exact,rtol=1e-10,atol=1e-10,equal_nan=True):raise ValueError('EXPANDED_ORIGINAL_SCORING_OWNER_PARITY')
            print('EXPANDED_SOURCE_REPLAY',p['scoring_signature'],flush=True)
        profile_data[p['scoring_signature']]=(outcomes,labels)
    count=0;cache={}
    for u in lock['units']:
        if unit_key and (u['scoring_signature']+':'+u['position'])!=unit_key:continue
        f=pd.read_csv(verified(root,u['features'],at),low_memory=False);pred=pd.read_csv(verified(root,u['predictions'],at),low_memory=False);folds=json.loads(verified(root,u['folds'],at).read_text())
        outcomes,labels=profile_data[u['scoring_signature']];expected=features(outcomes,stats,u['position'],contract)
        valid=outcomes[~outcomes.target_only_row.fillna(False).astype(bool)&outcomes.position_model.eq(u['position'])&(outcomes.week+3<=outcomes.season.map(game_last))]
        if set(map(tuple,f[KEYS].to_numpy()))!=set(map(tuple,valid[KEYS].to_numpy())):raise ValueError('EXPANDED_CUTOFF_POPULATION_DRIFT')
        expected=expected[pd.MultiIndex.from_frame(expected[KEYS]).isin(pd.MultiIndex.from_frame(f[KEYS]))].reset_index(drop=True)
        pd.testing.assert_frame_equal(f,expected,check_dtype=False,check_exact=False,rtol=1e-10,atol=1e-10)
        if full and replay_models:
            pair=f.merge(labels[KEYS+[TARGET,FULL]],on=KEYS,how='left',validate='one_to_one');pair['label_complete']=pair[FULL].fillna(False).astype(bool)
            key=hashlib.sha256(pd.util.hash_pandas_object(pair.drop(columns='scoring_signature'),index=False).values.tobytes()).hexdigest()
            if key not in cache:
                metrics,expected_pred,expected_folds=evaluate(f,labels,contract);choice,audit=select(pair,contract);model=fit(pair,choice,contract) if choice else None
                cache[key]=(metrics,expected_pred,expected_folds,model,audit)
            metrics,expected_pred,expected_folds,model,audit=cache[key]
            equivalent(u['metrics'],metrics);equivalent(folds,expected_folds);equivalent(u['model'],model);equivalent(u['selection_audit'],audit)
            expected_pred=expected_pred.copy();expected_pred['scoring_signature']=u['scoring_signature']
            pd.testing.assert_frame_equal(pred,expected_pred,check_dtype=False,check_exact=False,rtol=1e-10,atol=1e-10)
            print('EXPANDED_MODEL_REPLAY',u['scoring_signature'],u['position'],flush=True)
        count+=1
    if unit_key and count!=1:raise ValueError('EXPANDED_REPLAY_UNIT_UNKNOWN')
    captures=0
    for path in sorted((root/'data/research/prospective/waiver-expanded/forecasts').glob('*/week_*/capture.json')):
        validate_capture(root,json.loads(path.read_text()));captures+=1
    value={'status':'PASS_EXPANDED_REPLAY','units':count,'captures':captures,'full_model_replay':full and replay_models,'full_source_replay':source_args is not None,'network_requests':0}
    print(json.dumps(value));return value
if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--root',type=Path,default=ROOT);p.add_argument('--structure-only',action='store_true');p.add_argument('--sources-only',action='store_true');p.add_argument('--unit',help='signature:position, for bounded independent model replay');a=p.parse_args();validate(a.root,not a.structure_only,a.unit,not a.sources_only)
