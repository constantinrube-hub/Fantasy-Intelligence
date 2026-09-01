#!/usr/bin/env python3
"""Tranche 1 direct-fetch allowlist characterization."""
from __future__ import annotations
import argparse, json, re
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
ALLOW={
    "app/core/data-client.js":"CANONICAL_TRANSPORT",
    "app/core/research-report-service.js":"KNOWN_PRIMARY_RAW_FETCH",
    "app/current-snapshot-store.js":"RAW_FETCH_FALLBACK",
    "app/dst-intelligence.js":"RAW_FETCH_FALLBACK",
    "app/kicker-intelligence.js":"RAW_FETCH_FALLBACK",
    "app/core/special-teams-series.js":"RAW_FETCH_FALLBACK",
    "app/v9.3.4c-weekly-context.js":"RAW_FETCH_FALLBACK",
}
FALLBACK_TOKEN={
    "app/current-snapshot-store.js":"FIEDataClient",
    "app/dst-intelligence.js":"FIECurrentSnapshotStore",
    "app/kicker-intelligence.js":"FIECurrentSnapshotStore",
    "app/core/special-teams-series.js":"FIEDataClient",
    "app/v9.3.4c-weekly-context.js":"FIEDataClient",
}
PAT=re.compile(r"(?<![\w.$])fetch\s*\(")

def has_direct(text:str)->bool:
    # This deliberately detects browser global fetch(), not obj.fetch().
    return bool(PAT.search(text))

def main():
    ap=argparse.ArgumentParser();ap.add_argument("--mode",choices=["baseline","target"],default="baseline");a=ap.parse_args()
    observed={}
    for p in sorted((ROOT/"app").rglob("*.js")):
        rel=p.relative_to(ROOT).as_posix();txt=p.read_text(encoding="utf-8")
        if has_direct(txt): observed[rel]=ALLOW.get(rel,"UNALLOWLISTED")
    unknown={p:m for p,m in observed.items() if m=="UNALLOWLISTED"}
    assert not unknown, f"new raw-fetch app module requires explicit review: {unknown}"
    for p,token in FALLBACK_TOKEN.items():
        if p in observed:
            txt=(ROOT/p).read_text(encoding="utf-8")
            assert token in txt, f"{p} raw fetch exists without expected canonical/fallback owner token {token}"
    rr="app/core/research-report-service.js"
    if a.mode=="baseline":
        assert observed.get(rr)=="KNOWN_PRIMARY_RAW_FETCH","baseline must reproduce ResearchReportService primary raw fetch"
        print("KNOWN_GAP_REPRODUCED ResearchReportService primary raw fetch; all other direct app fetches are allowlisted fallbacks/transport")
    else:
        assert rr not in observed,"target: ResearchReportService must route primary transport through FIEDataClient"
    print(json.dumps({"mode":a.mode,"observed":observed},sort_keys=True))
if __name__=="__main__":main()
