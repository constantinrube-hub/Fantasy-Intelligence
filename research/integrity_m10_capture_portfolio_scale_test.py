#!/usr/bin/env python3
"""Regression checks for portfolio-scaled, bounded M10 weekly capture."""
from __future__ import annotations

import shutil
import tempfile
from pathlib import Path

import m10_prospective_weekly_producer as producer
from m10_prospective_capture_contract import capture_paths, write_json
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


def main() -> None:
    profile_population_checks()
    batch_scoring_checks()
    terminal_capture_retry_check()
    print("PASS M10 dynamic portfolio, batched scoring, and terminal retry integrity")


if __name__ == "__main__":
    main()
