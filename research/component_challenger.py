"""Validated chronological challenger interface; no hidden fit or promotion."""
from __future__ import annotations
import argparse
from pathlib import Path
from component_weekly_ops import REPO, PROJECT, REFERENCE, read, write_new, digest
from component_diagnostics import safe, finish

CONTRACT = REPO / 'config/component-challenger-contract-v1.json'

def validate_contract(contract):
    if contract.get('schema') != 'fie-component-challenger-contract-v1':
        raise ValueError('UNKNOWN_CHALLENGER_CONTRACT')
    if contract.get('training_enabled') or contract.get('feature_selection_enabled') or contract.get('candidate_weight_grid') is not None:
        raise ValueError('STATISTICAL_TRAINING_CHECKPOINT_REQUIRED')
    if contract.get('automatic_promotion') or contract.get('baseline_replacement_allowed'):
        raise ValueError('BASELINE_REPLACEMENT_NOT_AUTHORIZED')
    return contract

def validate_folds(folds):
    for fold in folds:
        if not fold['train_end'] < fold['validation_start'] <= fold['validation_end'] < fold['test_start']:
            raise ValueError('NON_CHRONOLOGICAL_CHALLENGER_FOLD')
    return True

def plan(project, fitted, training, output):
    contract = validate_contract(read(CONTRACT))
    fit = read(safe(project, fitted)); revision = read(safe(project, training) / 'training-view.json')
    if revision.get('through_week') != fit['through_week']:
        raise ValueError('CHALLENGER_TRAINING_CUTOFF_MISMATCH')
    path = safe(project, training) / 'training-2026.csv.gz'
    if digest(path) != revision['training_sha256']:
        raise ValueError('CHALLENGER_TRAINING_SOURCE_DRIFT')
    out = safe(project, output); out.mkdir(parents=True, exist_ok=False)
    result = {'schema': 'fie-component-challenger-plan-v1', 'status': 'INTERFACE_READY_NOT_TRAINED',
              'baseline_fit': str(fitted), 'baseline_fit_sha256': digest(safe(project, fitted)),
              'baseline_method_version': fit['version'], 'training_path': str(training),
              'training_sha256': digest(path), 'training_through_week': fit['through_week'],
              'contract_sha256': digest(CONTRACT), 'contract': contract, 'candidate_artifact': None,
              'feature_selection_performed': False, 'baseline_changed': False,
              'required_candidate_outputs': ['candidate_id', 'methodology_hash', 'source_cutoff', 'chronological_folds',
                                             'selected_weights', 'selected_features', 'support_counts', 'paired_validation',
                                             'coherence_validation', 'prospective_freeze']}
    write_new(out / 'challenger-plan.json', result)
    finish(out, {'type': 'challenger-interface', 'status': result['status'], 'contract_sha256': result['contract_sha256']})
    return result

if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--project', type=Path, default=PROJECT)
    parser.add_argument('--fit', type=Path, default=REFERENCE / 'fit/source-refit-final.json')
    parser.add_argument('--training', type=Path, default=REFERENCE / 'training/week05')
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    result = plan(args.project.resolve(), args.fit, args.training, args.output)
    print(result['status'])
