#!/usr/bin/env python3
"""Focused validator for Window 1A immutable evidence artifacts."""
from __future__ import annotations

import argparse
import json
from pathlib import Path

from fie_research_pipeline_contract import ROOT
from freeze_fie_2026_baseline import validate_baseline
from point_in_time_capture import validate_envelope


def load(path: Path):
    return json.loads(path.read_text(encoding="utf-8"))


def validate_waivers(root: Path) -> int:
    envelopes = sorted(root.glob("2026/week_*/*/*/source-envelope.json"))
    if not envelopes:
        raise AssertionError(f"no waiver source envelopes under {root}")
    for path in envelopes:
        value = load(path); validate_envelope(value)
        assert value["capture_intent"] == "WAIVER_TRANSACTION"
        week = int(path.parts[-4].split("_")[-1])
        normalized = path.with_name("normalized-transactions.json")
        if week >= 1:
            assert normalized.is_file()
            for row in load(normalized):
                assert row["schema_version"] == "fie-waiver-transaction-evidence-v1"
                assert row["week"] == week and row["raw_payload_sha256"] == value["payload_sha256"]
                assert row["transaction"]["waiver_bid"] is None or row["transaction"]["waiver_bid"] >= 0
            cycle = load(path.with_name("cycle-state.json"))
            assert cycle["schema_version"] == "fie-waiver-cycle-state-v1"
            assert cycle["visibility_status"] != "COMPLETE_ENOUGH_FOR_BID_MODEL"
            behavior = load(path.with_name("behavior-features.json"))
            assert behavior["schema_version"] == "fie-waiver-behavior-features-v1"
    return len(envelopes)


def validate_weather(root: Path) -> int:
    contexts = sorted(root.glob("2026/week_*/*/context-evidence.json"))
    if not contexts:
        raise AssertionError(f"no weather context evidence under {root}")
    for path in contexts:
        value = load(path)
        assert value["schema_version"] == "fie-context-evidence-v1"
        for game in value["games"]:
            env = game["environment"]
            if env.get("forecast_observed_at"):
                assert env.get("forecast_run_at") is not None or env.get("forecast_run_metadata_status") == "NOT_EXPOSED_BY_PROVIDER"
    return len(contexts)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--kind", choices=("waiver", "weather", "baseline", "all"), default="all")
    parser.add_argument("--root")
    args = parser.parse_args(argv)
    count = 0
    if args.kind in {"waiver", "all"}:
        count += validate_waivers(Path(args.root) if args.root else ROOT / "data/research/waivers/sleeper")
    if args.kind in {"weather", "all"}:
        count += validate_weather(Path(args.root) if args.root else ROOT / "data/research/context/weather")
    if args.kind in {"baseline", "all"}:
        path = Path(args.root) if args.root else ROOT / "data/research/baselines/2026/baseline-v1.json"
        validate_baseline(load(path), ROOT); count += 1
    print(f"PASS Window 1A evidence kind={args.kind} artifacts={count}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
