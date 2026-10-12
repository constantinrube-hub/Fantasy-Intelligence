"""Replay immutable research artifacts against a separately pinned report hash.

This validates the copied exact labels, past-feature construction, nested
selection, fitted specs, issued predictions and diagnostics. Raw PBP/event
reconstruction remains a separate source-closure audit; never an activation.
"""
from __future__ import annotations

import argparse
import json
import math
from pathlib import Path

import pandas as pd

from build_waiver_v2_label_batch import digest, label_frame
from waiver_v2_validation import (
    POLICY, SCHEMA, evaluate, features, keyed, policy,
)


def equivalent(actual, expected):
    if isinstance(expected, dict):
        if not isinstance(actual, dict) or set(actual) != set(expected):
            raise ValueError('WAIVER_ARTIFACT_REPLAY_KEYS_MISMATCH')
        for key in expected:
            equivalent(actual[key], expected[key])
    elif isinstance(expected, list):
        if not isinstance(actual, list) or len(actual) != len(expected):
            raise ValueError('WAIVER_ARTIFACT_REPLAY_LENGTH_MISMATCH')
        for left, right in zip(actual, expected):
            equivalent(left, right)
    elif isinstance(expected, float):
        if isinstance(actual, bool) or not isinstance(actual, (int, float)) or not math.isclose(actual, expected, rel_tol=1e-10, abs_tol=1e-10):
            raise ValueError('WAIVER_ARTIFACT_REPLAY_NUMBER_MISMATCH')
    elif actual != expected or isinstance(expected, bool) and not isinstance(actual, bool):
        raise ValueError('WAIVER_ARTIFACT_REPLAY_VALUE_MISMATCH')


def validate(report_path, expected_sha256, artifact_dir=None):
    if digest(report_path) != expected_sha256:
        raise ValueError('WAIVER_ARTIFACT_REPORT_HASH_MISMATCH')
    report = json.loads(report_path.read_text())
    contract = policy()
    if report.get('schema') != SCHEMA or report.get('activation_eligible') is not False:
        raise ValueError('WAIVER_ARTIFACT_WRONG_SCHEMA_OR_ACTIVATION')
    if report['methodology']['sha256'] != digest(POLICY):
        raise ValueError('WAIVER_ARTIFACT_METHOD_MISMATCH')
    if report['builder_sha256'] != digest(Path(__file__).with_name('waiver_v2_validation.py')):
        raise ValueError('WAIVER_ARTIFACT_BUILDER_MISMATCH')
    artifact_dir = artifact_dir or report_path.parent

    def read_binding(binding, source=False):
        # Copied artifacts use their original basename; the independent report
        # hash pins that name and byte hash, without rewriting provenance paths.
        local = artifact_dir / ('sources' if source else '') / Path(binding['path']).name
        path = local if local.is_file() else Path(binding['path'])
        if not path.is_file() or digest(path) != binding['sha256']:
            raise ValueError('WAIVER_ARTIFACT_BOUND_FILE_MISMATCH')
        return path

    expected_units = {(s, p) for s in contract['signatures'] for p in contract['positions']}
    units = report['units']
    identities = [(row['scoring_signature'], row['position']) for row in units]
    if set(identities) != expected_units or len(identities) != len(expected_units):
        raise ValueError('WAIVER_ARTIFACT_UNIT_SET_MISMATCH')
    for unit in units:
        labels = pd.read_csv(read_binding(unit['source_labels'], source=True))
        signature, position = unit['scoring_signature'], unit['position']
        rederived = label_frame(labels, signature, contract['seasons'])
        pd.testing.assert_frame_equal(labels, rederived, check_dtype=False, check_exact=False, rtol=1e-12, atol=1e-12)
        stats = pd.read_csv(read_binding(unit['source_inputs']['player_stats'], source=True), low_memory=False)
        schedule = pd.read_csv(read_binding(unit['source_inputs']['team_schedule'], source=True))
        # Retain the roster source bytes/hash for independent population audit.
        read_binding(unit['source_inputs']['weekly_roster'], source=True)
        last = labels.season.map(schedule.groupby('season').week.max().to_dict())
        decision = labels[(labels.position_model == position) & (labels.week + 3 <= last)]
        all_features = features(labels, stats, position, contract)
        expected_features = keyed(all_features).loc[keyed(decision).index].reset_index(drop=True)
        stored_features = pd.read_csv(read_binding(unit['artifacts']['features']))
        pd.testing.assert_frame_equal(stored_features, expected_features, check_dtype=False, check_exact=False, rtol=1e-10, atol=1e-10)
        result, predictions, models = evaluate(expected_features, decision, contract)
        equivalent({key: unit[key] for key in result}, result)
        stored_predictions = pd.read_csv(read_binding(unit['artifacts']['predictions']))
        pd.testing.assert_frame_equal(stored_predictions, predictions, check_dtype=False, check_exact=False, rtol=1e-10, atol=1e-10)
        equivalent(json.loads(read_binding(unit['artifacts']['fold_models']).read_text()), models)
    if report['eligible_forecast_units'] != 0 or report['research_signal_units'] != sum(unit['research_signal_passed'] for unit in units):
        raise ValueError('WAIVER_ARTIFACT_ROLLUP_MISMATCH')
    return {'status': 'PASS_RESEARCH_ARTIFACT_REPLAY', 'units': len(units), 'activation_eligible': False,
            'raw_event_reconstruction_replayed': False, 'report_sha256': expected_sha256}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--validation-report', type=Path, required=True)
    parser.add_argument('--expected-sha256', required=True, help='Separately reviewed/pinned report digest, not a digest taken from an untrusted report')
    parser.add_argument('--artifact-dir', type=Path)
    args = parser.parse_args()
    print(json.dumps(validate(args.validation_report, args.expected_sha256, args.artifact_dir), sort_keys=True))


if __name__ == '__main__':
    main()
