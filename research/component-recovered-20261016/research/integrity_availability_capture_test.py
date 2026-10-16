#!/usr/bin/env python3
"""No-network regression coverage for expanded immutable availability capture."""
from __future__ import annotations

import contextlib
from datetime import datetime, timezone
import gzip
import io
import json
from pathlib import Path
import tempfile
from unittest.mock import patch

import capture_fie_availability as m


def rejected(call):
    try:
        call()
    except (ValueError, FileNotFoundError):
        return
    raise AssertionError('Expected fail-closed rejection')


def main():
    # Berlin boundary guards, DST, and January's previous football season.
    for when, allowed in [
        ('2026-08-31T21:59:59Z', False), ('2026-08-31T22:00:00Z', True),
        ('2026-10-25T00:29:00Z', True), ('2026-10-25T01:29:00Z', True),
        ('2027-01-10T22:59:59Z', True), ('2027-01-10T23:00:00Z', False),
        ('2027-01-12T07:29:00Z', False), ('2027-04-25T06:29:00Z', False),
        ('2027-04-26T06:29:00Z', False), ('2027-08-31T06:29:00Z', False),
    ]:
        assert m.automatic_capture_allowed(when) is allowed
    assert m.football_season('2027-01-10T08:29:00Z') == 2026
    assert m.football_season('2026-08-31T22:00:00Z') == 2026
    rejected(lambda: m.automatic_capture_allowed('2026-10-03T08:00:00'))
    workflow = Path(__file__).resolve().parents[1] / '.github/workflows/capture-fie-availability.yml'
    text = workflow.read_text()
    assert '"29 8 * 9-12 *"' in text and '"29 8 1-10 1 *"' in text
    assert text.count('timezone: "Europe/Berlin"') == 2
    assert "github.ref == 'refs/heads/main'" in text and 'ref: main' in text

    # Every named IDP subtype, K/P, multi-position eligibility and no team D/ST.
    raw = m.fixture_players()
    for pos in sorted(m.IDP_POSITIONS | m.KICKER_POSITIONS):
        raw['p-' + pos] = {'player_id': 'p-' + pos, 'position': pos, 'team': None, 'status': None}
    raw['hybrid'] = {'position': 'ATH', 'fantasy_positions': ['DB', 'LB'], 'team': 'AAA'}
    raw['unknown'] = {'fantasy_positions': ['DL'], 'team': 'AAA'}
    raw['punter'] = {'position': 'P', 'fantasy_positions': ['P'], 'team': 'AAA'}
    raw['bad-team'] = {'position': 'LB', 'fantasy_positions': ['DEF'], 'team': 'AAA'}
    rows = m.compact(raw, '2026-10-03T08:29:00Z', '2026-10-03')
    by_id = {row['sleeper_id']: row for row in rows}
    assert set('p-' + pos for pos in m.IDP_POSITIONS | m.KICKER_POSITIONS) <= by_id.keys()
    assert 'AAA' not in by_id and 'bad-team' not in by_id and 'punter' not in by_id
    assert by_id['hybrid']['position_model'] == 'ATH' and by_id['hybrid']['fantasy_positions'] == ['DB', 'LB']
    assert by_id['unknown']['position_model'] is None
    assert by_id['5']['team'] is None and by_id['5']['active'] is False
    assert 'injury_status' not in by_id['3'] and 'status' not in by_id['p-LB']
    assert m.group_for(by_id['hybrid']) == 'IDP'
    assert m.coverage(rows)['IDP']['non_null_field_counts']['active'] == 1
    rejected(lambda: m.compact({'bad': None}, '2026-10-03T08:29:00Z', '2026-10-03'))
    rejected(lambda: m.compact({'a': {'player_id':'same','position':'K'}, 'b': {'player_id':'same','position':'K'}}, '2026-10-03T08:29:00Z', '2026-10-03'))

    with tempfile.TemporaryDirectory() as folder:
        root = Path(folder)
        # Idempotent retry does not fetch, change gzip bytes or upgrade old rows.
        result = m.capture(output_root=root, fixture=True, as_of='2026-10-03')
        path = Path(result['snapshot_path'])
        before = {p.name: p.read_bytes() for p in path.parent.iterdir()}
        with patch.object(m, 'fetch_players', side_effect=AssertionError('Retry must not fetch')), patch.object(m, 'now_iso', return_value='2026-10-03T15:00:00Z'):
            retry = m.capture(output_root=root)
        assert retry['capture_status'] == 'EXISTS'
        assert before == {p.name: p.read_bytes() for p in path.parent.iterdir()}
        assert result['coverage']['IDP']['rows'] == 2 and result['coverage']['KICKER']['rows'] == 1

        # Stored response authentication, metadata coverage and payload changes.
        meta_path = Path(str(path) + '.meta.json')
        meta = json.loads(meta_path.read_text())
        corrupted = {**meta, 'coverage': {}}
        meta_path.write_text(json.dumps(corrupted))
        rejected(lambda: m.validate_capture(path))
        meta_path.write_bytes(before[meta_path.name])
        source = path.parent / meta['source_archive']
        original = source.read_bytes()
        source.write_bytes(original + b'changed')
        rejected(lambda: m.validate_capture(path))
        source.write_bytes(original)
        assert m.validate_capture(path)['capture_contract'] == m.CONTRACT

        # Legacy daily offense-only archive remains byte-exact; a supplement is
        # observed now rather than pretending IDP was present in the old capture.
        legacy_root = root / 'legacy'
        legacy = legacy_root / '2026/availability_2026-10-03.jsonl.gz'
        legacy.parent.mkdir(parents=True)
        with gzip.open(legacy, 'wt') as handle:
            handle.write(json.dumps({'position_model': 'RB'}) + '\n')
        legacy_meta = Path(str(legacy) + '.meta.json')
        legacy_meta.write_text(json.dumps({'rows': 1, 'captured_at': '2026-10-03T06:29:00Z'}))
        old_bytes = (legacy.read_bytes(), legacy_meta.read_bytes())
        new = m.capture(output_root=legacy_root, fixture=True, as_of='2026-10-03')
        assert new['snapshot_path'].endswith('_expanded-v1.jsonl.gz')
        assert old_bytes == (legacy.read_bytes(), legacy_meta.read_bytes())

        # Scheduling exits before source requests, manual operation remains
        # explicit, and live data cannot impersonate an earlier observation.
        with patch.object(m, 'now_iso', return_value='2027-01-11T08:29:00Z'), patch.object(m, 'fetch_players', side_effect=AssertionError('Outside season must not fetch')):
            assert m.capture(output_root=root, automatic=True)['capture_status'] == 'SKIPPED_OUTSIDE_SEASON'
            rejected(lambda: m.capture(output_root=root, as_of='2026-10-03'))
            rejected(lambda: m.capture(output_root=root, as_of='2027-02-30'))
        jan = m.capture(output_root=root, fixture=True, automatic=True, as_of='2027-01-10')
        assert '/2026/availability_2027-01-10.jsonl.gz' in Path(jan['snapshot_path']).as_posix()

        # Actual timestamps follow response completion, even at UTC rollover.
        with patch.object(m, 'now_iso', side_effect=['2026-10-03T23:59:59Z','2026-10-04T00:00:01Z']), patch.object(m, 'fetch_players', return_value=m.fixture_players()):
            rollover = m.capture(output_root=root / 'rollover')
        assert rollover['availability_as_of'] == '2026-10-04' and rollover['captured_at'].endswith('00:00:01Z')
        with patch.object(m, 'now_iso', return_value='2026-10-03T08:29:00Z'), patch.object(m, 'fetch_players', side_effect=RuntimeError('source unavailable')):
            try:
                m.capture(output_root=root / 'source-failure')
            except RuntimeError:
                pass
            else:
                raise AssertionError('Source failure must not become empty availability')
        assert not (root / 'source-failure').exists()

        # Exact output-index path remains tied to this invocation.
        index = root / 'output.json'
        with contextlib.redirect_stdout(io.StringIO()):
            m.main(['--fixture', '--as-of', '2026-10-03', '--output-root', str(root), '--output-index', str(index)])
        assert json.loads(index.read_text())['snapshot_path'] == str(path)
    print('PASS availability capture (7 scenario groups)')


if __name__ == '__main__':
    main()
