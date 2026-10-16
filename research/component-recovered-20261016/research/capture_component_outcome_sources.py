"""Immutable actual-stat captures for C1. Does not capture or fit forecasts."""
from __future__ import annotations
import argparse
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime, timezone
import gzip
import hashlib
import json
from pathlib import Path
import time
from urllib.request import urlopen

ROOT = Path(__file__).resolve().parents[1]
DEFAULT = Path('data/research/components/2026-10-14/c0-c1-v1/sources')

def sha(data):
    return hashlib.sha256(data).hexdigest()

def capture(root, folder, season, week=None):
    name = f'sleeper-{season}-{week:02d}' if week is not None else f'rosters-{season}'
    url = (f'https://api.sleeper.app/v1/stats/nfl/regular/{season}/{week}' if week is not None
           else f'https://github.com/nflverse/nflverse-data/releases/download/weekly_rosters/roster_weekly_{season}.csv')
    path = folder / (name + ('.json.gz' if week is not None else '.csv.gz'))
    receipt = folder / (name + '.receipt.json')
    if receipt.exists():
        ref = json.loads(receipt.read_text())
        if ref['endpoint'] != url or sha(path.read_bytes()) != ref['sha256']:
            raise ValueError('COMPONENT_CAPTURE_CACHE_DRIFT:' + name)
        return ref
    if path.exists():
        raise ValueError('COMPONENT_CAPTURE_UNBOUND_FILE:' + name)
    error = None
    for attempt in range(3):
        try:
            with urlopen(url, timeout=60) as response:
                raw = response.read()
            observed = datetime.now(timezone.utc).isoformat()
            if week is not None:
                payload = json.loads(raw)
                if not isinstance(payload, dict) or not payload:
                    raise ValueError('COMPONENT_PROVIDER_RESPONSE_SCHEMA')
                if not all(isinstance(v, dict) for v in payload.values()):
                    raise ValueError('COMPONENT_PROVIDER_ROW_SCHEMA')
            else:
                if not raw.startswith(b'season,'):
                    raise ValueError('COMPONENT_ROSTER_RESPONSE_SCHEMA')
            compressed = gzip.compress(raw, mtime=0)
            ref = {'path':path.relative_to(root).as_posix(), 'endpoint':url,
                   'observed_at':observed, 'sha256':sha(compressed), 'raw_sha256':sha(raw),
                   'raw_size':len(raw), 'season':season, 'week':week,
                   'purpose':'ACTUAL_COMPONENT_OUTCOMES_ONLY', 'original_publication_time_verified':False,
                   'sparse_provider_omissions':'UNKNOWN_NOT_ZERO'}
            path.write_bytes(compressed)
            receipt.write_text(json.dumps(ref, indent=2, sort_keys=True) + '\n')
            return ref
        except Exception as exc:
            error = exc
            if attempt < 2:
                time.sleep(1 + attempt)
    raise error

def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--root', type=Path, default=ROOT)
    p.add_argument('--folder', type=Path, default=DEFAULT)
    p.add_argument('--seasons', nargs='+', type=int, default=[2021,2022,2023,2024,2025])
    p.add_argument('--current-season', type=int, default=2026)
    p.add_argument('--through-week', type=int, default=5)
    a = p.parse_args()
    root = a.root.resolve(); folder = (root/a.folder).resolve()
    if not folder.is_relative_to(root):
        raise ValueError('COMPONENT_SOURCE_FOLDER_OUTSIDE_ROOT')
    folder.mkdir(parents=True, exist_ok=True)
    jobs = [(year,week) for year in a.seasons for week in range(1,19)]
    jobs += [(a.current_season,week) for week in range(1,a.through_week+1)]
    jobs += [(year,None) for year in a.seasons]
    refs = []; failures = []
    with ThreadPoolExecutor(max_workers=6) as pool:
        futures = {pool.submit(capture,root,folder,year,week):(year,week) for year,week in jobs}
        for f in as_completed(futures):
            try:
                refs.append(f.result())
            except Exception as exc:
                failures.append({'season':futures[f][0], 'week':futures[f][1], 'error':str(exc)})
            if (len(refs)+len(failures)) % 10 == 0:
                print('C1_CAPTURE',len(refs),'success',len(failures),'failed',flush=True)
    refs.sort(key=lambda r:(r['season'],r['week'] or 0))
    manifest = {'schema':'fie-component-actual-source-manifest-v1', 'sources':refs,
                'failures':failures, 'publication_time_verified':False}
    (folder/'manifest.json').write_text(json.dumps(manifest,indent=2,sort_keys=True)+'\n')
    print('C1_CAPTURE_FINISHED',len(refs),'success',len(failures),'failed',flush=True)
    if failures:
        raise SystemExit(1)

if __name__ == '__main__':
    main()
