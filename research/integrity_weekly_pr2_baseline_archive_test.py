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
        capture = {'generated_at': '2026-10-01T12:00:00Z', 'leagues': [
            {'league_id': '1', 'evaluation_input': {'scoring_settings': {'rec': 1}, 'active_candidates': [
                {'captured_player_id': 'canonical:a', 'sleeper_id': 'a', 'position_model': 'RB'}]}}]}
        evaluation = {'season': 2026, 'week': 4, 'leagues': [
            {'league_id': '1', 'status': 'READY', 'paired_projection_rows': [
                {'captured_player_id': 'canonical:a', 'sleeper_mean': 10}]}]}
        result = audit(root, capture, evaluation)
        assert result['status_counts'] == {'VALUE_REPRODUCED_FROM_ARCHIVE': 1}
        assert result['scoring_comparability_certified'] is False
        assert result['archive']['sha256'] == receipt['sha256']
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
    print('PASS PR2 Sleeper archive: matching and divergent means, source cutoff, hash and missing receipt')


if __name__ == '__main__':
    main()
