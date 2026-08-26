#!/usr/bin/env python3
"""League-ID profile and registry utilities for FIE multi-league research.

Stdlib-only by design so GitHub Actions can build a league identity/profile
before installing or running the heavier research stack.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import re
import urllib.request
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict

try:
    from dst_contract import dst_profile_fields
except Exception:
    dst_profile_fields = None

try:
    from portfolio_rules import load_portfolio_config, entry_for
except Exception:
    load_portfolio_config = None
    entry_for = None

SCHEMA_VERSION = 2
LEAGUE_ID_RE = re.compile(r"^[0-9]{6,32}$")
FORMATS = {
    "AUTO", "REDRAFT", "DYNASTY", "CHOPPED",
    "REDRAFT_BESTBALL", "DYNASTY_BESTBALL",
}

# Sleeper settings include operational/progress fields (for example leg,
# daily_waivers_last_ran and last_chopped_leg). They must never invalidate a
# research model. Only structural/valuation settings belong in the contract.
STRUCTURAL_SETTING_KEYS = {
    "type", "best_ball", "waiver_budget", "reserve_slots", "taxi_slots",
    "playoff_teams", "playoff_week_start", "daily_waivers",
    "daily_waivers_days", "waiver_type", "waiver_clear_days",
    "trade_deadline", "taxi_years", "taxi_allow_vets", "taxi_deadline",
    "reserve_allow_na", "reserve_allow_dnr", "reserve_allow_sus",
    "reserve_allow_out", "reserve_allow_doubtful", "reserve_allow_cov",
    "max_keepers", "draft_rounds"
}

def structural_settings(settings: Dict[str, Any] | None) -> Dict[str, Any]:
    settings = settings or {}
    return {k: settings[k] for k in sorted(STRUCTURAL_SETTING_KEYS) if k in settings}

def structural_contract(league_id: str, fmt: str, scoring: Dict[str, Any], roster_positions: list[Any], settings: Dict[str, Any], total_rosters: Any, season: Any, season_type: Any, constraints: list[Any] | None = None) -> Dict[str, Any]:
    c = {
        "league_id": league_id,
        "format": fmt,
        "scoring_settings": scoring or {},
        "roster_positions": roster_positions or [],
        "structural_settings": structural_settings(settings),
        "total_rosters": total_rosters,
        "season": season,
        "season_type": season_type,
    }
    if constraints:
        c["research_constraints"] = list(constraints)
    return c


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def require_league_id(value: str) -> str:
    value = str(value or "").strip()
    if not LEAGUE_ID_RE.fullmatch(value):
        raise SystemExit("league_id must contain only 6-32 digits")
    return value


def canonical_json(value: Any) -> str:
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=True)


def sha256_json(value: Any) -> str:
    return hashlib.sha256(canonical_json(value).encode("utf-8")).hexdigest()


def scoring_signature(scoring: Dict[str, Any]) -> str:
    """Match research/fie_research.py scoring_signature exactly."""
    return hashlib.sha256(canonical_json(scoring or {}).encode("utf-8")).hexdigest()[:16]


def fetch_json(url: str, timeout: int = 20) -> Dict[str, Any]:
    req = urllib.request.Request(
        url,
        headers={"User-Agent": "Fantasy-Intelligence-Engine-MultiLeague/1.0", "Accept": "application/json"},
    )
    with urllib.request.urlopen(req, timeout=timeout) as response:
        if response.status != 200:
            raise RuntimeError(f"Sleeper returned HTTP {response.status}")
        return json.loads(response.read().decode("utf-8"))


def infer_format(league: Dict[str, Any], requested: str) -> str:
    requested = (requested or "AUTO").upper()
    if requested not in FORMATS:
        raise SystemExit(f"Unsupported format {requested!r}")
    if requested != "AUTO":
        return requested
    settings = league.get("settings") or {}
    league_type = str(league.get("type") or "").lower()
    name = str(league.get("name") or "").lower()

    # Sleeper introduced a native Chopped format.  Live league payloads use
    # settings.type == 3 for Chopped, settings.type == 2 for Dynasty, and
    # settings.type == 0 for ordinary Redraft.  Name heuristics remain a
    # backwards-compatible fallback for older/fixture payloads only.
    raw_type = settings.get("type")
    try:
        type_code = int(raw_type)
    except (TypeError, ValueError):
        type_code = None
    is_chopped = bool(
        type_code == 3
        or settings.get("last_chopped_leg") is not None
        or any(token in name for token in ("chopped", "guillotine", "eliminator", "elimination league", "chop league"))
    )
    is_dynasty = bool(type_code == 2 or "dynasty" in league_type or "dynasty" in name)
    is_best_ball = bool(settings.get("best_ball") in (1, 2, "1", "2") or "best ball" in name or "bestball" in name)
    if is_chopped:
        return "CHOPPED"
    if is_dynasty and is_best_ball:
        return "DYNASTY_BESTBALL"
    if is_best_ball:
        return "REDRAFT_BESTBALL"
    if is_dynasty:
        return "DYNASTY"
    return "REDRAFT"


def build_profile(league_id: str, requested_format: str = "AUTO", league_json: Dict[str, Any] | None = None, portfolio_entry: Dict[str, Any] | None = None) -> Dict[str, Any]:
    league_id = require_league_id(league_id)
    league = league_json or fetch_json(f"https://api.sleeper.app/v1/league/{league_id}")
    if str(league.get("league_id") or league_id) != league_id:
        raise RuntimeError("Sleeper response league_id does not match requested league")
    scoring = league.get("scoring_settings") or {}
    roster_positions = league.get("roster_positions") or []
    settings = league.get("settings") or {}
    fmt = infer_format(league, requested_format)

    constraints = list((portfolio_entry or {}).get("research_constraints") or [])
    league_contract = structural_contract(league_id, fmt, scoring, roster_positions, settings, league.get("total_rosters"), league.get("season"), league.get("season_type"), constraints)

    profile = {
        "schema_version": SCHEMA_VERSION,
        "league_id": league_id,
        "league_name": league.get("name"),
        "season": league.get("season"),
        "season_type": league.get("season_type"),
        "format": fmt,
        "format_source": "manual" if requested_format.upper() != "AUTO" else "auto",
        "total_rosters": league.get("total_rosters"),
        "roster_positions": roster_positions,
        "settings": settings,
        "structural_settings": structural_settings(settings),
        "scoring_settings": scoring,
        "scoring_signature": scoring_signature(scoring),
        "profile_fingerprint": sha256_json(league_contract),
        "captured_at": utc_now(),
        "source": "Sleeper league API",
    }
    if dst_profile_fields:
        profile.update(dst_profile_fields(profile))
    if constraints:
        profile["research_constraints"] = constraints
    if portfolio_entry:
        profile["portfolio"] = {
            "priority": portfolio_entry.get("priority"),
            "alias": portfolio_entry.get("alias"),
            "managed": True,
        }
    return profile


def load_json(path: Path, default: Any = None) -> Any:
    if not path.exists():
        return default
    with path.open("r", encoding="utf-8") as f:
        return json.load(f)


def write_json(path: Path, value: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_suffix(path.suffix + ".tmp")
    with tmp.open("w", encoding="utf-8") as f:
        json.dump(value, f, indent=2, sort_keys=True)
        f.write("\n")
    tmp.replace(path)


def update_registry(registry_path: Path, profile: Dict[str, Any], current_refresh: bool = True) -> Dict[str, Any]:
    reg = load_json(registry_path, {"schema_version": SCHEMA_VERSION, "leagues": {}})
    if not isinstance(reg, dict):
        reg = {"schema_version": SCHEMA_VERSION, "leagues": {}}
    reg.setdefault("schema_version", SCHEMA_VERSION)
    reg.setdefault("leagues", {})
    lid = profile["league_id"]
    existing = reg["leagues"].get(lid, {})
    reg["leagues"][lid] = {
        **existing,
        "enabled": True,
        "league_name": profile.get("league_name"),
        "format": profile.get("format"),
        "scoring_signature": profile.get("scoring_signature"),
        "profile_fingerprint": profile.get("profile_fingerprint"),
        "dst_enabled": bool(profile.get("dst_enabled")),
        "dst_starter_slots": int(profile.get("dst_starter_slots") or 0),
        "dst_scoring_signature": profile.get("dst_scoring_signature"),
        "dst_roster_signature": profile.get("dst_roster_signature"),
        "current_refresh": bool(current_refresh),
        "profile_path": f"data/research/leagues/{lid}/profile.json",
        "updated_at": utc_now(),
    }
    reg["updated_at"] = utc_now()
    write_json(registry_path, reg)
    return reg



def build_legacy_profile(league_id: str, requested_format: str, m1_bundle: Dict[str, Any]) -> Dict[str, Any]:
    """Build a migration profile whose scoring is the exact scoring embedded in legacy M1.

    Current Sleeper metadata is used for roster/name context, but historical scoring is
    never silently replaced. A mismatch is recorded so governance can stay fail-closed.
    """
    league_id=require_league_id(league_id)
    live=fetch_json(f"https://api.sleeper.app/v1/league/{league_id}")
    historical_scoring=((m1_bundle.get("scoring") or {}).get("settings") or {})
    embedded_id=str(((m1_bundle.get("scoring") or {}).get("provenance") or {}).get("league_id") or "")
    if embedded_id and embedded_id != league_id:
        raise SystemExit(f"legacy M1 belongs to league {embedded_id}, not requested {league_id}")
    fmt=infer_format(live, requested_format)
    live_scoring=live.get("scoring_settings") or {}
    league_contract=structural_contract(league_id, fmt, historical_scoring, live.get("roster_positions") or [], live.get("settings") or {}, live.get("total_rosters"), live.get("season"), live.get("season_type"))
    hist_sig=scoring_signature(historical_scoring); live_sig=scoring_signature(live_scoring)
    profile = {
        "schema_version":SCHEMA_VERSION,"league_id":league_id,"league_name":live.get("name"),
        "season":live.get("season"),"season_type":live.get("season_type"),"format":fmt,
        "format_source":"manual" if requested_format.upper()!="AUTO" else "auto",
        "total_rosters":live.get("total_rosters"),"roster_positions":live.get("roster_positions") or [],
        "settings":live.get("settings") or {},"structural_settings":structural_settings(live.get("settings") or {}),"scoring_settings":historical_scoring,
        "scoring_signature":hist_sig,"profile_fingerprint":sha256_json(league_contract),
        "captured_at":utc_now(),"source":"legacy M1 scoring + current Sleeper metadata",
        "migration":{"type":"legacy_single_profile","embedded_league_id":embedded_id or None,
          "current_sleeper_scoring_signature":live_sig,"historical_scoring_matches_current":hist_sig==live_sig},
    }
    if dst_profile_fields:
        profile.update(dst_profile_fields(profile))
    return profile

def cmd_legacy(args: argparse.Namespace) -> None:
    m1=load_json(Path(args.m1_bundle), {})
    prov=((m1.get("scoring") or {}).get("provenance") or {})
    lid=args.league_id or prov.get("league_id")
    if not lid: raise SystemExit("Could not infer legacy League ID from M1; provide --league-id")
    profile=build_legacy_profile(str(lid), args.format, m1)
    write_json(Path(args.output),profile)
    update_registry(Path(args.registry),profile,current_refresh=not args.disable_current_refresh)
    print(f"Wrote legacy migration profile for {profile['league_id']} format={profile['format']}")
    print(f"historical_scoring_matches_current={profile['migration']['historical_scoring_matches_current']}")

def cmd_build(args: argparse.Namespace) -> None:
    portfolio_entry = None
    if getattr(args, "portfolio_config", None) and load_portfolio_config and entry_for:
        cfg_path = Path(args.portfolio_config)
        if cfg_path.exists():
            cfg = load_portfolio_config(cfg_path)
            portfolio_entry = entry_for(cfg, args.league_id)
            if portfolio_entry and args.format == "AUTO":
                args.format = portfolio_entry.get("format") or args.format
    profile = build_profile(args.league_id, args.format, portfolio_entry=portfolio_entry)
    out = Path(args.output)
    write_json(out, profile)
    update_registry(Path(args.registry), profile, current_refresh=not args.disable_current_refresh)
    print(f"Wrote {out} for league {profile['league_id']} format={profile['format']}")
    print(f"scoring_signature={profile['scoring_signature']}")
    print(f"profile_fingerprint={profile['profile_fingerprint']}")


def cmd_fixture(args: argparse.Namespace) -> None:
    fixture = {
        "league_id": args.league_id,
        "name": "Fixture League",
        "season": "2026",
        "season_type": "regular",
        "total_rosters": 12,
        "roster_positions": ["QB", "RB", "RB", "WR", "WR", "TE", "FLEX", "BN", "BN"],
        "settings": {"best_ball": 0},
        "scoring_settings": {"pass_yd": 0.04, "pass_td": 4, "rec": 1, "rush_yd": 0.1, "rush_td": 6},
    }
    profile = build_profile(args.league_id, args.format, fixture)
    write_json(Path(args.output), profile)
    update_registry(Path(args.registry), profile)
    print(json.dumps(profile, indent=2, sort_keys=True))


def main() -> None:
    p = argparse.ArgumentParser()
    sub = p.add_subparsers(dest="cmd", required=True)
    b = sub.add_parser("build")
    b.add_argument("--league-id", required=True)
    b.add_argument("--format", default="AUTO", choices=sorted(FORMATS))
    b.add_argument("--output", required=True)
    b.add_argument("--registry", default="data/research/leagues/registry.json")
    b.add_argument("--portfolio-config", default=None, help="Optional managed-portfolio config; custom constraints become part of the research fingerprint")
    b.add_argument("--disable-current-refresh", action="store_true")
    b.set_defaults(func=cmd_build)
    f = sub.add_parser("fixture")
    f.add_argument("--league-id", default="123456789012345678")
    f.add_argument("--format", default="REDRAFT", choices=sorted(FORMATS))
    f.add_argument("--output", required=True)
    f.add_argument("--registry", required=True)
    f.set_defaults(func=cmd_fixture)
    l = sub.add_parser("legacy")
    l.add_argument("--league-id", default=None)
    l.add_argument("--format", default="AUTO", choices=sorted(FORMATS))
    l.add_argument("--m1-bundle", default="data/research/milestone1.json")
    l.add_argument("--output", required=True)
    l.add_argument("--registry", default="data/research/leagues/registry.json")
    l.add_argument("--disable-current-refresh", action="store_true")
    l.set_defaults(func=cmd_legacy)
    args = p.parse_args()
    args.func(args)


if __name__ == "__main__":
    main()
