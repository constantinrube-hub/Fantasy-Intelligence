#!/usr/bin/env python3
"""Resolve per-position FIE research readiness without promoting any model.

This is a selection/governance layer only. It reads existing M9/V9.7/DST/K
evidence and records the production model, best research challenger and whether a
review is justified.  A PROMOTION_REVIEW_READY result is never production
activation.
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

from fie_research_pipeline_contract import (
    MODEL_DECISIONS,
    OFFENSE,
    READINESS_SCHEMA,
    ROOT,
    applicable_positions,
    current_path,
    league_root,
    league_row,
    load_json,
    load_profile,
    pipeline_dir,
    profile_fingerprint,
    profile_format,
    roster_positions,
    roster_signature,
    scoring_signature,
    strategy_dir,
    team_count,
    utc_now,
    write_json,
)


def _status_from_reason(meta: dict) -> str:
    reason = str(meta.get("reason") or "").lower()
    if "scoring" in reason:
        return "BLOCKED_SCORING"
    if any(x in reason for x in ("fold", "ci", "head_to_head", "noninferior", "statistic", "gate")):
        return "BLOCKED_STATISTICS"
    if any(x in reason for x in ("profile", "identity", "team_change")):
        return "BLOCKED_PROFILE"
    if any(x in reason for x in ("data", "missing", "unavailable", "sample")):
        return "BLOCKED_DATA"
    return "DIAGNOSTIC_ONLY"


def _exact(meta: dict) -> bool:
    v972 = meta.get("all_v972_folds_exact_scoring_replay")
    m9 = meta.get("all_m9_folds_exact_scoring_replay")
    if v972 is None and m9 is None:
        return bool(meta.get("exact_scoring_replay") or meta.get("exact_scoring"))
    return bool(v972) and bool(m9)


def _compact_evidence(meta: dict) -> dict:
    keys = (
        "status", "reason", "folds", "n_test", "exact_m9_comparator_gate",
        "all_v972_folds_exact_scoring_replay", "all_m9_folds_exact_scoring_replay",
        "football_model_promotion_review_ready", "expected_season_points_ready",
        "v972_prior_gate_status", "ppg_mae_head_to_head_gate_vs_exact_m9",
        "expected_season_mae_head_to_head_gate_vs_exact_m9",
        "full_schedule_mae_head_to_head_gate_vs_exact_m9", "standalone_noninferiority",
        "weighted_metrics", "availability_vs_full_schedule_gate",
    )
    return {k: meta.get(k) for k in keys if k in meta}


def _approved_override(league_id: str, profile: dict, row: dict) -> dict[str, str]:
    """Read an explicit future promotion decision, never infer one from research."""
    path = league_root(league_id) / "governance/research_model_promotion.json"
    obj = load_json(path, {})
    if not obj or obj.get("approved") is not True:
        return {}
    if str(obj.get("league_id") or "") != str(league_id):
        return {}
    if str(obj.get("profile_fingerprint") or "") != profile_fingerprint(row, profile):
        return {}
    if str(obj.get("scoring_signature") or "") != scoring_signature(row, profile):
        return {}
    models = obj.get("production_preseason_model_by_position") or {}
    return {str(k).upper(): str(v) for k, v in models.items() if v}


def _offense_decision(pos: str, v974: dict, v975: dict, override: dict[str, str]) -> dict:
    m974 = ((v974.get("per_position") or {}).get(pos) or {})
    m975 = ((v975.get("per_position") or {}).get(pos) or {}) if pos == "QB" else {}

    selected = override.get(pos, "M9")
    production_status = "PRODUCTION_EXISTING"
    challenger = None
    challenger_meta: dict[str, Any] = {}

    # QB ensemble is the latest challenger when it exists.  It may be review-ready,
    # but does not supply a current-season production projection or activation.
    if pos == "QB" and m975:
        challenger = "V9.7.5"
        challenger_meta = m975
    elif m974:
        challenger = "V9.7.2"
        challenger_meta = m974

    if selected != "M9":
        # Only an explicit governance artifact can land here.
        decision = "PRODUCTION_EXISTING"
        reason = "explicit_governance_promotion_artifact"
    elif challenger_meta.get("football_model_promotion_review_ready") is True:
        decision = "PROMOTION_REVIEW_READY"
        reason = "unchanged_research_gates_cleared_but_no_automatic_activation"
    elif challenger_meta:
        decision = _status_from_reason(challenger_meta)
        reason = str(challenger_meta.get("reason") or "challenger_not_promotion_review_ready")
    elif v974 or v975:
        decision = "DIAGNOSTIC_ONLY"
        reason = "no_applicable_challenger_result"
    else:
        decision = "BLOCKED_DATA"
        reason = "v974_v975_evidence_missing"

    if decision not in MODEL_DECISIONS:
        raise ValueError(decision)

    exact = _exact(challenger_meta) if challenger_meta else False
    return {
        "selected_production_model": selected,
        "selected_production_status": production_status,
        "research_final_model": selected,  # no promotion occurs in this resolver
        "best_research_challenger": challenger,
        "decision": decision,
        "reason": reason,
        "exact_scoring": exact,
        "current_challenger_projection_activated": False,
        "evidence": {
            "v974": _compact_evidence(m974) if m974 else None,
            "v975": _compact_evidence(m975) if m975 else None,
        },
    }


def _special_decision(pos: str, profile: dict, m5: dict, current: dict) -> dict:
    slots = roster_positions(profile)
    if pos == "DST":
        enabled = any(s in {"DEF", "DST", "D/ST"} for s in slots)
        key = "dst"
        selected = "FIE_DST_DEDICATED"
        current_summary = ((current.get("summary") or {}).get("dst") or {})
    else:
        enabled = "K" in slots
        key = "kicker"
        selected = "FIE_KICKER_DEDICATED"
        current_summary = ((current.get("summary") or {}).get("kicker") or {})
    if not enabled:
        return {
            "selected_production_model": None,
            "selected_production_status": "NOT_APPLICABLE",
            "research_final_model": None,
            "best_research_challenger": None,
            "decision": "NOT_APPLICABLE",
            "reason": "position_not_rosterable",
            "exact_scoring": None,
            "evidence": None,
        }
    meta = m5.get(key) or {}
    status = str(meta.get("status") or "")
    active = bool(current_summary.get("weekly_active") or current_summary.get("entities"))
    if status in {"validated_candidate", "baseline_validated", "complete"} or active:
        decision = "PRODUCTION_EXISTING"
        reason = "existing_dedicated_specialist_engine"
    elif meta:
        decision = _status_from_reason(meta)
        reason = str(meta.get("reason") or status or "specialist_engine_diagnostic")
    else:
        decision = "BLOCKED_DATA"
        reason = "specialist_engine_evidence_missing"
    return {
        "selected_production_model": selected,
        "selected_production_status": decision,
        "research_final_model": selected,
        "best_research_challenger": None,
        "decision": decision,
        "reason": reason,
        "exact_scoring": bool(((current.get("scoring_support_relevant") or {}).get("exact_replay_eligible"))),
        "evidence": {"milestone5": meta, "current_summary": current_summary},
    }


def _idp_decision(pos: str, profile: dict, m5: dict) -> dict:
    slots = roster_positions(profile)
    aliases = {"DE": "EDGE", "DT": "IDL", "DL": "IDL", "DB": "S"}
    normalized = {aliases.get(x, x) for x in slots}
    if pos not in normalized:
        return {
            "selected_production_model": None,
            "selected_production_status": "NOT_APPLICABLE",
            "research_final_model": None,
            "best_research_challenger": None,
            "decision": "NOT_APPLICABLE",
            "reason": "position_not_rosterable",
            "exact_scoring": None,
            "evidence": None,
        }
    validated = set((m5.get("decision_gates") or {}).get("draft_policy_positions") or [])
    ok = pos in validated or any(x in validated for x in ({"EDGE", "IDL"} if pos in {"EDGE", "IDL"} else {pos}))
    return {
        "selected_production_model": "EXISTING_IDP_STACK",
        "selected_production_status": "PRODUCTION_EXISTING" if ok else "DIAGNOSTIC_ONLY",
        "research_final_model": "EXISTING_IDP_STACK",
        "best_research_challenger": None,
        "decision": "PRODUCTION_EXISTING" if ok else "DIAGNOSTIC_ONLY",
        "reason": "existing_idp_decision_stack" if ok else "idp_position_not_in_existing_draft_gate",
        "exact_scoring": None,
        "evidence": None,
    }


def build_readiness(league_id: str, season: int, *, adp_key: str, pipeline_fingerprint: str, pipeline_status: str = "complete_research_only") -> dict:
    row = league_row(league_id)
    profile = load_profile(league_id, row)
    sdir = strategy_dir(league_id, season)
    v974 = load_json(sdir / "preseason_v974_validation.json", {})
    v975 = load_json(sdir / "preseason_v975_validation.json", {})
    strategy = load_json(sdir / "strategy_stack.json", {})
    m5 = load_json(league_root(league_id) / "milestone5.json", {})
    try:
        from current_snapshot_storage import load_current_snapshot
        current = load_current_snapshot(current_path(league_id)) if current_path(league_id).is_file() else {}
    except Exception:
        current = load_json(current_path(league_id), {})
    override = _approved_override(league_id, profile, row)

    positions: dict[str, dict] = {}
    for pos in OFFENSE:
        positions[pos] = _offense_decision(pos, v974, v975, override)
    positions["DST"] = _special_decision("DST", profile, m5, current)
    positions["K"] = _special_decision("K", profile, m5, current)
    for pos in ("EDGE", "IDL", "LB", "CB", "S"):
        if pos in applicable_positions(profile):
            positions[pos] = _idp_decision(pos, profile, m5)

    lvmeta = strategy.get("league_value_meta") or {}
    market = {
        "adp_key": adp_key,
        "expected_adp_key": ((strategy.get("provenance") or {}).get("profile_expected_adp_key")),
        "snapshot_count": ((strategy.get("provenance") or {}).get("market_snapshot_count")),
        "latest_snapshot": ((strategy.get("provenance") or {}).get("latest_market_snapshot")),
    }
    readiness = {
        "schema": READINESS_SCHEMA,
        "schema_version": 1,
        "league": {
            "id": str(league_id),
            "name": str(row.get("league_name") or profile.get("league_name") or ""),
            "format": profile_format(profile, row),
            "teams": team_count(profile),
            "profile_fingerprint": profile_fingerprint(row, profile),
            "scoring_signature": scoring_signature(row, profile),
            "roster_signature": roster_signature(profile),
            "roster_positions": roster_positions(profile),
        },
        "pipeline": {
            "status": pipeline_status,
            "generated_at": utc_now(),
            "pipeline_fingerprint": pipeline_fingerprint,
        },
        "positions": positions,
        "market": market,
        "league_value": {
            "replacement": lvmeta.get("replacement_points") or {},
            "draft_horizon": ((lvmeta.get("draft_relevance") or {}).get("draft_horizon")),
            "watchlist_horizon": ((lvmeta.get("draft_relevance") or {}).get("watchlist_horizon")),
            "source": "existing_fie_strategy_stack",
        },
        "governance": {
            "adp_in_football_model": False,
            "automatic_promotion": False,
            "canonical_model_modified": False,
            "production_activation_from_research_pipeline": False,
            "promotion_override_present": bool(override),
        },
    }
    return readiness


def main(argv=None) -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--league-id", required=True)
    ap.add_argument("--season", type=int, required=True)
    ap.add_argument("--adp-key", required=True)
    ap.add_argument("--pipeline-fingerprint", required=True)
    ap.add_argument("--pipeline-status", default="complete_research_only")
    ap.add_argument("--output", default="")
    a = ap.parse_args(argv)
    out = Path(a.output) if a.output else pipeline_dir(a.league_id, a.season) / "readiness.json"
    readiness = build_readiness(a.league_id, a.season, adp_key=a.adp_key, pipeline_fingerprint=a.pipeline_fingerprint, pipeline_status=a.pipeline_status)
    write_json(out, readiness)
    print(json.dumps({"league_id": a.league_id, "status": readiness["pipeline"]["status"], "positions": {k: v["decision"] for k, v in readiness["positions"].items()}}, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
