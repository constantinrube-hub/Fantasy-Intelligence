#!/usr/bin/env python3
"""Regression for reproducible V9.3.2 build/deploy metadata."""
from __future__ import annotations
import json
from pathlib import Path
import build_app_manifest

ROOT=Path(__file__).resolve().parents[1]
release=json.loads((ROOT/'config/release.json').read_text())
first=build_app_manifest.build()
second=build_app_manifest.build()

assert first==second,'build manifest changes across identical builds'
assert first.get('generated_at')==release.get('built_at'),(
    'build manifest generated_at must use canonical release built_at, not wall-clock time'
)
src=(ROOT/'research/build_app_manifest.py').read_text()
assert 'datetime.now' not in src and 'timezone.utc' not in src,(
    'wall-clock timestamps make committed dist permanently stale after validation rebuilds'
)
print('PASS V9.3.2 deterministic build manifest')
