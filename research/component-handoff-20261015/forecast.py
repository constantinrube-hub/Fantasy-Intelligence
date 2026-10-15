"""Verify and export saved forecasts. Does not fit or issue a model. Python stdlib only."""
import argparse
import csv
import gzip
import hashlib
import json
import math
from collections import Counter, defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parent


def load(name):
    with gzip.open(ROOT / name, 'rt', encoding='utf-8') as f:
        return json.load(f)


def require(ok, message):
    if not ok:
        raise ValueError(message)


def verify():
    manifest = json.loads((ROOT / 'manifest.json').read_text(encoding='utf-8'))
    for name, item in manifest['files'].items():
        b = (ROOT / name).read_bytes()
        require(len(b) == item['bytes'], 'Size mismatch: ' + name)
        require(hashlib.sha256(b).hexdigest() == item['sha256'], 'Hash mismatch: ' + name)
    d = load('comparison.json.gz')
    require(len(d['keys']) == 117 and len(set(d['keys'])) == 117, 'Component keys')
    require(len(d['rows']) == 5577 and len(d['profiles']) == 23, 'Comparison coverage')
    require(not d['actual'], 'Unexpected actuals in saved comparison')
    require(len({(r[0], r[5]) for r in d['rows']}) == 5577, 'Duplicate comparison identity')
    idx = {(r[0], r[5]): r for r in d['rows']}
    count = Counter(model for r in d['rows'] for model in r[6])
    require(sum(count.values()) == 39000, 'Model row count')
    require(set(count) == set(manifest['coverage']['comparison_models']), 'Model identities')
    require(len(d['cohort']) == 55242, 'League cohort')
    for r in d['rows']:
        for model, values in r[6].items():
            require(len(values) == 117, 'Vector width: ' + model)
            require(all(v is None or math.isfinite(v) for v in values), 'Invalid forecast value')
    score_checks = 0
    for filename, model in [('step4.json.gz', 'STEP4'), ('step1.json.gz', 'STEP1')]:
        s = load(filename)
        require(s['keys'] == d['keys'], 'Mismatched component order')
        require(len(s['rows']) == 5577 and len(s['scores']) == 55242, 'Saved forecast coverage')
        require(len({(r[0], r[4]) for r in s['rows']}) == 5577, 'Duplicate saved forecast identity')
        rows = {(r[0], r[4]): r for r in s['rows']}
        ki = {k: i for i, k in enumerate(s['keys'])}
        for cid, week, lid, mean, p10, p50, p90 in s['scores']:
            row = rows[cid, week]
            terms = s['rules'][lid + '|' + row[2]]
            expected = sum(row[10][ki[component]] * weight for key, component, weight in terms)
            require(math.isclose(mean, expected, abs_tol=1e-8, rel_tol=1e-10), 'Score mismatch: ' + cid)
            require(p10 <= p50 <= p90, 'Quantile ordering')
            score_checks += 1
        if model == 'STEP4':
            for r in s['rows']:
                frozen = idx[r[0], r[4]][6]['STEP4']
                require(all(b is None or a == b for a, b in zip(r[10], frozen)), 'Step4 comparison mismatch')
            # Mean-level credits only; full draw-level validation requires missing archives.
            for week in (6, 7, 8):
                for team in {r[3] for r in s['rows'] if r[4] == week}:
                    actors = [r for r in s['rows'] if r[3] == team and r[4] == week and r[2] != 'D/ST']
                    for a, b in [('passing_completions', 'receptions'), ('passing_yards', 'receiving_yards'), ('passing_touchdowns', 'receiving_touchdowns')]:
                        va = sum(r[10][ki[a]] for r in actors)
                        vb = sum(r[10][ki[b]] for r in actors)
                        require(math.isclose(va, vb, abs_tol=1e-8), f'Team credits: {week} {team} {a}')
    print('PASS: hashes; 5,577 rows; 117 components; 23 leagues; 39,000 comparison rows;')
    print(f'{score_checks:,} Step1/Step4 mean-score replays; Step4 shared offensive mean credits.')
    print('Recovered outputs only. Model generators, scenario archives and Step5 evaluator are absent.')


def write_csv(path, header, rows):
    with path.open('w', encoding='utf-8-sig', newline='') as f:
        writer = csv.writer(f)
        writer.writerow(header)
        writer.writerows(rows)


def export(destination):
    verify()
    out = Path(destination)
    out.mkdir(parents=True, exist_ok=False)
    for filename, model in [('step4.json.gz', 'STEP4'), ('step1.json.gz', 'STEP1')]:
        s = load(filename)
        # Flatten vectors rather than serializing the vector in one cell.
        write_csv(out / (model.lower() + '-components.csv'),
                  ['canonical_id', 'name', 'position', 'team', 'week', 'opponent', 'available', 'bye', 'official_status', 'provider_injury'] + s['keys'],
                  (r[:10] + r[10] for r in s['rows']))
        write_csv(out / (model.lower() + '-league-scores.csv'),
                  ['canonical_id', 'week', 'league_id', 'mean', 'p10', 'p50', 'p90'], s['scores'])
        sums = defaultdict(list)
        for cid, week, lid, mean, *quantiles in s['scores']:
            sums[cid, lid].append((week, mean))
        require(len(sums) == 18414 and all({w for w, v in a} == {6, 7, 8} for a in sums.values()), 'Three-week coverage')
        write_csv(out / (model.lower() + '-three-week-mean-scores.csv'),
                  ['canonical_id', 'league_id', 'weeks', 'mean_sum'],
                  ([cid, lid, '6-8', sum(v for w, v in a)] for (cid, lid), a in sorted(sums.items())))
    d = load('comparison.json.gz')
    write_csv(out / 'comparison-components.csv',
              ['canonical_id', 'name', 'position', 'frozen_evaluation_role', 'team', 'week', 'model'] + d['keys'],
              (r[:6] + [model] + values for r in d['rows'] for model, values in r[6].items()))
    write_csv(out / 'leagues.csv', ['league_id', 'name'], d['profiles'])
    (out / 'README.txt').write_text(
        'Exact saved forecasts, not new model issuance. Blank comparison cells mean unsupported/missing, never zero.\n'
        'Step4 is latest. Step5 adds evaluation, not another projection. Step1 is separately recovered.\n'
        'Three-week means are sums of weekly means. No three-week quantiles are reconstructed.\n'
        'Step4/Step1 raw output includes structural zeros; comparison retains original applicability masks.\n'
        'Scoring includes saved expected bonus/bucket components; do not threshold mean yards to recreate bonuses.\n'
        'Missing model source and scenario archives prevent complete independent regeneration.\n', encoding='utf-8')
    print('Exported to ' + str(out.resolve()))


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest='command', required=True)
    sub.add_parser('verify')
    exp = sub.add_parser('export')
    exp.add_argument('--output', required=True, help='New directory; refuses existing destinations')
    args = parser.parse_args()
    if args.command == 'verify':
        verify()
    else:
        export(args.output)
