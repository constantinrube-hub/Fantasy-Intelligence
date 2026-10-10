#!/usr/bin/env python3
"""Pregame raw-response identity joins remain exact, timed and retrospective."""
import json
import tempfile
from datetime import datetime, timezone
from pathlib import Path
from unittest.mock import patch

import capture_fie_availability as availability
import weekly_usage_historical_identity as historical


def main():
    with tempfile.TemporaryDirectory() as directory:
        root = Path(directory)
        report_path = root / 'data/operations/weekly-performance/2026/week_04/reports/report.json'
        report_path.parent.mkdir(parents=True)
        report_path.write_text(json.dumps({'as_of_utc': '2026-10-08T12:00:00Z',
                                           'games': [{'game_id': 'early', 'kickoff_at': '2026-10-02T00:15:00Z'},
                                                     {'game_id': 'later', 'kickoff_at': '2026-10-05T17:00:00Z'}]}))
        usage = {'season': 2026, 'week': 4,
                 'performance_report': {'sha256': 'a' * 64}, 'dictionary': {'sha256': 'b' * 64},
                 'rows': [{'game_id': game, 'team': 'AAA', 'source_gsis_player_id': sid,
                           'source_row_index': index} for index, (game, sid) in enumerate([
                               ('early', 'gsis:g1'), ('later', 'gsis:g1'), ('later', 'gsis:g2'),
                               ('later', 'gsis:g3'), ('later', None)])]}
        players = availability.fixture_players()
        players['1']['gsis_id'] = 'g1'
        players['2']['gsis_id'] = 'g2'
        players['3']['gsis_id'] = 'g2'
        archive_root = root / historical.ARCHIVE_ROOT
        with patch.object(availability, 'fixture_players', return_value=players):
            receipt = availability.capture(output_root=archive_root, fixture=True, as_of='2026-10-03')
        with patch.object(historical, 'build_usage', return_value=usage):
            result = historical.build(root, report_path)
            assert [row['status'] for row in result['rows']] == [
                'BLOCKED_NO_SOURCE_BACKED_PREGAME_ARCHIVE', 'MATCHED_EXACT_PREGAME_GSIS',
                'AMBIGUOUS_PREGAME_GSIS', 'UNMATCHED_PREGAME_GSIS', 'SOURCE_PLAYER_ID_MISSING']
            assert [row['sleeper_player_id'] for row in result['rows']] == [None, '1', None, None, None]
            assert all(row['canonical_player_id'] is None for row in result['rows'])
            assert result['game_source_bindings']['early']['source'] is None
            assert result['game_source_bindings']['later']['source']['source_payload_sha256'] == receipt['source_payload_sha256']
            assert result['governance']['target_week_pregame_feature_eligible'] is False
            now = datetime(2026, 10, 10, 12, tzinfo=timezone.utc)
            first = historical.ensure_completed(root, 2026, 5, now)
            second = historical.ensure_completed(root, 2026, 5, now)
            assert first['status'] == 'HISTORICAL_IDENTITY_CREATED'
            assert second['status'] == 'NO_OP_EXISTING_HISTORICAL_IDENTITY'
            assert historical.ensure_completed(root, 2026, 5, datetime(2026, 10, 7, tzinfo=timezone.utc))['status'] == 'NO_OP_NO_STORED_PERFORMANCE_REPORT'
            source_path = Path(receipt['snapshot_path']).parent / receipt['source_archive']
            original = source_path.read_bytes()
            source_path.write_bytes(original + b'changed')
            try:
                historical.build(root, report_path)
                raise AssertionError('Corrupt archived response accepted')
            except ValueError as exc:
                assert 'archive hash mismatch' in str(exc)
    print('PASS weekly usage historical identity: archived response, pregame cutoff, ambiguous IDs, immutable retry, tampering blocked')


if __name__ == '__main__':
    main()
