"""Exact target isolation, missingness, source tampering and no promotion."""
from pathlib import Path
from tempfile import TemporaryDirectory
import json
import pandas as pd
import random
from build_waiver_v2_label_batch import build, digest, label_frame
from run_waiver_v2_historical_ledger import run as run_history
from run_waiver_v2_profile_batch import run_batch


def reject(action):
    try:action()
    except ValueError:return
    raise AssertionError('Invalid label source accepted')


def main():
    frame=pd.DataFrame([{'canonical_player_id':'p','season':year,'week':week,
                        'position_model':'WR','scoring_signature':'sig','exact_scoring':True,
                        'outcome_complete':True,'fantasy_points_exact':float(week),'outcome_status':'COMPLETE_EXACT'}
                       for year in (2024,2025) for week in (1,2,3,4,18)])
    labelled=label_frame(frame,'sig',[2024,2025])
    assert labelled.loc[0,'fp_next3_weeks_exact']==3
    assert not labelled.loc[4,'fp_next1_weeks_full_horizon']
    partial=frame.copy();partial.loc[1,'outcome_complete']=False
    assert not label_frame(partial,'sig',[2024,2025]).loc[0,'fp_next3_weeks_full_horizon']
    reject(lambda:label_frame(frame,'other',[2024,2025]))
    reject(lambda:label_frame(frame,'sig',[2025]))
    reject(lambda:label_frame(pd.concat([frame,frame]),'sig',[2024,2025]))
    changed=frame.copy();changed.loc[0,'exact_scoring']=False
    reject(lambda:label_frame(changed,'sig',[2024,2025]))
    rng=random.Random(71)
    records=[{'canonical_player_id':str(player),'season':year,'week':week,
              'position_model':'WR','scoring_signature':'sig','exact_scoring':True,
              'outcome_complete':rng.random()>.2,'fantasy_points_exact':rng.randint(-3,22)}
             for player in range(4) for year in (2024,2025) for week in range(1,19) if rng.random()>.12]
    rng.shuffle(records);sparse=pd.DataFrame(records);fast=label_frame(sparse,'sig',[2024,2025])
    lookup={(r['canonical_player_id'],r['season'],r['week']):r for r in records}
    for i,row in enumerate(records):
        for horizon in (1,2,3):
            future=[lookup.get((row['canonical_player_id'],row['season'],row['week']+offset)) for offset in range(1,horizon+1)]
            complete=[r for r in future if r and r['outcome_complete']]
            assert fast.loc[i,f'fp_next{horizon}_weeks_complete_count']==len(complete)
            if len(complete)==horizon:
                assert fast.loc[i,f'fp_next{horizon}_weeks_exact']==sum(r['fantasy_points_exact'] for r in complete)/horizon
            else:assert pd.isna(fast.loc[i,f'fp_next{horizon}_weeks_exact'])
    with TemporaryDirectory() as td:
        root=Path(td);ledger=root/'ledger.csv';frame.to_csv(ledger,index=False)
        before=ledger.read_bytes()
        reject(lambda:run_history(seasons=[2025],cache_dir=root/'unused-cache',scoring_path=root/'unused',output_dir=root,player_stats_complete=False))
        reject(lambda:run_batch(seasons=[2025],cache_dir=root/'unused-cache',profiles_root=root/'unused',portfolio_overview=None,output_dir=root,player_stats_complete=False))
        assert ledger.read_bytes()==before and not (root/'unused-cache').exists()
        profile={'scoring_signature':'sig','ledger':{'path':str(ledger),'sha256':digest(ledger),
                 'rows':10,'complete_exact_rows':10,'incomplete_rows':0},
                 'inventories':{p:{'exact_replay_eligible':True,'blocked_keys':[]} for p in ('QB','RB','WR','TE')}}
        path=root/'profile.json';path.write_text(json.dumps(profile))
        batch={'schema':'fie-waiver-v2-profile-batch-v1','requested_seasons':[2024,2025],
               'league_count':1,'profiles':[{'scoring_signature':'sig','league_ids':['one'],
                                           'outcome_report':{'path':str(path)}}]}
        source=root/'batch.json';source.write_text(json.dumps(batch))
        report=build(source,root/'labels');entry=report['profiles'][0]
        assert entry['complete_target_counts']['3']==2 and not entry['forecast_eligible']
        assert report['activation_eligible'] is False and entry['forecast_status']=='BLOCKED_MODEL_VALIDATION_REQUIRED'
        assert entry['model_validation_capacity']['WR']['maximum_possible_outer_holdouts']==0
        reject(lambda:build(source,root/'labels'))
        ledger.write_text('changed')
        reject(lambda:build(source,root/'tampered'))
        assert not (root/'tampered').exists()
    print('PASS exact label batch: source hashes, signature/season isolation, complete horizons, missingness and no activation')


if __name__=='__main__':main()
