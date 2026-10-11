"""Immutable raw CSV receipts for scoped nflverse research sources."""
from __future__ import annotations

import argparse
import csv
from datetime import datetime, timezone
import io
import json
from pathlib import Path
import requests

from point_in_time_capture import first_write_json, sha256_bytes
from weekly_evidence_audit import digest, stamp

ENDPOINTS = {
    'identity': 'https://github.com/nflverse/nflverse-data/releases/download/players/players.csv',
    'pbp': 'https://github.com/nflverse/nflverse-data/releases/download/pbp/play_by_play_{season}.csv',
    'snaps': 'https://github.com/nflverse/nflverse-data/releases/download/snap_counts/snap_counts_{season}.csv',
    'schedule': 'https://raw.githubusercontent.com/nflverse/nfldata/master/data/games.csv',
}
HEADERS = {'identity': {'gsis_id','pfr_id'}, 'pbp': {'game_id','play_id','season','week','posteam'},
           'snaps': {'game_id','season','week','pfr_player_id','team','offense_snaps'},
           'schedule': {'game_id','season','week','home_team','away_team','gameday','gametime'}}


def parse(raw: bytes, kind: str) -> list[dict]:
    stream = csv.DictReader(io.StringIO(raw.decode('utf-8-sig')))
    if not HEADERS[kind] <= set(stream.fieldnames or []):
        raise ValueError('RESEARCH_SOURCE_CSV_SCHEMA_MISMATCH')
    if len(stream.fieldnames) != len(set(stream.fieldnames)):
        raise ValueError('RESEARCH_SOURCE_DUPLICATE_COLUMNS')
    rows = list(stream)
    if not rows or any(None in row or any(v is None for v in row.values()) for row in rows):
        raise ValueError('RESEARCH_SOURCE_EMPTY_OR_MALFORMED_ROWS')
    return rows


def archive(root: Path, kind: str, season: int, raw: bytes, observed_at: str) -> Path:
    if kind not in ENDPOINTS or isinstance(season, bool) or not 1999 <= season <= 2100:
        raise ValueError('RESEARCH_SOURCE_TARGET_INVALID')
    observed = stamp(observed_at)
    rows = parse(raw, kind)
    if kind != 'identity' and not any(row['season'] == str(season) for row in rows):
        raise ValueError('RESEARCH_SOURCE_SEASON_ABSENT')
    sha = sha256_bytes(raw)
    base = root.resolve() / f'data/research/feature-lab/raw/{kind}/{season}/{observed.strftime("%Y%m%dT%H%M%S%fZ")}-{sha[:16]}'
    base.mkdir(parents=True, exist_ok=True)
    path = base/'source.csv'
    if path.exists():
        if path.read_bytes() != raw:
            raise ValueError('RESEARCH_RAW_FIRST_WRITE_COLLISION')
    else:
        with path.open('xb') as stream:
            stream.write(raw)
    receipt = base/'receipt.json'
    first_write_json(receipt, {'schema': 'fie-research-raw-csv-v1', 'kind': kind, 'season': season,
        'endpoint': ENDPOINTS[kind].format(season=season), 'observed_at': observed.isoformat(),
        'raw_path': path.relative_to(root.resolve()).as_posix(), 'raw_sha256': sha,
        'raw_size_bytes': len(raw), 'rows': len(rows), 'immutable_first_write': True,
        'as_of_semantics': 'Local download observation; original publication time and historical availability unverified.',
        'provider_percentage_scale': 'UNVERIFIED', 'production_authorized': False})
    return receipt


def read(root: Path, receipt_path: Path, *, kind: str, season: int, cutoff: str) -> tuple[list[dict], dict]:
    root, receipt_path = root.resolve(), receipt_path.resolve()
    owner = root/'data/research/feature-lab/raw'/kind/str(season)
    if not receipt_path.is_relative_to(owner) or receipt_path.name != 'receipt.json':
        raise ValueError('RESEARCH_RECEIPT_OUTSIDE_OWNER')
    receipt = json.loads(receipt_path.read_text())
    if (receipt.get('schema'),receipt.get('kind'),receipt.get('season')) != ('fie-research-raw-csv-v1',kind,season):
        raise ValueError('RESEARCH_RECEIPT_TARGET_MISMATCH')
    if receipt.get('immutable_first_write') is not True or receipt.get('production_authorized') is not False:
        raise ValueError('RESEARCH_RECEIPT_AUTHORITY_INVALID')
    if receipt.get('endpoint') != ENDPOINTS[kind].format(season=season) or stamp(receipt['observed_at']) > stamp(cutoff):
        raise ValueError('RESEARCH_RECEIPT_SOURCE_OR_CUTOFF_INVALID')
    raw_path = (root/receipt['raw_path']).resolve()
    if raw_path != receipt_path.parent/'source.csv' or not raw_path.is_file():
        raise ValueError('RESEARCH_RAW_PATH_INVALID')
    if digest(raw_path) != receipt['raw_sha256'] or raw_path.stat().st_size != receipt['raw_size_bytes']:
        raise ValueError('RESEARCH_RAW_HASH_OR_SIZE_MISMATCH')
    rows = parse(raw_path.read_bytes(), kind)
    if len(rows) != receipt['rows']:
        raise ValueError('RESEARCH_RAW_ROW_COUNT_MISMATCH')
    return rows, {'receipt_path': receipt_path.relative_to(root).as_posix(), 'receipt_sha256': digest(receipt_path), **receipt}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--root',type=Path,default=Path(__file__).resolve().parents[1])
    ap.add_argument('--kind',choices=ENDPOINTS,required=True)
    ap.add_argument('--season',type=int,required=True)
    args = ap.parse_args()
    response = requests.get(ENDPOINTS[args.kind].format(season=args.season),timeout=90)
    response.raise_for_status()
    receipt = archive(args.root,args.kind,args.season,response.content,datetime.now(timezone.utc).isoformat())
    print(receipt.relative_to(args.root.resolve()).as_posix())


if __name__ == '__main__':
    main()
