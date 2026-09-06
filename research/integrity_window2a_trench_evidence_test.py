#!/usr/bin/env python3
"""Synthetic integrity tests for Window 2A Trench Evidence + Feature Owner."""
from __future__ import annotations

import csv
import importlib.util
import json
import math
import tempfile
from pathlib import Path

HERE = Path(__file__).resolve().parent
SPEC = importlib.util.spec_from_file_location("window2a", HERE / "window2a_trench_evidence.py")
assert SPEC and SPEC.loader
w = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(w)


def close(a, b, tol=1e-9):
    assert a is not None and abs(float(a) - float(b)) <= tol, (a, b)


def write_fixture(path: Path) -> None:
    fields = [
        "season", "season_type", "week", "posteam", "defteam", "pass_attempt", "rush_attempt",
        "sack", "qb_hit", "qb_spike", "qb_scramble", "qb_kneel", "no_play", "epa", "success", "yards_gained",
    ]
    rows = []
    def add(week, off, deff, *, pa=0, ra=0, sack=0, hit="", spike=0, scramble=0, kneel=0, no_play=0, epa="", success="", yards=""):
        rows.append({"season":2026,"season_type":"REG","week":week,"posteam":off,"defteam":deff,"pass_attempt":pa,"rush_attempt":ra,"sack":sack,"qb_hit":hit,"qb_spike":spike,"qb_scramble":scramble,"qb_kneel":kneel,"no_play":no_play,"epa":epa,"success":success,"yards_gained":yards})
    # Week 1 A offense vs B: 2 dropbacks, 1 sack; 2 designed rushes, one stuffed.
    add(1,"A","B",pa=1,sack=1,hit=1,epa=-0.5,success=0,yards=-6)
    add(1,"A","B",pa=1,sack=0,hit=0,epa=0.4,success=1,yards=8)
    add(1,"A","B",ra=1,epa=0.5,success=1,yards=5)
    add(1,"A","B",ra=1,epa=-0.3,success=0,yards=0)
    # Scramble and kneel are not designed runs.
    add(1,"A","B",ra=1,scramble=1,epa=0.7,success=1,yards=9)
    add(1,"A","B",ra=1,kneel=1,epa=-0.1,success=0,yards=-1)
    # No-play pass is ignored.
    add(1,"A","B",pa=1,sack=1,hit=1,no_play=1,epa=-1,success=0,yards=-8)
    # Week 1 B offense vs A, enough mirrors.
    add(1,"B","A",pa=1,sack=0,hit="",epa=0.2,success=1,yards=7)
    add(1,"B","A",ra=1,epa=-0.4,success=0,yards=-1)
    # Week 2 is target-week realised data and must never enter target_week=2.
    add(2,"A","B",pa=1,sack=0,hit=0,epa=4,success=1,yards=60)
    add(2,"A","B",ra=1,epa=5,success=1,yards=80)
    with path.open("w", newline="", encoding="utf-8") as f:
        wr = csv.DictWriter(f, fieldnames=fields); wr.writeheader(); wr.writerows(rows)


def synthetic_team_week(team_strengths):
    """Build direct raw owner input for enough teams to test proxy direction."""
    result = {1:{}}
    for team, strength in team_strengths.items():
        off = w.empty_side(); deff = w.empty_side(); off["weeks"].add(1); deff["weeks"].add(1)
        off.update({
            "pass_dropbacks":100, "sacks":10-strength, "qb_hits":20-strength,
            "qb_hit_observed_passes":100, "designed_rushes":100,
            "rush_epa_sum":float(strength), "rush_epa_observed":100,
            "rush_successes":40+strength, "rush_success_observed":100,
            "stuffed_rushes":20-strength, "rush_yards_observed":100,
        })
        deff.update({
            "pass_dropbacks":100, "sacks":5+strength, "qb_hits":10+strength,
            "qb_hit_observed_passes":100, "designed_rushes":100,
            "rush_epa_sum":float(-strength), "rush_epa_observed":100,
            "rush_successes":50-strength, "rush_success_observed":100,
            "stuffed_rushes":10+strength, "rush_yards_observed":100,
        })
        result[1][team] = {"offense":off,"defense":deff}
    return result


def main():
    checks = 0
    with tempfile.TemporaryDirectory() as td:
        root = Path(td)
        fixture = root / "pbp.csv"
        write_fixture(fixture)
        tw = w.extract_team_week_evidence(fixture, 2026)

        # 1. Target-week leakage is excluded.
        snap = w.build_snapshot(tw, season=2026, target_week=2, source={"sha256":"x"}, min_teams=2, generated_at="t")
        assert snap["target_week_realised_stats_excluded"] is True and snap["max_input_week"] == 1; checks += 1

        # 2. Exact offense sack rate and no-play exclusion.
        a = snap["teams"]["A"]["offense"]
        assert a["pass_dropbacks"] == 2 and a["sacks_allowed"] == 1
        close(a["sack_rate_allowed"], 0.5); checks += 1

        # 3. Scrambles/kneels excluded from designed-rush denominator.
        assert a["designed_rushes"] == 2
        close(a["rush_epa_per_attempt"], 0.1)
        close(a["rush_success_rate"], 0.5)
        close(a["stuff_rate_allowed"], 0.5); checks += 1

        # 4. Defense mirrors opponent offensive evidence.
        bdef = snap["teams"]["B"]["defense"]
        assert bdef["pass_dropbacks"] == 2 and bdef["sacks_generated"] == 1
        close(bdef["sack_rate_generated"], 0.5); checks += 1

        # 5. Missing qb_hit remains missing rather than zero-imputed.
        b = snap["teams"]["B"]["offense"]
        assert b["qb_hit_observed_passes"] == 0 and b["qb_hit_rate_allowed"] is None and b["qb_hits_allowed"] is None; checks += 1

        # 6. Week 1 can never fabricate prior-week evidence.
        week1 = w.build_snapshot(tw, season=2026, target_week=1, source={}, min_teams=2)
        assert week1["status"] == "BLOCKED_INSUFFICIENT_PRIOR_WEEK_EVIDENCE" and week1["teams"] == {}; checks += 1

        # 7. Team coverage fails closed.
        low = w.build_snapshot(tw, season=2026, target_week=2, source={}, min_teams=3)
        assert low["status"] == "BLOCKED_INSUFFICIENT_TEAM_COVERAGE"; checks += 1

        # 8. Stronger offense receives higher proxy; weights are direction-aware.
        direct = synthetic_team_week({"T1":1,"T2":2,"T3":3,"T4":4})
        s2 = w.build_snapshot(direct, season=2026, target_week=2, source={}, min_teams=4, generated_at="x")
        assert s2["status"] == "READY_RESEARCH_ONLY"
        assert s2["teams"]["T4"]["offense"]["research_proxy_v1"] > s2["teams"]["T1"]["offense"]["research_proxy_v1"]; checks += 1

        # 9. Stronger defensive front receives higher proxy.
        assert s2["teams"]["T4"]["defense"]["research_proxy_v1"] > s2["teams"]["T1"]["defense"]["research_proxy_v1"]; checks += 1

        # 10. Owner contract is explicitly research-only and leaves M9/rankings untouched.
        assert s2["production_model"] == "M9" and s2["canonical_rankings_changed"] is False and s2["runtime_changed"] is False
        assert s2["feature_owner"]["production_validated"] is False and s2["feature_owner"]["validation_owner"] == "Window 2B"
        assert s2["adp_used_as_football_feature"] is False; checks += 1

        # 11. First write is idempotent despite capture timestamp volatility.
        p = root / "evidence.json"
        v1 = dict(s2); v1["generated_at"] = "one"; v1["source"] = {"sha256":"abc","captured_at":"one"}
        v2 = dict(s2); v2["generated_at"] = "two"; v2["source"] = {"sha256":"abc","captured_at":"two"}
        assert w.first_write_json(p, v1) == "written"
        assert w.first_write_json(p, v2) == "identical"; checks += 1

        # 12. Different source/evidence cannot overwrite an immutable capture.
        changed = dict(v2); changed["source"] = {"sha256":"DIFFERENT","captured_at":"three"}
        try:
            w.first_write_json(p, changed)
            raise AssertionError("collision not raised")
        except w.EvidenceError as exc:
            assert "FIRST_WRITE_COLLISION" in str(exc)
        checks += 1

        # 13. Historical snapshots remain chronological.
        hist = w.historical_season_payload(season=2026, team_week=direct | {2: direct[1]}, source={"sha256":"h"}, min_teams=4)
        first = hist["snapshots"][0]
        assert first["target_week"] == 2 and first["max_input_week"] == 1; checks += 1

        # 14. Historical output strips capture-time source volatility.
        assert "captured_at" not in hist["source"] and hist["target_week_realised_stats_excluded"] is True; checks += 1

        # 15. Zero is a legitimate measured value, distinct from missing.
        assert w.safe_rate(0, 10) == 0.0 and w.safe_rate(None, 10) is None and w.safe_rate(0, 0) is None; checks += 1

    print(f"PASS Window 2A trench evidence + feature owner integrity ({checks}/15)")


if __name__ == "__main__":
    main()
