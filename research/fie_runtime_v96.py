#!/usr/bin/env python3
"""Apply V9.6 controlled runtime intelligence to freshly built current snapshots.

Only QB/RB weekly residual models may alter the canonical main weekly decision because
those consumers were validated directly against FIE.  Component and horizon models are
attached as dedicated V9.6 outputs and do not overwrite M5 waiver/risk consumers.  The
function is fail-closed on identity, model hash, current-season availability, and the
existing M4/M5 weekly activation gate.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import math
from pathlib import Path
from types import SimpleNamespace
from typing import Any

import joblib

import fie_production_shadow as ps
from current_snapshot_storage import ROOT, load_current_snapshot

BUILD = "V9.6-CONTROLLED-RUNTIME-1"
MANIFEST_FILENAME = "v96_runtime.json"
MODEL_FILENAME = "v96_runtime_models.joblib"
PRIMARY_WEEKLY = {"QB": "histgb", "RB": "histgb"}


def read_json(path: str | Path) -> dict:
    p = Path(path)
    try:
        return json.loads(p.read_text(encoding="utf-8"))
    except Exception:
        return {}


def sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def finite(v) -> float | None:
    try:
        x = float(v)
    except (TypeError, ValueError):
        return None
    return x if math.isfinite(x) else None


def runtime_dir_for(league_id: str, season: int) -> Path:
    return ROOT / "data" / "research" / "leagues" / str(league_id) / "performance" / str(season) / "runtime"


def validate_manifest(current: dict, manifest: dict, runtime_dir: Path) -> Path:
    if manifest.get("status") != "approved_controlled_runtime":
        raise RuntimeError("V9.6 runtime manifest is not approved_controlled_runtime")
    if manifest.get("runtime_build") != BUILD:
        raise RuntimeError("Unexpected V9.6 runtime build")
    gov = manifest.get("governance") or {}
    if gov.get("runtime_activation_allowed") is not True or gov.get("controlled_runtime_only") is not True:
        raise RuntimeError("V9.6 runtime governance does not permit controlled activation")
    if gov.get("next_season_enabled") is not False or gov.get("prior_season_live_fallback") is not False:
        raise RuntimeError("V9.6 next-season/prior-season fallback guard changed")
    if gov.get("wr_te_histgb_enabled") is not False:
        raise RuntimeError("WR/TE HistGB unexpectedly enabled")
    if str(manifest.get("league_id") or "") != str(current.get("league_id") or ""):
        raise RuntimeError("V9.6 league mismatch")
    if int(manifest.get("report_season") or 0) != int(current.get("season") or 0):
        raise RuntimeError("V9.6 season mismatch")
    if str(manifest.get("profile_fingerprint") or "") != str(current.get("profile_fingerprint") or ""):
        raise RuntimeError("V9.6 profile fingerprint mismatch")
    if str(manifest.get("scoring_signature") or "") != str(current.get("scoring_signature") or ""):
        raise RuntimeError("V9.6 scoring signature mismatch")
    model_name = str(manifest.get("model_file") or MODEL_FILENAME)
    model_path = runtime_dir / model_name
    if not model_path.exists():
        raise RuntimeError(f"V9.6 model package missing: {model_path}")
    if sha256_file(model_path) != str(manifest.get("model_sha256") or ""):
        raise RuntimeError("V9.6 model package SHA256 mismatch")
    return model_path


def index_scored(scored: dict) -> tuple[dict, dict, dict]:
    weekly: dict[tuple[str, str], dict] = {}
    components: dict[str, dict[str, dict]] = {}
    horizons: dict[str, dict[str, dict]] = {}
    for r in scored.get("weekly_candidates") or []:
        cid = str(r.get("canonical_player_id") or "")
        cand = str(r.get("candidate") or "")
        if cid and cand:
            weekly[(cid, cand)] = r
    for r in scored.get("component_predictions") or []:
        cid = str(r.get("canonical_player_id") or "")
        comp = str(r.get("component") or "")
        if cid and comp:
            components.setdefault(cid, {})[comp] = r
    for r in scored.get("horizon_predictions") or []:
        cid = str(r.get("canonical_player_id") or "")
        horizon = str(r.get("horizon") or "")
        if cid and horizon:
            horizons.setdefault(cid, {})[horizon] = r
    return weekly, components, horizons


def apply_scored_outputs(current: dict, scored: dict, manifest: dict) -> dict:
    """Apply already-scored V9.6 outputs to a hydrated current snapshot.

    This pure transformation is also used by integrity tests.  Main weekly changes are
    restricted to QB/RB HistGB and to players already eligible under canonical weekly
    M4/M5 governance.  Dedicated horizon/component fields never overwrite canonical
    waiver/ROS/risk fields.
    """
    out = current
    weekly, components, horizons = index_scored(scored)
    overlay_players: dict[str, dict[str, Any]] = {}
    weekly_modified = 0
    component_attached = 0
    horizon_attached = 0

    for row in out.get("players") or []:
        cid = str(row.get("canonical_player_id") or "")
        if not cid:
            continue
        pos = str(row.get("position_model") or "")
        history_games = int(row.get("history_games") or 0)
        info: dict[str, Any] = {}

        # Only direct residual models are allowed to replace the main weekly decision.
        if pos in PRIMARY_WEEKLY and row.get("weekly_activation_eligible") is True and history_games >= 2:
            cand = weekly.get((cid, "histgb_residual"))
            if cand:
                old = finite(row.get("decision_weekly_projection"))
                new = finite(cand.get("shadow_decision_projection"))
                if old is not None and new is not None:
                    delta = new - old
                    row["decision_weekly_projection"] = round(max(0.0, new), 4)
                    # Keep all other player-row fields canonical so the shared-current
                    # deduplication contract is not fragmented by league-specific V9.6
                    # metadata. Risk/source overlays live in the league manifest below.
                    p10 = finite(row.get("p10")); p90 = finite(row.get("p90"))
                    info["weekly"] = {
                        "model": "histgb_residual",
                        "canonical_decision_projection": old,
                        "v96_decision_projection": row["decision_weekly_projection"],
                        "delta": round(delta, 4),
                        "feature_coverage": cand.get("feature_coverage"),
                        "canonical_projection_source": row.get("projection_source"),
                        "v96_projection_source": f"V9.6 controlled {pos} HistGB residual over canonical FIE",
                        "canonical_p10": p10,
                        "canonical_p90": p90,
                        "v96_shifted_p10": round(max(0.0, p10 + delta), 4) if p10 is not None else None,
                        "v96_shifted_p90": round(max(row["decision_weekly_projection"], p90 + delta), 4) if p90 is not None else None,
                    }
                    weekly_modified += 1

        # Keep the transparent RB single-feature model as a diagnostic alternate only.
        if pos == "RB":
            alt = weekly.get((cid, "ridge_backfield_competitor_count"))
            if alt:
                info["rb_weekly_alternate"] = {
                    "model": "ridge_backfield_competitor_count",
                    "projection": alt.get("shadow_decision_projection"),
                    "delta_vs_canonical": alt.get("delta_vs_canonical"),
                    "stack_policy": "diagnostic_only_never_summed_with_histgb",
                }

        # Component/horizon consumers are runtime-visible but do not replace canonical consumers.
        # Preserve the existing 2-game player gate for controlled rollout.
        if row.get("weekly_activation_eligible") is True and history_games >= 2:
            crows = components.get(cid) or {}
            if crows:
                vals = {}
                for name, rec in crows.items():
                    vals[name] = {
                        "next_game": rec.get("shadow_next_game_component"),
                        "current": rec.get("current_component"),
                        "feature_coverage": rec.get("feature_coverage"),
                    }
                info["components"] = vals
                component_attached += len(vals)

            hrows = horizons.get(cid) or {}
            if hrows:
                hvals = {}
                for name, rec in hrows.items():
                    # Next-3 also respects the existing waiver decision gate.
                    if name == "next_3_games" and row.get("waiver_activation_eligible") is not True:
                        continue
                    hvals[name] = {
                        "prediction": rec.get("shadow_prediction"),
                        "prediction_type": rec.get("prediction_type"),
                        "feature_coverage": rec.get("feature_coverage"),
                    }
                    field = {
                        "next_week": "v96_next_week_projection",
                        "next_3_games": "v96_next3_projection",
                        "rest_of_season": "v96_ros_projection",
                        "floor": "v96_floor_probability",
                        "ceiling": "v96_ceiling_probability",
                        "breakout": "v96_breakout_probability",
                    }.get(name)
                    if field:
                        hvals[name]["runtime_field"] = field
                    horizon_attached += 1
                if hvals:
                    info["horizons"] = hvals

        if info:
            overlay_players[cid] = info

    reason = scored.get("reason")
    if scored.get("status") != "complete_shadow_only":
        status = "blocked_" + str(reason or "no_current_features")
    elif weekly_modified or component_attached or horizon_attached:
        status = "active_controlled_runtime"
    else:
        status = "available_no_eligible_player_outputs"

    out["v96_runtime"] = {
        "runtime_build": manifest.get("runtime_build"),
        "status": status,
        "source_runtime_generated_at": manifest.get("generated_at"),
        "completed_weeks": scored.get("completed_weeks") or [],
        "weekly_main_projection_positions": ["QB", "RB"],
        "weekly_main_projection_model": "HistGB residual",
        "wr_te_histgb_enabled": False,
        "rb_competitor_model_role": "diagnostic_alternate_only",
        "component_outputs_replace_canonical": False,
        "horizon_outputs_replace_canonical": False,
        "next_season_enabled": False,
        "prior_season_live_fallback": False,
        "summary": {
            "weekly_main_projections_modified": weekly_modified,
            "component_outputs_attached": component_attached,
            "horizon_outputs_attached": horizon_attached,
            "players_with_v96_output": len(overlay_players),
        },
        "players": overlay_players,
    }
    return out


def apply_one(current_path: Path, runtime_dir: Path, current_cache: Path) -> dict:
    current = load_current_snapshot(current_path)
    if not current:
        raise RuntimeError(f"Unreadable current snapshot: {current_path}")
    manifest_path = runtime_dir / MANIFEST_FILENAME
    manifest = read_json(manifest_path)
    model_path = validate_manifest(current, manifest, runtime_dir)
    package = joblib.load(model_path)
    if package.get("runtime_build") != BUILD:
        raise RuntimeError("Loaded V9.6 package build mismatch")
    if str(package.get("league_id") or "") != str(current.get("league_id") or ""):
        raise RuntimeError("Loaded V9.6 package league mismatch")
    if package.get("primary_weekly") != PRIMARY_WEEKLY:
        raise RuntimeError("Loaded V9.6 primary weekly policy mismatch")

    # Current-season availability is evaluated from fresh completed-week sources.  A
    # preseason/Week-1 block is a valid result, not a workflow failure.
    args = SimpleNamespace(
        current_cache=str(current_cache),
        min_live_coverage=float((manifest.get("governance") or {}).get("minimum_live_feature_coverage") or ps.DEFAULT_MIN_LIVE_COVERAGE),
    )
    observed, team_hist, live_meta = ps.live_context(args, current)
    m4_path = current_path.parents[1] / "milestone4.json"
    m4 = read_json(m4_path)
    scored = ps.score_current(
        args,
        current,
        m4,
        package.get("registry") or [],
        package.get("fitted") or {},
        observed,
        team_hist,
        live_meta,
    )
    applied = apply_scored_outputs(current, scored, manifest)
    current_path.write_text(json.dumps(applied, indent=2, allow_nan=False) + "\n", encoding="utf-8")
    return applied.get("v96_runtime") or {}


def apply_portfolio(built_ids: Path, leagues_root: Path, strict_existing: bool = True) -> dict:
    ids = [x.strip() for x in built_ids.read_text(encoding="utf-8").splitlines() if x.strip()] if built_ids.exists() else []
    result = {"built_ids": len(ids), "applied": 0, "blocked": 0, "missing_bundle": 0, "errors": []}
    for lid in ids:
        root = leagues_root / lid
        current_path = root / "current" / "milestone5_current.json"
        current = load_current_snapshot(current_path)
        if not current:
            result["errors"].append(f"{lid}:current_missing")
            continue
        season = int(current.get("season") or 0)
        runtime_dir = root / "performance" / str(season) / "runtime"
        manifest_path = runtime_dir / MANIFEST_FILENAME
        if not manifest_path.exists():
            result["missing_bundle"] += 1
            print(f"V9.6 {lid}: no runtime bundle; canonical FIE preserved")
            continue
        try:
            meta = apply_one(current_path, runtime_dir, ROOT / ".cache" / "fie-current" / "leagues" / lid)
            if str(meta.get("status") or "").startswith("blocked_"):
                result["blocked"] += 1
            else:
                result["applied"] += 1
            print(f"V9.6 {lid}: {meta.get('status')} {meta.get('summary')}")
        except Exception as e:
            result["errors"].append(f"{lid}:{e}")
            print(f"V9.6 ERROR {lid}: {e}")
    if result["errors"] and strict_existing:
        raise RuntimeError("; ".join(result["errors"]))
    return result


def self_test() -> None:
    manifest = {
        "runtime_build": BUILD,
        "generated_at": "x",
    }
    current = {
        "players": [
            {
                "canonical_player_id": "qb1", "position_model": "QB", "history_games": 3,
                "weekly_activation_eligible": True, "waiver_activation_eligible": True,
                "decision_weekly_projection": 20.0, "p10": 15.0, "p90": 26.0,
                "projection_source": "canonical",
            },
            {
                "canonical_player_id": "wr1", "position_model": "WR", "history_games": 3,
                "weekly_activation_eligible": True, "waiver_activation_eligible": True,
                "decision_weekly_projection": 15.0, "waiver_next3_projection": 14.5,
            },
            {
                "canonical_player_id": "rb0", "position_model": "RB", "history_games": 3,
                "weekly_activation_eligible": False, "waiver_activation_eligible": True,
                "decision_weekly_projection": 12.0,
            },
        ]
    }
    scored = {
        "status": "complete_shadow_only", "completed_weeks": [1, 2, 3],
        "weekly_candidates": [
            {"canonical_player_id": "qb1", "candidate": "histgb_residual", "shadow_decision_projection": 22.0, "feature_coverage": .9},
            {"canonical_player_id": "rb0", "candidate": "histgb_residual", "shadow_decision_projection": 14.0, "feature_coverage": .9},
        ],
        "component_predictions": [
            {"canonical_player_id": "wr1", "component": "target_volume", "shadow_next_game_component": 8.2, "current_component": 7.0, "feature_coverage": .9},
        ],
        "horizon_predictions": [
            {"canonical_player_id": "wr1", "horizon": "next_3_games", "shadow_prediction": 16.1, "prediction_type": "fantasy_points", "feature_coverage": .9},
            {"canonical_player_id": "wr1", "horizon": "breakout", "shadow_prediction": .31, "prediction_type": "probability", "feature_coverage": .9},
        ],
    }
    out = apply_scored_outputs(current, scored, manifest)
    qb = out["players"][0]; wr = out["players"][1]; rb = out["players"][2]
    assert qb["decision_weekly_projection"] == 22.0
    assert qb["p10"] == 15.0 and qb["p90"] == 26.0  # canonical risk rows stay shareable
    assert rb["decision_weekly_projection"] == 12.0  # canonical gate remains authoritative
    assert wr["decision_weekly_projection"] == 15.0  # WR horizon never replaces weekly FIE
    assert wr["waiver_next3_projection"] == 14.5      # canonical M5 next3 not overwritten
    assert "v96_next3_projection" not in wr  # dedicated outputs live at league level
    assert out["v96_runtime"]["players"]["wr1"]["horizons"]["next_3_games"]["prediction"] == 16.1
    assert out["v96_runtime"]["players"]["wr1"]["horizons"]["breakout"]["prediction"] == .31
    assert out["v96_runtime"]["next_season_enabled"] is False
    print("PASS V9.6 controlled-runtime integrity")


def main(argv=None):
    p = argparse.ArgumentParser()
    sub = p.add_subparsers(dest="cmd", required=True)
    sp = sub.add_parser("apply-portfolio")
    sp.add_argument("--built-ids", required=True)
    sp.add_argument("--leagues-root", default="data/research/leagues")
    sp.add_argument("--allow-invalid-existing", action="store_true")
    sub.add_parser("self-test")
    a = p.parse_args(argv)
    if a.cmd == "self-test":
        self_test(); return
    result = apply_portfolio(
        Path(a.built_ids),
        ROOT / a.leagues_root,
        strict_existing=not a.allow_invalid_existing,
    )
    print("V9.6 portfolio result:", result)


if __name__ == "__main__":
    main()
