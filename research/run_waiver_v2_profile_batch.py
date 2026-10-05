#!/usr/bin/env python3
"""Run Waiver-v2 historical ledger diagnostics once per active scoring profile."""
from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

from build_waiver_v2_outcome_ledger import build as build_ledger, scoring_signature
from run_waiver_v2_historical_ledger import _parse_seasons, run as run_historical
from waiver_v2_exact_replay_closure import CLOSURE_SCHEMA, build_exact_replay_closure


BATCH_SCHEMA = "fie-waiver-v2-profile-batch-v1"


def load_profile_groups(profiles_root: Path, portfolio_overview: Path | None = None) -> list[dict[str, Any]]:
    """Read active league profiles and group exact-equivalent scoring settings."""
    active_ids: set[str] | None = None
    if portfolio_overview is not None:
        overview = json.loads(portfolio_overview.read_text(encoding="utf-8"))
        active_ids = {str(row["league_id"]) for row in overview.get("leagues") or [] if row.get("league_id")}
        if not active_ids:
            raise ValueError("waiver-v2 profile batch portfolio overview has no active league ids")
    grouped: dict[str, dict[str, Any]] = {}
    for path in sorted(profiles_root.glob("*/profile.json")):
        profile = json.loads(path.read_text(encoding="utf-8"))
        league_id = str(profile.get("league_id") or path.parent.name)
        if active_ids is not None and league_id not in active_ids:
            continue
        settings = profile.get("scoring_settings")
        if not isinstance(settings, dict):
            raise ValueError(f"waiver-v2 profile {league_id} has no scoring_settings object")
        signature = scoring_signature(settings)
        declared = str(profile.get("scoring_signature") or "")
        if declared and declared != signature:
            raise ValueError(f"waiver-v2 profile {league_id} scoring signature does not match its scoring settings")
        group = grouped.setdefault(signature, {"scoring_signature": signature, "scoring_path": path, "league_ids": [], "league_names": []})
        group["league_ids"].append(league_id)
        group["league_names"].append(str(profile.get("league_name") or league_id))
    if not grouped:
        raise ValueError("waiver-v2 profile batch found no active league profiles")
    return [
        {**group, "league_ids": sorted(group["league_ids"]), "league_names": sorted(group["league_names"])}
        for _, group in sorted(grouped.items())
    ]


def run_batch(
    *, seasons: list[int], cache_dir: Path, profiles_root: Path, portfolio_overview: Path | None,
    output_dir: Path, player_stats_complete: bool, event_evidence: bool = True, participation_evidence: bool = False,
) -> dict[str, Any]:
    groups = load_profile_groups(profiles_root, portfolio_overview)
    # Build/cache raw history only once. The first profile's ledger is retained
    # as source-run provenance; every profile gets its own ledger below.
    shared = run_historical(
        seasons=seasons, cache_dir=cache_dir, scoring_path=Path(groups[0]["scoring_path"]),
        output_dir=output_dir / "shared-source", player_stats_complete=player_stats_complete,
        event_evidence=event_evidence, participation_evidence=participation_evidence,
    )
    adapted = shared["adapter_receipt"]["outputs"]
    event_receipt = shared.get("event_ledger_receipt") or {}
    entries = []
    for group in groups:
        signature = group["scoring_signature"]
        profile_dir = output_dir / "profiles" / signature
        receipt = build_ledger(
            player_stats_path=Path(adapted["player_stats"]["path"]),
            weekly_roster_path=Path(adapted["weekly_roster"]["path"]),
            team_schedule_path=Path(adapted["team_schedule"]["path"]),
            scoring_path=Path(group["scoring_path"]),
            output_path=profile_dir / "offensive-outcome-ledger.csv.gz",
            report_path=profile_dir / "offensive-outcome-ledger-report.json",
            player_stats_complete=player_stats_complete,
            event_weekly_stats_path=(Path(event_receipt["event_weekly_stats"]["path"]) if event_receipt else None),
            event_rule_support=(event_receipt.get("rule_support") if event_receipt else None),
        )
        entries.append({
            "scoring_signature": signature,
            "league_ids": group["league_ids"],
            "league_names": group["league_names"],
            "scoring_profile_path": str(group["scoring_path"]),
            "coverage": receipt["ledger"],
            "position_exact_replay": {position: bool(value["exact_replay_eligible"]) for position, value in receipt["inventories"].items()},
            "outcome_report": {"path": str(profile_dir / "offensive-outcome-ledger-report.json")},
        })
    batch_report_path = output_dir / "profile-batch-report.json"
    closure_path = output_dir / "exact-replay-closure.json"
    report = {
        "schema": BATCH_SCHEMA,
        "diagnostic_only": True,
        "activation_eligible": False,
        "requested_seasons": seasons,
        "profile_count": len(entries),
        "league_count": sum(len(entry["league_ids"]) for entry in entries),
        "shared_source_run": shared,
        "profiles": entries,
        "exact_replay_closure": {"schema": CLOSURE_SCHEMA, "path": str(closure_path)},
        "limitations": [
            "Each signature is isolated; a coverage result for one profile cannot activate another profile.",
            "This batch produces only historical research diagnostics and cannot alter M5, app rankings, recommendations, or transactions.",
        ],
    }
    output_dir.mkdir(parents=True, exist_ok=True)
    batch_report_path.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8", newline="\n")
    build_exact_replay_closure(batch_report_path=batch_report_path, output_path=closure_path)
    return report


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Build research-only Waiver-v2 ledgers for active scoring profiles")
    parser.add_argument("--seasons", default="2019-2025")
    parser.add_argument("--cache-dir", default=".cache/fie-waiver-v2")
    parser.add_argument("--profiles-root", default="data/research/leagues")
    parser.add_argument("--portfolio-overview", default="data/research/portfolio/2026/research-overview.json")
    parser.add_argument("--output-dir", required=True)
    parser.add_argument("--player-stats-complete", action="store_true")
    parser.add_argument("--without-event-evidence", action="store_true")
    parser.add_argument("--with-participation", action="store_true")
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> None:
    args = parse_args(argv)
    overview = Path(args.portfolio_overview) if args.portfolio_overview else None
    report = run_batch(
        seasons=_parse_seasons(args.seasons), cache_dir=Path(args.cache_dir), profiles_root=Path(args.profiles_root),
        portfolio_overview=overview, output_dir=Path(args.output_dir), player_stats_complete=bool(args.player_stats_complete),
        event_evidence=not bool(args.without_event_evidence), participation_evidence=bool(args.with_participation),
    )
    print(json.dumps({"schema": BATCH_SCHEMA, "profiles": report["profile_count"], "leagues": report["league_count"], "activation_eligible": False}, indent=2))


if __name__ == "__main__":
    main()
