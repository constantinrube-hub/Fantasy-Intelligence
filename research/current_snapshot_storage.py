#!/usr/bin/env python3
"""Shared storage helpers for league-specific current Milestone 5 snapshots.

The logical M5 current contract remains unchanged after hydration. On disk, a
league snapshot may instead be a lightweight manifest referencing a shared
player base plus a scoring-specific projection overlay.
"""
from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
STORAGE_FORMAT = "fie-current-split-v1"
BASE_FORMAT = "fie-current-player-base-v1"
OVERLAY_FORMAT = "fie-current-scoring-overlay-v1"
PROJECTION_FIELDS = ("decision_weekly_projection", "sleeper_weekly_projection")


def read_json(path: str | Path, default: Any = None) -> Any:
    p = Path(path)
    try:
        return json.loads(p.read_text(encoding="utf-8"))
    except Exception:
        return default


def write_json(path: str | Path, obj: Any, *, compact: bool = False) -> None:
    p = Path(path)
    p.parent.mkdir(parents=True, exist_ok=True)
    if compact:
        text = json.dumps(obj, separators=(",", ":"), allow_nan=False)
    else:
        text = json.dumps(obj, indent=2, allow_nan=False)
    p.write_text(text + "\n", encoding="utf-8")


def stable_bytes(obj: Any) -> bytes:
    return json.dumps(obj, sort_keys=True, separators=(",", ":"), allow_nan=False).encode("utf-8")


def content_hash(obj: Any, length: int = 16) -> str:
    return hashlib.sha256(stable_bytes(obj)).hexdigest()[:length]


def player_id(row: dict) -> str:
    sid = row.get("sleeper_id")
    if sid is not None and str(sid):
        return str(sid)
    cid = row.get("canonical_player_id")
    if cid is not None and str(cid):
        return f"canonical:{cid}"
    raise ValueError("Current snapshot row lacks sleeper_id/canonical_player_id")


def base_row(row: dict) -> dict:
    return {k: v for k, v in row.items() if k not in PROJECTION_FIELDS}


def projection_pair(row: dict) -> list:
    return [row.get(PROJECTION_FIELDS[0]), row.get(PROJECTION_FIELDS[1])]


def projection_is_default(pair: list) -> bool:
    # Only explicit numeric zero can use the overlay default. Preserve None and
    # any non-numeric sentinel exactly by storing the pair.
    def zero(v: Any) -> bool:
        return isinstance(v, (int, float)) and not isinstance(v, bool) and abs(float(v)) <= 1e-12
    return zero(pair[0]) and zero(pair[1])


def is_split_manifest(obj: Any) -> bool:
    return isinstance(obj, dict) and (obj.get("storage") or {}).get("format") == STORAGE_FORMAT


def resolve_ref(ref: str, *, root: Path = ROOT) -> Path:
    p = Path(ref)
    return p if p.is_absolute() else root / p


def load_current_snapshot(path: str | Path, *, root: Path = ROOT, cache: dict | None = None) -> dict:
    """Load either a legacy full snapshot or a split manifest into the full contract."""
    p = Path(path)
    if not p.is_absolute():
        p = root / p
    raw = read_json(p, {}) or {}
    if not is_split_manifest(raw):
        return raw

    cache = cache if cache is not None else {}
    storage = raw.get("storage") or {}
    base_ref = str(storage.get("player_base") or "")
    overlay_ref = str(storage.get("scoring_overlay") or "")
    if not base_ref or not overlay_ref:
        raise ValueError(f"Split current snapshot is missing shared references: {p}")

    def cached(ref: str) -> dict:
        rp = resolve_ref(ref, root=root)
        key = str(rp.resolve())
        if key not in cache:
            cache[key] = read_json(rp, {}) or {}
        return cache[key]

    base = cached(base_ref)
    overlay = cached(overlay_ref)
    if base.get("format") != BASE_FORMAT:
        raise ValueError(f"Unexpected current player-base format: {base_ref}")
    if overlay.get("format") != OVERLAY_FORMAT:
        raise ValueError(f"Unexpected current scoring-overlay format: {overlay_ref}")
    if str(overlay.get("scoring_signature") or "") != str(raw.get("scoring_signature") or ""):
        raise ValueError(f"Scoring overlay mismatch for {p}")

    rows = base.get("players") or []
    include = storage.get("included_player_ids")
    exclude = set(map(str, storage.get("excluded_player_ids") or []))
    projections = overlay.get("projections") or {}
    hydrated = []
    if isinstance(include, list):
        by_id = {player_id(b): b for b in rows}
        ordered_rows = [(str(pid), by_id.get(str(pid))) for pid in include]
    else:
        ordered_rows = [(player_id(b), b) for b in rows]
    for pid, b in ordered_rows:
        if b is None or pid in exclude:
            continue
        pair = projections.get(pid, [0.0, 0.0])
        if not isinstance(pair, list) or len(pair) < 2:
            raise ValueError(f"Invalid projection pair for {pid} in {overlay_ref}")
        r = dict(b)
        r[PROJECTION_FIELDS[0]] = pair[0]
        r[PROJECTION_FIELDS[1]] = pair[1]
        hydrated.append(r)

    expected = int(storage.get("player_count") or len(hydrated))
    if expected != len(hydrated):
        raise ValueError(f"Hydrated player-count mismatch for {p}: expected {expected}, got {len(hydrated)}")

    out = {k: v for k, v in raw.items() if k != "storage"}
    out["scoring_settings"] = overlay.get("scoring_settings") or {}
    out["players"] = hydrated
    return out
