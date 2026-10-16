#!/usr/bin/env python3
"""Quarantine Sleeper benchmark snapshots that cannot prove decision-time eligibility.

This does not destroy evidence. Invalid/unverifiable snapshots are moved outside
`data/research/market/sleeper`, so M4 cannot accidentally treat them as a market
benchmark, and their manifest entries are removed. A future legitimate capture may
then write the canonical week file during the verified pregame window.
"""
from __future__ import annotations

import argparse
import json
import shutil
from datetime import datetime, timezone
from pathlib import Path


def load_json(path: Path) -> dict:
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return {}


def valid_verified_capture(meta: dict) -> tuple[bool, str]:
    if not meta.get("pregame_eligible"):
        return True, "not_marked_eligible"
    try:
        ver = int(meta.get("capture_policy_version") or 0)
    except Exception:
        ver = 0
    if ver < 2:
        return False, "eligible_snapshot_missing_capture_policy_v2"
    st = str(meta.get("season_type") or "").lower()
    if st != "regular":
        return False, f"eligible_snapshot_season_type_{st or 'unknown'}"
    try:
        hours = float(meta.get("hours_before_kickoff"))
        window = float(meta.get("capture_window_hours"))
    except Exception:
        return False, "eligible_snapshot_missing_timing_fields"
    if not (0 < hours <= window):
        return False, f"eligible_snapshot_outside_window_{hours:.3f}h"
    if not meta.get("first_kickoff_utc"):
        return False, "eligible_snapshot_missing_first_kickoff"
    return True, "verified"


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--root", default="data/research/market/sleeper")
    ap.add_argument("--quarantine-root", default="data/research/quarantine/sleeper")
    ap.add_argument("--dry-run", action="store_true")
    a = ap.parse_args()

    root = Path(a.root)
    qroot = Path(a.quarantine_root)
    manifest_path = root / "manifest.json"
    manifest = load_json(manifest_path) or {"schema_version": 1, "snapshots": {}}
    entries = manifest.setdefault("snapshots", {})
    moved = []

    for key, row in list(entries.items()):
        raw_path = Path(str(row.get("path") or ""))
        if not raw_path.is_absolute() and not raw_path.exists():
            # Stored paths are repository-relative.
            raw_path = Path.cwd() / raw_path
        meta_path = raw_path.with_suffix(raw_path.suffix + ".meta.json")
        meta = load_json(meta_path) or dict(row)
        ok, reason = valid_verified_capture(meta)
        if ok:
            continue
        rel = Path(str(row.get("season") or "unknown")) / raw_path.name
        dest = qroot / rel
        moved.append({"key": key, "path": str(raw_path), "quarantine": str(dest), "reason": reason})
        if a.dry_run:
            continue
        dest.parent.mkdir(parents=True, exist_ok=True)
        if raw_path.exists():
            shutil.move(str(raw_path), str(dest))
        if meta_path.exists():
            shutil.move(str(meta_path), str(dest.with_suffix(dest.suffix + ".meta.json")))
        note = dest.with_suffix(dest.suffix + ".quarantine.json")
        note.write_text(json.dumps({
            "quarantined_at": datetime.now(timezone.utc).isoformat(),
            "reason": reason,
            "original_manifest_entry": row,
        }, indent=2, sort_keys=True) + "\n", encoding="utf-8")
        entries.pop(key, None)

    if not a.dry_run:
        manifest["updated_at"] = datetime.now(timezone.utc).isoformat()
        manifest_path.parent.mkdir(parents=True, exist_ok=True)
        manifest_path.write_text(json.dumps(manifest, indent=2, sort_keys=True) + "\n", encoding="utf-8")

    print(json.dumps({"status": "DRY_RUN" if a.dry_run else "COMPLETE", "quarantined": moved, "remaining": len(entries)}, indent=2))


if __name__ == "__main__":
    main()
