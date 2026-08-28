#!/usr/bin/env python3
"""Fail-closed guard for the production application shell."""
from __future__ import annotations
import argparse
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

REQUIRED = (
    '<title>Fantasy Intelligence Engine · Current Release</title>',
    'id="releaseMarkerV7"',
    'app/decision-ui.css',
    'app/current-snapshot-store.js',
    'app/decision-engines.js',
    'app/value-finder.js',
    'app/dst-intelligence.js',
    'app/kicker-intelligence.js',
)

FORBIDDEN = (
    '<title>Fantasy Intelligence Engine V5</title>',
    '<h1>Fantasy Intelligence Engine <span style="color:var(--accent)">V5</span></h1>',
    'V5 · Dynasty + Waivers + Start/Sit',
)

# sync_league_app_snapshots.py performs this single approved deploy-only
# transformation after build_dist.py has copied root index.html into dist/.
# Keeping the exact tag here makes the release gate fail closed if that
# transformation ever changes unexpectedly.
CALIBRATION_TAG = (
    '<script src="app/core/value-calibration-guard.js?v=933-calibration"></script>'
)


def validate_shell(path: Path, label: str) -> None:
    assert path.exists(), f'{label} missing: {path}'
    text = path.read_text(encoding='utf-8')

    for marker in REQUIRED:
        assert marker in text, f'{label} missing modern marker: {marker!r}'

    for marker in FORBIDDEN:
        assert marker not in text, f'{label} contains obsolete V5 marker: {marker!r}'

    assert len(text) > 500_000, (
        f'{label} unexpectedly small/truncated: {len(text)} chars'
    )


def shadow_files():
    return sorted(
        {
            p
            for pat in ('index.html.txt', 'index.html*.txt', 'index.html(*)*')
            for p in ROOT.glob(pat)
            if p.is_file() and p.name != 'index.html'
        }
    )


def validate_source() -> None:
    validate_shell(ROOT / 'index.html', 'source index')

    bad = shadow_files()
    assert not bad, (
        'accidental shadow index file(s) found; delete: '
        + ', '.join(p.name for p in bad)
    )

    guard = ROOT / 'app/core/value-calibration-guard.js'
    assert guard.exists(), f'calibration guard missing: {guard}'


def expected_dist_index() -> bytes:
    """Return the exact deploy shell expected after approved dist injection."""
    text = (ROOT / 'index.html').read_text(encoding='utf-8')

    # Future-proofing: if the tag is eventually committed directly into the
    # source shell, sync_league_app_snapshots.py becomes a no-op and strict
    # parity naturally returns to byte-for-byte source == dist.
    if CALIBRATION_TAG not in text:
        marker = '</body>'
        assert marker in text, (
            'source index.html missing </body> required for calibration injection'
        )
        text = text.replace(marker, CALIBRATION_TAG + '\n' + marker, 1)

    return text.encode('utf-8')


def validate_dist() -> None:
    dist_index = ROOT / 'dist/index.html'
    validate_shell(dist_index, 'dist index')

    dist_guard = ROOT / 'dist/app/core/value-calibration-guard.js'
    assert dist_guard.exists(), f'dist calibration guard missing: {dist_guard}'

    dist_bytes = dist_index.read_bytes()
    expected = expected_dist_index()

    assert dist_bytes == expected, (
        'dist/index.html differs from the approved deploy shell transformation '
        '(root index.html + exact calibration guard injection only)'
    )

    assert CALIBRATION_TAG.encode('utf-8') in dist_bytes, (
        'dist/index.html missing approved calibration guard script tag'
    )


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--source-only', action='store_true')
    ns = ap.parse_args()

    validate_source()

    if not ns.source_only:
        validate_dist()

    print(
        'PASS app shell guard: modern root shell'
        + (
            ' validated'
            if ns.source_only
            else ' + approved calibration-injected dist validated'
        )
    )


if __name__ == '__main__':
    main()
