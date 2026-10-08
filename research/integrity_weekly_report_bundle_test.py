#!/usr/bin/env python3
"""Product completeness, time, target, and immutable-owner preservation checks."""
import json
import tempfile
from pathlib import Path
import weekly_report_bundle as w


def main():
    with tempfile.TemporaryDirectory() as td:
        root = Path(td)
        now = w.stamp('2026-10-08T01:00:00Z')
        empty = w.bundle(root, 2026, 5, now)
        assert len(empty['products']) == 7 and empty['complete_product_count'] == 0
        assert all(row['status'] == 'BLOCKED_MISSING_PRODUCT' for row in empty['products'].values())
        base = root / 'data/research/evaluation/2026/weeks/week-5'
        path = base / 'waivers/portfolio-latest.json'
        path.parent.mkdir(parents=True)
        rows = [{'league_id': 'a', 'season': 2026, 'week': 5, 'format': 'REDRAFT', 'status': 'BLOCKED'},
                {'league_id': 'z', 'season': 2026, 'week': 5, 'format': 'CHOPPED', 'status': 'PARTIAL'}]
        value = {'schema': 'fie-window1d-optimal-waiver-portfolio-v1', 'season': 2026, 'week': 5,
                 'as_of_utc': '2026-10-08T00:00:00Z', 'generated_at': '2026-10-08T00:30:00Z', 'leagues': rows}
        path.write_text(json.dumps(value))
        before = path.read_bytes()
        report = w.bundle(root, 2026, 5, now)
        waiver = report['products']['WAIVER_GUIDE']
        assert waiver['status'] == 'PARTIAL_OWNER_OUTPUT' and waiver['complete'] is False
        assert waiver['content']['leagues'][0]['league_id'] == 'z'
        assert report['complete_product_count'] == 0 and path.read_bytes() == before
        assert report['products']['DST_HOLD_STREAM']['status'] == 'BLOCKED_MISSING_PRODUCT'
        for mutate, reason in [
            (lambda v: v.update(week=4), 'TARGET_MISMATCH'),
            (lambda v: v.update(generated_at='2026-10-08T02:00:00Z'), 'AFTER_AS_OF'),
            (lambda v: v.update(as_of_utc='2026-10-05T00:00:00Z'), 'STALE'),
            (lambda v: v.update(leagues=[rows[0], rows[0]]), 'DUPLICATE'),
            (lambda v: v.update(schema='unknown'), 'SCHEMA_MISMATCH'),
        ]:
            altered = json.loads(before)
            mutate(altered)
            path.write_text(json.dumps(altered))
            rejected = w.bundle(root, 2026, 5, now)
            source = rejected['sources']['WINDOW_1D']
            assert source['status'] == 'BLOCKED_INVALID_SOURCE' and reason in source['reason'], source
            assert rejected['products']['WAIVER_GUIDE']['content'] is None
        path.write_text(before.decode())
        output = w.markdown(report)
        assert '0/7' in output and 'PARTIAL_OWNER_OUTPUT' in output
    print('PASS weekly report bundle: seven products, honest partial states, Chopped priority, source lineage, target/time/staleness guards, read-only owners')

if __name__ == '__main__':
    main()
