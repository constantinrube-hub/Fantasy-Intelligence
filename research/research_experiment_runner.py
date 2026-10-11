"""Replay predeclared, source-bound forecast ablations without promotion."""
from __future__ import annotations

import argparse
from collections import Counter, defaultdict
import json
from pathlib import Path
from statistics import mean

from point_in_time_capture import first_write_json
from strict_sleeper_baseline import finite
from weekly_evidence_audit import digest, stamp


def run(root:Path, protocol:dict, rows:list[dict]) -> dict:
    root=root.resolve()
    registry=json.loads((root/'config/roadmap-research-registry.json').read_text())
    ids={r['research_id'] for r in registry['experiments']}
    if protocol.get('schema')!='fie-research-ablation-protocol-v1' or protocol.get('research_id') not in ids:
        raise ValueError('EXPERIMENT_PROTOCOL_ID_OR_SCHEMA_INVALID')
    if protocol.get('production_authorized') is not False or protocol.get('metric')!='paired_absolute_error':
        raise ValueError('EXPERIMENT_AUTHORITY_OR_METRIC_INVALID')
    train_end=stamp(protocol['training_cutoff']);evaluation_start=stamp(protocol['evaluation_start'])
    if train_end>=evaluation_start or stamp(protocol['registered_at'])>evaluation_start:
        raise ValueError('EXPERIMENT_PROTOCOL_REGISTERED_TOO_LATE_OR_TRAIN_OVERLAP')
    if protocol.get('evaluation_mode') not in {'HISTORICAL','PROSPECTIVE_SHADOW'}:
        raise ValueError('EXPERIMENT_MODE_INVALID')
    bindings=protocol.get('evidence') or []
    if not bindings:
        raise ValueError('EXPERIMENT_EVIDENCE_MISSING')
    evidence_times=[]
    for ref in bindings:
        path=(root/ref['path']).resolve()
        if not path.is_relative_to(root/'data/research') or not path.is_file() or digest(path)!=ref['sha256']:
            raise ValueError('EXPERIMENT_EVIDENCE_HASH_OR_PATH_INVALID')
        evidence_times.append(stamp(ref['observed_at']))
    accepted,rejections,seen=defaultdict(list),Counter(),set()
    for row in rows:
        key=(row['season'],row['week'],row['league_id'],row['canonical_player_id'])
        if key in seen:
            raise ValueError('EXPERIMENT_DUPLICATE_OBSERVATION')
        seen.add(key)
        forecast_at,kickoff,outcome_at=[stamp(row[k]) for k in ('forecast_at','kickoff','outcome_observed_at')]
        if not evaluation_start<=forecast_at<kickoff<outcome_at or any(t>forecast_at for t in evidence_times):
            rejections['TIME_OR_FEATURE_OBSERVATION_INVALID']+=1
            continue
        if row.get('exact_scoring') is not True or not row.get('scoring_signature'):
            rejections['EXACT_SCORING_UNVERIFIED']+=1
            continue
        baseline,candidate,actual=[finite(row.get(k)) for k in ('baseline_mean','candidate_mean','realized_points')]
        if any(v is None for v in (baseline,candidate,actual)):
            rejections['MISSING_OR_NONFINITE_PAIR']+=1
            continue
        accepted[(row['season'],row['week'],row['scoring_signature'])].append((abs(baseline-actual),abs(candidate-actual)))
    slices=[{'season':key[0],'week':key[1],'scoring_signature':key[2],'rows':len(values),
             'baseline_mae':mean(v[0] for v in values),'candidate_mae':mean(v[1] for v in values),
             'paired_mae_delta_candidate_minus_baseline':mean(v[1]-v[0] for v in values)}
            for key,values in sorted(accepted.items())]
    return {'schema':'fie-research-ablation-result-v1','research_id':protocol['research_id'],
            'status':protocol['evaluation_mode']+'_DESCRIPTIVE_RESULTS' if slices else 'BLOCKED_MISSING_OR_INELIGIBLE_ROWS',
            'protocol':protocol,'slices':slices,'accepted_rows':sum(r['rows'] for r in slices),
            'rejection_counts':dict(sorted(rejections.items())),
            'inference':'Dependent league/player/game observations; no significance, automatic validation or promotion.',
            'production_authorized':False}


def main():
    ap=argparse.ArgumentParser()
    ap.add_argument('--root',type=Path,default=Path(__file__).resolve().parents[1])
    ap.add_argument('--input',type=Path,required=True)
    ap.add_argument('--output',type=Path,required=True)
    args=ap.parse_args();payload=json.loads(args.input.read_text())
    result=run(args.root,payload['protocol'],payload['rows'])
    result['input_sha256']=digest(args.input)
    print(first_write_json(args.output,result))


if __name__=='__main__':
    main()
