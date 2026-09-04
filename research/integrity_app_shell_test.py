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
    'app/core/semantic-ux.js',
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

# sync_league_app_snapshots.py is allowed to perform only these exact
# deploy-only script injections after build_dist.py has copied root index.html
# into dist/.  The release gate reconstructs the expected dist shell from the
# source shell and these exact tags, so any additional mutation still fails
# byte-for-byte parity.
CALIBRATION_TAG = (
    '<script src="app/core/value-calibration-guard.js?v=933-calibration"></script>'
)
RESEARCH_SERVICE_TAG = (
    '<script src="app/core/research-report-service.js?v=unified-research-v1"></script>'
)
RESEARCH_UI_TAG = (
    '<script src="app/research-report-ui.js?v=unified-research-v1"></script>'
)
RESEARCH_VALUE_FINDER_TAG = (
    '<script src="app/core/research-value-finder-bridge.js?v=unified-research-v1"></script>'
)

APPROVED_DEPLOY_TAGS = (
    CALIBRATION_TAG,
    RESEARCH_SERVICE_TAG,
    RESEARCH_UI_TAG,
    RESEARCH_VALUE_FINDER_TAG,
)

APPROVED_DEPLOY_FILES = (
    'app/core/value-calibration-guard.js',
    'app/core/research-report-service.js',
    'app/research-report-ui.js',
    'app/core/research-value-finder-bridge.js',
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

    for rel in APPROVED_DEPLOY_FILES:
        p = ROOT / rel
        assert p.exists(), f'approved deploy script missing: {p}'


def expected_dist_index() -> bytes:
    """Return exact deploy shell after only approved script injections."""
    text = (ROOT / 'index.html').read_text(encoding='utf-8')
    marker = '</body>'
    assert marker in text, (
        'source index.html missing </body> required for approved deploy injection'
    )

    # Match sync_league_app_snapshots.py exactly: each missing tag is appended
    # immediately before </body>, in the fixed order above.  If a tag is ever
    # committed directly into source index.html, that individual injection
    # naturally becomes a no-op.
    for tag in APPROVED_DEPLOY_TAGS:
        if tag not in text:
            text = text.replace(marker, tag + '\n' + marker, 1)

    return text.encode('utf-8')


def validate_dist() -> None:
    dist_index = ROOT / 'dist/index.html'
    validate_shell(dist_index, 'dist index')

    for rel in APPROVED_DEPLOY_FILES:
        p = ROOT / 'dist' / rel
        assert p.exists(), f'dist approved deploy script missing: {p}'

    dist_bytes = dist_index.read_bytes()
    expected = expected_dist_index()

    assert dist_bytes == expected, (
        'dist/index.html differs from the approved deploy shell transformation '
        '(root index.html + exact calibration/research script injections only)'
    )

    for tag in APPROVED_DEPLOY_TAGS:
        assert tag.encode('utf-8') in dist_bytes, (
            f'dist/index.html missing approved deploy script tag: {tag}'
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
            else ' + exact approved calibration/research-injected dist validated'
        )
    )


if __name__ == '__main__':
    main()
