#!/usr/bin/env python3
"""Capture exact Tranche 3A replacement/scarcity/VOR source bytes + hashes."""
from __future__ import annotations
import argparse, hashlib, json, shutil, subprocess
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
FILES=[
    "app/core/core-services.js",
    "app/v9.3.4a3-score-performance.js",
    "app/v9.3.4d-starter-economics.js",
    "app/core/draft-value-service.js",
    "app/decision-model-v9.js",
    "app/decision-engines.js",
    "app/draft-monte-carlo-worker.js",
    "app/value-finder.js",
    "app/decision-ui.js",
    "app/runtime-foundation.js",
    "app/generated/runtime-contracts.js",
    "config/contracts/runtime-contracts.json",
    "config/build-manifest.json",
    "config/model-config.json",
    "config/release.json",
    "index.html",
    "research/build_app_manifest.py",
    "research/integrity_tranche1_replacement_parity_characterization.js",
    "research/integrity_tranche3a_replacement_ownership.js",
    "research/integrity_v93_scarcity_runtime_test.js",
    "research/integrity_v9_model_runtime_test.js",
    "research/integrity_decision_service_test.js",
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
    ap.add_argument("--output-dir",default="artifacts/tranche3a/preflight-source")
    a=ap.parse_args()
    out=ROOT/a.output_dir
    if out.exists(): shutil.rmtree(out)
    out.mkdir(parents=True)
    rows=[]
    for rel in FILES:
        src=ROOT/rel
        if not src.exists():
            raise SystemExit(f"missing capture source: {rel}")
        dst=out/rel
        dst.parent.mkdir(parents=True,exist_ok=True)
        shutil.copy2(src,dst)
        rows.append({"path":rel,"bytes":src.stat().st_size,"sha256":sha256(src)})
    manifest={
        "schema_version":1,
        "tranche":"3A",
        "change_package":"C10-004",
        "phase":"preflight_source_capture",
        "head":git("rev-parse","HEAD"),
        "tree":git("rev-parse","HEAD^{tree}"),
        "parent":git("rev-parse","HEAD^"),
        "file_count":len(rows),
        "files":rows,
    }
    (out/"SOURCE_MANIFEST.json").write_text(json.dumps(manifest,indent=2)+"\n",encoding="utf-8")
    print(json.dumps(manifest,indent=2))
if __name__=="__main__":
    main()
