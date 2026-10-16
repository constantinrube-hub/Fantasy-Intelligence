#!/usr/bin/env python3
"""Capture exact source bytes for Tranche 3C / C10-007 player identity."""
from __future__ import annotations
import argparse, hashlib, json, shutil, subprocess
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
FILES=[
    "app/core/core-services.js",
    "app/current-player-features.js",
    "app/current-snapshot-store.js",
    "app/decision-model-v9.js",
    "app/decision-engines.js",
    "app/value-finder.js",
    "app/dst-intelligence.js",
    "app/kicker-intelligence.js",
    "app/core/special-teams-series.js",
    "app/core/data-client.js",
    "app/core/research-report-service.js",
    "app/generated/runtime-contracts.js",
    "config/contracts/runtime-contracts.json",
    "research/integrity_tranche3c_player_identity.js",
    "research/integrity_tranche1_research_stage_identity.py",
    "research/current_snapshot_storage.py",
    "research/build_app_manifest.py",
    "research/release_gate.py",
    "tools/build_dist.py",
    "tools/release_build.py",
]
def sha256(path:Path)->str:
    h=hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda:f.read(1024*1024),b""):
            h.update(chunk)
    return h.hexdigest()
def git(*args):
    return subprocess.check_output(["git",*args],cwd=ROOT,text=True).strip()
def main():
    ap=argparse.ArgumentParser()
    ap.add_argument("--output-dir",default="artifacts/tranche3c/preflight-source")
    a=ap.parse_args()
    out=ROOT/a.output_dir
    if out.exists():shutil.rmtree(out)
    out.mkdir(parents=True)
    rows=[]
    for rel in FILES:
        src=ROOT/rel
        if not src.exists():
            raise SystemExit(f"missing Tranche 3C capture source: {rel}")
        dst=out/rel;dst.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(src,dst)
        rows.append({"path":rel,"bytes":src.stat().st_size,"sha256":sha256(src)})
    manifest={
        "schema_version":1,
        "tranche":"3C",
        "change_package":"C10-007",
        "phase":"preflight_source_capture",
        "head":git("rev-parse","HEAD"),
        "tree":git("rev-parse","HEAD^{tree}"),
        "file_count":len(rows),
        "files":rows
    }
    (out/"SOURCE_MANIFEST.json").write_text(json.dumps(manifest,indent=2)+"\n",encoding="utf-8")
    print(json.dumps(manifest,indent=2))
if __name__=="__main__":
    main()
