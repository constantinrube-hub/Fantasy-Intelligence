#!/usr/bin/env python3
"""Permanent FIE V8.8-M6 runtime governance and rollback manifest.

AUTO promotes only when every required artifact is compatible and fresh. CONTROL
hard-disables all M5/M6 overrides while keeping the app functional on the frozen
V8.2.2 live path. The operator override is versioned in Git so rollback is auditable.
"""
from __future__ import annotations

import argparse
import json
import hashlib
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional

ACTIVE_BUILD = "V8.8-M6"
CONTROL_BUILD = "V8.2.2"


def now() -> datetime: return datetime.now(timezone.utc)
def iso() -> str: return now().isoformat()

def load(path: str) -> dict:
    p=Path(path)
    return json.loads(p.read_text()) if p.exists() else {}

def write(path: str, obj: dict):
    p=Path(path);p.parent.mkdir(parents=True,exist_ok=True);p.write_text(json.dumps(obj,indent=2,allow_nan=False))

def sha256_file(path: str) -> Optional[str]:
    p=Path(path)
    if not p.exists(): return None
    h=hashlib.sha256()
    with p.open("rb") as f:
        for chunk in iter(lambda:f.read(1024*1024), b""):
            h.update(chunk)
    return h.hexdigest()

def parse_time(v) -> Optional[datetime]:
    if not v:return None
    try:return datetime.fromisoformat(str(v).replace("Z","+00:00")).astimezone(timezone.utc)
    except Exception:return None

def snapshot_age_hours(cur: dict) -> Optional[float]:
    t=parse_time(cur.get("generated_at"))
    return (now()-t).total_seconds()/3600 if t else None

def effective_mode(override: dict, cli_mode: str) -> str:
    if cli_mode in {"AUTO","CONTROL"}:return cli_mode
    mode=str(override.get("mode") or "AUTO").upper()
    return mode if mode in {"AUTO","CONTROL"} else "CONTROL"

def build(args) -> dict:
    m4=load(args.m4_bundle);m5=load(args.m5_bundle);m6=load(args.m6_bundle);cur=load(args.current_snapshot);ov=load(args.operator_override)
    mode=effective_mode(ov,args.mode)
    age=snapshot_age_hours(cur);max_age=float(cur.get("snapshot_max_age_hours") or args.max_age_hours)
    sig5=m5.get("scoring_signature");sigc=cur.get("scoring_signature");sig6=m6.get("scoring_signature")
    checks={
      "operator_auto": mode=="AUTO",
      "m4_complete": m4.get("status")=="complete",
      "m5_complete": m5.get("status")=="complete",
      "m6_complete": m6.get("status")=="complete",
      "current_complete": str(cur.get("status") or "").lower() in {"complete","ready","active"},
      "current_producer": cur.get("producer_build")==ACTIVE_BUILD,
      "current_contract": cur.get("m5_build")=="V8.7-M5",
      "scoring_signature_match": bool(sig5 and sigc and sig5==sigc and (not sig6 or sig6==sig5)),
      "fresh_snapshot": age is not None and age>=0 and age<=max_age,
      "target_week_leakage_guard": cur.get("target_week_realised_stats_excluded") is True,
      "eligible_players": int((cur.get("summary") or {}).get("activation_eligible") or 0)>0,
    }
    enabled=all(checks.values())
    reason="all promotion checks passed" if enabled else "; ".join(k for k,v in checks.items() if not v)
    gates=(m5.get("activation") or {}).get("decision_gates") or {}
    return {
      "schema_version":1,"active_build":ACTIVE_BUILD,"control_build":CONTROL_BUILD,"generated_at":iso(),
      "operator_mode":mode,"runtime_enabled":bool(enabled),"runtime_allow_m5":bool(enabled),"fallback":CONTROL_BUILD,
      "reason":reason,"checks":checks,
      "current_snapshot":{"path":args.current_snapshot,"season":cur.get("season"),"week":cur.get("week"),"generated_at":cur.get("generated_at"),"age_hours":age,"max_age_hours":max_age,"eligible_players":int((cur.get("summary") or {}).get("activation_eligible") or 0)},
      "scoring_signature":sig5,
      "decision_gates":gates,
      "model_lineage":{
        "research_window":str((m4.get("methodology") or {}).get("research_window") or "rollover-safe historical window; see milestone bundles"),
        "time_safe_folds":(m4.get("methodology") or {}).get("time_safe_folds",[]),
        "m4_research_build":m4.get("research_build"),
        "m5_research_build":m5.get("research_build"),
        "m6_research_build":m6.get("research_build"),
        "m4_validated_positions":[r.get("position") for r in (m4.get("final_position_models") or {}).get("aggregate",[]) if r.get("status")=="validated_candidate"],
        "m6_validated_candidate_positions":(m6.get("advanced_second_wave") or {}).get("validated_candidate_positions",[]),
        "artifact_sha256":{
          "milestone4":sha256_file(args.m4_bundle),
          "milestone5":sha256_file(args.m5_bundle),
          "milestone6":sha256_file(args.m6_bundle),
          "current_snapshot":sha256_file(args.current_snapshot),
        },
        "audit_rule":"Feature lists, coefficients, sample sizes and holdout metrics remain versioned in the milestone bundles referenced above; promotion is allowed only through their validated decision gates."
      },
      "rollback":{"mode":"CONTROL","operator_override":args.operator_override,"effect":"All M5/M6 decision overrides disabled; V8.2.2 remains live fallback.","code_change_required":False},
      "promotion":{"mode":"AUTO","rule":"All checks above must pass on every scheduled rebuild; a failed check automatically falls back without editing live scoring functions."},
    }

def parse_args(argv=None):
    p=argparse.ArgumentParser(description="Build FIE permanent runtime governance manifest")
    p.add_argument("--m4-bundle",default="data/research/milestone4.json")
    p.add_argument("--m5-bundle",default="data/research/milestone5.json")
    p.add_argument("--m6-bundle",default="data/research/milestone6.json")
    p.add_argument("--current-snapshot",default="data/research/current/milestone5_current.json")
    p.add_argument("--operator-override",default="data/research/governance/operator_override.json")
    p.add_argument("--output",default="data/research/governance/active_release.json")
    p.add_argument("--mode",choices=["KEEP","AUTO","CONTROL"],default="KEEP")
    p.add_argument("--max-age-hours",type=float,default=18.0)
    p.add_argument("--persist-mode",action="store_true",help="When --mode AUTO/CONTROL is supplied, persist that mode to operator_override.json")
    return p.parse_args(argv)

def main(argv=None):
    a=parse_args(argv)
    if a.persist_mode and a.mode in {"AUTO","CONTROL"}:
        write(a.operator_override,{"schema_version":1,"mode":a.mode,"updated_at":iso(),"note":"Versioned operator runtime override. CONTROL is the emergency rollback switch."})
    b=build(a);write(a.output,b)
    print(f"Wrote {a.output} mode={b['operator_mode']} runtime_enabled={b['runtime_enabled']} reason={b['reason']}")

if __name__=="__main__":main()
