#!/usr/bin/env python3
"""Run the complete Tranche 1 characterization suite and save one artifact."""
from __future__ import annotations
import argparse,json,subprocess,sys,os
from pathlib import Path
from datetime import datetime,timezone
ROOT=Path(__file__).resolve().parents[1]
CFG=json.loads((ROOT/"config/tranche1-characterization.json").read_text(encoding="utf-8"))
TESTS=[
 ["node","research/integrity_tranche1_six_format_runtime_characterization.js"],
 ["node","research/integrity_tranche1_all_league_runtime_profiles.js"],
 ["node","research/integrity_tranche1_replacement_parity_characterization.js"],
 ["node","research/integrity_tranche1_data_client_scope_characterization.js"],
 [sys.executable,"research/integrity_tranche1_direct_fetch_allowlist.py"],
 [sys.executable,"research/integrity_tranche1_research_stage_identity.py"],
 [sys.executable,"research/integrity_tranche1_responsive_decision_visibility.py"],
]
def run(cmd):
    p=subprocess.run(cmd,cwd=ROOT,text=True,capture_output=True)
    return {"cmd":cmd,"returncode":p.returncode,"ok":p.returncode==0,"stdout":p.stdout,"stderr":p.stderr}
def git(*args):
    p=subprocess.run(["git",*args],cwd=ROOT,text=True,capture_output=True,check=True);return p.stdout.strip()
def main():
    ap=argparse.ArgumentParser();ap.add_argument("--mode",choices=["baseline","target"],default="baseline");ap.add_argument("--output-dir",default="artifacts/tranche1");a=ap.parse_args()
    if os.getenv("GITHUB_REF_NAME") and os.getenv("GITHUB_REF_NAME")!=CFG["implementation_branch"]:
        raise SystemExit(f"wrong branch: {os.getenv('GITHUB_REF_NAME')}")
    head=git("rev-parse","HEAD");tr0=CFG["tranche0_head"]
    subprocess.run(["git","merge-base","--is-ancestor",tr0,head],cwd=ROOT,check=True)
    changed=[x for x in git("diff","--name-only",f"{tr0}..HEAD").splitlines() if x]
    unexpected=sorted(set(changed)-set(CFG["allowed_tranche1_changes"]))
    if unexpected: raise SystemExit("unexpected changes after Tranche 0:\n- "+"\n- ".join(unexpected))
    results=[]
    for base in TESTS:
        cmd=[*base,"--mode",a.mode]
        r=run(cmd);results.append(r)
        print(("PASS" if r["ok"] else "FAIL")," ".join(cmd))
        if r["stdout"]: print(r["stdout"][-8000:])
        if r["stderr"]: print(r["stderr"][-8000:],file=sys.stderr)
    out=ROOT/a.output_dir;out.mkdir(parents=True,exist_ok=True)
    report={"schema":"fie-tranche1-characterization-result-v1","generated_at":datetime.now(timezone.utc).isoformat(),"mode":a.mode,"tranche0_head":tr0,"head_commit":head,"changes_vs_tranche0":changed,"unexpected_changes":unexpected,"tests":results,"pass":all(x["ok"] for x in results) and not unexpected}
    (out/"tranche1-characterization.json").write_text(json.dumps(report,indent=2)+"\n",encoding="utf-8")
    lines=["# FIE Controlled Implementation — Tranche 1 Characterization",f"",f"- Mode: **{a.mode}**",f"- Tranche 0 head: `{tr0}`",f"- Harness HEAD: `{head}`",f"- Overall: **{'PASS' if report['pass'] else 'FAIL'}**","","## Characterization checks",""]
    for r in results:
        marker="PASS" if r["ok"] else "FAIL";first=next((x for x in r["stdout"].splitlines() if "KNOWN_GAP_REPRODUCED" in x),"")
        lines.append(f"- {marker} — `{' '.join(r['cmd'])}`{(' — '+first) if first else ''}")
    lines += ["","Baseline mode is intentionally green only when audited known gaps are reproduced exactly and positive guards remain intact.","No production model/runtime semantics or statistical thresholds are changed by this tranche."]
    (out/"tranche1-characterization.md").write_text("\n".join(lines)+"\n",encoding="utf-8")
    return 0 if report["pass"] else 1
if __name__=="__main__":raise SystemExit(main())
