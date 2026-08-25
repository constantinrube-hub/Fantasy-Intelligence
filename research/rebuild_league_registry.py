#!/usr/bin/env python3
"""Rebuild generated League-ID registry and portfolio readiness status from disk."""
from __future__ import annotations

import argparse
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict

from portfolio_rules import load_portfolio_config

ROOT = Path(__file__).resolve().parents[1]
LEAGUES_ROOT = ROOT / "data" / "research" / "leagues"
REQUIRED = [f"milestone{i}.json" for i in range(1, 7)]


def now() -> str:
    return datetime.now(timezone.utc).isoformat()


def load(path: Path, default=None):
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return default


def write(path: Path, obj: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(obj, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def research_complete(root: Path) -> bool:
    if not (root / "profile.json").exists():
        return False
    return all((root / x).exists() for x in REQUIRED)


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--config", default=str(ROOT / "config" / "league-portfolio.json"))
    ap.add_argument("--registry", default=str(LEAGUES_ROOT / "registry.json"))
    ap.add_argument("--status", default=str(LEAGUES_ROOT / "portfolio-status.json"))
    ap.add_argument("--plan", default=None, help="Optional bulk-plan JSON to retain live names/errors and expected build states")
    a = ap.parse_args()

    cfg = load_portfolio_config(a.config)
    plan = load(Path(a.plan), {}) if a.plan else {}
    plan_rows = {str(r.get("league_id")): r for r in (plan or {}).get("leagues", [])}
    old_reg = load(Path(a.registry), {}) or {}
    old_rows = old_reg.get("leagues") or {}

    registry: Dict[str, Any] = {"schema_version": 1, "updated_at": now(), "leagues": {}}
    status: Dict[str, Any] = {"schema_version": 1, "updated_at": now(), "managed_count": len(cfg["leagues"]), "leagues": {}}

    for entry in cfg["leagues"]:
        lid = entry["league_id"]
        root = LEAGUES_ROOT / lid
        profile = load(root / "profile.json", {}) or {}
        m5 = load(root / "milestone5.json", {}) or {}
        current = load(root / "current" / "milestone5_current.json", {}) or {}
        gov = load(root / "governance" / "active_release.json", {}) or {}
        complete = research_complete(root)
        current_ok = bool(current)
        gov_ok = bool(gov)
        plan_row = plan_rows.get(lid, {})
        league_name = profile.get("league_name") or plan_row.get("league_name") or entry.get("alias")
        research_rev = int(m5.get("contract_revision") or 0) if m5 else None
        if complete and research_rev and research_rev >= 4 and current_ok and gov_ok:
            readiness = "READY"
        elif complete:
            readiness = "REFRESH_ONLY"
        elif plan_row.get("state") == "ERROR":
            readiness = "ERROR"
        elif plan_row.get("state") in {"NEW", "PROFILE_CHANGED"}:
            readiness = "BUILD_REQUIRED"
        else:
            readiness = "NOT_BUILT"

        status["leagues"][lid] = {
            "league_id": lid,
            "league_name": league_name,
            "format": entry["format"],
            "priority": entry["priority"],
            "alias": entry.get("alias"),
            "research_constraints": entry.get("research_constraints") or [],
            "status": readiness,
            "historical_research": bool(complete),
            "research_contract_revision": research_rev,
            "current_snapshot": current_ok,
            "governance": gov_ok,
            "season": profile.get("season") or plan_row.get("season"),
            "season_type": current.get("season_type") or profile.get("season_type") or plan_row.get("season_type"),
            "analysis_week": current.get("week"),
            "runtime_enabled": gov.get("runtime_enabled") if gov else False,
            "plan_state": plan_row.get("state"),
            "last_error": "; ".join(plan_row.get("reasons") or []) if plan_row.get("state") == "ERROR" else None,
            "updated_at": now(),
        }

        if complete and profile:
            old = old_rows.get(lid, {})
            registry["leagues"][lid] = {
                "enabled": bool(old.get("enabled", True)),
                "league_name": profile.get("league_name"),
                "format": profile.get("format"),
                "scoring_signature": profile.get("scoring_signature"),
                "profile_fingerprint": profile.get("profile_fingerprint"),
                "current_refresh": bool(old.get("current_refresh", True)),
                "profile_path": f"data/research/leagues/{lid}/profile.json",
                "research_contract_revision": research_rev,
                "priority": entry["priority"],
                "updated_at": now(),
            }

    write(Path(a.registry), registry)
    write(Path(a.status), status)
    print(f"Registry rebuilt: {len(registry['leagues'])} research-ready league namespace(s)")
    counts: Dict[str, int] = {}
    for r in status["leagues"].values():
        counts[r["status"]] = counts.get(r["status"], 0) + 1
    print("Portfolio status:", ", ".join(f"{k}={v}" for k, v in sorted(counts.items())))


if __name__ == "__main__":
    main()
