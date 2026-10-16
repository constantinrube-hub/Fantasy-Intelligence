#!/usr/bin/env python3
"""Reconcile observed transaction revisions without inventing private claims."""
from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path
from typing import Any
from zoneinfo import ZoneInfo

from point_in_time_capture import canonical_bytes, parse_time, sha256_bytes, validate_envelope

SCHEMA = "fie-waiver-reconciliation-v1"
BERLIN = ZoneInfo("Europe/Berlin")


def automatic_capture_allowed(as_of: datetime) -> bool:
    """September–December plus Jan 1–11; January polls enforce daily capture.

    January cron has only a day-of-month restriction, avoiding cron's OR
    interaction between restricted day-of-month and day-of-week fields.
    Fri–Mon runs in the 08:00–11:59 Berlin window; Tue–Thu uses every poll.
    The window allows a queued 08:17 run to arrive late. This is not a guarantee
    of exact execution time, or a post-draft preseason activation policy.
    """
    if as_of.tzinfo is None:
        raise ValueError("CAPTURE_TIMEZONE_MISSING")
    local = as_of.astimezone(BERLIN)
    if local.month in {9, 10, 11, 12}:
        return True
    return bool(local.month == 1 and local.day <= 11
                and (local.weekday() in {1, 2, 3} or 8 <= local.hour < 12))


def rolling_rounds(state: dict[str, Any], lookback: int = 2) -> list[int]:
    if not 0 <= lookback <= 18:
        raise ValueError("ROUND_LOOKBACK_OUT_OF_RANGE")
    season_type = str(state.get("season_type") or "").lower()
    if season_type in {"pre", "preseason"}:
        return [0]
    if season_type not in {"regular", "reg"}:
        raise ValueError("STATE_OUTSIDE_CAPTURE_SEASON")
    value = state.get("week")
    if isinstance(value, bool) or value is None or str(value) != str(int(value)):
        raise ValueError("STATE_TRANSACTION_ROUND_INVALID")
    current = int(value)
    if not 1 <= current <= 18:
        raise ValueError("STATE_TRANSACTION_ROUND_OUT_OF_RANGE")
    return list(range(max(0, current - lookback), current + 1))


def automatic_capture_due(output_root: Path, as_of: datetime, enabled_count: int) -> bool:
    if not automatic_capture_allowed(as_of):
        return False
    local = as_of.astimezone(BERLIN)
    if local.weekday() in {1, 2, 3}:
        return True
    # Serialized jobs check the newest main checkout. An automatic daily
    # portfolio observation suppresses delayed/duplicate polls, regardless of
    # whether a response was partial; the next day's lookback can recover it.
    for path in output_root.glob("*/visibility-audits/audit_*.json"):
        audit = json.loads(path.read_text(encoding="utf-8"))
        if (audit.get("capture_mode") == "AUTOMATIC"
                and audit.get("capture_schedule_date") == local.date().isoformat()
                and audit.get("captured_league_count") == enabled_count):
            return False
    return True


def reconcile(output_root: Path, season: int, league_id: str, cutoff: str) -> dict[str, Any]:
    # Local import avoids a cycle while using the existing normalizer's semantics.
    from capture_fie_waivers import normalize_transactions, deduplicate_transactions

    records: dict[str, dict[str, Any]] = {}
    latest_rounds: dict[int, dict[str, Any]] = {}
    skipped_without_id = 0
    failure_count = 0
    candidates = []
    for path in (output_root / str(season)).glob(f"week_*/{league_id}/*/source-envelope.json"):
        env = json.loads(path.read_text(encoding="utf-8"))
        validate_envelope(env)
        if parse_time(env["observed_at"]) <= parse_time(cutoff):
            candidates.append((parse_time(env["observed_at"]), path, env))
    for _, path, env in sorted(candidates, key=lambda x: (x[0], x[1].as_posix())):
        if env["capture_intent"] != "WAIVER_TRANSACTION":
            raise ValueError(f"RECONCILIATION_WRONG_CAPTURE_INTENT:{path}")
        week = int(path.parts[-4].split("_")[-1])
        payload = env.get("payload") or {}
        league = payload.get("league")
        live_id = str(league.get("league_id") or "") if isinstance(league, dict) else ""
        if live_id and live_id != str(league_id):
            raise ValueError(f"RECONCILIATION_LEAGUE_ID_MISMATCH:{path}")
        transactions = payload.get("transactions")
        available = isinstance(transactions, list) and all(isinstance(row, dict) for row in transactions)
        errors = list(payload.get("source_errors") or [])
        failure_count += int(not available or bool(errors))
        reference = {"source_envelope": path.relative_to(output_root).as_posix(),
                     "payload_sha256": env["payload_sha256"], "observed_at": env["observed_at"], "round": week}
        latest_rounds[week] = {**reference, "transaction_source_status": "OBSERVED" if available else "SOURCE_UNAVAILABLE",
                              "source_errors": errors}
        if not available:
            continue
        # One source response can contain the same ID twice. The normalizer
        # selects its last provider revision instead of counting both claims.
        normalized = normalize_transactions(transactions, league_id=league_id, week=week,
                                            fetched_at=env["observed_at"], raw_sha256=env["payload_sha256"])
        skipped_without_id += sum(not str(raw.get("transaction_id") or "").strip() for raw in transactions)
        raw_by_id = deduplicate_transactions(transactions)
        user_rows = payload.get("users")
        users = {str(u.get("user_id")): u for u in user_rows if isinstance(u, dict) and u.get("user_id")} if isinstance(user_rows, list) else {}
        for row in normalized:
            tx = row["transaction"]
            txid = tx["transaction_id"]
            digest = sha256_bytes(canonical_bytes(raw_by_id[txid]))
            creator = tx.get("creator")
            user = users.get(str(creator)) or {}
            observed = {"transaction": tx, "source_observation_type": row["source_observation_type"],
                        "creator_display_name": user.get("display_name") or user.get("username"),
                        "creator_identity_status": "SOURCE_USER_MATCH" if user else "ID_ONLY_OR_UNRESOLVED",
                        "raw_transaction_sha256": digest, **reference}
            record = records.setdefault(txid, {"transaction_id": txid, "first_observed_at": env["observed_at"],
                                               "observed_rounds": set(), "revisions": {}})
            record["observed_rounds"].add(week)
            record["last_observed_at"] = env["observed_at"]
            record["latest_observed"] = observed
            revision = record["revisions"].setdefault(digest, {"raw_transaction_sha256": digest,
                "first_observed_at": env["observed_at"], "transaction": tx, "observations": []})
            revision["last_observed_at"] = env["observed_at"]
            revision["observations"].append(reference)
    transactions = []
    for _, record in sorted(records.items()):
        record["observed_rounds"] = sorted(record["observed_rounds"])
        record["revisions"] = list(record["revisions"].values())
        record["distinct_revision_count"] = len(record["revisions"])
        record["source_observation_count"] = sum(len(x["observations"]) for x in record["revisions"])
        transactions.append(record)
    return {"schema_version": SCHEMA, "league_id": str(league_id), "season": int(season), "cutoff": cutoff,
            "identity": "SEASON_LEAGUE_TRANSACTION_ID", "latest_semantics": "LAST_OBSERVED_RESPONSE_NOT_PROVIDER_FINALITY",
            "decision_model_eligible": False, "private_claim_absence_inferred": False,
            "unique_transaction_count": len(transactions), "source_envelope_count": len(candidates),
            "source_failure_observation_count": failure_count, "observed_records_without_transaction_id": skipped_without_id,
            "latest_round_sources": [x for _, x in sorted(latest_rounds.items())], "transactions": transactions}


def validate_reconciliation(report: dict[str, Any], output_root: Path) -> None:
    from capture_fie_waivers import normalize_transactions
    assert report["schema_version"] == SCHEMA
    assert report["decision_model_eligible"] is False and report["private_claim_absence_inferred"] is False
    rows = report["transactions"]
    assert report["unique_transaction_count"] == len(rows) == len({r["transaction_id"] for r in rows})
    root = output_root.resolve()
    source_cache = {}
    for row in rows:
        assert row["distinct_revision_count"] == len(row["revisions"])
        references = [ref for revision in row["revisions"] for ref in revision["observations"]]
        assert row["source_observation_count"] == len(references)
        assert row["observed_rounds"] == sorted({r["round"] for r in references})
        assert parse_time(row["first_observed_at"]) == min(parse_time(r["observed_at"]) for r in references)
        assert parse_time(row["last_observed_at"]) == max(parse_time(r["observed_at"]) for r in references)
        for revision in row["revisions"]:
            for reference in revision["observations"]:
                source = (root / reference["source_envelope"]).resolve()
                source.relative_to(root)
                if source not in source_cache:
                    env = json.loads(source.read_text(encoding="utf-8")); validate_envelope(env)
                    source_cache[source] = (env, {(str(raw.get("transaction_id") or "").strip(), sha256_bytes(canonical_bytes(raw)))
                                                 for raw in env["payload"]["transactions"]})
                env, raw_keys = source_cache[source]
                assert source.parts[-4] == f"week_{reference['round']:02d}"
                assert source.parts[-3] == report["league_id"] and source.parts[-5] == str(report["season"])
                assert env["payload_sha256"] == reference["payload_sha256"]
                assert env["observed_at"] == reference["observed_at"]
                assert parse_time(env["observed_at"]) <= parse_time(report["cutoff"])
                assert (row["transaction_id"], revision["raw_transaction_sha256"]) in raw_keys
        latest = row["latest_observed"]
        source = (root / latest["source_envelope"]).resolve()
        assert source in source_cache
        env, keys = source_cache[source]
        assert (row["transaction_id"], latest["raw_transaction_sha256"]) in keys
        assert latest["observed_at"] == row["last_observed_at"] == env["observed_at"]
        assert latest["payload_sha256"] == env["payload_sha256"]
        assert source.parts[-4] == f"week_{latest['round']:02d}"
        raw = next(r for r in env["payload"]["transactions"] if str(r.get("transaction_id") or "").strip() == row["transaction_id"]
                   and sha256_bytes(canonical_bytes(r)) == latest["raw_transaction_sha256"])
        expected = normalize_transactions([raw], league_id=report["league_id"], week=latest["round"],
            fetched_at=env["observed_at"], raw_sha256=env["payload_sha256"])[0]
        assert latest["transaction"] == expected["transaction"]
        assert latest["source_observation_type"] == expected["source_observation_type"]
        user_rows = env["payload"].get("users")
        users = {str(u.get("user_id")): u for u in user_rows if isinstance(u, dict) and u.get("user_id")} if isinstance(user_rows, list) else {}
        user = users.get(str(expected["transaction"].get("creator"))) or {}
        assert latest["creator_display_name"] == (user.get("display_name") or user.get("username"))
        assert latest["creator_identity_status"] == ("SOURCE_USER_MATCH" if user else "ID_ONLY_OR_UNRESOLVED")
