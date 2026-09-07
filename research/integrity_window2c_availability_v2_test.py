#!/usr/bin/env python3
"""Synthetic fail-closed integrity tests for Window 2C."""
from __future__ import annotations

import gzip
import importlib.util
import json
import tempfile
from pathlib import Path

MODULE_PATH = Path(__file__).with_name("window2c_availability_v2.py")
spec = importlib.util.spec_from_file_location("window2c_availability_v2", MODULE_PATH)
m = importlib.util.module_from_spec(spec)
assert spec and spec.loader
spec.loader.exec_module(m)

PASS = 0


def check(name: str, condition: bool) -> None:
    global PASS
    if not condition:
        raise AssertionError(name)
    PASS += 1
    print(f"PASS {name}")


def write_snapshot(root: Path, captured_at: str, rows: list[dict]) -> Path:
    day = captured_at[:10]
    base = root / "data/research/availability/sleeper/2026"
    base.mkdir(parents=True, exist_ok=True)
    data = base / f"availability_{day}.jsonl.gz"
    meta = Path(str(data) + ".meta.json")
    with gzip.open(data, "wt", encoding="utf-8") as handle:
        for row in rows:
            full = {"captured_at": captured_at, "availability_as_of": day, "source": "fixture", **row}
            handle.write(json.dumps(full) + "\n")
    meta.write_text(json.dumps({
        "captured_at": captured_at,
        "availability_as_of": day,
        "source": "fixture",
        "immutable_first_write": True,
    }), encoding="utf-8")
    return data


def opportunity(rows: list[dict]) -> dict[tuple[str, str], dict]:
    return {(r["team"], r["sleeper_id"], r["role_family"]): r for r in rows}


def main() -> None:
    # 1–6 typed-state semantics.
    check("official OUT maps to OUT", m.normalize_availability_state({"status":"Active","injury_status":"Out"})[0] == "OUT")
    check("questionable remains uncertain", m.normalize_availability_state({"status":"Active","injury_status":"Questionable"})[0] == "QUESTIONABLE")
    check("doubtful remains uncertain", m.normalize_availability_state({"status":"Active","injury_status":"Doubtful"})[0] == "DOUBTFUL")
    check("limited practice is LIMITED not OUT", m.normalize_availability_state({"status":"Active","practice_participation":"Limited"})[0] == "LIMITED")
    check("injured reserve maps to IR", m.normalize_availability_state({"status":"Injured Reserve"})[0] == "IR")
    check("missing status stays UNKNOWN", m.normalize_availability_state({})[0] == "UNKNOWN")

    with tempfile.TemporaryDirectory() as td:
        root = Path(td)
        base_rows = [
            {"sleeper_id":"a1","full_name":"RB One","team":"AAA","position_model":"RB","status":"Active","injury_status":"Out","depth_chart_order":1},
            {"sleeper_id":"a2","full_name":"RB Two","team":"AAA","position_model":"RB","status":"Active","depth_chart_order":2},
            {"sleeper_id":"a3","full_name":"RB Three","team":"AAA","position_model":"RB","status":"Active","depth_chart_order":3},
            {"sleeper_id":"a4","full_name":"RB Four","team":"AAA","position_model":"RB","status":"Inactive","depth_chart_order":4},
            {"sleeper_id":"b1","full_name":"RB Other","team":"BBB","position_model":"RB","status":"Active","depth_chart_order":1},
            {"sleeper_id":"a5","full_name":"WR Q","team":"AAA","position_model":"WR","status":"Active","injury_status":"Questionable","depth_chart_order":1},
        ]
        old = write_snapshot(root, "2026-09-05T12:00:00+00:00", base_rows)
        # A post-kickoff capture contains contradictory evidence and must never be selected.
        post_rows = [dict(row) for row in base_rows]
        post_rows[0]["injury_status"] = None
        post = write_snapshot(root, "2026-09-11T12:00:00+00:00", post_rows)

        games = [{
            "game_id":"2026_01_BBB_AAA", "home_team":"AAA", "away_team":"BBB",
            "kickoff":"2026-09-10T20:00:00+00:00",
        }]
        payload = m.build_availability_contract(
            root=root, season=2026, week=1, as_of="2026-09-12T00:00:00+00:00", games=games,
            schedule_binding={"status":"FIXTURE"},
        )
        by_id = {row["sleeper_id"]: row for row in payload["players"]}
        # 7–11 point-in-time and governance.
        check("latest eligible snapshot is pre-kickoff", by_id["a1"]["evidence_source_path"].endswith(old.name))
        check("post-kickoff snapshot rejected", not by_id["a1"]["evidence_source_path"].endswith(post.name))
        check("confirmed unavailable flag only for unavailable", by_id["a1"]["confirmed_unavailable"] and not by_id["a5"]["confirmed_unavailable"])
        check("uncertain flag is explicit", by_id["a5"]["uncertain_availability"] is True)
        check("availability contract never changes projections", payload["direct_fantasy_projection_adjustment"] is False and payload["canonical_rankings_changed"] is False)

        opp_rows = [
            {"team":"AAA","sleeper_id":"a1","role_family":"RB","baseline_share":0.50,"observed_at":"2026-09-05T10:00:00+00:00","source":"fixture"},
            {"team":"AAA","sleeper_id":"a2","role_family":"RB","baseline_share":0.30,"observed_at":"2026-09-05T10:00:00+00:00","source":"fixture"},
            {"team":"AAA","sleeper_id":"a3","role_family":"RB","baseline_share":0.20,"observed_at":"2026-09-05T10:00:00+00:00","source":"fixture"},
            {"team":"AAA","sleeper_id":"a4","role_family":"RB","baseline_share":0.10,"observed_at":"2026-09-05T10:00:00+00:00","source":"fixture"},
            {"team":"BBB","sleeper_id":"b1","role_family":"RB","baseline_share":0.90,"observed_at":"2026-09-05T10:00:00+00:00","source":"fixture"},
        ]
        red = m.build_redistribution_contract(payload, opportunity=opportunity(opp_rows), opportunity_binding={"status":"FIXTURE"})
        out = next(row for row in red["scenarios"] if row["trigger_sleeper_id"] == "a1")
        alloc = {row["sleeper_id"]: row["redistributed_share"] for row in out["allocations"]}
        # 12–17 redistribution safeguards.
        check("confirmed absence gets confirmed scenario", out["scenario_kind"] == "CONFIRMED_ABSENCE")
        check("redistribution conserves vacated share", abs(sum(alloc.values()) + out["residual_unallocated_share"] - 0.50) < 1e-9)
        check("unavailable recipient excluded", "a4" not in alloc)
        check("cross-team recipient excluded", "b1" not in alloc)
        check("same-role recipients receive proportional share", abs(alloc["a2"] - 0.30) < 1e-9 and abs(alloc["a3"] - 0.20) < 1e-9)
        q = next(row for row in red["scenarios"] if row["trigger_sleeper_id"] == "a5")
        check("questionable is only IF_ABSENT scenario", q["scenario_kind"] == "IF_ABSENT_SCENARIO")

        red_missing = m.build_redistribution_contract(payload, opportunity={}, opportunity_binding={"status":"NOT_BOUND"})
        missing_out = next(row for row in red_missing["scenarios"] if row["trigger_sleeper_id"] == "a1")
        # 18–19 missing evidence behavior.
        check("missing opportunity baseline stays blocked", missing_out["status"] == "BLOCKED_OPPORTUNITY_BASELINE_MISSING")
        check("missing opportunity is not zero-imputed", missing_out["vacated_share"] is None and missing_out["allocations"] == [])

        # 20 post-cutoff opportunity evidence fails closed.
        bad_opp = opportunity([{**opp_rows[0], "observed_at":"2026-09-10T21:00:00+00:00"}])
        try:
            m.build_redistribution_contract(payload, opportunity=bad_opp, opportunity_binding={"status":"FIXTURE"})
            post_cutoff_failed = False
        except m.AvailabilityError as exc:
            post_cutoff_failed = "POST_CUTOFF_OPPORTUNITY_EVIDENCE" in str(exc)
        check("post-cutoff opportunity evidence rejected", post_cutoff_failed)

        # 21 explicit share validation.
        baseline_path = root / "bad-opportunity.json"
        baseline_path.write_text(json.dumps({"schema":m.OPPORTUNITY_SCHEMA,"rows":[{
            "sleeper_id":"a1","team":"AAA","role_family":"RB","baseline_share":1.2,
            "observed_at":"2026-09-05T10:00:00+00:00"
        }]}), encoding="utf-8")
        try:
            m.load_opportunity_baseline(baseline_path)
            bad_share_failed = False
        except m.AvailabilityError as exc:
            bad_share_failed = "OUT_OF_RANGE" in str(exc)
        check("invalid opportunity share rejected", bad_share_failed)

        # 22 immutable first-write collision.
        immutable = root / "immutable.json"
        check("first write created", m.first_write_json(immutable, {"a":1}) == "CREATED")
        check("identical retry is no-op", m.first_write_json(immutable, {"a":1}) == "EXISTS_IDENTICAL")
        try:
            m.first_write_json(immutable, {"a":2})
            collision_failed = False
        except m.AvailabilityError as exc:
            collision_failed = "IMMUTABLE_FIRST_WRITE_COLLISION" in str(exc)
        check("different retry collision fails closed", collision_failed)

        # 25 deterministic semantics for identical inputs.
        payload2 = m.build_availability_contract(
            root=root, season=2026, week=1, as_of="2026-09-12T00:00:00+00:00", games=games,
            schedule_binding={"status":"FIXTURE"},
        )
        check("availability build deterministic", m.canonical_bytes(payload) == m.canonical_bytes(payload2))

        multi_role = opportunity(opp_rows + [
            {"team":"AAA","sleeper_id":"a1","role_family":"TARGETS","baseline_share":0.15,"observed_at":"2026-09-05T10:00:00+00:00","source":"fixture"},
            {"team":"AAA","sleeper_id":"a2","role_family":"TARGETS","baseline_share":0.10,"observed_at":"2026-09-05T10:00:00+00:00","source":"fixture"},
            {"team":"AAA","sleeper_id":"a3","role_family":"TARGETS","baseline_share":0.05,"observed_at":"2026-09-05T10:00:00+00:00","source":"fixture"},
        ])
        multi = m.build_redistribution_contract(payload, opportunity=multi_role, opportunity_binding={"status":"FIXTURE"})
        a1_roles = {row["role_family"] for row in multi["scenarios"] if row["trigger_sleeper_id"] == "a1"}
        check("multiple explicit opportunity roles stay separate", a1_roles == {"RB", "TARGETS"})

    print(f"PASS Window 2C integrity: {PASS}/26 checks")


if __name__ == "__main__":
    main()
