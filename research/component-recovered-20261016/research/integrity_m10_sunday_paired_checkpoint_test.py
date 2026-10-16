#!/usr/bin/env python3
"""No-network coverage for timing, pairing, scoring and immutable collisions."""
from __future__ import annotations

import gzip
from pathlib import Path
import tempfile

from capture_fie_sunday_paired_checkpoint import (
    CHECKPOINT_ID, checkpoint_decision, create_paired_checkpoint, paths,
    validate_checkpoint,
)
from m10_prospective_capture_contract import canonical_bytes, capture_hours, read_json, read_jsonl_gzip, sha256_bytes, sha256_file, write_json
from m10_prospective_weekly_producer import fixture_raw_envelope
from validate_sunday_paired_checkpoint_write_plan import validate as validate_write_plan


def game(kickoff: str, home: str, away: str) -> dict[str, str]:
    return {"kickoff_at": kickoff, "home_team": home, "away_team": away}


def test_timing() -> None:
    # October EDT and November EST resolve from America/New_York, not Berlin.
    october = [game("2026-10-04T17:00:00+00:00", "AAA", "BBB")]
    assert checkpoint_decision(october, "2026-10-04T10:59:59+00:00")["status"] == "WINDOW_NOT_REACHED"
    assert checkpoint_decision(october, "2026-10-04T11:00:00+00:00")["status"] == "DUE"
    assert checkpoint_decision(october, "2026-10-04T12:30:00+00:00")["status"] == "DUE"
    assert checkpoint_decision(october, "2026-10-04T12:30:01+00:00")["status"] == "WINDOW_MISSED"
    november = [game("2026-11-08T18:00:00+00:00", "AAA", "BBB")]
    assert checkpoint_decision(november, "2026-11-08T12:00:00+00:00")["status"] == "DUE"
    no_main = [game("2026-10-04T13:30:00+00:00", "AAA", "BBB")]
    assert checkpoint_decision(no_main, "2026-10-04T11:00:00+00:00")["status"] == "NO_MAIN_SLATE"


def test_remaining_games() -> None:
    games = [
        game("2026-10-02T00:15:00+00:00", "III", "JJJ"),
        game("2026-10-04T11:20:00+00:00", "KKK", "LLL"),
        game("2026-10-04T13:30:00+00:00", "AAA", "BBB"),
        game("2026-10-04T17:00:00+00:00", "CCC", "DDD"),
    ]
    value = checkpoint_decision(games, "2026-10-04T11:00:00+00:00")
    assert value["status"] == "DUE"
    assert {(row["home_team"], row["away_team"]) for row in value["eligible_games"]} == {("AAA", "BBB"), ("CCC", "DDD")}
    assert len(value["excluded_games"]) == 2


def fixture_input(root: Path) -> tuple[Path, dict[str, str], bytes]:
    observed, anchor = "2026-10-04T11:00:00+00:00", "2026-10-04T17:00:00+00:00"
    manifest = fixture_raw_envelope(root, observed_at=observed)
    value = read_json(manifest); folder = manifest.parent
    schedule_path = folder / "schedule.json"; schedule = read_json(schedule_path)
    kickoffs = ("2026-10-04T13:30:00+00:00", anchor, "2026-10-04T20:25:00+00:00", "2026-10-05T00:20:00+00:00")
    for row, kickoff in zip(schedule["games"], kickoffs): row["kickoff_at"] = kickoff
    schedule["first_kickoff_at"] = anchor; schedule["checkpoint_id"] = CHECKPOINT_ID; schedule["excluded_games"] = []
    write_json(schedule_path, schedule)
    value["checkpoint_id"] = CHECKPOINT_ID; value["capture"]["observed_at"] = observed; value["capture"]["first_kickoff_at"] = anchor; value["capture"]["hours_before_first_kickoff"] = capture_hours(observed, anchor)
    record = next(row for row in value["source_records"] if row["role"] == "schedule")
    record["sha256"] = sha256_file(schedule_path)
    for item in record["response_files"]:
        if item["path"] == "schedule.json": item["sha256"] = sha256_file(schedule_path)
    write_json(manifest, value)
    ids = {"sid-qb": "fixture-qb", "sid-rb": "fixture-rb", "sid-wr": "fixture-wr", "sid-te": "fixture-te"}
    provider = []
    for sid, position in zip(ids, ("QB", "RB", "WR", "TE")):
        provider.append({"player_id": sid, "player": {"player_id": sid, "position": position}, "stats": {"pass_yd": 250 if position == "QB" else 0, "pass_td": 2 if position == "QB" else 0, "rush_yd": 20, "rec": 4 if position != "QB" else 0, "rec_yd": 55 if position != "QB" else 0}})
    provider.append({"player_id": "unresolved", "player": {"position": "WR"}, "stats": {"rec": 2}})
    return manifest, ids, canonical_bytes(provider)


def test_capture() -> None:
    with tempfile.TemporaryDirectory(prefix="fie-sunday-checkpoint-") as folder:
        root = Path(folder); raw, ids, payload = fixture_input(root / "fixture")
        result = create_paired_checkpoint(raw, payload, "2026-10-04T11:05:00+00:00", ids, output_root=root)
        assert result["status"] == "CREATED"
        value = validate_checkpoint(root, 2026, 5); p = paths(root, 2026, 5)
        assert value["source_drift_seconds"] == 300
        assert value["coverage"]["m10_eligible"] == 4
        assert value["coverage"]["matched"] == 4
        assert value["coverage"]["league_profiles"] == 22
        assert value["coverage"]["scoring_rows"] == 88
        assert value["coverage"]["excluded_by_reason"] == {"IDENTITY_UNRESOLVED": 1}
        assert p["sleeper_raw"].is_file() and p["sleeper_scoring"].is_file()
        m10_manifest = read_json(root / value["m10"]["manifest_path"])
        assert m10_manifest["schedule_snapshot_sha256"] == value["schedule_snapshot_sha256"]
        projections = read_jsonl_gzip(p["sleeper_rows"])
        scoring = read_jsonl_gzip(p["sleeper_scoring"])
        assert len(projections) == 4 and len(scoring) == 4 * 22
        assert all(row["checkpoint_id"] == CHECKPOINT_ID for row in projections + scoring)
        with gzip.open(p["sleeper_raw"], "rb") as handle:
            assert sha256_bytes(handle.read()) == value["sleeper_raw_payload_sha256"]
        assert not (root / "data/research/prospective/m10/forecasts/2026/week_05/capture-manifest.json").exists()
        first = p["manifest"].read_bytes()
        assert create_paired_checkpoint(raw, payload, "2026-10-04T11:05:00+00:00", ids, output_root=root)["status"] == "EXISTS"
        assert p["manifest"].read_bytes() == first
        try:
            create_paired_checkpoint(raw, payload + b" ", "2026-10-04T11:05:00+00:00", ids, output_root=root)
        except ValueError as error:
            assert "divergent first-write" in str(error)
        else: raise AssertionError("divergent retry accepted")


def test_drift_fails_before_output() -> None:
    with tempfile.TemporaryDirectory(prefix="fie-sunday-drift-") as folder:
        root = Path(folder); raw, ids, payload = fixture_input(root / "fixture")
        try: create_paired_checkpoint(raw, payload, "2026-10-04T11:10:01+00:00", ids, output_root=root)
        except ValueError as error: assert "drift" in str(error)
        else: raise AssertionError("source drift accepted")
        assert not paths(root, 2026, 5)["manifest"].exists()


def test_invalid_provider_payload_leaves_no_partial_checkpoint() -> None:
    with tempfile.TemporaryDirectory(prefix="fie-sunday-provider-failure-") as folder:
        root = Path(folder); raw, ids, _ = fixture_input(root / "fixture")
        try:
            create_paired_checkpoint(raw, b'{"unexpected":"object"}', "2026-10-04T11:05:00+00:00", ids, output_root=root)
        except ValueError as error:
            assert "must be a list" in str(error)
        else:
            raise AssertionError("invalid provider payload accepted")
        p = paths(root, 2026, 5)
        assert not p["manifest"].exists() and not p["m10_root"].exists() and not p["sleeper_root"].exists()


def test_write_allowlist() -> None:
    validate_write_plan("refs/heads/main", [
        "data/research/prospective/m10/checkpoints/2026/week_05/sunday-main-t6/forecast.jsonl.gz",
        "data/research/prospective/paired-checkpoints/2026/week_05/sunday-main-t6/manifest.json",
        "data/research/market/sleeper/checkpoints/2026/week_05/sunday-main-t6/projection.jsonl.gz",
        "data/research/portfolio/2026/point-in-time-evidence-report.json",
    ])
    for ref, changed in (
        ("refs/heads/feature", ["data/research/prospective/m10/checkpoints/2026/week_05/sunday-main-t6/x"]),
        ("refs/heads/main", ["data/research/prospective/m10/forecasts/2026/week_05/forecast.jsonl.gz"]),
        ("refs/heads/main", ["app/data/snapshot.json"]),
    ):
        try:
            validate_write_plan(ref, changed)
        except ValueError:
            pass
        else:
            raise AssertionError(f"write allowlist accepted ref={ref} paths={changed}")


def test_workflow_contract() -> None:
    workflow = (Path(__file__).parents[1] / ".github/workflows/capture-fie-sunday-paired-checkpoint.yml").read_text(encoding="utf-8")
    for token in (
        "timezone: America/New_York", "cancel-in-progress: false", "github.ref == 'refs/heads/main'",
        "uses: ./.github/workflows/_fie-calendar-policy.yml", "purpose: m10",
        "validate_sunday_paired_checkpoint_write_plan.py", "git rebase origin/main",
    ):
        assert token in workflow
    assert "--force" not in workflow
    assert "data/research/prospective/m10/forecasts" not in workflow


def main() -> int:
    test_timing(); test_remaining_games(); test_capture(); test_drift_fails_before_output(); test_invalid_provider_payload_leaves_no_partial_checkpoint(); test_write_allowlist(); test_workflow_contract()
    print("PASS Sunday paired checkpoint (timing, cohort, pairing, scoring, drift, first-write, partial-failure, write allowlist)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
