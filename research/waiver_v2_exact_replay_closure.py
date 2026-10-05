#!/usr/bin/env python3
"""Publish a fail-closed Waiver-v2 exact-replay closure from one batch run."""
from __future__ import annotations

import argparse
import hashlib
import json
from collections import Counter
from pathlib import Path
from typing import Any


CLOSURE_SCHEMA = "fie-waiver-v2-exact-replay-closure-v1"
POSITIONS = ("QB", "RB", "WR", "TE")


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1 << 20), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _profile_report_path(entry: dict[str, Any], batch_root: Path) -> Path:
    declared = entry.get("outcome_report") or {}
    if declared.get("path"):
        return Path(str(declared["path"]))
    signature = str(entry.get("scoring_signature") or "")
    if not signature:
        raise ValueError("waiver-v2 exact replay closure profile has no scoring signature")
    return batch_root / "profiles" / signature / "offensive-outcome-ledger-report.json"


def build_exact_replay_closure(*, batch_report_path: Path, output_path: Path) -> dict[str, Any]:
    """Summarize all profile blockers without relaxing any exact-replay gate."""
    batch = json.loads(batch_report_path.read_text(encoding="utf-8"))
    if batch.get("schema") != "fie-waiver-v2-profile-batch-v1":
        raise ValueError("waiver-v2 exact replay closure requires a profile-batch-v1 report")
    entries = batch.get("profiles")
    if not isinstance(entries, list) or not entries:
        raise ValueError("waiver-v2 exact replay closure requires one or more profile entries")

    profile_rows: list[dict[str, Any]] = []
    blocker_counts: Counter[tuple[str, str, str, tuple[str, ...], str]] = Counter()
    position_exact_counts: Counter[str] = Counter()
    complete_exact_rows = 0
    incomplete_rows = 0
    all_position_exact_profiles = 0

    for entry in entries:
        report_path = _profile_report_path(entry, batch_report_path.parent)
        if not report_path.exists():
            raise ValueError(f"waiver-v2 exact replay closure missing profile report: {report_path}")
        profile = json.loads(report_path.read_text(encoding="utf-8"))
        signature = str(entry.get("scoring_signature") or "")
        if profile.get("scoring_signature") != signature:
            raise ValueError(f"waiver-v2 exact replay closure signature mismatch: {signature}")
        inventories = profile.get("inventories") or {}
        missing_positions = [position for position in POSITIONS if position not in inventories]
        if missing_positions:
            raise ValueError(f"waiver-v2 exact replay closure profile {signature} lacks inventories: {', '.join(missing_positions)}")
        position_exact = {position: bool(inventories[position].get("exact_replay_eligible")) for position in POSITIONS}
        position_exact_counts.update(position for position, ready in position_exact.items() if ready)
        if all(position_exact.values()):
            all_position_exact_profiles += 1
        blockers_by_position: dict[str, list[dict[str, Any]]] = {}
        for position in POSITIONS:
            blockers = list(inventories[position].get("blocked_keys") or [])
            blockers_by_position[position] = blockers
            for blocker in blockers:
                required = tuple(sorted(str(value) for value in (blocker.get("required_columns") or [])))
                key = (
                    position,
                    str(blocker.get("key") or ""),
                    str(blocker.get("support_status") or ""),
                    required,
                    str(blocker.get("reason") or ""),
                )
                blocker_counts[key] += 1
        coverage = dict(entry.get("coverage") or profile.get("ledger") or {})
        complete_exact_rows += int(coverage.get("complete_exact_rows") or 0)
        incomplete_rows += int(coverage.get("incomplete_rows") or 0)
        profile_rows.append({
            "scoring_signature": signature,
            "league_ids": list(entry.get("league_ids") or []),
            "league_names": list(entry.get("league_names") or []),
            "coverage": coverage,
            "position_exact_replay": position_exact,
            "blockers_by_position": blockers_by_position,
            "outcome_report": {"path": str(report_path), "sha256": _sha256(report_path)},
        })

    rollup = [
        {
            "position": position,
            "rule": rule,
            "support_status": status,
            "required_columns": list(required),
            "profiles_blocked": count,
            "reason": reason,
        }
        for (position, rule, status, required, reason), count in blocker_counts.items()
    ]
    rollup.sort(key=lambda row: (-row["profiles_blocked"], row["position"], row["rule"], row["support_status"]))
    event_receipt = (batch.get("shared_source_run") or {}).get("event_ledger_receipt") or {}
    report = {
        "schema": CLOSURE_SCHEMA,
        "diagnostic_only": True,
        "activation_eligible": False,
        "batch_report": {"path": str(batch_report_path), "sha256": _sha256(batch_report_path)},
        "event_rule_support": event_receipt.get("rule_support") or {},
        "summary": {
            "profile_count": len(profile_rows),
            "league_count": int(batch.get("league_count") or 0),
            "all_positions_exact_profile_count": all_position_exact_profiles,
            "position_exact_profile_counts": {position: int(position_exact_counts[position]) for position in POSITIONS},
            "complete_exact_rows": complete_exact_rows,
            "incomplete_rows": incomplete_rows,
            "blocker_rollup": rollup,
        },
        "profiles": profile_rows,
        "limitations": [
            "A blocked exact-scoring rule leaves every affected player-week incomplete; the closure never substitutes zero or an estimate.",
            "This closure is historical research evidence only and cannot activate M5, app rankings, recommendations, or transactions.",
        ],
    }
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8", newline="\n")
    return report


def main(argv: list[str] | None = None) -> None:
    parser = argparse.ArgumentParser(description="Publish a Waiver-v2 exact-replay closure report")
    parser.add_argument("--batch-report", required=True)
    parser.add_argument("--output", required=True)
    args = parser.parse_args(argv)
    report = build_exact_replay_closure(batch_report_path=Path(args.batch_report), output_path=Path(args.output))
    print(json.dumps(report["summary"], indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
