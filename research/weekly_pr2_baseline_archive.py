#!/usr/bin/env python3
"""Read-only reproduction of PR2 Sleeper means from the frozen market archive."""
from __future__ import annotations

import gzip
import json
from collections import Counter
from pathlib import Path

from league_profile import sha256_json
from weekly_evidence_audit import digest, stamp


def audit(root: Path, capture: dict, evaluation: dict) -> dict:
    from build_current_snapshot import score_sleeper_projection

    season, week = evaluation.get('season'), evaluation.get('week')
    base = root / f'data/research/market/sleeper/{season}/week_{int(week):02d}.jsonl.gz'
    meta_path = Path(str(base) + '.meta.json')
    blocked = lambda reason: {'status': 'BLOCKED_BASELINE_ARCHIVE', 'reason': reason,
                              'archive': None, 'paired_rows': 0, 'status_counts': {}}
    if not base.is_file() or not meta_path.is_file():
        return blocked('ARCHIVE_OR_SIDECAR_MISSING')
    try:
        meta = json.loads(meta_path.read_text(encoding='utf-8'))
        capture_time = stamp(capture['generated_at'])
        observed, kickoff = stamp(meta['captured_at']), stamp(meta['first_kickoff_utc'])
        if (meta.get('season'), meta.get('week')) != (season, week) or meta.get('pregame_eligible') is not True:
            return blocked('ARCHIVE_TARGET_OR_PREGAME_STATUS_INVALID')
        if not observed < kickoff or observed > capture_time:
            return blocked('ARCHIVE_AFTER_KICKOFF_OR_CAPTURE')
        if meta.get('sha256') != digest(base):
            return blocked('ARCHIVE_HASH_MISMATCH')
        archived = {}
        with gzip.open(base, 'rt', encoding='utf-8') as stream:
            for line in stream:
                if not line.strip():
                    continue
                row = json.loads(line)
                if ((row.get('season'), row.get('week')) != (season, week) or
                    row.get('captured_at') != meta['captured_at'] or row.get('pregame_eligible') is not True):
                    return blocked('ARCHIVE_ROW_TARGET_OR_TIME_INVALID')
                sid = str(row.get('sleeper_id') or '')
                if not sid or sid in archived:
                    return blocked('ARCHIVE_PLAYER_ID_DUPLICATE_OR_MISSING')
                archived[sid] = row
        if not archived or len(archived) != meta.get('rows'):
            return blocked('ARCHIVE_ROW_COUNT_INVALID')
    except (OSError, ValueError, TypeError, KeyError, json.JSONDecodeError):
        return blocked('ARCHIVE_UNREADABLE_OR_METADATA_INVALID')

    reports = {str(item.get('league_id')): item for item in capture.get('leagues', []) if isinstance(item, dict)}
    counts = Counter()
    source_bindings = []
    archived_stats_hash = sha256_json({sid: row.get('stats') for sid, row in archived.items()})
    for league in evaluation.get('leagues', []):
        if league.get('status') != 'READY':
            continue
        source = (reports.get(str(league.get('league_id'))) or {}).get('evaluation_input') or {}
        receipt = source.get('sleeper_baseline_receipt') or {}
        binding_status = 'SOURCE_RECEIPT_MISSING'
        try:
            if receipt:
                if (receipt.get('season'), receipt.get('week')) != (season, week):
                    binding_status = 'SOURCE_RECEIPT_TARGET_MISMATCH'
                elif (receipt.get('archive_sha256') != meta['sha256'] or
                      receipt.get('archive_stats_sha256') != archived_stats_hash or
                      receipt.get('archive_captured_at') != meta['captured_at']):
                    binding_status = 'SOURCE_RECEIPT_ARCHIVE_MISMATCH'
                elif (not receipt.get('source_observed_at') or
                      not observed <= stamp(receipt['source_observed_at']) <= capture_time):
                    binding_status = 'SOURCE_RECEIPT_TIME_INVALID'
                elif (not receipt.get('scoring_signature') or receipt.get('scoring_signature') !=
                      (league.get('capture_evidence') or {}).get('scoring_signature')):
                    binding_status = 'SOURCE_RECEIPT_SCORING_SIGNATURE_MISMATCH'
                elif (receipt.get('status') == 'ARCHIVED_PROJECTION_STATS_MATCH' and
                      receipt.get('refresh_stats_sha256') == archived_stats_hash and
                      receipt.get('archive_player_count') == len(archived) and
                      receipt.get('refresh_player_count') == len(archived)):
                    binding_status = 'REFRESH_PROJECTION_STATS_BOUND_TO_ARCHIVE'
                else:
                    binding_status = 'REFRESH_PROJECTION_STATS_UNBOUND'
        except (TypeError, ValueError, KeyError, AttributeError):
            binding_status = 'SOURCE_RECEIPT_INVALID'
        source_bindings.append({'league_id': str(league.get('league_id')), 'status': binding_status})
        candidates = {str(item.get('captured_player_id')): item for item in source.get('active_candidates', []) if isinstance(item, dict)}
        scoring = source.get('scoring_settings') or {}
        for pair in league.get('paired_projection_rows', []):
            candidate = candidates.get(str(pair.get('captured_player_id'))) or {}
            row = archived.get(str(candidate.get('sleeper_id') or ''))
            if row is None:
                counts['ARCHIVE_PLAYER_MISSING'] += 1
            elif row.get('position_model') and row['position_model'] != candidate.get('position_model'):
                counts['ARCHIVE_POSITION_MISMATCH'] += 1
            elif not isinstance(row.get('stats'), dict) or not scoring:
                counts['ARCHIVE_RAW_STATS_OR_SCORING_MISSING'] += 1
            else:
                try:
                    reproduced = round(score_sleeper_projection(row['stats'], scoring, candidate.get('position_model') or ''), 4)
                    captured = round(float(pair['sleeper_mean']), 4)
                except (TypeError, ValueError, OverflowError):
                    counts['ARCHIVE_SCORING_REPLAY_INVALID'] += 1
                    continue
                counts['VALUE_REPRODUCED_FROM_ARCHIVE' if reproduced == captured else 'CAPTURED_VALUE_DIFFERS_FROM_ARCHIVE'] += 1
    count = sum(counts.values())
    return {'status': 'PARTIAL_BASELINE_ARCHIVE_REPLAY' if count else 'BLOCKED_NO_PAIRED_ROWS',
            'archive': {'path': base.relative_to(root).as_posix(), 'sha256': meta['sha256'],
                        'sidecar_path': meta_path.relative_to(root).as_posix(), 'sidecar_sha256': digest(meta_path),
                        'captured_at_utc': observed.isoformat(), 'first_kickoff_utc': kickoff.isoformat()},
            'paired_rows': count, 'status_counts': dict(sorted(counts.items())),
            'refresh_source_bindings': source_bindings,
            'refresh_source_bound_leagues': sum(row['status'] == 'REFRESH_PROJECTION_STATS_BOUND_TO_ARCHIVE' for row in source_bindings),
            'scoring_comparability_certified': False,
            'note': 'This replays the existing Sleeper scoring function on stored archive stats. A bound refresh receipt proves the fetched projection stats matched the archived projection stats, but does not prove every scoring key was supported or that independent league-player rows exist.'}
