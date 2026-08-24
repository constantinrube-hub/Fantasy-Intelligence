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

SCHEMA_VERSION = 1
LEAGUE_ID_RE = re.compile(r"^[0-9]{6,32}$")
FORMATS = {
    "AUTO", "REDRAFT", "DYNASTY", "CHOPPED",
    "REDRAFT_BESTBALL", "DYNASTY_BESTBALL",
}


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
    # Sleeper has no canonical 'Chopped' league type, so AUTO never guesses it.
    # Best-ball/dynasty hints are used only when explicitly present in metadata.
    league_type = str(league.get("type") or "").lower()
    name = str(league.get("name") or "").lower()
    is_dynasty = bool(settings.get("type") == 2 or "dynasty" in league_type or "dynasty" in name)
    is_best_ball = bool(settings.get("best_ball") == 1 or "best ball" in name or "bestball" in name)
    if is_dynasty and is_best_ball:
        return "DYNASTY_BESTBALL"
    if is_best_ball:
        return "REDRAFT_BESTBALL"
    if is_dynasty:
        return "DYNASTY"
    return "REDRAFT"


def build_profile(league_id: str, requested_format: str = "AUTO", league_json: Dict[str, Any] | None = None) -> Dict[str, Any]:
    league_id = require_league_id(league_id)
    league = league_json or fetch_json(f"https://api.sleeper.app/v1/league/{league_id}")
    if str(league.get("league_id") or league_id) != league_id:
        raise RuntimeError("Sleeper response league_id does not match requested league")
    scoring = league.get("scoring_settings") or {}
    roster_positions = league.get("roster_positions") or []
    settings = league.get("settings") or {}
    fmt = infer_format(league, requested_format)

    league_contract = {
        "league_id": league_id,
        "format": fmt,
        "scoring_settings": scoring,
        "roster_positions": roster_positions,
        "settings": settings,
        "total_rosters": league.get("total_rosters"),
        "season": league.get("season"),
        "season_type": league.get("season_type"),
    }

    return {
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
        "scoring_settings": scoring,
        "scoring_signature": scoring_signature(scoring),
        "profile_fingerprint": sha256_json(league_contract),
        "captured_at": utc_now(),
        "source": "Sleeper league API",
    }


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
    league_contract={
        "league_id":league_id,"format":fmt,"scoring_settings":historical_scoring,
        "roster_positions":live.get("roster_positions") or [],"settings":live.get("settings") or {},
        "total_rosters":live.get("total_rosters"),"season":live.get("season"),"season_type":live.get("season_type"),
    }
    hist_sig=scoring_signature(historical_scoring); live_sig=scoring_signature(live_scoring)
    return {
        "schema_version":SCHEMA_VERSION,"league_id":league_id,"league_name":live.get("name"),
        "season":live.get("season"),"season_type":live.get("season_type"),"format":fmt,
        "format_source":"manual" if requested_format.upper()!="AUTO" else "auto",
        "total_rosters":live.get("total_rosters"),"roster_positions":live.get("roster_positions") or [],
        "settings":live.get("settings") or {},"scoring_settings":historical_scoring,
        "scoring_signature":hist_sig,"profile_fingerprint":sha256_json(league_contract),
        "captured_at":utc_now(),"source":"legacy M1 scoring + current Sleeper metadata",
        "migration":{"type":"legacy_single_profile","embedded_league_id":embedded_id or None,
          "current_sleeper_scoring_signature":live_sig,"historical_scoring_matches_current":hist_sig==live_sig},
    }

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
    profile = build_profile(args.league_id, args.format)
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
