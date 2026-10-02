#!/usr/bin/env python3
"""Regression checks for portfolio-scaled, bounded M10 weekly capture."""
from __future__ import annotations

import shutil
import tempfile
from pathlib import Path

import pandas as pd
import numpy as np
import capture_m10_prospective_weekly_raw as raw_capture
from capture_m10_prospective_weekly_raw import current_roster_identity
import m10_prospective_weekly_producer as producer
from m10_prospective_capture_contract import (
    capture_paths, create_fixture_capture, fixture_scoring_rows, read_json,
    read_jsonl_gzip, sha256_file, validate_capture, write_json, write_jsonl_gzip,
)
from m10_prospective_source_bundle import validate_profile_population
from m10_prospective_weekly_producer import fixture_raw_envelope
from run_m10_prospective_weekly_capture import main as run_capture


def profile_population_checks() -> None:
    profiles = [{"league_id": f"league-{index:02d}"} for index in range(23)]
    states = [{"league_id": row["league_id"]} for row in profiles]
    payload = {
        "enabled_league_count": 23,
        "profiles": profiles,
        "league_roster_states": states,
    }
    assert len(validate_profile_population(payload)) == 23

    duplicate = {**payload, "profiles": [*profiles[:-1], profiles[0]]}
    try:
        validate_profile_population(duplicate)
    except AssertionError:
        pass
    else:
        raise AssertionError("duplicate league profile was accepted")


def batch_scoring_checks() -> None:
    rows = [
        {
            "forecast_id": f"forecast-{index}",
            "canonical_player_id": f"player-{index}",
            "model": "M9",
            "position_model": "RB",
            "predicted_raw_components": {"yards": 10.0 + index, "opportunities": 2.0},
        }
        for index in range(2)
    ]
    profiles = [
        {
            "league_id": f"league-{index:02d}",
            "league_format": "REDRAFT",
            "profile_scoring_signature": f"score-{index:02d}",
            "profile_fingerprint": str(index).zfill(64),
            "scoring_settings": {"factor": float(index + 1)},
            "captured_at": "2026-09-09T06:00:00+00:00",
        }
        for index in range(23)
    ]
    calls = 0
    original_many = producer._score_many
    original_residual = producer._residual_components

    def fake_many(items, scoring):
        nonlocal calls
        calls += 1
        if isinstance(items, pd.DataFrame):
            items = items.to_dict("records")
        factor = float(scoring["factor"])
        return [
            factor * sum(float(value) for value in item.values() if isinstance(value, (int, float)))
            for item in items
        ]

    def fake_residual(_lock, row):
        point = row["predicted_raw_components"]
        return [
            {name: float(value) + offset for name, value in point.items()}
            for offset in (-1.0, 0.0, 1.0)
        ]

    try:
        producer._score_many = fake_many
        producer._residual_components = fake_residual
        scored = producer.exact_profile_scoring(rows, profiles, {})
    finally:
        producer._score_many = original_many
        producer._residual_components = original_residual

    assert len(scored) == len(rows) * len(profiles)
    assert calls == 2 * len(profiles), calls
    assert [row["league_id"] for row in scored[:23]] == [row["league_id"] for row in profiles]
    assert all(row["forecast_id"] == "forecast-0" for row in scored[:23])
    assert all(row["forecast_id"] == "forecast-1" for row in scored[23:])


def terminal_capture_retry_check() -> None:
    root = Path(tempfile.mkdtemp(prefix="fie-m10-terminal-retry-"))
    try:
        raw = fixture_raw_envelope(root / "raw")
        output = root / "output"
        manifest = capture_paths(output, 2026, 5)["manifest"]
        write_json(manifest, {"status": "CAPTURED", "immutable": True})
        before = manifest.read_bytes()
        assert run_capture([
            "--raw-envelope", str(raw),
            "--output-root", str(output),
        ]) == 0
        assert manifest.read_bytes() == before
    finally:
        shutil.rmtree(root)


def current_roster_universe_check() -> None:
    """Current roster membership and current team must replace historical teams."""
    def row(pid, team="AAA", position="WR", status="ACT", season=2026, week=4):
        return {"gsis_id": pid, "team": team, "position": position, "status": status,
            "season": season, "week": week, "game_type": "REG", "full_name": f"Fixture {pid}"}
    rosters = pd.DataFrame([
        row("transfer", team="OLD", week=3), row("transfer", team="AAA"),
        row("transfer", team="AAA"), row("rookie", position="RB"),
        row("practice", status="DEV"), row("reserve", status="RES", position="TE"),
        row("inactive", status="INA"), row("inactive-spaced", status=" ina "),
        row("retired", status="RET"), row("cut", status="CUT"),
        row("old-season", season=2025), row("future", week=5),
        row(None), row("conflict", team="AAA"), row("conflict", team="BBB"),
    ])
    value = current_roster_identity(rosters, season=2026, week=4)
    players = {item["canonical_player_id"]: item for item in value["players"]}
    assert set(players) == {"transfer", "rookie", "practice", "reserve", "inactive", "inactive-spaced"}
    assert players["transfer"]["team"] == "AAA"
    assert players["rookie"]["position_model"] == "RB"
    assert value["current_roster_verified"] and value["roster_snapshot_week"] == 4
    assert value["ambiguous_count"] == 1
    reasons = {item["reason"] for item in value["symmetric_identity_exclusions"]}
    assert reasons == {"NOT_CURRENT_NFL_ROSTER_MEMBER", "UNRESOLVED_CURRENT_ROSTER_GSIS_ID", "AMBIGUOUS_CURRENT_ROSTER_IDENTITY"}
    target = producer._identity_targets({"games": [{"home_team": "AAA", "away_team": "BBB", "kickoff_at": "2026-10-02T00:15:00Z"}]}, value, season=2026, week=4)
    assert len(target) == 6
    assert set(target["canonical_player_id"]) == set(players)
    for bad in (rosters[rosters["week"] == 3], rosters.assign(status="UNKNOWN"), rosters.assign(status=None)):
        try:
            current_roster_identity(bad, season=2026, week=4)
        except ValueError:
            pass
        else:
            raise AssertionError("missing current roster or unknown membership status was accepted")
    try:
        current_roster_identity(pd.DataFrame([row("bad", status="NEW_CODE")]), season=2026, week=4)
    except ValueError as exc:
        assert "2026 week 4" in str(exc) and "NEW_CODE" in str(exc), str(exc)
    else:
        raise AssertionError("unknown status was accepted")
    # Live envelopes may never silently accept the old all-time identity list.
    with tempfile.TemporaryDirectory(prefix="fie-m10-live-roster-guard-") as directory:
        raw = fixture_raw_envelope(Path(directory))
        envelope = read_json(raw)
        envelope["fixture"] = False
        write_json(raw, envelope)
        try:
            producer.validate_raw_envelope(raw)
        except AssertionError:
            pass
        else:
            raise AssertionError("live historical-catalog universe was accepted")
        record = next(item for item in envelope["source_records"] if item["role"] == "identity_snapshot")
        path = raw.parent / record["path"]
        identity = read_json(path)
        identity.update(current_roster_verified=True, roster_snapshot_season=2026, roster_snapshot_week=5)
        write_json(path, identity)
        record["sha256"] = record["response_files"][0]["sha256"] = sha256_file(path)
        write_json(raw, envelope)
        assert producer.validate_raw_envelope(raw)[0]["fixture"] is False
        identity["roster_snapshot_week"] = 4
        write_json(path, identity)
        record["sha256"] = record["response_files"][0]["sha256"] = sha256_file(path)
        write_json(raw, envelope)
        try:
            producer.validate_raw_envelope(raw)
        except AssertionError:
            pass
        else:
            raise AssertionError("wrong-week live roster was accepted")


def early_window_source_check() -> None:
    """Early runs need only state/schedule, not an unpublished next-week roster."""
    calls = []
    original_fetch, original_now = raw_capture._fetch, raw_capture._now
    def fake_fetch(url, destination):
        calls.append(url)
        destination.parent.mkdir(parents=True, exist_ok=True)
        if url == raw_capture.STATE_URL:
            write_json(destination, {"season": "2026", "week": 4, "season_type": "regular"})
        elif url == raw_capture.GAMES_URL:
            destination.write_text("season,week,game_type,gameday,gametime,home_team,away_team\n2026,4,REG,2026-10-01,20:15,AAA,BBB\n", encoding="utf-8")
        else:
            raise AssertionError("early run requested football/roster sources")
        return {"path": destination, "sha256": sha256_file(destination), "source_identity": url, "release_or_etag": "fixture"}
    try:
        raw_capture._fetch, raw_capture._now = fake_fetch, lambda: "2026-09-29T00:00:00+00:00"
        with tempfile.TemporaryDirectory(prefix="fie-m10-early-roster-") as directory:
            assert raw_capture.capture(Path(directory), season=None, week=None, output_root=Path(directory) / "evidence") is None
            assert not (Path(directory) / "raw-envelope.json").exists()
        assert calls == [raw_capture.STATE_URL, raw_capture.GAMES_URL]
    finally:
        raw_capture._fetch, raw_capture._now = original_fetch, original_now


def terminal_raw_capture_retry_check() -> None:
    """Frozen evidence must not depend on mutable post-cutoff source status."""
    original_fetch, original_now = raw_capture._fetch, raw_capture._now
    calls = []

    def fake_fetch(url, destination):
        calls.append(url)
        assert url == raw_capture.STATE_URL, "terminal retry requested schedule or football sources"
        write_json(destination, {"season": "2026", "week": 4, "season_type": "regular"})
        return {"path": destination, "sha256": sha256_file(destination), "source_identity": url, "release_or_etag": "fixture"}

    try:
        raw_capture._fetch = fake_fetch
        for key in ("manifest", "missed"):
            for observed in ("2026-10-01T20:00:00+00:00", "2026-10-02T17:00:00+00:00"):
                raw_capture._now = lambda: observed
                with tempfile.TemporaryDirectory(prefix="fie-m10-raw-terminal-") as directory:
                    root = Path(directory)
                    evidence = root / "evidence"
                    terminal = capture_paths(evidence, 2026, 4)[key]
                    write_json(terminal, {"immutable": True, "fixture": True})
                    before = terminal.read_bytes()
                    calls.clear()
                    assert raw_capture.capture(root / "raw", season=None, week=None, output_root=evidence) is None
                    assert calls == [raw_capture.STATE_URL]
                    assert terminal.read_bytes() == before
                    assert not (root / "raw/raw-envelope.json").exists()
                    # Explicit target arguments must select that target's
                    # terminal evidence rather than the state API's week.
                    target = capture_paths(evidence, 2026, 5)[key]
                    write_json(target, {"immutable": True, "fixture": True})
                    calls.clear()
                    assert raw_capture.capture(root / "override", season=2026, week=5, output_root=evidence) is None
                    assert calls == [raw_capture.STATE_URL]
                    assert not (root / "override/raw-envelope.json").exists()
    finally:
        raw_capture._fetch, raw_capture._now = original_fetch, original_now


def bounded_residual_parity_check() -> None:
    """Match independent scalar replay across chunk boundaries and scoring rules."""
    positions = ("QB", "RB", "WR", "TE")
    models = ("M9", "M10_LINEAR", "M10_HGB")
    rows = [{
        "forecast_id": f"forecast-{index}", "canonical_player_id": f"player-{index}",
        "model": model, "position_model": position,
        "predicted_raw_components": {"receptions": 2.0, "receiving_yards": 99.0, "passing_yards": 299.0, "interceptions": 1.0},
    } for index, (position, model) in enumerate((pos, model) for pos in positions for model in models)]
    lock = {"residual_samples": [{"position_model": pos, "model": model,
        "residuals": {"receptions": offset, "receiving_yards": offset * 3, "passing_yards": offset * 3, "interceptions": offset}}
        for pos in positions for model in models for offset in (-1.0, 0.0, 1.0)]}
    settings = [
        {"rec": 1.0, "rec_yd": 0.1, "pass_yd": 0.04, "pass_int": -2.0},
        {"rec": 0.5, "bonus_rec_te": 1.0, "bonus_rec_rb": 0.2, "rec_yd": 0.1, "bonus_rec_yd_100": 3.0},
        {"pass_yd": 0.04, "bonus_pass_yd_300": 3.0, "pass_int": -3.0},
    ]
    profiles = [{"league_id": f"league-{index:02d}", "league_format": "REDRAFT",
        "profile_scoring_signature": f"score-{index}", "profile_fingerprint": str(index).zfill(64),
        "scoring_settings": settings[index % len(settings)]} for index in range(23)]
    expected = []
    for row in rows:
        for profile in profiles:
            point = {**row["predicted_raw_components"], "position_model": row["position_model"]}
            samples = [{**sample, "position_model": row["position_model"]} for sample in producer._residual_components(lock, row)]
            scalar_scores = [producer._score(sample, profile["scoring_settings"]) for sample in samples]
            scalar_quantiles = {str(q): float(np.quantile(scalar_scores, q)) for q in (0.1, 0.25, 0.5, 0.75, 0.9)}
            expected.append((producer._score(point, profile["scoring_settings"]), scalar_quantiles))
    sizes = []
    original_many = producer._score_many
    def measured_many(items, scoring):
        sizes.append(len(items))
        return original_many(items, scoring)
    try:
        producer._score_many = measured_many
        actual = producer.exact_profile_scoring(rows, profiles, lock, residual_batch_rows=4)
    finally:
        producer._score_many = original_many
    assert len(actual) == len(expected) == 12 * 23
    for index, (record, (point, quantiles)) in enumerate(zip(actual, expected)):
        assert record["scored_fantasy_points"] == point
        assert record["scored_prediction_quantiles"] == quantiles
        assert record["canonical_player_id"] == rows[index // 23]["canonical_player_id"]
        assert record["profile_fingerprint"] == profiles[index % 23]["profile_fingerprint"]
    # The three initial point matrices are small; every subsequent residual
    # matrix stays bounded even though the full test slate has 36 residuals.
    assert sizes[:3] == [len(rows)] * 3
    assert sizes[3:] and max(sizes[3:]) <= 4
    assert len(sizes) == 3 + 12 * 3, sizes
    # A single distribution larger than the configured chunk is kept complete,
    # retaining quantiles rather than truncating or averaging partial quantiles.
    large = producer.exact_profile_scoring(rows[:1], profiles[:1], lock, residual_batch_rows=1)
    assert large[0]["scored_prediction_quantiles"] == expected[0][1]
    for invalid in ([], [{"passing_yards": float("inf")} ]):
        try:
            producer._score_many(invalid, {"pass_yd": 0.04})
        except ValueError:
            pass
        else:
            raise AssertionError("empty or non-finite scoring distribution was accepted")


def operational_capture_validation_check() -> None:
    # Synthetic data exercise the non-fixture validation branch only; no
    # operational evidence is persisted or promoted by this no-network test.
    with tempfile.TemporaryDirectory(prefix="fie-m10-slate-validator-") as directory:
        root = Path(directory)
        create_fixture_capture(root, 2026, 1, "2026-09-09T06:00:00+00:00", "2026-09-10T00:00:00+00:00")
        paths = capture_paths(root, 2026, 1)
        forecasts = read_jsonl_gzip(paths["forecasts"])
        forecasts += [{**row, "forecast_id": "extra-current-player", "canonical_player_id": "extra-current-player"}
                      for row in forecasts if row["position_model"] == "QB"]
        decisions = read_jsonl_gzip(paths["decisions"])
        for row in decisions:
            row.update(status="BLOCKED_INCOMPLETE_LEGAL_ROSTER", blocker="INCOMPLETE_LEGAL_ROSTER_AT_CUTOFF",
                       legal_forecast_ids=[], selected_forecast_ids=[])
        manifest = read_json(paths["manifest"])
        manifest["fixture"] = False

        def save() -> None:
            for ledger, key, rows in (("forecast", "forecasts", forecasts),
                                      ("scoring_replay", "scoring", fixture_scoring_rows(forecasts)),
                                      ("decision_trace", "decisions", decisions)):
                write_jsonl_gzip(paths[key], rows)
                manifest["ledgers"][ledger].update(sha256=sha256_file(paths[key]), rows=len(rows))
            write_json(paths["manifest"], manifest)

        save()
        assert validate_capture(root, 2026, 1, require_fixture=False)["forecast_rows"] == 15
        decisions[0]["blocker"] = "UNAPPROVED_BLOCK"
        save()
        try:
            validate_capture(root, 2026, 1, require_fixture=False)
        except AssertionError:
            pass
        else:
            raise AssertionError("unapproved decision block was accepted")
        decisions[0]["blocker"] = "INCOMPLETE_LEGAL_ROSTER_AT_CUTOFF"
        forecasts[0]["captured_at"] = "2026-09-09T07:00:00+00:00"
        save()
        try:
            validate_capture(root, 2026, 1, require_fixture=False)
        except AssertionError:
            pass
        else:
            raise AssertionError("forecast capture timestamp drift was accepted")


def main() -> None:
    profile_population_checks()
    batch_scoring_checks()
    current_roster_universe_check()
    early_window_source_check()
    terminal_raw_capture_retry_check()
    bounded_residual_parity_check()
    terminal_capture_retry_check()
    operational_capture_validation_check()
    print("PASS M10 current roster universe, dynamic portfolio, bounded residual scoring parity, and terminal retry integrity")


if __name__ == "__main__":
    main()
