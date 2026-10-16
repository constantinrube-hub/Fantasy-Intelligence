#!/usr/bin/env python3
"""No-network deadline, tamper, and preservation regressions."""
import hashlib
import json
import tempfile
from pathlib import Path
from unittest.mock import patch

import weekly_evidence_audit as w
from point_in_time_capture import canonical_bytes, build_envelope


def fixture(root):
    path = root / "data/research/context/weather/2026/week_05/capture/schedule-source-envelope.json"
    payload = {"season": 2026, "week": 5, "games": [
        {"game_id": "thu", "kickoff": "2026-10-09T00:15:00Z"},
        {"game_id": "sun", "kickoff": "2026-10-11T17:00:00Z"},
    ]}
    path.parent.mkdir(parents=True)
    path.write_text(json.dumps({"observed_at": "2026-10-07T12:00:00Z", "payload": payload,
        "payload_sha256": hashlib.sha256(canonical_bytes(payload)).hexdigest()}))
    return path


def main():
    with tempfile.TemporaryDirectory() as td:
        root = Path(td)
        source = fixture(root)
        before = {p: p.read_bytes() for p in root.rglob("*") if p.is_file()}
        with patch.object(w, "validate_capture", side_effect=AssertionError("missing capture cannot be validated")):
            early = w.audit(root, 2026, 5, w.stamp("2026-10-08T00:15:00Z"))
            assert early["status"] == "ON_TRACK"
            assert [r["status"] for r in early["checkpoints"]] == ["NOT_DUE"] * 4
            due = w.audit(root, 2026, 5, w.stamp("2026-10-08T06:15:00Z"))
            assert due["checkpoints"][0]["status"] == "DUE_MISSING"
            closed = w.audit(root, 2026, 5, w.stamp("2026-10-09T00:15:00Z"))
            assert closed["checkpoints"][0]["status"] == "DUE_MISSING"
            missed = w.audit(root, 2026, 5, w.stamp("2026-10-09T00:15:01Z"))
            assert missed["status"] == "ATTENTION" and missed["checkpoints"][0]["status"] == "MISSED_UNRECORDED"
            sunday = w.audit(root, 2026, 5, w.stamp("2026-10-11T11:00:00Z"))
            assert sunday["checkpoints"][1]["status"] == "DUE_MISSING"
        pr2_due = w.audit(root, 2026, 5, w.stamp("2026-10-08T16:45:00Z"))
        assert pr2_due["checkpoints"][2]["status"] == "DUE_MISSING"
        pr2_closed = w.audit(root, 2026, 5, w.stamp("2026-10-08T20:15:01Z"))
        assert pr2_closed["checkpoints"][2]["status"] == "MISSED_UNRECORDED"
        assert before == {p: p.read_bytes() for p in root.rglob("*") if p.is_file()}, "Audit modified capture evidence"
        # A source-backed PR2 capture must bind schedule, matchups, league scope,
        # and checkpoint observation time. Current roster files are unnecessary.
        capture = root / "data/research/evaluation/2026/weeks/week-5/lineups/evidence/captures/portfolio-test"
        capture.mkdir(parents=True)
        observed = "2026-10-08T18:00:00Z"
        games, _ = w.schedule(root, 2026, 5, w.stamp(observed))
        schedule_rows = [{"game_id": game["game_id"], "kickoff_utc": game["kickoff_at"]} for game in games]
        schedule_hash = hashlib.sha256(canonical_bytes(schedule_rows)).hexdigest()
        matchups = {"league": [{"roster_id": 1, "starters": ["player"]}]}
        payload = {"schedule_games": schedule_rows, "matchup_payloads": matchups}
        envelope = build_envelope(capture_id="test", capture_intent="OTHER_GOVERNED", provider="fixture",
            endpoint="fixture", observed_at=observed, as_of_semantics="fixture", payload=payload)
        source_path = capture / "source-envelope.json"
        source_path.write_text(json.dumps(envelope))
        item = {"season": 2026, "week": 5, "captured_at": observed}
        evidence = {**item, "schema": w.PR2_SCHEMA, "checkpoint_id": "PR2_WEEK_OPEN_T6",
            "schedule_games": schedule_rows, "schedule_games_sha256": schedule_hash,
            "league_bindings": [{"league_id": "league", "matchup_payload_sha256": hashlib.sha256(canonical_bytes(matchups["league"])).hexdigest()}],
            "lock_evidence_by_league": {"league": {**item, "schedule_games_sha256": schedule_hash}},
            "matchup_evidence_by_league": {"league": {**item, "rows": matchups["league"]}}}
        evidence_path = capture / "operational-evidence.json"
        evidence_path.write_text(json.dumps(evidence))
        checked = w.audit(root, 2026, 5, w.stamp("2026-10-08T19:00:00Z"))
        assert checked["checkpoints"][2]["status"] == "CAPTURED_VALIDATED"
        earlier = w.audit(root, 2026, 5, w.stamp("2026-10-08T17:00:00Z"))
        assert earlier["checkpoints"][2]["status"] == "DUE_MISSING"
        evidence["matchup_evidence_by_league"]["league"]["rows"] = []
        evidence_path.write_text(json.dumps(evidence))
        tampered = w.audit(root, 2026, 5, w.stamp("2026-10-08T19:00:00Z"))
        assert tampered["checkpoints"][2]["status"] == "BLOCKED_INVALID_EVIDENCE"
        assert "MATCHUP_BINDING" in tampered["checkpoints"][2]["errors"][0]["reason"]
        future = w.audit(root, 2026, 5, w.stamp("2026-10-07T11:00:00Z"))
        assert future["status"] == "BLOCKED" and "SCHEDULE_UNAVAILABLE" in future["reason"]
        raw = json.loads(source.read_text())
        raw["payload"]["games"][0]["kickoff"] = "2026-10-10T00:15:00Z"
        source.write_text(json.dumps(raw))
        assert "HASH_MISMATCH" in w.audit(root, 2026, 5, w.stamp("2026-10-08T00:00:00Z"))["reason"]
        manifest, missed = root / "manifest.json", root / "missed.json"
        manifest.write_text(json.dumps({"season": 2026, "week": 5, "captured_at": "2026-10-08T12:00:00Z"}))
        timing = {"season": 2026, "week": 5, "status": "DUE_MISSING"}
        row = w.terminal(root, manifest, missed, lambda _: {}, timing, w.stamp("2026-10-08T11:00:00Z"))
        assert row["status"] == "BLOCKED_INVALID_EVIDENCE"
        manifest.write_text(json.dumps({"season": 2026, "week": 4, "captured_at": "2026-10-08T10:00:00Z"}))
        assert "TARGET_MISMATCH" in w.terminal(root, manifest, missed, lambda _: {}, timing, w.stamp("2026-10-08T11:00:00Z"))["reason"]
        missed.write_text("{}")
        assert w.terminal(root, manifest, missed, lambda _: {}, timing, w.stamp("2026-10-08T11:00:00Z"))["status"] == "BLOCKED_CONFLICTING_TERMINAL_EVIDENCE"
    try:
        w.stamp("2026-10-08T00:00:00")
        raise AssertionError("Naive timestamp accepted")
    except ValueError:
        pass
    print("PASS weekly evidence audit: due boundaries, schedule hash, target identity, future evidence, conflicts, read-only preservation")


if __name__ == "__main__":
    main()
