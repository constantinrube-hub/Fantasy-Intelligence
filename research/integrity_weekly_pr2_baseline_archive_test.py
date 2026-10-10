#!/usr/bin/env python3
"""Exact stored market rows reproduce numbers only under typed archive evidence."""
import json
import tempfile
from pathlib import Path
from unittest.mock import patch

import pandas as pd

import build_current_snapshot as current
from weekly_pr2_baseline_archive import audit


def main():
    with tempfile.TemporaryDirectory() as td:
        root = Path(td)
        context = {'capture_policy_version': 2, 'season_type': 'regular',
                   'first_kickoff_utc': '2026-10-02T00:15:00Z'}
        with patch.object(current, 'utc_now', return_value='2026-10-01T06:00:00Z'):
            receipt = current.archive_sleeper_projection(
                [{'player_id': 'a', 'player': {'position': 'RB'}, 'stats': {'rec': 10}}],
                2026, 4, pd.DataFrame(), root/'data/research/market/sleeper', True, capture_context=context)
        with patch.object(current, 'utc_now', return_value='2026-10-01T07:00:00Z'):
            source_receipt = current.sleeper_baseline_source_receipt(
                [{'player_id': 'a', 'stats': {'rec': 10}}], 2026, 4,
                root/'data/research/market/sleeper', 'scoring:one')
        assert source_receipt['status'] == 'ARCHIVED_PROJECTION_STATS_MATCH'
        assert source_receipt['archive_sha256'] == receipt['sha256']
        capture = {'generated_at': '2026-10-01T12:00:00Z', 'leagues': [
            {'league_id': '1', 'evaluation_input': {'scoring_settings': {'rec': 1},
             'sleeper_baseline_receipt': source_receipt, 'active_candidates': [
                {'captured_player_id': 'canonical:a', 'sleeper_id': 'a', 'position_model': 'RB'}]}}]}
        evaluation = {'season': 2026, 'week': 4, 'leagues': [
            {'league_id': '1', 'status': 'READY', 'capture_evidence': {'scoring_signature': 'scoring:one'}, 'paired_projection_rows': [
                {'captured_player_id': 'canonical:a', 'sleeper_mean': 10}]}]}
        result = audit(root, capture, evaluation)
        assert result['status_counts'] == {'VALUE_REPRODUCED_FROM_ARCHIVE': 1}
        assert result['refresh_source_bound_leagues'] == 1
        assert result['scoring_comparability_certified'] is False
        assert result['archive']['sha256'] == receipt['sha256']
        with patch.object(current, 'utc_now', return_value='2026-10-01T08:00:00Z'):
            changed = current.sleeper_baseline_source_receipt(
                [{'player_id': 'a', 'stats': {'rec': 11}}], 2026, 4,
                root/'data/research/market/sleeper', 'scoring:one')
        assert changed['status'] == 'ARCHIVED_PROJECTION_STATS_DIFFER'
        capture['leagues'][0]['evaluation_input']['sleeper_baseline_receipt'] = changed
        assert audit(root, capture, evaluation)['refresh_source_bound_leagues'] == 0
        capture['leagues'][0]['evaluation_input']['sleeper_baseline_receipt'] = source_receipt
        evaluation['leagues'][0]['capture_evidence']['scoring_signature'] = 'scoring:two'
        assert audit(root, capture, evaluation)['refresh_source_bindings'][0]['status'] == 'SOURCE_RECEIPT_SCORING_SIGNATURE_MISMATCH'
        evaluation['leagues'][0]['capture_evidence']['scoring_signature'] = 'scoring:one'
        capture['leagues'][0]['evaluation_input']['sleeper_baseline_receipt'] = {}
        assert audit(root, capture, evaluation)['refresh_source_bindings'][0]['status'] == 'SOURCE_RECEIPT_MISSING'
        capture['leagues'][0]['evaluation_input']['sleeper_baseline_receipt'] = source_receipt
        evaluation['leagues'][0]['paired_projection_rows'][0]['sleeper_mean'] = 11
        assert audit(root, capture, evaluation)['status_counts'] == {'CAPTURED_VALUE_DIFFERS_FROM_ARCHIVE': 1}
        capture['generated_at'] = '2026-10-01T05:00:00Z'
        assert audit(root, capture, evaluation)['reason'] == 'ARCHIVE_AFTER_KICKOFF_OR_CAPTURE'
        capture['generated_at'] = '2026-10-01T12:00:00Z'
        archive = Path(receipt['path'])
        archive.write_bytes(archive.read_bytes() + b'changed')
        assert audit(root, capture, evaluation)['reason'] == 'ARCHIVE_HASH_MISMATCH'
        archive.unlink()
        assert audit(root, capture, evaluation)['reason'] == 'ARCHIVE_OR_SIDECAR_MISSING'
        assert current.sleeper_baseline_source_receipt(
            [{'player_id': 'a', 'stats': {'rec': 10}}], 2026, 4,
            root/'data/research/market/sleeper', 'scoring:one')['status'] == 'ARCHIVE_MISSING'
    print('PASS PR2 Sleeper archive: matching and divergent means, source cutoff, hash and missing receipt')


if __name__ == '__main__':
    main()
