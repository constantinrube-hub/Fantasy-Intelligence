#!/usr/bin/env python3
"""Static contract test for the V9.3.3A-C runtime integrity patch.

This test deliberately checks user-visible invariants rather than only file
existence. It is lightweight enough for GitHub Actions and local validation.
"""
from pathlib import Path
import re
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[1]
SNAP = ROOT / "app" / "current-snapshot-store.js"
RUNTIME = ROOT / "app" / "v9.3.3-runtime-integrity.js"


def require(text: str, needle: str, label: str) -> None:
    assert needle in text, f"missing {label}: {needle!r}"


def forbid(text: str, needle: str, label: str) -> None:
    assert needle not in text, f"forbidden {label}: {needle!r}"


def main() -> int:
    assert SNAP.exists(), f"missing {SNAP.relative_to(ROOT)}"
    assert RUNTIME.exists(), f"missing {RUNTIME.relative_to(ROOT)}"
    snap = SNAP.read_text(encoding="utf-8")
    runtime = RUNTIME.read_text(encoding="utf-8")

    # 9.3.3A: a missing projection is not a real zero.
    forbid(snap, "Array.isArray(proj[id])?proj[id]:[0,0]", "synthetic zero projection pair")
    require(snap, "Array.isArray(proj[id])?proj[id]:null", "null projection overlay")
    require(snap, "decision_weekly_projection:decision", "null-safe decision projection")
    require(snap, "sleeper_weekly_projection:sleeper", "null-safe Sleeper projection")

    # 9.3.3A: stale simulations are rejected by league and week context.
    require(runtime, "Object.defineProperty(eng,'leagueSim'", "league simulation guard")
    require(runtime, "candidate!==intended", "cross-league simulation rejection")
    require(runtime, "candidateWeek", "cross-week simulation rejection")
    require(runtime, "fie:league-changing", "league-change invalidation")

    # 9.3.3A: season cannot silently remain 0.
    require(runtime, "ensureSeasonInvariant", "canonical season invariant")
    require(runtime, "Number(st.league.season)<=1900", "invalid season repair")

    # 9.3.3B: switching can hydrate from generated league snapshots immediately.
    require(runtime, "loadLeagueSnapshot", "snapshot-first league hydration")
    require(runtime, "snapshotFastHits", "snapshot fast-path diagnostics")
    # No automatic Sleeper live refresh is scheduled on every switch. Live data
    # can still enter through explicit/manual FIEDataClient.refreshLeague calls.
    forbid(runtime, "scheduleLiveRefresh", "automatic live-refresh-on-switch")

    # 9.3.3B/C: schedule and selected-week projections are local cached inputs.
    require(runtime, "/api/data/nflverse/schedule", "canonical NFL schedule route")
    require(runtime, "/api/data/sleeper/projections/${s}/${w}", "selected-week projection route")
    require(runtime, "opponentForTeam", "schedule-backed opponent resolution")
    require(runtime, "p.weeklyProjection=null", "unavailable weekly projection semantics")
    require(runtime, "p.weeklyProjection=0", "verified bye true-zero semantics")

    # 9.3.3B: background enrichment must not force every intermediate re-render.
    require(runtime, "automaticRendersSuppressed", "render coalescing diagnostics")
    require(runtime, "enrichmentActive", "enrichment publication gate")
    require(runtime, "recentUserInput", "interactive navigation bypass")
    require(runtime, "flushAutomaticRender", "one coherent final render")

    # 9.3.3C: required UX corrections.
    require(runtime, "Matchup / playoffs week", "visible Matchup/Playoffs week filter")
    require(runtime, "Next 3 Avg", "unambiguous next-three average label")
    require(runtime, "not P10/P90", "honest special-teams range label")
    require(runtime, "repairPlayerNames", "O/Q player-name repair")
    require(snap, "sanitizeUncertainty", "degenerate D/ST/K range rejection")

    # Both shipped JS files must parse in Node.
    for path in (SNAP, RUNTIME):
        proc = subprocess.run(["node", "--check", str(path)], capture_output=True, text=True)
        assert proc.returncode == 0, f"node --check failed for {path.name}:\n{proc.stderr}"

    print("V9.3.3A-C integrity: PASS")
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except AssertionError as exc:
        print(f"V9.3.3A-C integrity: FAIL: {exc}", file=sys.stderr)
        raise SystemExit(1)
