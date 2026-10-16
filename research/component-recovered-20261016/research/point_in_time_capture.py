#!/usr/bin/env python3
"""Canonical first-write point-in-time source envelopes for research evidence."""
from __future__ import annotations

import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Iterable


SCHEMA = "fie-point-in-time-source-envelope-v1"
INTENTS = {"WAIVER_TRANSACTION", "AVAILABILITY", "WEATHER_FORECAST", "OTHER_GOVERNED"}
REVISION_STATES = {"EXPOSED", "NOT_EXPOSED_BY_PROVIDER", "UNKNOWN"}


def canonical_bytes(value: Any) -> bytes:
    return json.dumps(
        value, sort_keys=True, separators=(",", ":"), ensure_ascii=True, allow_nan=False
    ).encode("utf-8")


def sha256_bytes(value: bytes) -> str:
    return hashlib.sha256(value).hexdigest()


def sha256_file(path: Path) -> str:
    return sha256_bytes(path.read_bytes())


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def parse_time(value: str) -> datetime:
    parsed = datetime.fromisoformat(str(value).replace("Z", "+00:00"))
    if parsed.tzinfo is None:
        parsed = parsed.replace(tzinfo=timezone.utc)
    return parsed.astimezone(timezone.utc)


def compact_timestamp(value: str) -> str:
    return parse_time(value).strftime("%Y%m%dT%H%M%S%fZ")


def build_envelope(
    *,
    capture_id: str,
    capture_intent: str,
    provider: str,
    endpoint: str,
    observed_at: str,
    as_of_semantics: str,
    payload: Any,
    effective_at: str | None = None,
    release_identifier: str | None = None,
    revision_identifier: str | None = None,
    revision_metadata_status: str = "UNKNOWN",
) -> dict[str, Any]:
    envelope = {
        "schema_version": SCHEMA,
        "capture_id": str(capture_id),
        "capture_intent": capture_intent,
        "provider": str(provider),
        "endpoint": str(endpoint),
        "observed_at": parse_time(observed_at).isoformat(),
        "effective_at": parse_time(effective_at).isoformat() if effective_at else None,
        "as_of_semantics": str(as_of_semantics),
        "release_identifier": release_identifier,
        "revision_identifier": revision_identifier,
        "revision_metadata_status": revision_metadata_status,
        "immutable_first_write": True,
        "payload_sha256": sha256_bytes(canonical_bytes(payload)),
        "payload": payload,
    }
    validate_envelope(envelope)
    return envelope


def validate_envelope(value: dict[str, Any]) -> None:
    assert value.get("schema_version") == SCHEMA
    assert value.get("capture_id")
    assert value.get("capture_intent") in INTENTS
    assert value.get("provider") and value.get("endpoint")
    parse_time(value["observed_at"])
    if value.get("effective_at"):
        parse_time(value["effective_at"])
    assert value.get("as_of_semantics")
    assert value.get("revision_metadata_status") in REVISION_STATES
    assert value.get("immutable_first_write") is True
    assert value.get("payload_sha256") == sha256_bytes(canonical_bytes(value.get("payload")))


def first_write_json(path: Path, value: Any) -> str:
    """Write canonical JSON once; identical retries no-op and collisions fail closed."""
    encoded = canonical_bytes(value) + b"\n"
    if path.exists():
        if path.read_bytes() != encoded:
            raise ValueError(f"immutable first-write collision: {path}")
        return "EXISTS"
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(encoded)
    return "CREATED"


def latest_eligible(
    rows: Iterable[dict[str, Any]], *, cutoff: str, observed_key: str = "observed_at"
) -> dict[str, Any] | None:
    """Return the last source observation known at cutoff; later rows are excluded."""
    limit = parse_time(cutoff)
    eligible = [row for row in rows if parse_time(str(row[observed_key])) <= limit]
    return max(eligible, key=lambda row: parse_time(str(row[observed_key]))) if eligible else None
