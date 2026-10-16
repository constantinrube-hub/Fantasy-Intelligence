#!/usr/bin/env python3
"""Integrity check for the fail-closed Waiver-v2 exact-replay closure."""
from __future__ import annotations

import json
import csv
import tempfile
from pathlib import Path

from waiver_v2_exact_replay_closure import CLOSURE_SCHEMA, build_exact_replay_closure, _sha256


with tempfile.TemporaryDirectory() as raw:
    root = Path(raw)
    profiles = root / "profiles"
    alpha = profiles / "alpha"; beta = profiles / "beta"
    alpha.mkdir(parents=True); beta.mkdir(parents=True)
    def write_ledger(path: Path, rows: list[tuple[str, bool]]) -> None:
        with path.open("w", encoding="utf-8", newline="") as handle:
            writer = csv.DictWriter(handle, fieldnames=["position_model", "exact_scoring", "outcome_complete", "outcome_status"])
            writer.writeheader()
            for position, complete in rows:
                writer.writerow({"position_model": position, "exact_scoring": complete,
                                 "outcome_complete": complete, "outcome_status": "COMPLETE_EXACT" if complete else "BLOCKED_UNSUPPORTED_EXACT_SCORING"})

    alpha_ledger = alpha / "offensive-outcome-ledger.csv"
    beta_ledger = beta / "offensive-outcome-ledger.csv"
    write_ledger(alpha_ledger, [("QB", True)] * 2 + [("RB", False)] * 6 + [("WR", True), ("TE", True)])
    write_ledger(beta_ledger, [("QB", True)] * 4 + [("RB", True)] * 3 + [("WR", True)] * 2 + [("TE", True)])
    alpha_report = {
        "scoring_signature": "alpha",
        "ledger": {"path": str(alpha_ledger), "sha256": _sha256(alpha_ledger), "rows": 10, "complete_exact_rows": 4, "incomplete_rows": 6},
        "inventories": {
            "QB": {"exact_replay_eligible": True, "blocked_keys": []},
            "RB": {"exact_replay_eligible": False, "blocked_keys": [{"key": "fum_lost", "support_status": "BLOCKED_EVENT_SEMANTICS", "required_columns": [], "reason": "ambiguous attribution"}]},
            "WR": {"exact_replay_eligible": True, "blocked_keys": []},
            "TE": {"exact_replay_eligible": True, "blocked_keys": []},
        },
    }
    beta_report = {
        "scoring_signature": "beta",
        "ledger": {"path": str(beta_ledger), "sha256": _sha256(beta_ledger), "rows": 10, "complete_exact_rows": 10, "incomplete_rows": 0},
        "inventories": {position: {"exact_replay_eligible": True, "blocked_keys": []} for position in ("QB", "RB", "WR", "TE")},
    }
    for directory, payload in ((alpha, alpha_report), (beta, beta_report)):
        (directory / "offensive-outcome-ledger-report.json").write_text(json.dumps(payload), encoding="utf-8")
    blocker_path = root / "event-blockers.jsonl"
    blocker_path.write_text('{"phase":"E2","status":"BLOCKED_EVENT_SEMANTICS"}\n', encoding="utf-8")
    batch = {
        "schema": "fie-waiver-v2-profile-batch-v1", "league_count": 3,
        "shared_source_run": {"event_ledger_receipt": {"rule_support": {"pass_sack": {"support_status": "EXACT_EVENT_READY"}},
                                                      "blockers": {"path": str(blocker_path), "sha256": _sha256(blocker_path), "rows": 1}}},
        "profiles": [
            {"scoring_signature": "alpha", "league_ids": ["1", "2"], "league_names": ["One", "Two"], "coverage": alpha_report["ledger"], "outcome_report": {"path": str(alpha / "offensive-outcome-ledger-report.json")}},
            {"scoring_signature": "beta", "league_ids": ["3"], "league_names": ["Three"], "coverage": beta_report["ledger"], "outcome_report": {"path": str(beta / "offensive-outcome-ledger-report.json")}},
        ],
    }
    batch_path = root / "profile-batch-report.json"; output_path = root / "exact-replay-closure.json"
    batch_path.write_text(json.dumps(batch), encoding="utf-8")
    closure = build_exact_replay_closure(batch_report_path=batch_path, output_path=output_path)
    assert closure["schema"] == CLOSURE_SCHEMA and not closure["activation_eligible"]
    assert closure["summary"]["all_positions_exact_profile_count"] == 1
    assert closure["summary"]["position_exact_profile_counts"] == {"QB": 2, "RB": 1, "WR": 2, "TE": 2}
    assert closure["summary"]["complete_exact_rows"] == 14 and closure["summary"]["incomplete_rows"] == 6
    assert closure["summary"]["position_complete_exact_outcome_rows"] == {"QB": 6, "RB": 3, "WR": 3, "TE": 2}
    assert closure["profiles"][0]["outcome_ledger"]["sha256"] and closure["profiles"][0]["exact_outcome_rows_by_position"]["RB"]["rows"] == 6
    assert closure["event_blockers"]["sha256"] == _sha256(blocker_path)
    assert closure["summary"]["blocker_rollup"] == [{"position": "RB", "rule": "fum_lost", "support_status": "BLOCKED_EVENT_SEMANTICS", "required_columns": [], "profiles_blocked": 1, "reason": "ambiguous attribution"}]
    assert output_path.exists()
    write_ledger(alpha_ledger, [("QB", True)])
    try:
        build_exact_replay_closure(batch_report_path=batch_path, output_path=output_path)
        raise AssertionError("truncated stored outcome ledger must fail closure")
    except ValueError as error:
        assert "hash mismatch" in str(error)
    write_ledger(alpha_ledger, [("QB", True)] * 2 + [("RB", False)] * 6 + [("WR", True), ("TE", True)])
    write_ledger(alpha_ledger, [("QB", True)] * 2 + [("RB", False)] * 6 + [("WR", True), ("QB", True)])
    try:
        build_exact_replay_closure(batch_report_path=batch_path, output_path=output_path)
        raise AssertionError("same-count altered outcome ledger must fail closure")
    except ValueError as error:
        assert "hash mismatch" in str(error)
    write_ledger(alpha_ledger, [("QB", True)] * 2 + [("RB", False)] * 6 + [("WR", True), ("TE", True)])
    blocker_path.write_text("changed\n", encoding="utf-8")
    try:
        build_exact_replay_closure(batch_report_path=batch_path, output_path=output_path)
        raise AssertionError("changed event blocker ledger must fail closure")
    except ValueError as error:
        assert "event blocker evidence is missing or changed" in str(error)

print("OK waiver-v2 exact replay closure is per-profile and fail-closed")
