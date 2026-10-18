#!/usr/bin/env python3
"""WP-V1 — measure the weekly outcome spread around Sleeper projections (research, read-only).

Projections: frozen Thursday Sleeper weekly projections data/research/market/sleeper/<season>/week_NN.jsonl.gz
(pts_ppr). Outcomes: nflverse stats_player_week (fantasy_points_ppr) from a committed weekly-source capture,
joined to Sleeper IDs through the captured dynastyprocess ID map. Players projected >= --min-proj points;
a projected player without a stat row counts as 0 (did not play).

Prints per position: n, share inside the current x0.78-1.22 band, P10/P50/P90 of actual/projection, relative SD,
mean bias, and the JSON block for config/ui-decision-policy.json > variance.calibration.positions.

    python research/wpv1_measure_spread.py --weeks 1-5
    python research/wpv1_measure_spread.py --weeks 6 --check   # out-of-sample coverage of the current policy block
"""
from __future__ import annotations
import argparse, csv, gzip, io, json, statistics
from collections import defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
STATS = 'https://github.com/nflverse/nflverse-data/releases/download/stats_player/stats_player_week_2026.csv'
IDS = 'https://raw.githubusercontent.com/dynastyprocess/data/master/files/db_playerids.csv'


def receipts(capture: Path) -> dict[str, str]:
    out = {}
    for f in capture.glob('*-response-receipt.json'):
        r = json.loads(f.read_text(encoding='utf-8'))
        out[r['endpoint']] = r['path']
    return out


def latest_capture_with_stats(season: int) -> Path:
    base = ROOT / 'data' / 'research' / 'prospective' / 'weekly-sources' / str(season)
    caps = sorted((d for w in base.iterdir() for d in w.iterdir() if d.is_dir()), key=lambda p: p.name)
    for cap in reversed(caps):
        if STATS in receipts(cap):
            return cap
    raise SystemExit('no capture with nflverse weekly stats found')


def quantile(xs: list[float], q: float) -> float:
    s = sorted(xs)
    i = (len(s) - 1) * q
    lo, hi = int(i), min(len(s) - 1, int(i) + 1)
    return s[lo] + (s[hi] - s[lo]) * (i - lo)


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument('--season', type=int, default=2026)
    ap.add_argument('--weeks', default='1-5')
    ap.add_argument('--min-proj', type=float, default=5.0)
    ap.add_argument('--capture', default=None, help='weekly-source capture dir with nflverse stats (default: latest)')
    ap.add_argument('--check', action='store_true', help='report coverage of the policy calibration on these weeks')
    a = ap.parse_args()
    lo, _, hi = a.weeks.partition('-')
    weeks = list(range(int(lo), int(hi or lo) + 1))
    cap = Path(a.capture) if a.capture else latest_capture_with_stats(a.season)
    rc = receipts(ROOT / cap if not cap.is_absolute() else cap)
    raw = lambda ep: gzip.open(ROOT / rc[ep]).read().decode('utf-8')
    g2s = {r['gsis_id']: r['sleeper_id'] for r in csv.DictReader(io.StringIO(raw(IDS))) if r['gsis_id'] and r['sleeper_id'] not in ('', 'NA')}
    actual: dict[int, dict[str, float]] = defaultdict(dict)
    for r in csv.DictReader(io.StringIO(raw(STATS))):
        if r['season_type'] == 'REG' and r['player_id'] in g2s:
            actual[int(r['week'])][g2s[r['player_id']]] = float(r['fantasy_points_ppr'] or 0)
    rows = []
    for wk in weeks:
        f = ROOT / 'data' / 'research' / 'market' / 'sleeper' / str(a.season) / f'week_{wk:02d}.jsonl.gz'
        if not f.exists() or wk not in actual:
            print(f'week {wk}: projections or outcomes missing — skipped')
            continue
        for line in gzip.open(f, 'rt', encoding='utf-8'):
            x = json.loads(line)
            p, pos = x['stats'].get('pts_ppr'), x.get('position_model')
            if p is None or pos not in ('QB', 'RB', 'WR', 'TE') or p < a.min_proj:
                continue
            rows.append((pos, p, actual[wk].get(x['sleeper_id'], 0.0)))
    policy = json.loads((ROOT / 'config' / 'ui-decision-policy.json').read_text(encoding='utf-8'))
    cal = policy.get('variance', {}).get('calibration', {}).get('positions', {})
    block = {}
    print(f'capture {cap.name if hasattr(cap, "name") else cap} · weeks {weeks} · n={len(rows)}')
    print('pos      n  in x0.78-1.22   P10   P50   P90   SD/proj   bias' + ('   in policy P10-P90' if a.check else ''))
    for pos in ('QB', 'RB', 'WR', 'TE'):
        xs = [(p, act) for q, p, act in rows if q == pos]
        if len(xs) < 2:
            continue
        ratios = [act / p for p, act in xs]
        band = sum(1 for p, act in xs if 0.78 * p <= act <= 1.22 * p) / len(xs)
        rel = [(act - p) / p for p, act in xs]
        q10, q50, q90 = quantile(ratios, .1), quantile(ratios, .5), quantile(ratios, .9)
        line = f'{pos:3} {len(xs):6}  {band:12.1%}  {q10:5.2f} {q50:5.2f} {q90:5.2f}   {statistics.pstdev(rel):6.3f}  {statistics.mean(rel):+6.1%}'
        if a.check and pos in cal:
            c = cal[pos]
            line += f'   {sum(1 for p, act in xs if c["p10"] * p <= act <= c["p90"] * p) / len(xs):10.1%}'
        print(line)
        block[pos] = {'p10': round(q10, 2), 'p50': round(q50, 2), 'p90': round(q90, 2), 'sd': round(statistics.pstdev(rel), 3), 'n': len(xs)}
    print(json.dumps(block, indent=2))


if __name__ == '__main__':
    main()
