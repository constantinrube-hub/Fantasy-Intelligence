#!/usr/bin/env python3
"""Bind a captured provider stat payload to one immutable PR2 lineup capture.

This adapter deliberately does no network I/O.  The source owner captures a
provider payload first, then this module translates only identities present in
the frozen lineup candidate universe.  A missing provider row stays missing;
it is never transformed into a zero-point player outcome.
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

try:
    from build_in_season_pr2_lineup_outcome import RAW_SCHEMA
    from point_in_time_capture import canonical_bytes, sha256_bytes
except ModuleNotFoundError:  # pragma: no cover - package import support
    from research.build_in_season_pr2_lineup_outcome import RAW_SCHEMA
    from research.point_in_time_capture import canonical_bytes, sha256_bytes


SOURCE_SCHEMA = "fie-in-season-pr2-lineup-provider-stat-source-v1"


def read_json(path: Path) -> dict[str, Any]:
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise ValueError(f"object required: {path}")
    return value


def capture_candidates(capture: dict[str, Any]) -> list[tuple[str, str, str]]:
    """Return (league id, immutable player id, provider source id) bindings."""
    bindings: list[tuple[str, str, str]] = []
    source_to_canonical: dict[str, str] = {}
    for report in capture.get("leagues") or []:
        if not isinstance(report, dict) or report.get("status") == "NOT_APPLICABLE_AUTOMATIC_LINEUP":
            continue
        league_id = str(report.get("league_id") or "")
        source = report.get("evaluation_input") or {}
        if source.get("schema") != "fie-in-season-pr2-lineup-evaluation-input-v1":
            continue
        for candidate in source.get("active_candidates") or []:
            if not isinstance(candidate, dict):
                continue
            canonical_id = str(candidate.get("captured_player_id") or "")
            provider_id = str(candidate.get("sleeper_id") or canonical_id)
            if not league_id or not canonical_id or not provider_id:
                raise ValueError("capture candidate identity incomplete")
            prior = source_to_canonical.setdefault(provider_id, canonical_id)
            if prior != canonical_id:
                raise ValueError(f"provider identity maps to conflicting capture identities: {provider_id}")
            bindings.append((league_id, canonical_id, provider_id))
    if not bindings:
        raise ValueError("no evaluable frozen capture candidates")
    return bindings


def source_identity(candidate: dict[str, Any], namespace: str) -> str | None:
    """Return an already-frozen exact source identity; never name-match."""
    if namespace == "sleeper":
        value = candidate.get("sleeper_id")
        return str(value) if value is not None and str(value).strip() else None
    if namespace == "gsis":
        for value in (candidate.get("gsis_id"), candidate.get("canonical_player_id")):
            text = str(value or "").strip()
            if text.startswith("00-"):
                return text
        captured = str(candidate.get("captured_player_id") or "")
        return captured.removeprefix("canonical:") if captured.removeprefix("canonical:").startswith("00-") else None
    raise ValueError(f"unsupported provider source identity namespace: {namespace}")


def adapt_source(capture: dict[str, Any], source: dict[str, Any]) -> dict[str, Any]:
    """Translate provider-keyed rows into the raw outcome scorer contract."""
    if source.get("schema") != SOURCE_SCHEMA:
        raise ValueError("provider source schema invalid")
    if not capture.get("capture_id") or not capture.get("capture_content_sha256"):
        raise ValueError("immutable capture required")
    expected_season = capture.get("leagues", [{}])[0].get("season") if capture.get("leagues") else None
    expected_week = capture.get("leagues", [{}])[0].get("week") if capture.get("leagues") else None
    if source.get("season") != expected_season or source.get("week") != expected_week:
        raise ValueError("provider source target does not match immutable capture season/week")
    if source.get("sparse_zero_fields_are_explicit") is not True:
        raise ValueError("provider source must explicitly declare sparse zero-field semantics")
    provider_stats = source.get("stats_by_source_player_id")
    if not isinstance(provider_stats, dict):
        raise ValueError("provider source stats_by_source_player_id object required")
    direct_stats = source.get("direct_stats_by_captured_player_id", {})
    if not isinstance(direct_stats, dict):
        raise ValueError("provider source direct_stats_by_captured_player_id object required")

    namespace = str(source.get("source_player_id_namespace") or "sleeper").lower()
    if namespace not in {"sleeper", "gsis"}:
        raise ValueError(f"unsupported provider source identity namespace: {namespace}")
    stats_by_player_id: dict[str, dict[str, Any]] = {}
    bindings = []
    seen: set[tuple[str, str]] = set()
    source_to_canonical: dict[str, str] = {}
    for report in capture.get("leagues") or []:
        if not isinstance(report, dict) or report.get("status") == "NOT_APPLICABLE_AUTOMATIC_LINEUP":
            continue
        league_id = str(report.get("league_id") or "")
        for candidate in (report.get("evaluation_input") or {}).get("active_candidates") or []:
            if not isinstance(candidate, dict):
                continue
            canonical_id = str(candidate.get("captured_player_id") or "")
            key = (league_id, canonical_id)
            if key in seen:
                continue
            seen.add(key)
            direct = direct_stats.get(canonical_id)
            position = str(candidate.get("position_model") or "").upper()
            if direct is not None and (not canonical_id.startswith("teamdef:") or position not in {"DEF", "DST", "D/ST"}):
                raise ValueError(f"direct provider outcome is only valid for frozen team-defense identity: {canonical_id}")
            if direct is not None and not isinstance(direct, dict):
                raise ValueError(f"direct provider stat row must be an object: {canonical_id}")
            provider_id = None if direct is not None else source_identity(candidate, namespace)
            if provider_id is not None:
                prior = source_to_canonical.setdefault(provider_id, canonical_id)
                if prior != canonical_id:
                    raise ValueError(f"provider identity maps to conflicting capture identities: {provider_id}")
            status = "MISSING_PROVIDER_SOURCE_IDENTITY" if provider_id is None else "MISSING_PROVIDER_STAT_ROW"
            raw = direct if direct is not None else (provider_stats.get(provider_id) if provider_id is not None else None)
            if isinstance(raw, dict):
                stats_by_player_id[canonical_id] = dict(raw)
                status = "READY_DIRECT_TEAM_DEFENSE" if direct is not None else "READY"
            elif raw is not None:
                raise ValueError(f"provider stat row must be an object: {provider_id}")
            bindings.append({"league_id": league_id, "captured_player_id": canonical_id, "provider_player_id": provider_id, "source_player_id_namespace": "teamdef" if direct is not None else namespace, "status": status})

    return {
        "schema": RAW_SCHEMA,
        "provider": source.get("provider"),
        "endpoint": source.get("endpoint"),
        "observed_at": source.get("observed_at"),
        "sparse_zero_fields_are_explicit": True,
        "stats_by_player_id": dict(sorted(stats_by_player_id.items())),
        "capture_id": capture["capture_id"],
        "capture_content_sha256": capture["capture_content_sha256"],
        "provider_source_payload_sha256": sha256_bytes(canonical_bytes(source)),
        "source_player_id_namespace": namespace,
        "identity_bindings": sorted(bindings, key=lambda row: (row["league_id"], row["captured_player_id"])),
        "governance": {
            "research_only": True,
            "provider_payload_captured_before_adapter": True,
            "missing_provider_rows_zero_imputed": False,
            "later_current_snapshot_identity_fallback": False,
        },
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Adapt captured provider player stats to immutable PR2 lineup identities")
    parser.add_argument("--capture", required=True)
    parser.add_argument("--provider-source", required=True)
    parser.add_argument("--output", required=True)
    args = parser.parse_args(argv)
    raw = adapt_source(read_json(Path(args.capture)), read_json(Path(args.provider_source)))
    output = Path(args.output)
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(raw, sort_keys=True, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({"output": str(output), "player_rows": len(raw["stats_by_player_id"])}, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
