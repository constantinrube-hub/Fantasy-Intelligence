"""Exact source-identifier bridge for descriptive snap research."""
from __future__ import annotations

import argparse
from collections import Counter
from datetime import datetime, timezone
import hashlib
from pathlib import Path
import re

from point_in_time_capture import first_write_json
from research_feature_tables import snap_table
from research_source_archive import read


def bind(rows: list[dict], identity_rows: list[dict]) -> dict:
    lookup = {}
    for row in identity_rows:
        pfr = str(row.get('pfr_id') or '').strip()
        gsis = str(row.get('gsis_id') or '').strip()
        if not pfr:
            continue
        if pfr in lookup:
            raise ValueError('SNAP_DUPLICATE_PFR_BINDING')
        lookup[pfr] = gsis if re.fullmatch(r'00-\d{7}', gsis) else None
    output, statuses, seen = [], Counter(), set()
    for row in rows:
        source_id = row.get('source_pfr_player_id')
        if not isinstance(source_id, str) or not source_id.startswith('pfr:') or not source_id[4:]:
            raise ValueError('SNAP_PFR_SOURCE_ID_INVALID')
        pfr = source_id[4:]
        status = ('BLOCKED_PFR_ID_UNMAPPED' if pfr not in lookup else
                  'BLOCKED_GSIS_IDENTITY' if lookup[pfr] is None else 'CANONICAL_GSIS_BOUND')
        if lookup.get(pfr) is not None:
            canonical_key = (row.get('season'), row.get('week'), row.get('game_id'), row.get('team'), lookup[pfr])
            if canonical_key in seen:
                raise ValueError('SNAP_DUPLICATE_CANONICAL_PLAYER_GAME')
            seen.add(canonical_key)
        statuses[status] += 1
        output.append({**row, 'canonical_player_id': lookup.get(pfr), 'identity_status': status,
                       'identity_join_method': 'EXACT_PFR_TO_GSIS_SOURCE_BINDING',
                       'percentage_scale': 'UNVERIFIED', 'offense_snap_share': None,
                       'routes': None, 'production_authorized': False})
    return {'rows': output, 'identity_status_counts': dict(statuses),
            'name_matching_used': False, 'production_authorized': False}


def build(root: Path, snaps: Path, identity: Path, *, season: int, target_week: int, cutoff: str) -> dict:
    if isinstance(target_week, bool) or not 1 <= target_week <= 18:
        raise ValueError('SNAP_TARGET_WEEK_INVALID')
    raw_snaps, snap_receipt = read(root, snaps, kind='snaps', season=season, cutoff=cutoff)
    raw_identity, identity_receipt = read(root, identity, kind='identity', season=season, cutoff=cutoff)
    prior = snap_table(raw_snaps, season, target_week)
    report = bind(prior['rows'], raw_identity)
    return {'schema': 'fie-research-canonical-snaps-v1', 'season': season,
            'target_week': target_week, 'cutoff': cutoff, 'snapshot_scope': 'OBSERVED_MASTER_NOT_HISTORICAL_IDENTITY_AVAILABILITY',
            'builder_sha256': {name: hashlib.sha256(Path(__file__).with_name(name).read_bytes()).hexdigest()
                               for name in ('research_snap_identity.py', 'research_feature_tables.py', 'research_source_archive.py')},
            'sources': {'snaps': snap_receipt, 'identity': identity_receipt},
            'excluded_rows': prior['excluded_rows'], **report}


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--root', type=Path, default=Path(__file__).resolve().parents[1])
    parser.add_argument('--snaps', type=Path, required=True)
    parser.add_argument('--identity', type=Path, required=True)
    parser.add_argument('--season', type=int, required=True)
    parser.add_argument('--target-week', type=int, required=True)
    parser.add_argument('--cutoff', required=True)
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    result = build(args.root, args.snaps, args.identity, season=args.season,
                   target_week=args.target_week, cutoff=args.cutoff)
    result['generated_at'] = datetime.now(timezone.utc).isoformat()
    first_write_json(args.output, result)
    print(result['identity_status_counts'])


if __name__ == '__main__':
    main()
