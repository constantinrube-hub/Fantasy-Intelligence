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
            expected.append((producer._score(point, profile["scoring_settings"]),
                producer._quantiles([producer._score(sample, profile["scoring_settings"]) for sample in samples])))
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


def main() -> None:
    profile_population_checks()
    batch_scoring_checks()
    bounded_residual_parity_check()
    terminal_capture_retry_check()
    print("PASS M10 dynamic portfolio, bounded residual scoring parity, and terminal retry integrity")


if __name__ == "__main__":
    main()
