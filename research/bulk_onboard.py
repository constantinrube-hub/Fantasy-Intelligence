#!/usr/bin/env python3
"""Plan FIE bulk portfolio onboarding without mutating research artifacts.

PLAN_ONLY is intentionally safe: it validates all managed leagues, resolves the
Sleeper user/roster and historical league chain, computes the exact prospective
league profile/fingerprint, and emits a build matrix. One failing league is
recorded as ERROR while other leagues remain actionable.
"""
from __future__ import annotations

import argparse
import json
import os
import urllib.parse
import urllib.request
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Callable, Dict, List

from league_profile import build_profile
from portfolio_rules import load_portfolio_config, qualifies_priority

ROOT = Path(__file__).resolve().parents[1]
DEFAULT_REGISTRY = ROOT / "data" / "research" / "leagues" / "registry.json"
REQUIRED = [f"milestone{i}.json" for i in range(1, 7)]


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def load_json(path: Path, default=None):
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return default


def fetch_any(url: str, timeout: int = 20) -> Any:
    req = urllib.request.Request(url, headers={"User-Agent": "Fantasy-Intelligence-Bulk-Onboard/1.0", "Accept": "application/json"})
    with urllib.request.urlopen(req, timeout=timeout) as r:
        if r.status != 200:
            raise RuntimeError(f"Sleeper returned HTTP {r.status} for {url}")
        return json.loads(r.read().decode("utf-8"))


def resolve_user(username: str, fetcher: Callable[[str], Any] = fetch_any) -> Dict[str, Any]:
    user = fetcher(f"https://api.sleeper.app/v1/user/{urllib.parse.quote(username)}")
    if not isinstance(user, dict) or not user.get("user_id"):
        raise RuntimeError(f"Sleeper user {username!r} could not be resolved")
    return user


def league_history(league: Dict[str, Any], fetcher: Callable[[str], Any], limit: int = 12) -> List[Dict[str, Any]]:
    out: List[Dict[str, Any]] = []
    seen = {str(league.get("league_id") or "")}
    prev = str(league.get("previous_league_id") or "").strip()
    while prev and prev != "0" and prev not in seen and len(out) < limit:
        seen.add(prev)
        try:
            row = fetcher(f"https://api.sleeper.app/v1/league/{prev}")
        except Exception as exc:
            out.append({"league_id": prev, "error": str(exc)})
            break
        if not isinstance(row, dict):
            out.append({"league_id": prev, "error": "non-object Sleeper response"})
            break
        out.append({"league_id": str(row.get("league_id") or prev), "season": row.get("season"), "name": row.get("name")})
        prev = str(row.get("previous_league_id") or "").strip()
    return out


def research_state(league_id: str, prospective: Dict[str, Any], research_root: Path) -> tuple[str, List[str]]:
    root = research_root / league_id
    profile_path = root / "profile.json"
    existing = load_json(profile_path, {}) or {}
    reasons: List[str] = []
    if not profile_path.exists():
        return "NEW", ["no existing League-ID research profile"]
    if str(existing.get("profile_fingerprint") or "") != str(prospective.get("profile_fingerprint") or ""):
        reasons.append("research-relevant profile fingerprint changed")
        if str(existing.get("scoring_signature") or "") != str(prospective.get("scoring_signature") or ""):
            reasons.append("scoring signature changed")
        if existing.get("research_constraints") != prospective.get("research_constraints"):
            reasons.append("custom cohort/roster constraints changed")
        return "PROFILE_CHANGED", reasons
    missing = [name for name in REQUIRED if not (root / name).exists()]
    if missing:
        return "NEW", ["historical bundle incomplete: " + ", ".join(missing)]
    m5 = load_json(root / "milestone5.json", {}) or {}
    if int(m5.get("contract_revision") or 0) < 4:
        return "PROFILE_CHANGED", ["historical research contract predates M5 R4"]
    current = root / "current" / "milestone5_current.json"
    governance = root / "governance" / "active_release.json"
    if not current.exists() or not governance.exists():
        return "REFRESH_ONLY", ["historical R4 research is current; current-season snapshot/governance missing"]
    return "CURRENT", ["profile and M1-M6 R4 research match the live league"]


def inspect_league(entry: Dict[str, Any], user_id: str, fetcher: Callable[[str], Any], research_root: Path) -> Dict[str, Any]:
    lid = entry["league_id"]
    result: Dict[str, Any] = {
        "league_id": lid,
        "format": entry["format"],
        "priority": entry["priority"],
        "alias": entry.get("alias"),
        "research_constraints": entry.get("research_constraints") or [],
        "state": "ERROR",
        "reasons": [],
    }
    try:
        league = fetcher(f"https://api.sleeper.app/v1/league/{lid}")
        if not isinstance(league, dict) or str(league.get("league_id") or lid) != lid:
            raise RuntimeError("Sleeper league response did not match the requested League ID")
        rosters = fetcher(f"https://api.sleeper.app/v1/league/{lid}/rosters")
        drafts = fetcher(f"https://api.sleeper.app/v1/league/{lid}/drafts")
        rosters = rosters if isinstance(rosters, list) else []
        drafts = drafts if isinstance(drafts, list) else []
        mine = [r for r in rosters if str(r.get("owner_id") or "") == str(user_id) or str(user_id) in [str(x) for x in (r.get("co_owners") or [])]]
        if not mine:
            raise RuntimeError("configured Sleeper user is not an owner/co-owner in this league")
        prospective = build_profile(lid, entry["format"], league_json=league, portfolio_entry=entry)
        state, reasons = research_state(lid, prospective, research_root)
        history = league_history(league, fetcher)
        result.update({
            "state": state,
            "reasons": reasons,
            "league_name": league.get("name"),
            "season": league.get("season"),
            "season_type": league.get("season_type"),
            "status": league.get("status"),
            "total_rosters": league.get("total_rosters"),
            "user_roster_ids": [r.get("roster_id") for r in mine],
            "profile_fingerprint": prospective.get("profile_fingerprint"),
            "scoring_signature": prospective.get("scoring_signature"),
            "drafts": [{"draft_id": str(d.get("draft_id") or ""), "status": d.get("status"), "season": d.get("season"), "type": d.get("type")} for d in drafts],
            "previous_leagues": history,
        })
    except Exception as exc:
        result["state"] = "ERROR"
        result["reasons"] = [str(exc)]
    return result


def build_plan(config_path: Path, registry_path: Path, priority_cutoff: str, fetcher: Callable[[str], Any] = fetch_any) -> Dict[str, Any]:
    cfg = load_portfolio_config(config_path)
    user = resolve_user(cfg["sleeper_username"], fetcher)
    research_root = registry_path.parent
    rows = [inspect_league(entry, str(user["user_id"]), fetcher, research_root) for entry in cfg["leagues"] if entry.get("enabled", True)]
    rows.sort(key=lambda r: ({"VERY_HIGH": 4, "HIGH": 3, "MEDIUM": 2, "LOW": 1}.get(r["priority"], 0) * -1, r["league_id"]))
    build_rows = [r for r in rows if r["state"] in {"NEW", "PROFILE_CHANGED"} and qualifies_priority(r["priority"], priority_cutoff)]
    refresh_rows = [r for r in rows if r["state"] in {"CURRENT", "REFRESH_ONLY"}]
    errors = [r for r in rows if r["state"] == "ERROR"]
    counts: Dict[str, int] = {}
    for r in rows:
        counts[r["state"]] = counts.get(r["state"], 0) + 1
    matrix = {"include": [{"league_id": r["league_id"], "format": r["format"], "priority": r["priority"]} for r in build_rows]}
    return {
        "schema_version": 1,
        "generated_at": utc_now(),
        "config_path": str(config_path),
        "sleeper_username": cfg["sleeper_username"],
        "sleeper_user_id": str(user["user_id"]),
        "priority_cutoff": priority_cutoff,
        "counts": counts,
        "requested": len(rows),
        "build_required": len(build_rows),
        "refresh_candidates": len(refresh_rows),
        "errors": len(errors),
        "build_matrix": matrix,
        "leagues": rows,
    }


def markdown_summary(plan: Dict[str, Any]) -> str:
    lines = [
        "# FIE Bulk Portfolio Plan",
        "",
        f"Managed leagues: **{plan['requested']}**  ",
        f"Build required at selected priority cutoff: **{plan['build_required']}**  ",
        f"Errors requiring attention: **{plan['errors']}**",
        "",
        "| Priority | League | Format | State | Reason |",
        "|---|---|---|---|---|",
    ]
    for r in plan["leagues"]:
        name = str(r.get("league_name") or r.get("alias") or r["league_id"]).replace("|", "/")
        reason = "; ".join(r.get("reasons") or []).replace("|", "/")
        lines.append(f"| {r['priority'].replace('_',' ')} | {name} `{r['league_id']}` | {r['format']} | **{r['state']}** | {reason} |")
    return "\n".join(lines) + "\n"


def write_github_outputs(plan: Dict[str, Any]) -> None:
    path = os.environ.get("GITHUB_OUTPUT")
    if not path:
        return
    matrix = json.dumps(plan["build_matrix"], separators=(",", ":"))
    with open(path, "a", encoding="utf-8") as f:
        f.write(f"matrix={matrix}\n")
        f.write(f"has_builds={'true' if plan['build_required'] else 'false'}\n")
        f.write(f"error_count={plan['errors']}\n")
        f.write(f"managed_count={plan['requested']}\n")


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("command", choices=["plan"])
    ap.add_argument("--config", default=str(ROOT / "config" / "league-portfolio.json"))
    ap.add_argument("--registry", default=str(DEFAULT_REGISTRY))
    ap.add_argument("--priority-cutoff", default="ALL", choices=["VERY_HIGH", "HIGH", "MEDIUM", "LOW", "ALL"])
    ap.add_argument("--output", required=True)
    ap.add_argument("--summary")
    args = ap.parse_args()
    plan = build_plan(Path(args.config), Path(args.registry), args.priority_cutoff)
    out = Path(args.output); out.parent.mkdir(parents=True, exist_ok=True); out.write_text(json.dumps(plan, indent=2) + "\n", encoding="utf-8")
    summary = markdown_summary(plan)
    print(summary)
    if args.summary:
        Path(args.summary).write_text(summary, encoding="utf-8")
    write_github_outputs(plan)


if __name__ == "__main__":
    main()
