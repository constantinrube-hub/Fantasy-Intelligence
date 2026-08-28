#!/usr/bin/env python3
"""Static + unit contract test for FIE V9.3.4A-B.

Browser timing still needs deployment QA. This gate verifies that the code which
removes known critical-path work and fixes the confirmed B-side defects is
actually present and syntactically valid.
"""
from __future__ import annotations

import importlib.util
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
RUNTIME = ROOT / "app" / "v9.3.3-runtime-integrity.js"
SNAP = ROOT / "app" / "current-snapshot-store.js"
WORKER = ROOT / "app" / "workers" / "csv-parse-worker.js"
BUILDER = ROOT / "research" / "build_league_app_snapshots.py"
FAST_TEST = ROOT / "research" / "integrity_fast_switch_artifacts_test.py"
SYNC = ROOT / "tools" / "sync_league_app_snapshots.py"


def require(text: str, needle: str, label: str) -> None:
    assert needle in text, f"missing {label}: {needle!r}"


def main() -> int:
    for path in (RUNTIME, SNAP, WORKER, BUILDER, FAST_TEST, SYNC):
        assert path.exists(), f"missing {path.relative_to(ROOT)}"

    runtime = RUNTIME.read_text(encoding="utf-8")
    snap = SNAP.read_text(encoding="utf-8")
    builder = BUILDER.read_text(encoding="utf-8")
    fast_test = FAST_TEST.read_text(encoding="utf-8")
    sync = SYNC.read_text(encoding="utf-8")

    # Release + cold-load rescue.
    require(runtime, "const VERSION='9.3.4A-B'", "9.3.4 release identity")
    require(runtime, "PLAYER_CATALOG_URL='/data/research/app/player-catalog.json'", "compact catalog runtime route")
    require(runtime, "primePlayerCatalog", "catalog prewarm")
    require(runtime, "installPlayerCatalogGate", "league-switch catalog gate")
    require(runtime, "playerCatalogGateMs", "catalog gate timing diagnostic")
    require(builder, 'PLAYER_CATALOG_SCHEMA = "fie-player-catalog-v1"', "catalog build schema")
    require(builder, "compact_player_catalog", "catalog compactor")
    require(builder, '"player_catalog": catalog_meta', "catalog index publication")
    require(builder, '"shared": {', "league core shared-input reference")
    require(fast_test, "check_player_catalog", "generated catalog validation")
    require(snap, "v9.3.3-runtime-integrity.js?v=9.3.4", "runtime cache bust")
    require(sync, "player-catalog.json", "deploy-tree player catalog sync")

    # Main-thread / week-switch rescue.
    require(runtime, "installCsvFastPath", "off-main public CSV path")
    require(runtime, "csv-parse-worker.js?v=9.3.4", "CSV worker load")
    require(runtime, "installCooperativeEnhancements", "serialized cooperative enhancement controller")
    require(runtime, "staged('season-projections'", "season projection stage")
    require(runtime, "staged('research'", "research stage")
    require(runtime, "staged('public-enrichment'", "public enrichment stage")
    require(runtime, "installOptimizedPublicEnrichment", "cooperative optimized public enrichment")
    require(runtime, "atomic enhancement publish", "single atomic score publication")
    require(runtime, "restorePlayerState(published)", "published player-state freeze")
    require(runtime, "isVolatilePlayerField", "week/roster state preservation during atomic enrichment")
    require(runtime, "rerunSimulation=false", "cheap default week switch")
    require(runtime, "scheduleDeferredScoreRecompute", "deferred full score recomputation")
    require(runtime, "automaticRendersSuppressed", "atomic render diagnostics")
    require(runtime, "userRenderTickets", "navigation remains renderable during enrichment")

    # B correctness quick wins.
    require(runtime, "normalizeNFLTeam", "canonical NFL team normalization")
    for alias in ("LA:'LAR'", "JAC:'JAX'", "WSH:'WAS'", "OAK:'LV'", "SD:'LAC'"):
        require(runtime, alias, f"team alias {alias}")
    require(runtime, "preloadSpecialTeamsWindow", "initial D/ST/K next-three preload")
    require(runtime, "Loading selected week + next two weeks", "honest first-render special-teams loading state")
    require(runtime, "syncWeeklyPanelVisibility", "Start/Sit panel surface isolation")
    require(runtime, "panel.hidden=!show", "weekly panel hidden outside Start/Sit")
    require(runtime, "syncLeaguePositionFilter", "league-specific position filter")
    require(runtime, "c.legalPositions", "league capability filter source")
    require(runtime, "window.FIE934AB=API;window.FIE933ABC=API", "compatibility API alias")

    # Unit-test catalog compaction without network access.
    spec = importlib.util.spec_from_file_location("fie_build_snapshots", BUILDER)
    assert spec and spec.loader
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    raw = {
        "1": {
            "player_id": "1",
            "sport": "nfl",
            "team": "LAR",
            "full_name": "Active Player",
            "position": "WR",
            "fantasy_positions": ["WR"],
            "years_exp": 2,
            "search_rank": 10,
            "extra_unused": "drop me",
        },
        "2": {
            "player_id": "2",
            "sport": "nfl",
            "team": None,
            "full_name": "Retired Player",
            "position": "WR",
        },
        "3": {
            "player_id": "3",
            "sport": "nba",
            "team": "LAL",
            "full_name": "Wrong Sport",
            "position": "G",
        },
    }
    # validate_player_catalog intentionally requires a production-sized catalog,
    # so test the compaction predicate by expanding the valid fixture.
    fixture = {
        str(i): {**raw["1"], "player_id": str(i), "full_name": f"Player {i}"}
        for i in range(1, 501)
    }
    fixture["retired"] = raw["2"]
    fixture["other"] = raw["3"]
    catalog = mod.compact_player_catalog(fixture)
    assert catalog["player_count"] == 500
    assert "retired" not in catalog["players"]
    assert "other" not in catalog["players"]
    assert "extra_unused" not in catalog["players"]["1"]
    assert catalog["players"]["1"]["team"] == "LAR"

    # Parse all shipped JS touched by this patch.
    for path in (RUNTIME, SNAP, WORKER):
        proc = subprocess.run(["node", "--check", str(path)], capture_output=True, text=True)
        assert proc.returncode == 0, f"node --check failed for {path.name}:\n{proc.stderr}"

    print("V9.3.4A-B integrity: PASS")
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except AssertionError as exc:
        print(f"V9.3.4A-B integrity: FAIL: {exc}", file=sys.stderr)
        raise SystemExit(1)
