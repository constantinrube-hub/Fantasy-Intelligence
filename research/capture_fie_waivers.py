#!/usr/bin/env python3
"""Capture immutable Sleeper waiver evidence without changing production decisions."""
from __future__ import annotations

import argparse
import json
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any
from urllib.request import Request, urlopen

from fie_research_pipeline_contract import ROOT
from point_in_time_capture import (
    build_envelope,
    canonical_bytes,
    compact_timestamp,
    first_write_json,
    sha256_bytes,
    utc_now,
    validate_envelope,
)


BASE = "https://api.sleeper.app/v1"
UA = "Fantasy-Intelligence-Waiver-Evidence/1.0"
EVIDENCE_SCHEMA = "fie-waiver-transaction-evidence-v1"
CYCLE_SCHEMA = "fie-waiver-cycle-state-v1"
BEHAVIOR_SCHEMA = "fie-waiver-behavior-features-v1"
AUDIT_SCHEMA = "fie-sleeper-waiver-payload-visibility-audit-v1"


def fetch_json(url: str) -> Any:
    request = Request(url, headers={"User-Agent": UA, "Accept": "application/json"})
    with urlopen(request, timeout=30) as response:
        if response.status != 200:
            raise RuntimeError(f"HTTP {response.status}: {url}")
        return json.loads(response.read().decode("utf-8"))


def safe_fetch_json(url: str) -> tuple[Any | None, str | None]:
    try:
        return fetch_json(url), None
    except Exception as error:
        return None, f"{type(error).__name__}: {error}"


def enabled_leagues(registry_path: Path) -> dict[str, dict[str, Any]]:
    raw = json.loads(registry_path.read_text(encoding="utf-8"))
    leagues = {
        str(league_id): value
        for league_id, value in (raw.get("leagues") or {}).items()
        if value.get("enabled") is True
    }
    if len(leagues) != 22:
        raise ValueError(f"expected 22 enabled leagues, found {len(leagues)}")
    if len({value.get("format") for value in leagues.values()}) != 6:
        raise ValueError("all six league formats must remain represented")
    return leagues


def failure_reason(raw: dict[str, Any]) -> str | None:
    metadata = raw.get("metadata") or {}
    for key in ("notes", "reason", "message"):
        value = metadata.get(key)
        if value is not None and str(value).strip():
            return str(value)
    return None


def observation_type(raw: dict[str, Any]) -> str:
    kind, status = str(raw.get("type") or "").lower(), str(raw.get("status") or "").lower()
    if kind == "waiver" and status == "complete":
        return "COMPLETED_WAIVER"
    if kind == "waiver" and status in {"failed", "rejected"}:
        return "FAILED_OR_REJECTED_WAIVER"
    if kind == "free_agent" and status == "complete":
        return "FREE_AGENT_ADD"
    if raw:
        return "OBSERVED_OTHER_TRANSACTION"
    return "SOURCE_MISSING"


def visibility_for_payload(transactions: list[dict[str, Any]]) -> tuple[str, str]:
    waivers = [row for row in transactions if str(row.get("type") or "").lower() == "waiver"]
    failed = [row for row in waivers if str(row.get("status") or "").lower() in {"failed", "rejected"}]
    if failed:
        return (
            "PARTIAL_OBSERVED",
            "Sleeper exposed at least one failed/rejected claim; the endpoint does not guarantee a complete private bid book.",
        )
    if waivers:
        return (
            "WINNER_ONLY_OBSERVED",
            "Only completed waiver claims were observed in this payload; absent losing claims are unknown.",
        )
    return "UNKNOWN", "No waiver claims were returned for this league/week observation."


def normalize_transactions(
    transactions: list[dict[str, Any]], *, league_id: str, week: int, fetched_at: str, raw_sha256: str
) -> list[dict[str, Any]]:
    visibility, reason = visibility_for_payload(transactions)
    by_id: dict[str, dict[str, Any]] = {}
    for raw in transactions:
        transaction_id = str(raw.get("transaction_id") or "").strip()
        if not transaction_id:
            continue
        prior = by_id.get(transaction_id)
        if prior is None or int(raw.get("status_updated") or raw.get("created") or 0) >= int(prior.get("status_updated") or prior.get("created") or 0):
            by_id[transaction_id] = raw
    rows = []
    for raw in sorted(by_id.values(), key=lambda row: (int(row.get("created") or 0), str(row.get("transaction_id") or ""))):
        transaction_id = str(raw.get("transaction_id") or "").strip()
        if not transaction_id:
            continue
        settings = raw.get("settings") or {}
        bid = settings.get("waiver_bid")
        priority = settings.get("waiver_position")
        kind = observation_type(raw)
        row_visibility = "NOT_APPLICABLE" if kind == "FREE_AGENT_ADD" else visibility
        rows.append({
            "schema_version": EVIDENCE_SCHEMA,
            "source_observation_type": kind,
            "league_id": str(league_id),
            "week": int(week),
            "fetched_at": fetched_at,
            "raw_payload_sha256": raw_sha256,
            "transaction": {
                "transaction_id": transaction_id,
                "status": raw.get("status"),
                "type": raw.get("type"),
                "created": raw.get("created"),
                "status_updated": raw.get("status_updated"),
                "creator": str(raw.get("creator")) if raw.get("creator") is not None else None,
                "roster_ids": list(raw.get("roster_ids") or []),
                "adds": raw.get("adds"),
                "drops": raw.get("drops"),
                "waiver_bid": float(bid) if isinstance(bid, (int, float)) and bid >= 0 else None,
                "waiver_priority": float(priority) if isinstance(priority, (int, float)) and priority >= 0 else None,
                "failure_reason": failure_reason(raw),
            },
            "visibility": {"losing_claim_visibility": row_visibility, "reason": reason},
        })
    return rows


def observed_bid_book_summary(bids: list[float], *, source_complete: bool) -> dict[str, Any]:
    ordered = sorted((float(value) for value in bids if value >= 0), reverse=True)
    winner = ordered[0] if ordered else None
    second = ordered[1] if source_complete and len(ordered) >= 2 else None
    return {
        "winning_bid": winner,
        "second_highest_observed_bid": second,
        "over_second": winner - second if winner is not None and second is not None else None,
        "complete_observed_bid_book": bool(source_complete),
    }


def cycle_visibility(transactions: list[dict[str, Any]]) -> str:
    visibility, _ = visibility_for_payload(transactions)
    if visibility == "PARTIAL_OBSERVED":
        return "PARTIAL_BEHAVIOR_ONLY"
    if visibility == "WINNER_ONLY_OBSERVED":
        return "INSUFFICIENT_BID_VISIBILITY"
    return "INSUFFICIENT_BID_VISIBILITY"


def cycle_state(
    *,
    league_id: str,
    season: int,
    week: int,
    observed_at: str,
    profile: dict[str, Any],
    rosters: list[dict[str, Any]],
    player_ids: set[str],
    transactions: list[dict[str, Any]],
    source_available: bool = True,
) -> dict[str, Any]:
    budget = profile.get("settings", {}).get("waiver_budget")
    rostered = {
        str(player_id)
        for roster in rosters
        for key in ("players", "reserve", "taxi")
        for player_id in (roster.get(key) or [])
    }
    teams = []
    for roster in sorted(rosters, key=lambda row: int(row.get("roster_id") or 0)):
        settings = roster.get("settings") or {}
        used = settings.get("waiver_budget_used")
        observed_spend = sum(
            float((row.get("settings") or {}).get("waiver_bid"))
            for row in transactions
            if str(row.get("type") or "").lower() == "waiver"
            and str(row.get("status") or "").lower() == "complete"
            and roster.get("roster_id") in (row.get("roster_ids") or [])
            and isinstance((row.get("settings") or {}).get("waiver_bid"), (int, float))
        )
        remaining = None
        if isinstance(budget, (int, float)) and isinstance(used, (int, float)):
            remaining = max(0, float(budget) - float(used))
        teams.append({
            "roster_id": roster.get("roster_id"),
            "faab_remaining": remaining,
            "waiver_priority": settings.get("waiver_position") if isinstance(settings.get("waiver_position"), (int, float)) else None,
            "faab_used_source": float(used) if isinstance(used, (int, float)) else None,
            "observed_completed_waiver_spend": observed_spend,
            "faab_reconciliation": "MATCH" if isinstance(used, (int, float)) and float(used) == observed_spend else "GAP_OR_DIFFERENT_HISTORY_SCOPE",
        })
    released = sorted({str(pid) for row in transactions for pid in (row.get("drops") or {})})
    return {
        "schema_version": CYCLE_SCHEMA,
        "league_id": str(league_id),
        "season": int(season),
        "week": int(week),
        "cutoff": observed_at,
        "teams": teams,
        "available_player_ids": sorted(player_ids - rostered),
        "released_player_ids": released,
        "remaining_chopped_teams": None,
        "visibility_status": cycle_visibility(transactions) if source_available else "SOURCE_UNAVAILABLE",
    }


def behavior_features(
    normalized: list[dict[str, Any]], *, league_id: str, as_of: str, budget: float | None, player_positions: dict[str, str]
) -> dict[str, Any]:
    claims: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for row in normalized:
        tx = row["transaction"]
        if str(tx.get("type") or "").lower() != "waiver" or not tx.get("creator"):
            continue
        claims[str(tx["creator"])].append(row)
    managers = []
    for manager_id, rows in sorted(claims.items()):
        bids = [float(row["transaction"]["waiver_bid"]) for row in rows if row["transaction"].get("waiver_bid") is not None]
        positions = Counter()
        for row in rows:
            for player_id in (row["transaction"].get("adds") or {}):
                position = player_positions.get(str(player_id))
                if position:
                    positions[position] += 1
        sample = len(rows)
        endings = Counter(int(bid) % 10 for bid in bids if float(bid).is_integer())
        managers.append({
            "manager_id": manager_id,
            "sample_size": sample,
            "reliability": "PERSONALIZED" if sample >= 8 else "LEAGUE_FALLBACK",
            "participation_rate": None,
            "spend_fraction_mean": (sum(bids) / len(bids) / float(budget)) if bids and budget else None,
            "position_tendencies": {key: round(value / sum(positions.values()), 6) for key, value in sorted(positions.items())} if positions else {},
            "rounding_profile": {"integer_bid_count": sum(endings.values()), "last_digit_counts": {str(k): v for k, v in sorted(endings.items())}} if bids else None,
            "evidence_scope": "SOURCE_OBSERVED_CLAIMS_ONLY",
        })
    return {"schema_version": BEHAVIOR_SCHEMA, "league_id": str(league_id), "as_of": as_of, "managers": managers}


def fixture_payload() -> tuple[dict[str, Any], list[dict[str, Any]], dict[str, Any]]:
    profile = {"settings": {"waiver_budget": 100}, "format": "REDRAFT"}
    rosters = [
        {"roster_id": 1, "players": ["old"], "settings": {"waiver_budget_used": 41, "waiver_position": 3}},
        {"roster_id": 2, "players": [], "settings": {"waiver_budget_used": 27, "waiver_position": 1}},
    ]
    transactions = [
        {"transaction_id": "tx_win", "type": "waiver", "status": "complete", "creator": "m1", "roster_ids": [1], "adds": {"rb": 1}, "drops": {"old": 1}, "settings": {"waiver_bid": 41}, "created": 1, "status_updated": 3, "metadata": {}},
        {"transaction_id": "tx_fail", "type": "waiver", "status": "failed", "creator": "m2", "roster_ids": [2], "adds": {"rb": 2}, "drops": None, "settings": {"waiver_bid": 27}, "created": 2, "status_updated": 3, "metadata": {"notes": "This player was claimed by another owner."}},
        {"transaction_id": "tx_fa", "type": "free_agent", "status": "complete", "creator": "m1", "roster_ids": [1], "adds": {"te": 1}, "drops": None, "settings": {}, "created": 4, "status_updated": 4, "metadata": {}},
    ]
    return profile, rosters, {"transactions": transactions, "league": {"league_id": "123456789012345678"}, "rosters": rosters}


def stored_visibility_audit(
    *, output_root: Path, season: int, weeks: list[int], registry: dict[str, dict[str, Any]]
) -> dict[str, Any]:
    audit_rows, observed_values = [], []
    for league_id, entry in sorted(registry.items()):
        for week in weeks:
            candidates = sorted((output_root / str(season) / f"week_{week:02d}" / league_id).glob("*/source-envelope.json"))
            if not candidates:
                audit_rows.append({
                    "league_id": league_id, "league_format": entry.get("format"), "requested_week": week,
                    "transaction_count": 0, "transaction_status_counts": {}, "losing_claim_visibility": "UNKNOWN",
                    "visibility_reason": "No source observation has been captured.", "source_status": "SOURCE_UNAVAILABLE",
                    "source_errors": ["NO_CAPTURED_SOURCE_ENVELOPE"], "source_envelope_sha256": None,
                })
                continue
            envelope = json.loads(candidates[-1].read_text(encoding="utf-8")); validate_envelope(envelope)
            observed_values.append(envelope["observed_at"])
            payload = envelope.get("payload") or {}; transactions = payload.get("transactions")
            errors = list(payload.get("source_errors") or [])
            available = isinstance(transactions, list)
            rows = transactions if available else []
            visibility, reason = visibility_for_payload(rows)
            if not available:
                visibility, reason = "UNKNOWN", "Sleeper transaction response was unavailable; no absence inference is permitted."
            kinds = Counter(f"{row.get('type')}/{row.get('status')}" for row in rows)
            audit_rows.append({
                "league_id": league_id, "league_format": entry.get("format"), "requested_week": week,
                "transaction_count": len(rows), "transaction_status_counts": dict(sorted(kinds.items())),
                "losing_claim_visibility": visibility, "visibility_reason": reason,
                "source_status": "OBSERVED" if available else "SOURCE_UNAVAILABLE", "source_errors": errors,
                "source_envelope_sha256": sha256_bytes(canonical_bytes(envelope)),
            })
    observed_at = max(observed_values) if observed_values else utc_now()
    return {
        "schema_version": AUDIT_SCHEMA, "season": season, "observed_at": observed_at,
        "enabled_league_count": len(registry), "requested_weeks": weeks,
        "source_completeness_claim": "ENDPOINT_RESPONSE_COMPLETE_ONLY_PRIVATE_BID_BOOK_NOT_GUARANTEED",
        "production_behavior_changed": False, "bid_probability_or_optimization": False, "leagues": audit_rows,
    }


def capture(
    *, output_root: Path, season: int, weeks: list[int], fixture: bool = False,
    league_scope: set[str] | None = None,
) -> dict[str, Any]:
    observed_at = "2026-09-06T09:00:00+00:00" if fixture else utc_now()
    all_registry = enabled_leagues(ROOT / "data/research/leagues/registry.json") if not fixture else {
        "123456789012345678": {"format": "REDRAFT", "profile_path": "fixture"}
    }
    registry = {key: value for key, value in all_registry.items() if league_scope is None or key in league_scope}
    if not registry:
        raise ValueError("league scope selected no enabled leagues")
    catalog_path = ROOT / "data/research/app/player-catalog.json"
    catalog = json.loads(catalog_path.read_text(encoding="utf-8")) if catalog_path.exists() else {"players": {}}
    player_positions = {str(pid): str(row.get("position") or "") for pid, row in (catalog.get("players") or {}).items()}
    player_ids = set(player_positions)
    audit_rows = []
    for league_id, entry in sorted(registry.items()):
        if fixture:
            profile, rosters, payload = fixture_payload()
            league, league_error, roster_error = payload["league"], None, None
        else:
            profile = json.loads((ROOT / str(entry["profile_path"])).read_text(encoding="utf-8"))
            league, league_error = safe_fetch_json(f"{BASE}/league/{league_id}")
            rosters, roster_error = safe_fetch_json(f"{BASE}/league/{league_id}/rosters")
            rosters = rosters if isinstance(rosters, list) else []
        for week in weeks:
            if fixture:
                transactions = payload["transactions"]
                combined = payload
                transaction_error = None
            else:
                transactions, transaction_error = safe_fetch_json(f"{BASE}/league/{league_id}/transactions/{week}")
                source_errors = [value for value in (league_error, roster_error, transaction_error) if value]
                combined = {"transactions": transactions, "league": league, "rosters": rosters, "source_errors": source_errors}
            if transactions is not None and not isinstance(transactions, list):
                raise ValueError(f"invalid Sleeper transaction payload for {league_id} week {week}")
            observed_transactions = transactions if isinstance(transactions, list) else []
            envelope = build_envelope(
                capture_id=f"sleeper-waiver-{season}-{week:02d}-{league_id}-{compact_timestamp(observed_at)}",
                capture_intent="WAIVER_TRANSACTION",
                provider="Sleeper",
                endpoint=f"{BASE}/league/{league_id}/transactions/{week} + league + rosters",
                observed_at=observed_at,
                as_of_semantics="Exact provider responses observed at observed_at; absent transactions or claims are not inferred.",
                payload=combined,
                revision_metadata_status="NOT_EXPOSED_BY_PROVIDER",
            )
            validate_envelope(envelope)
            capture_dir = output_root / str(season) / f"week_{week:02d}" / league_id / compact_timestamp(observed_at)
            first_write_json(capture_dir / "source-envelope.json", envelope)
            visibility, reason = visibility_for_payload(observed_transactions)
            if transaction_error:
                visibility, reason = "UNKNOWN", "Sleeper transaction response unavailable; no absence inference is permitted."
            kinds = Counter(f"{row.get('type')}/{row.get('status')}" for row in observed_transactions)
            audit_rows.append({
                "league_id": league_id, "league_format": entry.get("format"), "requested_week": week,
                "transaction_count": len(transactions), "transaction_status_counts": dict(sorted(kinds.items())),
                "losing_claim_visibility": visibility, "visibility_reason": reason,
                "source_status": "SOURCE_UNAVAILABLE" if transaction_error else "OBSERVED",
                "source_errors": list(combined.get("source_errors") or []),
                "source_envelope_sha256": sha256_bytes(canonical_bytes(envelope)),
            })
            if week < 1:
                continue
            normalized = normalize_transactions(
                observed_transactions, league_id=league_id, week=week, fetched_at=observed_at,
                raw_sha256=envelope["payload_sha256"],
            )
            first_write_json(capture_dir / "normalized-transactions.json", normalized)
            first_write_json(capture_dir / "cycle-state.json", cycle_state(
                league_id=league_id, season=season, week=week, observed_at=observed_at,
                profile=profile, rosters=rosters, player_ids=player_ids, transactions=observed_transactions,
                source_available=transaction_error is None and roster_error is None,
            ))
            budget = profile.get("settings", {}).get("waiver_budget")
            first_write_json(capture_dir / "behavior-features.json", behavior_features(
                normalized, league_id=league_id, as_of=observed_at,
                budget=float(budget) if isinstance(budget, (int, float)) and budget > 0 else None,
                player_positions=player_positions,
            ))
    audit = {
        "schema_version": AUDIT_SCHEMA,
        "season": season,
        "observed_at": observed_at,
        "enabled_league_count": len(registry),
        "requested_weeks": weeks,
        "source_completeness_claim": "ENDPOINT_RESPONSE_COMPLETE_ONLY_PRIVATE_BID_BOOK_NOT_GUARANTEED",
        "production_behavior_changed": False,
        "bid_probability_or_optimization": False,
        "leagues": audit_rows,
    }
    if not fixture:
        audit = stored_visibility_audit(output_root=output_root, season=season, weeks=weeks, registry=all_registry)
    first_write_json(output_root / str(season) / "visibility-audits" / f"audit_{compact_timestamp(observed_at)}.json", audit)
    return audit


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output-root", default="data/research/waivers/sleeper")
    parser.add_argument("--season", type=int, default=2026)
    parser.add_argument("--weeks", default="", help="Comma-separated Sleeper rounds; defaults to current state week")
    parser.add_argument("--fixture", action="store_true")
    parser.add_argument("--league-scope", default="", help="Optional comma-separated enabled league IDs")
    args = parser.parse_args(argv)
    output_root = Path(args.output_root)
    if not output_root.is_absolute():
        output_root = ROOT / output_root
    if args.weeks:
        weeks = sorted({int(value) for value in args.weeks.split(",") if value.strip()})
    elif args.fixture:
        weeks = [1]
    else:
        state = fetch_json(f"{BASE}/state/nfl")
        if str(state.get("season_type") or "").lower() not in {"regular", "reg", "pre"}:
            print("NO_WRITE_OUTSIDE_NFL_CAPTURE_SEASON")
            return 0
        args.season = int(state.get("season") or args.season)
        weeks = [max(1, int(state.get("week") or 1))]
    scope = {value.strip() for value in args.league_scope.split(",") if value.strip()} or None
    audit = capture(output_root=output_root, season=args.season, weeks=weeks, fixture=args.fixture, league_scope=scope)
    print(f"PASS waiver evidence leagues={audit['enabled_league_count']} observations={len(audit['leagues'])}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
