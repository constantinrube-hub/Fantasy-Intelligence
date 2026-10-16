#!/usr/bin/env python3
"""Tranche 1 unified research-stage provenance characterization."""
from __future__ import annotations
import argparse, json
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
PILOT="1391803939736801280"
REQUIRED=("artifact_type","producer","validator","schema")
DEDICATED={
 "feature_evidence":["research/fie_feature_evidence.py","research/fie_feature_evidence_hardening.py"],
 "production_shadow":["research/fie_production_shadow.py"],
 "controlled_runtime":["research/build_v96_runtime_bundle.py","research/validate_v96_runtime_bundle.py"],
}
def main():
    ap=argparse.ArgumentParser();ap.add_argument("--mode",choices=["baseline","target"],default="baseline");a=ap.parse_args()
    manifest_path=ROOT/f"data/research/leagues/{PILOT}/performance/2026/research_pipeline/stage-manifest.json"
    assert manifest_path.is_file(),manifest_path
    manifest=json.loads(manifest_path.read_text(encoding="utf-8"))
    stages={x.get("name"):x for x in manifest.get("stages",[]) if isinstance(x,dict)}
    source=(ROOT/"research/run_fie_league_research_pipeline.py").read_text(encoding="utf-8")
    rows=[]
    for name,files in DEDICATED.items():
        assert name in stages,f"{name} absent from pilot manifest"
        for f in files: assert (ROOT/f).is_file(),f"dedicated implementation missing: {f}"
        st=stages[name];missing=[k for k in REQUIRED if k not in st]
        invoked=[f for f in files if Path(f).name in source]
        rows.append({"stage":name,"status":st.get("status"),"reason":st.get("reason"),"missing_typed_fields":missing,"dedicated_files":files,"dedicated_names_referenced_by_unified_runner":invoked,"outputs":st.get("outputs",{})})
    if a.mode=="baseline":
        assert all(r["missing_typed_fields"] for r in rows),"baseline unexpectedly has full typed stage identity"
        assert not rows[0]["dedicated_names_referenced_by_unified_runner"],"feature evidence dedicated builder unexpectedly wired"
        assert not rows[1]["dedicated_names_referenced_by_unified_runner"],"production shadow dedicated builder unexpectedly wired"
        assert not rows[2]["dedicated_names_referenced_by_unified_runner"],"controlled runtime dedicated builder unexpectedly wired"
        print("KNOWN_GAP_REPRODUCED unified research stages are status-labelled but not typed to exact dedicated producers")
    else:
        for r in rows:
            assert not r["missing_typed_fields"],f"target typed provenance missing: {r}"
            assert r["outputs"],f"target stage must identify governed output: {r['stage']}"
    print(json.dumps({"mode":a.mode,"pilot":PILOT,"rows":rows},sort_keys=True))
if __name__=="__main__":main()
