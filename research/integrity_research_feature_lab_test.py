"""Research data leakage, units, identities, missingness and source integrity."""
from copy import deepcopy
import json
from pathlib import Path
import tempfile

from research_source_archive import archive, read
from research_feature_tables import pbp_tables, snap_table, role_changes
from research_experiment_runner import run
from research_strategy_replay import replay
from research_rest_context import rest_features


def rejects(action):
    try:
        action()
    except (ValueError,AssertionError):
        return
    raise AssertionError('invalid input accepted')


def main():
    play={'season':'2026','week':'1','season_type':'REG','game_id':'g','play_id':'1','posteam':'A',
          'no_play':'0','pass_attempt':'0','rush_attempt':'1','fixed_drive':'1','yardline_100':'4',
          'qtr':'1','score_differential':'0','epa':'1','success':'1','yards_gained':'4',
          'first_down':'1','touchdown':'1','rusher_player_id':'00-a','drive_start_transition':'KICKOFF'}
    future={**play,'week':'2','play_id':'2'}
    report=pbp_tables([play,future],2026,2)
    provider_variant={**play,'play_type':'run'}
    del provider_variant['no_play']
    assert pbp_tables([provider_variant],2026,2)['team_games'][0]['scrimmage_plays']==1
    assert report['excluded_rows']['TARGET_OR_FUTURE_WEEK']==1
    assert report['team_games'][0]['epa_per_observed_play']==1
    assert report['red_zone_players'][0]['metrics']['goal_line_carries']==1
    assert report['red_zone_players'][0]['canonical_player_id'] is None
    missing={**play,'yards_gained':'','epa':'','drive_start_transition':''}
    partial=pbp_tables([missing],2026,2)
    assert partial['drive_scrimmage_summaries'][0]['scrimmage_yards'] is None
    assert partial['team_games'][0]['epa_per_observed_play'] is None
    pick_six={**play,'td_team':'B'}
    assert pbp_tables([pick_six],2026,2)['drive_scrimmage_summaries'][0]['offensive_touchdown_observed'] is False
    assert pbp_tables([play],2026,2)['drive_scrimmage_summaries'][0]['offensive_touchdown_observed'] is None
    rejects(lambda:pbp_tables([play,play],2026,2))
    snap={'season':'2026','week':'1','game_type':'REG','game_id':'g','team':'A','pfr_player_id':'P1',
          'offense_snaps':'20','offense_pct':'0.5'}
    parsed=snap_table([snap],2026,2)['rows'][0]
    assert parsed['offense_pct_provider_units']==0.5 and parsed['offense_snap_share'] is None
    assert parsed['defense_snaps'] is None
    rejects(lambda:snap_table([snap,snap],2026,2))
    history=[{'season':2026,'week':i,'game_id':str(i),'team':'A','source_gsis_player_id':'gsis:a',
              'metric':'target_share','numerator':1 if i<4 else 4,'denominator':10,
              'observed_at':'2026-10-01T00:00:00Z'} for i in range(1,6)]
    role=role_changes(history,target_week=6,cutoff='2026-10-02T00:00:00Z')[0]
    assert round(role['delta'],6)==0.3 and role['same_direction_recent_games']
    history[-1]['team']='B'
    assert role_changes(history,target_week=6,cutoff='2026-10-02T00:00:00Z')[0]['status']=='BLOCKED_TEAM_CHANGE'
    history[-1]['observed_at']='2026-10-03T00:00:00Z'
    assert role_changes(history,target_week=6,cutoff='2026-10-02T00:00:00Z')[0]['delta'] is None
    with tempfile.TemporaryDirectory() as td:
        root=Path(td)
        raw=b'game_id,season,week,pfr_player_id,team,offense_snaps\ng,2026,1,a,A,20\n'
        receipt=archive(root,'snaps',2026,raw,'2026-10-01T00:00:00Z')
        rows,ref=read(root,receipt,kind='snaps',season=2026,cutoff='2026-10-02T00:00:00Z')
        assert len(rows)==1
        rejects(lambda:read(root,receipt,kind='snaps',season=2026,cutoff='2026-09-30T00:00:00Z'))
        (root/'config').mkdir()
        (root/'config/roadmap-research-registry.json').write_text(json.dumps({'experiments':[{'research_id':'P2_USAGE'}]}))
        protocol={'schema':'fie-research-ablation-protocol-v1','research_id':'P2_USAGE','production_authorized':False,
                  'metric':'paired_absolute_error','evaluation_mode':'PROSPECTIVE_SHADOW',
                  'registered_at':'2026-10-01T00:00:00Z','training_cutoff':'2026-09-30T00:00:00Z',
                  'evaluation_start':'2026-10-01T01:00:00Z','evidence':[{'path':ref['raw_path'],
                  'sha256':ref['raw_sha256'],'observed_at':ref['observed_at']}]}
        row={'season':2026,'week':2,'league_id':'1','canonical_player_id':'gsis:a','scoring_signature':'s',
             'exact_scoring':True,'baseline_mean':10,'candidate_mean':12,'realized_points':11,
             'forecast_at':'2026-10-01T02:00:00Z','kickoff':'2026-10-02T00:00:00Z',
             'outcome_observed_at':'2026-10-03T00:00:00Z'}
        assert run(root,protocol,[row])['slices'][0]['paired_mae_delta_candidate_minus_baseline']==0
        row['forecast_at']=row['kickoff']
        assert run(root,protocol,[row])['accepted_rows']==0
        (root/ref['raw_path']).write_bytes(raw+b'changed')
        rejects(lambda:read(root,receipt,kind='snaps',season=2026,cutoff='2026-10-02T00:00:00Z'))
        rejects(lambda:run(root,protocol,[row]))
    week={'season':2026,'week':1,'league_id':'l','prospective_universe_bound':True,'exact_scoring':True,
          'candidates':[{'canonical_player_id':sid,'position':'DST','available':True,'bye':False,'mean':value,
                         'realized_points':points} for sid,value,points in [('a',1,10),('b',2,0)]]}
    result=replay([week],held_player_id='a',position='DST')[0]
    assert result['strategies']['FULL_HOLD']['realized_points']==10
    assert result['strategies']['FULL_STREAM']['realized_points']==0
    assert result['selected_hold_status'].startswith('BLOCKED')
    games=[{'season':2026,'week':i,'game_id':str(i),'home_team':'B','away_team':'A',
            'kickoff':f'2026-10-0{i}T12:00:00Z'} for i in (1,2)]
    rest=rest_features(games,season=2026,target_week=2,observed_at='2026-10-01T13:00:00Z',cutoff='2026-10-02T01:00:00Z')
    assert rest[0]['kickoff_gap_hours']==24 and rest[0]['consecutive_away_games']==2
    rejects(lambda:rest_features(games,season=2026,target_week=2,observed_at='2026-10-03T00:00:00Z',cutoff='2026-10-02T01:00:00Z'))
    print('PASS research feature lab: prior-week isolation, source hashes, nulls, units, roles and strategy selection')


if __name__=='__main__':
    main()
