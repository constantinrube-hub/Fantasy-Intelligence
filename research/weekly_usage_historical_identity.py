#!/usr/bin/env python3
"""Retrospective usage ID coverage from verified, pregame Sleeper response archives."""
from __future__ import annotations

import argparse
import gzip
import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path

from capture_fie_availability import CONTRACT, validate_capture
from point_in_time_capture import first_write_json, canonical_bytes
from weekly_evidence_audit import digest, stamp
from weekly_usage_table import build as build_usage


SCHEMA = 'fie-weekly-usage-historical-identity-v1'
ARCHIVE_ROOT = Path('data/research/availability/sleeper')


def verified_archives(root: Path, season: int, last_kickoff: datetime) -> list[dict]:
    sources = []
    for path in sorted((root / ARCHIVE_ROOT / str(season)).glob('availability_*.jsonl.gz')):
        sidecar = Path(str(path) + '.meta.json')
        if not sidecar.is_file():
            continue  # Legacy archives have no source-backed identity receipt.
        declared = json.loads(sidecar.read_text(encoding='utf-8'))
        if declared.get('capture_contract') != CONTRACT:
            continue
        observed = stamp(declared['captured_at'])
        if observed > last_kickoff:
            continue
        meta = validate_capture(path)  # Replays compact rows against the original response.
        if meta['season'] != season:
            raise ValueError('HISTORICAL_IDENTITY_ARCHIVE_SEASON_MISMATCH')
        source = path.parent / meta['source_archive']
        with gzip.open(source, 'rt', encoding='utf-8') as stream:
            response = json.load(stream)
        by_gsis: dict[str, set[str]] = {}
        for sleeper_id, player in response['payload'].items():
            if not isinstance(player, dict):
                continue
            if player.get('player_id') is not None and str(player['player_id']) != str(sleeper_id):
                raise ValueError('HISTORICAL_IDENTITY_SOURCE_PLAYER_ID_MISMATCH')
            gsis = player.get('gsis_id')
            if isinstance(gsis, str) and gsis.strip():
                by_gsis.setdefault(gsis.strip(), set()).add(str(sleeper_id))
        sources.append({'observed': observed, 'by_gsis': by_gsis,
                        'binding': {'snapshot_path': path.relative_to(root).as_posix(),
                                    'snapshot_sha256': meta['snapshot_sha256'],
                                    'meta_path': sidecar.relative_to(root).as_posix(), 'meta_sha256': digest(sidecar),
                                    'source_path': source.relative_to(root).as_posix(),
                                    'source_archive_sha256': meta['source_archive_sha256'],
                                    'source_payload_sha256': meta['source_payload_sha256'],
                                    'observed_at_utc': observed.isoformat()}})
    return sorted(sources, key=lambda item: (item['observed'], item['binding']['snapshot_path']))


def build(root: Path, performance_path: Path) -> dict:
    root, performance_path = root.resolve(), performance_path.resolve()
    usage = build_usage(root, performance_path)  # Exact source/dictionary/performance replay.
    performance = json.loads(performance_path.read_text(encoding='utf-8'))
    kickoffs = {str(game['game_id']): stamp(game['kickoff_at']) for game in performance['games']}
    if not kickoffs or any(str(row['game_id']) not in kickoffs for row in usage['rows']):
        raise ValueError('HISTORICAL_IDENTITY_GAME_KICKOFF_MISSING')
    archives = verified_archives(root, usage['season'], max(kickoffs.values()))
    game_sources = {}
    for game_id, kickoff in sorted(kickoffs.items()):
        earlier = [source for source in archives if source['observed'] <= kickoff]
        game_sources[game_id] = earlier[-1] if earlier else None
    counts = {status: 0 for status in ('MATCHED_EXACT_PREGAME_GSIS', 'UNMATCHED_PREGAME_GSIS',
                                       'AMBIGUOUS_PREGAME_GSIS', 'SOURCE_PLAYER_ID_MISSING',
                                       'BLOCKED_NO_SOURCE_BACKED_PREGAME_ARCHIVE')}
    rows = []
    for row in usage['rows']:
        game_id, source_id = str(row['game_id']), row['source_gsis_player_id']
        archive = game_sources[game_id]
        matches = archive['by_gsis'].get(source_id[5:], set()) if archive and source_id else set()
        status = ('SOURCE_PLAYER_ID_MISSING' if source_id is None else
                  'BLOCKED_NO_SOURCE_BACKED_PREGAME_ARCHIVE' if archive is None else
                  'UNMATCHED_PREGAME_GSIS' if not matches else
                  'AMBIGUOUS_PREGAME_GSIS' if len(matches) > 1 else 'MATCHED_EXACT_PREGAME_GSIS')
        counts[status] += 1
        rows.append({'game_id': game_id, 'team': row['team'],
                     'source_gsis_player_id': source_id, 'source_row_index': row['source_row_index'],
                     'sleeper_player_id': next(iter(matches)) if len(matches) == 1 else None,
                     'canonical_player_id': None, 'status': status})
    bindings = {game_id: {'kickoff_at_utc': kickoff.isoformat(),
                          'source': game_sources[game_id]['binding'] if game_sources[game_id] else None}
                for game_id, kickoff in sorted(kickoffs.items())}
    return {'schema': SCHEMA, 'season': usage['season'], 'week': usage['week'],
            'performance_report': usage['performance_report'], 'usage_dictionary': usage['dictionary'],
            'game_source_bindings': bindings, 'player_game_rows': len(rows), 'status_counts': counts, 'rows': rows,
            'governance': {'retrospective_only': True, 'target_week_pregame_feature_eligible': False,
                           'canonical_identity_resolved': False, 'model_or_ranking_changed': False,
                           'note': 'Each exact Sleeper ID candidate comes from an authenticated full player response observed before its game kickoff. Missing earlier source archives stay blocked. Realized usage rows and these joins are retrospective; no name/team inference or backdating.'}}


def ensure_completed(root: Path, season: int, current_week: int, as_of: datetime) -> dict:
    root = root.resolve()
    if as_of.tzinfo is None or not 1 <= current_week <= 18:
        raise ValueError('HISTORICAL_IDENTITY_TARGET_OR_TIME_INVALID')
    candidates = []
    for week in range(1, current_week + 1):
        for path in (root / f'data/operations/weekly-performance/{season}/week_{week:02d}/reports').glob('*.json'):
            report = json.loads(path.read_text(encoding='utf-8'))
            observed = stamp(report['as_of_utc'])
            if observed <= as_of:
                candidates.append((week, observed, path))
    if not candidates:
        return {'status': 'NO_OP_NO_STORED_PERFORMANCE_REPORT', 'season': season}
    week, _, path = max(candidates, key=lambda item: (item[0], item[1], str(item[2])))
    report = build(root, path)
    identity = hashlib.sha256(canonical_bytes(report['game_source_bindings'])).hexdigest()
    output = root / f'data/operations/weekly-usage-identity/{season}/week_{week:02d}/historical-{report["performance_report"]["sha256"][:12]}-{report["usage_dictionary"]["sha256"][:12]}-{identity[:12]}.json'
    state = first_write_json(output, report)
    return {'status': 'HISTORICAL_IDENTITY_CREATED' if state == 'CREATED' else 'NO_OP_EXISTING_HISTORICAL_IDENTITY',
            'season': season, 'week': week, 'report': output.relative_to(root).as_posix(),
            'status_counts': report['status_counts']}


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument('--root', type=Path, default=Path(__file__).resolve().parents[1])
    parser.add_argument('--season', type=int, required=True)
    parser.add_argument('--week', type=int, required=True)
    args = parser.parse_args()
    print(json.dumps(ensure_completed(args.root, args.season, args.week, datetime.now(timezone.utc)), sort_keys=True))


if __name__ == '__main__':
    main()
