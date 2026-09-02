#!/usr/bin/env python3
"""Capture exact C10-006 transport/access source bytes for Tranche 3B."""
from __future__ import annotations
import argparse, hashlib, json, shutil, subprocess
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
FILES=[
    "app/core/data-client.js",
    "app/core/research-report-service.js",
    "app/current-snapshot-store.js",
    "app/core/special-teams-series.js",
    "app/dst-intelligence.js",
    "app/kicker-intelligence.js",
    "app/v9.3.3-runtime-integrity.js",
    "app/v9.3.4c-weekly-context.js",
    "app/generated/runtime-contracts.js",
    "research/integrity_tranche1_data_client_scope_characterization.js",
    "research/integrity_tranche1_direct_fetch_allowlist.py",
    "research/integrity_tranche3b_data_client_scope.js",
    "research/integrity_v931_persistent_cache_test.js",
    "research/integrity_league_fast_switch_runtime_test.js",
    "research/integrity_v932_build_determinism_test.py",
    "research/build_app_manifest.py",
    "research/release_gate.py",
    "tools/release_build.py",
]
def sha256(p:Path)->str:
    h=hashlib.sha256()
    with p.open("rb") as f:
        for b in iter(lambda:f.read(1024*1024),b""):h.update(b)
    return h.hexdigest()
def git(*args):return subprocess.check_output(["git",*args],cwd=ROOT,text=True).strip()
def main():
    ap=argparse.ArgumentParser()
    ap.add_argument("--output-dir",default="artifacts/tranche3b/preflight-source")
    a=ap.parse_args()
    out=ROOT/a.output_dir
    if out.exists():shutil.rmtree(out)
    out.mkdir(parents=True)
    rows=[]
    for rel in FILES:
        src=ROOT/rel
        if not src.exists():raise SystemExit(f"missing 3B capture source: {rel}")
        dst=out/rel;dst.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(src,dst)
        rows.append({"path":rel,"bytes":src.stat().st_size,"sha256":sha256(src)})
    manifest={
        "schema_version":1,"tranche":"3B","change_package":"C10-006",
        "phase":"preflight_source_capture","head":git("rev-parse","HEAD"),
        "tree":git("rev-parse","HEAD^{tree}"),"file_count":len(rows),"files":rows
    }
    (out/"SOURCE_MANIFEST.json").write_text(json.dumps(manifest,indent=2)+"\n",encoding="utf-8")
    print(json.dumps(manifest,indent=2))
if __name__=="__main__":main()
