"""Source-bound exact calendar-week targets; never a forecast promotion."""
from __future__ import annotations
import argparse
import hashlib
import json
from pathlib import Path
import pandas as pd

from waiver_v2_contract import build_same_season_horizon_targets, _true
from waiver_v2_exact_replay_closure import build_exact_replay_closure

POLICY = Path(__file__).resolve().parents[1] / 'config/offensive-waiver-eligibility-design.json'


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def validation_capacity(frame):
    """Upper bound only: two earlier training seasons are already required."""
    policy = json.loads(POLICY.read_text())['model_validation']
    if policy['temporal_design'] != 'whole-season expanding outer folds with at least two prior training seasons and at least four valid holdout seasons':
        raise ValueError('WAIVER_LABEL_VALIDATION_PROTOCOL_CHANGED')
    required = int(policy['minimum_outer_folds'])
    output = {}
    for position, rows in frame.groupby('position_model'):
        eligible = rows[rows['fp_next3_weeks_full_horizon']]
        counts = {str(year):int(len(group)) for year,group in eligible.groupby('season')}
        output[str(position)] = {'exact_label_rows_by_season':counts,
            'maximum_possible_outer_holdouts':max(0,len(counts)-2),
            'required_outer_holdouts':required,'feature_rows_verified':False,
            'status':'BLOCKED_INSUFFICIENT_HOLDOUT_SEASONS' if max(0,len(counts)-2)<required else 'BLOCKED_MODEL_VALIDATION_REQUIRED'}
    return output


def label_frame(frame, signature, seasons):
    if set(frame['scoring_signature'].astype(str)) != {signature}:
        raise ValueError('WAIVER_LABEL_SIGNATURE_MISMATCH')
    if not set(frame['season']).issubset(set(seasons)):
        raise ValueError('WAIVER_LABEL_SEASON_MISMATCH')
    complete = frame['outcome_complete'].map(_true)
    exact = frame['exact_scoring'].map(_true)
    if (complete & ~exact).any():
        raise ValueError('WAIVER_LABEL_COMPLETE_NONEXACT_OUTCOME')
    # Incomplete source values cannot leak into a target even if a caller
    # supplies a numeric diagnostic fantasy score alongside a blocker.
    result = frame.copy()
    result['outcome_complete'] = complete & exact
    for horizon in (1, 2, 3):
        result = build_same_season_horizon_targets(result, horizon_weeks=horizon)
    return result


def build(batch_report: Path, output_dir: Path):
    if output_dir.exists():
        raise ValueError('WAIVER_LABEL_OUTPUT_MUST_BE_NEW')
    batch = json.loads(batch_report.read_text())
    # Reuse the existing closure's source/report/ledger hash and coverage checks.
    closure = build_exact_replay_closure(batch_report_path=batch_report, output_path=None)
    prepared = []
    seen = set()
    for profile in closure['profiles']:
        signature = profile['scoring_signature']
        if signature in seen:
            raise ValueError('WAIVER_LABEL_DUPLICATE_SIGNATURE')
        seen.add(signature)
        source = Path(profile['outcome_ledger']['path'])
        frame = label_frame(pd.read_csv(source), signature, batch['requested_seasons'])
        prepared.append((profile, frame))
    output_dir.mkdir(parents=True)
    profiles = []
    for profile, frame in prepared:
        signature = profile['scoring_signature']
        path = output_dir / f'{signature}-exact-targets.csv.gz'
        frame.to_csv(path, index=False, compression={'method':'gzip','mtime':0})
        counts = {str(h): int(frame[f'fp_next{h}_weeks_full_horizon'].sum()) for h in (1,2,3)}
        by_position = {str(pos): {str(h): int(rows[f'fp_next{h}_weeks_full_horizon'].sum()) for h in (1,2,3)}
                       for pos, rows in frame.groupby('position_model')}
        profiles.append({'scoring_signature':signature, 'league_ids':profile['league_ids'],
                         'source_outcome_ledger':profile['outcome_ledger'],
                         'source_outcome_report':profile['outcome_report'],
                         'labels':{'path':str(path),'sha256':digest(path),'rows':len(frame)},
                         'complete_target_counts':counts,'complete_targets_by_position':by_position,
                         'model_validation_capacity':validation_capacity(frame),
                         'target_status':'EXACT_NEXT3_TARGETS_AVAILABLE' if counts['3'] else 'BLOCKED_NO_EXACT_NEXT3_TARGETS',
                         'forecast_status':'BLOCKED_MODEL_VALIDATION_REQUIRED',
                         'forecast_eligible':False,'ranking_eligible':False,
                         'recommendation_eligible':False,'transaction_eligible':False})
    report = {'schema':'fie-waiver-v2-label-batch-v1','batch_source':{'path':str(batch_report),'sha256':digest(batch_report)},
              'builder_sha256':{p:digest(Path(__file__).with_name(p)) for p in
                                 ('build_waiver_v2_label_batch.py','waiver_v2_contract.py')},
              'requested_seasons':batch['requested_seasons'],'profiles':profiles,
              'profile_count':len(profiles),'diagnostic_only':True,'activation_eligible':False,
              'validation_policy':{'path':str(POLICY),'sha256':digest(POLICY)},
              'point_in_time_feature_rows_verified':False,
              'note':'Exact targets advance the label gate only. Missing outcomes remain missing; same-season calendar weeks are mandatory. No model, prospective validation, or production eligibility is certified.'}
    (output_dir/'label-batch-report.json').write_text(json.dumps(report,indent=2,sort_keys=True)+'\n')
    return report


def main():
    parser=argparse.ArgumentParser();parser.add_argument('--batch-report',type=Path,required=True)
    parser.add_argument('--output-dir',type=Path,required=True);args=parser.parse_args()
    report=build(args.batch_report,args.output_dir)
    print({p['scoring_signature']:p['complete_target_counts'] for p in report['profiles']})


if __name__=='__main__':main()
