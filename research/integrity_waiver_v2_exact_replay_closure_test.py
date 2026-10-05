#!/usr/bin/env python3
"""Integrity check for the fail-closed Waiver-v2 exact-replay closure."""
from __future__ import annotations

import json
import tempfile
from pathlib import Path

from waiver_v2_exact_replay_closure import CLOSURE_SCHEMA, build_exact_replay_closure


with tempfile.TemporaryDirectory() as raw:
    root = Path(raw)
    profiles = root / "profiles"
    alpha = profiles / "alpha"; beta = profiles / "beta"
    alpha.mkdir(parents=True); beta.mkdir(parents=True)
    alpha_report = {
        "scoring_signature": "alpha",
        "ledger": {"complete_exact_rows": 4, "incomplete_rows": 6},
        "inventories": {
            "QB": {"exact_replay_eligible": True, "blocked_keys": []},
            "RB": {"exact_replay_eligible": False, "blocked_keys": [{"key": "fum_lost", "support_status": "BLOCKED_EVENT_SEMANTICS", "required_columns": [], "reason": "ambiguous attribution"}]},
            "WR": {"exact_replay_eligible": True, "blocked_keys": []},
            "TE": {"exact_replay_eligible": True, "blocked_keys": []},
        },
    }
    beta_report = {
        "scoring_signature": "beta",
        "ledger": {"complete_exact_rows": 10, "incomplete_rows": 0},
        "inventories": {position: {"exact_replay_eligible": True, "blocked_keys": []} for position in ("QB", "RB", "WR", "TE")},
    }
    for directory, payload in ((alpha, alpha_report), (beta, beta_report)):
        (directory / "offensive-outcome-ledger-report.json").write_text(json.dumps(payload), encoding="utf-8")
    batch = {
        "schema": "fie-waiver-v2-profile-batch-v1", "league_count": 3,
        "shared_source_run": {"event_ledger_receipt": {"rule_support": {"pass_sack": {"support_status": "EXACT_EVENT_READY"}}}},
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
    assert closure["summary"]["blocker_rollup"] == [{"position": "RB", "rule": "fum_lost", "support_status": "BLOCKED_EVENT_SEMANTICS", "required_columns": [], "profiles_blocked": 1, "reason": "ambiguous attribution"}]
    assert output_path.exists()

print("OK waiver-v2 exact replay closure is per-profile and fail-closed")
