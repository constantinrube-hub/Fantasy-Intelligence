#!/usr/bin/env python3
"""Reconcile stale current snapshots with freshly rebuilt league profiles.

Used by the all-league research publisher after restoring league artifacts.

Important boundaries:
- It never changes a research profile or its fingerprint.
- It rebuilds only an EXISTING current snapshot whose captured Sleeper structural
  contract no longer matches the current profile.
- It never weakens structural fingerprint validation.
- After any rebuilds it deduplicates current storage, rebuilds governance for the
  changed leagues, then runs the same storage/profile integrity gates used by the
  production current workflow.
"""
from __future__ import annotations

import argparse
import json
import subprocess
import sys
from pathlib import Path
from typing import Optional

from current_snapshot_storage import load_current_snapshot
from league_profile import structural_contract, sha256_json

ROOT=Path(__file__).resolve().parents[1]
LEAGUES=ROOT/"data"/"research"/"leagues"


def load_json(path:Path)->dict:
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return {}


def captured_structural_fingerprint(profile:dict,current:dict)->Optional[str]:
    pf=((current.get("scoring_provenance") or {}).get("profile_fields") or {})
    if not pf:
        return None
    contract=structural_contract(
        str(profile.get("league_id") or ""),
        profile.get("format"),
        current.get("scoring_settings") or profile.get("scoring_settings") or {},
        pf.get("roster_positions") or [],
        pf.get("settings") or {},
        pf.get("total_rosters"),
        pf.get("season"),
        pf.get("season_type"),
        profile.get("research_constraints") or [],
    )
    return sha256_json(contract)


def existing_current_needs_rebuild(profile_path:Path,current_path:Path)->tuple[bool,str]:
    if not profile_path.is_file() or not current_path.is_file():
        return False,"missing_profile_or_current"
    profile=load_json(profile_path)
    try:
        current=load_current_snapshot(current_path,root=ROOT)
    except Exception as exc:
        return True,f"current_hydration_failed:{type(exc).__name__}"
    got=captured_structural_fingerprint(profile,current)
    if got is None:
        # Preserve historical behavior for snapshots without captured live-profile
        # provenance. This reconciler is intentionally not a new-current builder.
        return False,"no_captured_profile_fields"
    expected=profile.get("profile_fingerprint")
    if got != expected:
        return True,f"captured={got} profile={expected}"
    return False,"match"


def run(args:list[str])->None:
    print("+"," ".join(args),flush=True)
    subprocess.run(args,cwd=ROOT,check=True)


def rebuild_current(lid:str,season:Optional[int])->None:
    lr=LEAGUES/lid
    profile=lr/"profile.json"
    current=lr/"current"/"milestone5_current.json"

    for validator,bundle in [
        ("validate_m4_bundle.py","milestone4.json"),
        ("validate_m5_bundle.py","milestone5.json"),
        ("validate_m6_bundle.py","milestone6.json"),
    ]:
        run([sys.executable,str(ROOT/"research"/validator),str(lr/bundle)])

    cmd=[
        sys.executable,str(ROOT/"research"/"build_current_snapshot.py"),
        "--league-id",lid,
        "--league-profile",str(profile),
        "--m4-bundle",str(lr/"milestone4.json"),
        "--m5-bundle",str(lr/"milestone5.json"),
        "--m6-bundle",str(lr/"milestone6.json"),
        "--cache-dir",str(ROOT/".cache"/"fie-current"/"leagues"/lid),
        "--sleeper-archive",str(ROOT/"data"/"research"/"market"/"sleeper"),
        "--output",str(current),
    ]
    if season is not None:
        cmd += ["--season",str(season)]
    run(cmd)

    # If Sleeper changed structurally again between the research profile capture
    # and this current rebuild, remain fail-closed and require another research run.
    needs,reason=existing_current_needs_rebuild(profile,current)
    if needs:
        raise SystemExit(
            f"{lid}: current snapshot still does not match rebuilt research profile "
            f"after refresh ({reason})"
        )


def rebuild_governance(lid:str)->None:
    lr=LEAGUES/lid
    run([
        sys.executable,str(ROOT/"research"/"fie_governance.py"),
        "--league-id",lid,
        "--league-profile",str(lr/"profile.json"),
        "--m4-bundle",str(lr/"milestone4.json"),
        "--m5-bundle",str(lr/"milestone5.json"),
        "--m6-bundle",str(lr/"milestone6.json"),
        "--current-snapshot",str(lr/"current"/"milestone5_current.json"),
        "--operator-override",str(lr/"governance"/"operator_override.json"),
        "--global-operator-override",str(ROOT/"data"/"research"/"governance"/"operator_override.json"),
        "--output",str(lr/"governance"/"active_release.json"),
    ])


def main()->None:
    ap=argparse.ArgumentParser()
    ap.add_argument("--season",type=int,default=None)
    args=ap.parse_args()

    registry=load_json(LEAGUES/"registry.json")
    enabled=[
        str(lid) for lid,row in sorted((registry.get("leagues") or {}).items())
        if row.get("enabled",True)
    ]

    stale=[]
    for lid in enabled:
        profile=LEAGUES/lid/"profile.json"
        current=LEAGUES/lid/"current"/"milestone5_current.json"
        needs,reason=existing_current_needs_rebuild(profile,current)
        if needs:
            stale.append((lid,reason))

    if stale:
        print("Current/profile structural mismatches requiring refresh:")
        for lid,reason in stale:
            print(f"  {lid}: {reason}")
    else:
        print("No existing current/profile structural mismatches.")

    rebuilt=[]
    for lid,_ in stale:
        rebuild_current(lid,args.season)
        rebuilt.append(lid)

    # All-league artifacts may contain legacy full current snapshots. Normalize
    # every existing current snapshot to the canonical shared-base/overlay format
    # before release_build.py executes its fail-closed storage gate.
    run([sys.executable,str(ROOT/"research"/"deduplicate_current_snapshots.py")])

    # A refreshed current snapshot changes the governance input. Rebuild only the
    # affected leagues and preserve their existing operator mode/override behavior.
    for lid in rebuilt:
        rebuild_governance(lid)

    run([sys.executable,str(ROOT/"research"/"integrity_current_storage_test.py")])
    run([sys.executable,str(ROOT/"research"/"integrity_v932_structural_profile_test.py")])

    print(
        f"PASS current/profile reconciliation enabled={len(enabled)} "
        f"rebuilt={len(rebuilt)}"
    )


if __name__=="__main__":
    main()
