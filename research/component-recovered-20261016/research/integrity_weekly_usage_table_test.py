#!/usr/bin/env python3
"""Source-bound retrospective usage rows preserve null, zero and unresolved IDs."""
import csv
import gzip
import hashlib
import io
import json
import shutil
import tempfile
from pathlib import Path

from point_in_time_capture import build_envelope, canonical_bytes
from weekly_evidence_audit import stamp
import weekly_player_performance as performance
import weekly_usage_table as usage


def main() -> None:
    with tempfile.TemporaryDirectory() as td:
        root = Path(td)
        dictionary = root / usage.DICTIONARY_PATH
        dictionary.parent.mkdir(parents=True)
        shutil.copyfile(Path(__file__).resolve().parents[1] / usage.DICTIONARY_PATH, dictionary)
        schedule = root / 'data/research/context/weather/2026/week_04/a/schedule-source-envelope.json'
        schedule.parent.mkdir(parents=True)
        games = {'season': 2026, 'week': 4, 'games': [{'game_id': 'game', 'home_team': 'AAA', 'away_team': 'BBB',
                                                    'kickoff': '2026-10-05T17:00:00Z'}]}
        schedule.write_text(json.dumps({'observed_at': '2026-10-01T00:00:00Z', 'payload': games,
                                        'payload_sha256': hashlib.sha256(canonical_bytes(games)).hexdigest()}))
        rows = [
            {'player_id': 'a', 'player_display_name': 'A', 'season': '2026', 'week': '4', 'season_type': 'REG',
             'game_id': 'game', 'team': 'AAA', 'targets': '0', 'receptions': '0', 'carries': '3'},
            {'player_id': '', 'player_display_name': 'Unattributed', 'season': '2026', 'week': '4', 'season_type': 'REG',
             'game_id': 'game', 'team': 'BBB', 'targets': '2', 'receptions': '', 'carries': ''},
        ]
        stream = io.StringIO()
        writer = csv.DictWriter(stream, fieldnames=list(rows[0])); writer.writeheader(); writer.writerows(rows)
        raw = stream.getvalue().encode()
        archive = root / 'data/operations/weekly-performance/2026/week_04/sources/raw.csv.gz'
        archive.parent.mkdir(parents=True)
        archive.write_bytes(gzip.compress(raw, mtime=0))
        source_path = archive.with_name('source-envelope.json')
        source_path.write_text(json.dumps(build_envelope(
            capture_id='usage-fixture', capture_intent='OTHER_GOVERNED', provider='fixture', endpoint='fixture',
            observed_at='2026-10-06T06:00:00Z', as_of_semantics='retrospective',
            payload={'season': 2026, 'week': 4, 'rows': performance.target_rows(raw, 2026, 4),
                     'raw_path': archive.relative_to(root).as_posix(), 'raw_response_sha256': hashlib.sha256(raw).hexdigest(),
                     'raw_archive_sha256': performance.digest(archive)})))
        as_of = stamp('2026-10-06T07:00:00Z')
        report = performance.build(root, source_path, 2026, 4, as_of)
        report_path = root / 'data/operations/weekly-performance/2026/week_04/reports/report.json'
        report_path.parent.mkdir(parents=True)
        report_path.write_text(json.dumps(report))
        result = usage.build(root, report_path)
        assert result['player_game_rows'] == 2 and result['unresolved_source_rows'] == 1
        assert result['status'] == 'DESCRIPTIVE_PARTIAL'
        by_team = {row['team']: row for row in result['rows']}
        assert by_team['AAA']['metrics']['targets'] == 0 and by_team['AAA']['metrics']['passing_yards'] is None
        assert by_team['BBB']['source_gsis_player_id'] is None and by_team['BBB']['canonical_player_id'] is None
        assert by_team['BBB']['metrics']['targets'] == 2 and by_team['BBB']['metrics']['receptions'] is None
        assert result['governance']['target_week_pregame_feature_eligible'] is False
        assert 'routes' in result['unsupported_fields'] and 'snaps' in result['unsupported_fields']
        first = usage.ensure_completed(root, 2026, 5, as_of)
        second = usage.ensure_completed(root, 2026, 5, as_of)
        assert first['status'] == 'USAGE_TABLE_CREATED' and second['status'] == 'NO_OP_EXISTING_USAGE_TABLE'
        bad = json.loads(report_path.read_text()); bad['games'][0]['teams'][0]['players'][0]['metrics']['targets'] = 99
        report_path.write_text(json.dumps(bad))
        try:
            usage.build(root, report_path)
            raise AssertionError('tampered performance metrics accepted')
        except ValueError as exc:
            assert 'REPLAY_MISMATCH' in str(exc)
    print('PASS weekly usage: source replay, null versus zero, unresolved GSIS, immutable retry, no pregame authority')


if __name__ == '__main__':
    main()
