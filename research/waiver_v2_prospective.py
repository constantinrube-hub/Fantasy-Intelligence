"""Shared-owner frozen research inference and calendar-horizon evaluation."""
from __future__ import annotations
import argparse
import json
from pathlib import Path
import numpy as np
import pandas as pd
from prospective_research_io import binding, clock, gates, now, sha, verified, write
from waiver_v2_validation import KEYS, TARGET, FULL, features, fit, policy, predict, select, _true
from waiver_v2_contract import build_same_season_horizon_targets

ROOT = Path(__file__).resolve().parents[1]
POP = 'data/research/waiver-v2/population/2026-10-12/revision-1'
CORRECTED = POP+'/corrected-challenger'
OWNER = 'research/waiver_v2_validation.py'


def freeze(root, output, season=2026, frozen_at=None):
    at = frozen_at or now()
    contract = policy()
    if season != 2026 or clock(at).year != season:
        raise ValueError('WAIVER_LOCK_SEASON_UNSUPPORTED')
    report_path = root/CORRECTED/'corrected-challenger-report.json'
    report = json.loads(report_path.read_text())
    population = json.loads((root/POP/'population-report.json').read_text())
    if report['feature_validation_owner_sha256'] != sha(root/OWNER):
        raise ValueError('WAIVER_LOCK_SHARED_OWNER_DRIFT')
    if report['methodology']['sha256'] != sha(root/'config/waiver-v2-statistical-methodology.json'):
        raise ValueError('WAIVER_LOCK_METHOD_DRIFT')
    units, sources = [], [binding(root,report_path,at)]
    for old in report['units']:
        sig, position = old['scoring_signature'], old['position']
        profile = next(p for p in population['profiles'] if p['scoring_signature']==sig)
        source = root/CORRECTED/Path(old['artifacts']['features']['path']).name
        label = root/POP/Path(profile['expanded_labels']['path']).name
        if sha(source)!=old['artifacts']['features']['sha256'] or sha(label)!=profile['expanded_labels']['sha256']:
            raise ValueError('WAIVER_LOCK_TRAINING_SOURCE_CHANGED')
        frame = pd.read_csv(source,low_memory=False)
        labels = pd.read_csv(label,low_memory=False)[KEYS+[TARGET,FULL]]
        if not set(frame.season).issubset(contract['seasons']) or max(frame.season)>=season:
            raise ValueError('WAIVER_LOCK_FUTURE_TRAINING')
        frame = frame.merge(labels,on=KEYS,how='left',validate='one_to_one')
        frame['label_complete'] = frame[FULL].map(_true)&np.isfinite(pd.to_numeric(frame[TARGET],errors='coerce'))
        frame['feature_admissible'] = frame.feature_admissible.map(_true)
        choice, audit = select(frame,contract)
        spec = fit(frame,choice,contract) if choice else None
        sources.extend([binding(root,source,at),binding(root,label,at)])
        units.append({'scoring_signature':sig,'position':position,'model':spec,
                      'selection_audit':audit,'historical_research_signal':old['research_signal_passed'],
                      'status':'FROZEN_RESEARCH_SPEC' if spec else 'BLOCKED_HISTORICAL_SELECTION',
                      **gates(['BLOCKED_PROSPECTIVE_VALIDATION_REQUIRED','BLOCKED_PROMOTION_REVIEW_REQUIRED'])})
    expected={(s,p) for s in contract['signatures'] for p in contract['positions']}
    if {(u['scoring_signature'],u['position']) for u in units} != expected or len(units)!=len(expected):
        raise ValueError('WAIVER_LOCK_UNIT_POPULATION')
    lock={'schema':'fie-waiver-v2-prospective-lock-v1','season':season,'frozen_at':at,
          'horizon_weeks':3,'baseline':'same_cutoff_fp_prior_4',
          'methodology':binding(root,root/'config/waiver-v2-statistical-methodology.json',at),
          'feature_owner':binding(root,root/OWNER,at),'historical_sources':sources,'units':units,
          'parameters_selected_from_2026':False,'independent_confirmation':False,
          **gates(['BLOCKED_PROSPECTIVE_VALIDATION_REQUIRED','BLOCKED_PROMOTION_REVIEW_REQUIRED'])}
    write(output,lock)
    return lock


def validate_lock(root, path):
    lock=json.loads(Path(path).read_text())
    expected=json.loads((root/'config/week6-evidence-preparation.json').read_text())['waiver']['lock_sha256']
    if sha(path)!=expected:
        raise ValueError('WAIVER_LOCK_PARAMETER_HASH_DRIFT')
    if lock.get('schema')!='fie-waiver-v2-prospective-lock-v1' or lock.get('parameters_selected_from_2026') is not False:
        raise ValueError('WAIVER_LOCK_SCHEMA_OR_SELECTION')
    if lock['horizon_weeks']!=3 or any(lock.get(k) is not False for k in ['activation_eligible','forecast_eligible','ranking_eligible','recommendation_eligible','transaction_eligible']):
        raise ValueError('WAIVER_LOCK_AUTHORITY')
    for ref in [lock['methodology'],lock['feature_owner'],*lock['historical_sources']]:
        verified(root,ref,lock['frozen_at'])
    expected={(s,p) for s in policy()['signatures'] for p in policy()['positions']}
    if len(lock['units'])!=len(expected) or {(u['scoring_signature'],u['position']) for u in lock['units']}!=expected:
        raise ValueError('WAIVER_LOCK_UNIT_DRIFT')
    for unit in lock['units']:
        model=unit['model']
        if model is None: continue
        n=len(model['columns'])*2
        if any(len(model[key])!=n for key in ['means','scales','coefficients']) or len(model['medians'])!=n//2:
            raise ValueError('WAIVER_LOCK_MODEL_SHAPE')
        if not set(model['training_seasons']).issubset(policy()['seasons']) or max(model['training_seasons'])>=lock['season']:
            raise ValueError('WAIVER_LOCK_TRAINING_SEASON')
        vals=[model['intercept'],*model['medians'],*model['means'],*model['scales'],*model['coefficients']]
        if not np.isfinite(vals).all() or min(model['scales'])<=0:
            raise ValueError('WAIVER_LOCK_MODEL_NONFINITE')
    return lock


def replay_lock(root,path):
    lock=validate_lock(root,path)
    report=json.loads((root/CORRECTED/'corrected-challenger-report.json').read_text())
    population=json.loads((root/POP/'population-report.json').read_text())
    contract=policy()
    for unit in lock['units']:
        original=next(u for u in report['units'] if (u['scoring_signature'],u['position'])==(unit['scoring_signature'],unit['position']))
        profile=next(p for p in population['profiles'] if p['scoring_signature']==unit['scoring_signature'])
        frame=pd.read_csv(root/CORRECTED/Path(original['artifacts']['features']['path']).name,low_memory=False)
        labels=pd.read_csv(root/POP/Path(profile['expanded_labels']['path']).name,low_memory=False)[KEYS+[TARGET,FULL]]
        frame=frame.merge(labels,on=KEYS,how='left',validate='one_to_one')
        frame['feature_admissible']=frame.feature_admissible.map(_true)
        frame['label_complete']=frame[FULL].map(_true)&np.isfinite(pd.to_numeric(frame[TARGET],errors='coerce'))
        choice,audit=select(frame,contract)
        expected=fit(frame,choice,contract) if choice else None
        actual=unit['model']
        if (actual is None)!=(expected is None):raise ValueError('WAIVER_LOCK_MODEL_SUPPORT_REPLAY')
        if actual is None:continue
        for key in ['choice','columns','supported_patterns','training_rows','training_seasons']:
            if actual[key]!=expected[key]:raise ValueError('WAIVER_LOCK_SELECTION_REPLAY')
        for key in ['intercept','medians','means','scales','coefficients']:
            if not np.allclose(actual[key],expected[key],rtol=1e-10,atol=1e-10):
                raise ValueError('WAIVER_LOCK_PARAMETER_REPLAY')
    return lock


def current_features(history, stats, universe, season, completed_week, position, signature=None):
    """The decision universe is observed now; source history ends at W."""
    if completed_week<1 or completed_week+3>18:
        raise ValueError('WAIVER_CAPTURE_FULL_HORIZON_REQUIRED')
    if history.duplicated(KEYS).any() or stats.duplicated(KEYS).any():
        raise ValueError('WAIVER_CAPTURE_DUPLICATE_HISTORY')
    ids=[r['canonical_player_id'] for r in universe]
    if len(ids)!=len(set(ids)) or any(not x for x in ids):
        raise ValueError('WAIVER_CAPTURE_DUPLICATE_UNIVERSE')
    history=history[(history.season==season)&(history.week<=completed_week)].copy()
    signatures=set(history.scoring_signature.dropna().astype(str))
    if len(signatures)>1 or (signature is not None and signatures and signatures!={signature}):
        raise ValueError('WAIVER_CAPTURE_HISTORY_SIGNATURE_MISMATCH')
    signature=signature or (next(iter(signatures)) if signatures else None)
    stats=stats[(stats.season==season)&(stats.week<=completed_week)].copy()
    # Placeholder cutoff rows establish membership only. Their score/opportunity
    # is unknown unless an original observed row exists; no synthetic zero.
    for player in universe:
        mask=(history.canonical_player_id==player['canonical_player_id'])&(history.week==completed_week)
        if mask.any():
            history.loc[mask,['position_model','team']]=[player['position_model'],player.get('team')]
        else:
            history=pd.concat([history,pd.DataFrame([{**player,'season':season,'week':completed_week,
                            'scoring_signature':signature,'fantasy_points_exact':np.nan,'outcome_complete':False,'exact_scoring':False}])],ignore_index=True)
    frame=features(history,stats,position)
    allowed={r['canonical_player_id'] for r in universe if r['position_model']==position}
    return frame[(frame.week==completed_week)&frame.canonical_player_id.isin(allowed)].copy()


def forecast(lock, signature, history, stats, universe, *, season, completed_week, captured_at, first_kickoff):
    if season!=lock['season'] or not clock(lock['frozen_at'])<=clock(captured_at)<clock(first_kickoff):
        raise ValueError('WAIVER_CAPTURE_LOCK_OR_PREGAME_TIME')
    if signature not in policy()['signatures']:
        raise ValueError('WAIVER_CAPTURE_UNSUPPORTED_SIGNATURE')
    result=[]
    for position in policy()['positions']:
        unit=next(u for u in lock['units'] if (u['scoring_signature'],u['position'])==(signature,position))
        frame=current_features(history,stats,universe,season,completed_week,position,signature)
        values=predict(unit['model'],frame) if unit['model'] else np.full(len(frame),np.nan)
        for (_,row),value in zip(frame.iterrows(),values):
            base=float(row.fp_prior_4) if np.isfinite(row.fp_prior_4) else None
            fields={k:(None if pd.isna(v) else v.item() if isinstance(v,np.generic) else v)
                    for k,v in row.items()}
            result.append({'canonical_player_id':row.canonical_player_id,'position':position,'season':season,
                           'completed_week':completed_week,'target_weeks':list(range(completed_week+1,completed_week+4)),
                           'scoring_signature':signature,'forecast_mean':float(value) if np.isfinite(value) else None,
                           'baseline_mean':base,'features':fields,'captured_at':captured_at,'first_kickoff':first_kickoff,
                           'status':'RESEARCH_FORECAST' if np.isfinite(value) else 'BLOCKED_FEATURE_OR_MODEL_SUPPORT',
                           **gates(['BLOCKED_PROSPECTIVE_VALIDATION_REQUIRED','BLOCKED_PROMOTION_REVIEW_REQUIRED'])})
    return result


def evaluate_rows(rows, outcomes, *, observed_at, horizon_end):
    if clock(observed_at)<=clock(horizon_end):
        raise ValueError('WAIVER_OUTCOME_HORIZON_NOT_FINISHED')
    keys=KEYS+['scoring_signature']
    if outcomes.duplicated(keys).any():
        raise ValueError('WAIVER_OUTCOME_DUPLICATE_PROFILE_WEEK')
    lookup=outcomes.set_index(keys)
    evaluated=[]
    for row in rows:
        expected=list(range(row['completed_week']+1,row['completed_week']+4))
        if row['target_weeks']!=expected or expected[-1]>18:
            raise ValueError('WAIVER_OUTCOME_CHANGED_HORIZON')
        values=[]
        for week in expected:
            key=(row['canonical_player_id'],row['season'],week,row['scoring_signature'])
            if key not in lookup.index: break
            source=lookup.loc[key]
            point=pd.to_numeric(source.fantasy_points_exact,errors='coerce')
            if not _true(source.outcome_complete) or not _true(source.exact_scoring) or not np.isfinite(point): break
            values.append(float(point))
        complete=len(values)==3
        actual=float(np.mean(values)) if complete else None
        prediction=row['forecast_mean'];baseline=row['baseline_mean']
        evaluated.append({**row,'outcome_status':'EXACT_FULL_HORIZON' if complete else 'BLOCKED_INCOMPLETE_EXACT_OUTCOME',
                          'realized_mean':actual,'complete_target_weeks':len(values),
                          'model_absolute_error':abs(prediction-actual) if complete and prediction is not None else None,
                          'baseline_absolute_error':abs(baseline-actual) if complete and baseline is not None else None,
                          'outcome_observed_at':observed_at})
    return evaluated


def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--root',type=Path,default=ROOT)
    p.add_argument('--freeze',type=Path);p.add_argument('--validate-lock',type=Path);p.add_argument('--replay-lock',type=Path);a=p.parse_args()
    if a.freeze: r=freeze(a.root,a.freeze)
    elif a.validate_lock: r=validate_lock(a.root,a.validate_lock)
    elif a.replay_lock: r=replay_lock(a.root,a.replay_lock)
    else: p.error('choose --freeze or --validate-lock')
    print(json.dumps({'units':len(r['units']),'research_only':True,'activation_eligible':False}))


if __name__=='__main__':main()
