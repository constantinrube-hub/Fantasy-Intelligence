"""Replay published population certificates/targets and corrected research fits.

The derivative graph is self-contained. Raw PBP certificate derivation is
separately recorded and fixture-tested; this replay does not reparse raw PBP.
"""
from __future__ import annotations
import argparse
import json
from pathlib import Path
import numpy as np
import pandas as pd
from build_waiver_v2_label_batch import digest,label_frame
from waiver_v2_population import extend,stress,CONTRACT,GLOBAL_CONTRACT
from waiver_v2_validation import KEYS,features,keyed,evaluate,policy
from waiver_v2_outcomes import build_offensive_scoring_inventory,_score_exact_row
from week1_game_projections import canonical_team
from validate_waiver_v2_validation import equivalent

ROOT=Path(__file__).resolve().parents[1]
FROZEN=ROOT/'data/research/waiver-v2/model-validation/2026-10-12/revision-1'


def bound(binding,folder):
    path=folder/Path(binding['path']).name
    if not path.is_file() or digest(path)!=binding['sha256']:raise ValueError('WAIVER_POPULATION_ARTIFACT_HASH_MISMATCH')
    return path


def same(actual,expected):
    pd.testing.assert_frame_equal(actual.reset_index(drop=True),expected.reset_index(drop=True),
                                  check_dtype=False,check_exact=False,rtol=1e-10,atol=1e-10)


def validate(population_path,expected_sha256,corrected_path=None,corrected_sha256=None):
    if digest(population_path)!=expected_sha256:raise ValueError('WAIVER_POPULATION_PINNED_REPORT_MISMATCH')
    r=json.loads(population_path.read_text());folder=population_path.parent
    if r['schema']!='fie-waiver-v2-population-revision-v1' or r['activation_eligible'] is not False or r['model_refitted'] is not False:
        raise ValueError('WAIVER_POPULATION_INVALID_AUTHORITY')
    if r['builder_sha256']!=digest(Path(__file__).with_name('waiver_v2_population.py')) or r['contract']['sha256']!=digest(CONTRACT) or r['global_contract']['sha256']!=digest(GLOBAL_CONTRACT):
        raise ValueError('WAIVER_POPULATION_SOURCE_OWNER_CHANGED')
    expected_profiles=set(json.loads(CONTRACT.read_text())['scoring_signatures'])
    if {p['scoring_signature'] for p in r['profiles']}!=expected_profiles or len(r['profiles'])!=len(expected_profiles):
        raise ValueError('WAIVER_POPULATION_PROFILE_SET_CHANGED')
    frozen_path=FROZEN/'validation-report.json'
    if digest(frozen_path)!=r['frozen_validation_report']['sha256']:raise ValueError('WAIVER_POPULATION_OLD_REPORT_CHANGED')
    old=json.loads(frozen_path.read_text())
    cert=pd.read_csv(bound(r['certificates'],folder));games=pd.read_csv(bound(r['game_proof_audit'],folder))
    actors=pd.read_csv(bound(r['actor_index'],folder));bound(r['published_absence_audit'],folder)
    if games.game_id.duplicated().any() or len(games)!=r['game_count']:raise ValueError('WAIVER_POPULATION_GAME_AUDIT_CHANGED')
    ready=games.groupby(['season','week']).proof_ready.all();ready_weeks=set(ready[ready].index)
    if int(games.proof_ready.sum())!=r['ready_games'] or len(ready_weeks)!=r['ready_weeks']:raise ValueError('WAIVER_POPULATION_GAME_ROLLUP_CHANGED')
    if games.loc[games.proof_ready,'blockers'].notna().any():raise ValueError('WAIVER_POPULATION_CONTRADICTORY_READY_GAME')
    actor_keys=set(pd.MultiIndex.from_frame(actors[KEYS].drop_duplicates()))
    stats=pd.read_csv(FROZEN/'sources/player-stats.csv.gz',low_memory=False)
    event_weekly=pd.read_csv(bound(r['event_weekly_stats'],folder))
    complete_stats=keyed(stats.merge(event_weekly,on=KEYS,how='left',validate='one_to_one'))
    schedule=pd.read_csv(FROZEN/'sources/team-schedule.csv.gz')
    stat_keys=set(keyed(stats).index)
    roster=keyed(pd.read_csv(FROZEN/'sources/weekly-roster.csv.gz'))
    for row in cert.itertuples(index=False):
        key=(row.canonical_player_id,row.season,row.week)
        if key not in roster.index or key in actor_keys or key in stat_keys or (row.season,row.week) not in ready_weeks:
            raise ValueError('WAIVER_POPULATION_INVALID_ABSENCE_CERTIFICATE')
        member=roster.loc[key]
        if member.team!=row.team or member.position_model!=row.position_model or not bool(member.roster_complete):
            raise ValueError('WAIVER_POPULATION_MEMBERSHIP_CERTIFICATE_MISMATCH')
    prepared={}
    for profile in r['profiles']:
        signature=profile['scoring_signature'];unit=next(u for u in old['units'] if u['scoring_signature']==signature)
        source=pd.read_csv(bound(profile['source_labels'],FROZEN/'sources'))
        labels=pd.read_csv(bound(profile['expanded_labels'],folder),low_memory=False)
        scoring=json.loads(bound(profile['scoring_profile'],folder).read_text())['scoring_settings']
        global_proofs=pd.read_csv(bound(profile['global_identity_proofs'],folder))
        original,count=extend(source,cert,r['certificates']['sha256'])
        if count!=profile['certified_zero_rows_added']:raise ValueError('WAIVER_POPULATION_ZERO_COUNT_CHANGED')
        stored_original=labels[~labels.target_only_row]
        # Targets may now include target-only rows, so compare immutable scores
        # and source fields here; all horizon columns are replayed below.
        point_cols=KEYS+['team','position_model','fantasy_points_exact','outcome_complete','outcome_status','exact_scoring']
        same(stored_original[point_cols],original[point_cols])
        rederived=label_frame(labels,signature,old['requested_seasons']);same(labels,rederived)
        additions=labels[labels.target_only_row]
        if len(additions)!=len(global_proofs) or not additions.future_membership_verified.eq(False).all():
            raise ValueError('WAIVER_POPULATION_TARGET_ONLY_AUTHORITY')
        anchors=source.groupby(['canonical_player_id','season']).week.min()
        proof_lookup=keyed(global_proofs)
        for row in additions.itertuples(index=False):
            key=(row.canonical_player_id,row.season,row.week);p=proof_lookup.loc[key]
            if p.identity_anchor_week!=anchors[(row.canonical_player_id,row.season)] or p.identity_anchor_week>=row.week or row.fantasy_points_exact!=p.fantasy_points_proven:
                raise ValueError('WAIVER_POPULATION_INVALID_IDENTITY_ANCHOR')
            if p.proof_basis=='GLOBAL_NFL_WEEK_NO_EVENT':
                if key in actor_keys or key in stat_keys or (row.season,row.week) not in ready_weeks or row.fantasy_points_exact!=0 or pd.notna(row.team) or pd.notna(row.position_model):
                    raise ValueError('WAIVER_POPULATION_GLOBAL_ABSENCE_MISMATCH')
            elif p.proof_basis=='EXACT_PUBLISHED_PLAYER_WEEK':
                if key not in stat_keys or key not in actor_keys:raise ValueError('WAIVER_POPULATION_PUBLISHED_IDENTITY_MISMATCH')
                observation=complete_stats.loc[key]
                inv=build_offensive_scoring_inventory(scoring,position=observation.position_model,available_columns=set(complete_stats),event_rule_support=r['event_rule_support'])
                required={col for rule in inv['relevant_nonzero_rules'] for col in rule['required_columns']}
                if not inv['exact_replay_eligible'] or any(pd.isna(observation.get(col)) for col in required):
                    raise ValueError('WAIVER_POPULATION_PUBLISHED_RULE_BLOCKED')
                selected=schedule[(schedule.season==row.season)&(schedule.week==row.week)&schedule.team.map(canonical_team).eq(canonical_team(observation.team))]
                if len(selected)!=1 or not bool(selected.team_has_game.iloc[0]) or not bool(selected.game_complete.iloc[0]) or not np.isclose(row.fantasy_points_exact,_score_exact_row(observation,scoring,observation.position_model),rtol=0,atol=1e-12):
                    raise ValueError('WAIVER_POPULATION_PUBLISHED_SCORE_MISMATCH')
            else:raise ValueError('WAIVER_POPULATION_UNKNOWN_GLOBAL_PROOF')
        for stress_unit in profile['units']:
            predictions=pd.read_csv(bound(stress_unit['frozen_forecasts'],FROZEN))
            expected,paired=stress(predictions,labels)
            equivalent(stress_unit['seasons'],expected)
            same(pd.read_csv(bound(stress_unit['stress_artifact'],folder)),paired)
            if any(stress_unit[layer] is not False for layer in ['forecast_eligible','ranking_eligible','recommendation_eligible','transaction_eligible']):
                raise ValueError('WAIVER_POPULATION_ELIGIBILITY_CHANGED')
        prepared[signature]=labels
    replayed=0
    if corrected_path is not None:
        if digest(corrected_path)!=corrected_sha256:raise ValueError('WAIVER_CORRECTED_PINNED_REPORT_MISMATCH')
        c=json.loads(corrected_path.read_text());out=corrected_path.parent
        if c['population_report']['sha256']!=expected_sha256 or c['activation_eligible'] is not False or c['independent_confirmation'] is not False:
            raise ValueError('WAIVER_CORRECTED_UNAUTHORIZED_CONFIRMATION')
        if c['builder_sha256']!=digest(Path(__file__).with_name('waiver_v2_corrected_challenger.py')):
            raise ValueError('WAIVER_CORRECTED_OWNER_CHANGED')
        expected_units={(s,p) for s in expected_profiles for p in ['QB','RB','WR','TE']}
        if {(u['scoring_signature'],u['position']) for u in c['units']}!=expected_units or len(c['units'])!=len(expected_units) or c['eligible_forecast_units']!=0 or c['hyperparameter_grid_changed'] is not False:
            raise ValueError('WAIVER_CORRECTED_UNIT_SET_OR_AUTHORITY_CHANGED')
        for unit in c['units']:
            signature,position=unit['scoring_signature'],unit['position'];labels=prepared[signature]
            old_features=pd.read_csv(bound(unit['original_cutoff_features'],FROZEN))
            frame=keyed(features(labels,stats,position,policy())).loc[keyed(old_features).index].reset_index(drop=True)
            same(pd.read_csv(bound(unit['artifacts']['features'],out)),frame)
            result,predictions,models=evaluate(frame,labels,policy())
            equivalent({key:unit[key] for key in result},result)
            same(pd.read_csv(bound(unit['artifacts']['predictions'],out)),predictions)
            equivalent(json.loads(bound(unit['artifacts']['fold_models'],out).read_text()),models)
            replayed+=1
    return {'status':'PASS_POPULATION_AND_CORRECTED_REPLAY','profiles':len(prepared),'corrected_units':replayed,
            'raw_pbp_reparsed':False,'activation_eligible':False}


def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--population-report',type=Path,required=True)
    p.add_argument('--expected-sha256',required=True);p.add_argument('--corrected-report',type=Path);p.add_argument('--corrected-sha256')
    a=p.parse_args();print(json.dumps(validate(a.population_report,a.expected_sha256,a.corrected_report,a.corrected_sha256),sort_keys=True))


if __name__=='__main__':main()
