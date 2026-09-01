#!/usr/bin/env python3
"""Tranche 1 responsive primary-decision visibility characterization."""
from __future__ import annotations
import argparse,json,re
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
def labels(chunk:str):
    return re.findall(r"label:'([^']+)'",chunk)
def between(src,start,end):
    i=src.index(start);j=src.index(end,i);return src[i:j]
def main():
    ap=argparse.ArgumentParser();ap.add_argument("--mode",choices=["baseline","target"],default="baseline");a=ap.parse_args()
    css=(ROOT/"app/decision-ui.css").read_text(encoding="utf-8")
    ui=(ROOT/"app/decision-ui.js").read_text(encoding="utf-8")
    nth1150="th:nth-child(n+9)" in css and "td:nth-child(n+9)" in css
    nth760="th:nth-child(n+7)" in css and "td:nth-child(n+7)" in css
    start_labels=labels(between(ui,"function renderStartSit()","renderTable('startsit'"))
    wchunk=between(ui,"function renderWaivers()","function renderTargets()")
    waiver_schemas=[labels(x) for x in re.findall(r"schema=\[(.*?)\];",wchunk,re.S)]
    assert start_labels and waiver_schemas
    def pos(xs,name): return xs.index(name)+1 if name in xs else None
    hidden={
      "startsit":{"Decision":pos(start_labels,"Decision"),"tablet_hidden":pos(start_labels,"Decision") is not None and pos(start_labels,"Decision")>=9,"mobile_hidden":pos(start_labels,"Decision") is not None and pos(start_labels,"Decision")>=7},
      "waivers":[{"FAAB":pos(x,"FAAB"),"Action":pos(x,"Action"),"tablet_action_hidden":pos(x,"Action") is not None and pos(x,"Action")>=9,"mobile_faab_hidden":pos(x,"FAAB") is not None and pos(x,"FAAB")>=7,"mobile_action_hidden":pos(x,"Action") is not None and pos(x,"Action")>=7} for x in waiver_schemas]
    }
    specialist={}
    for name,path in [("dst","app/dst-intelligence.js"),("kicker","app/kicker-intelligence.js")]:
        s=(ROOT/path).read_text(encoding="utf-8")
        tables=re.findall(r"<thead><tr>(.*?)</tr></thead>",s,re.S)
        parsed=[]
        for t in tables:
            xs=re.findall(r"<th>(.*?)</th>",t)
            if "Action" in xs: parsed.append({"labels":xs,"Action":xs.index("Action")+1})
        specialist[name]=parsed
    if a.mode=="baseline":
        assert nth1150 and nth760,"baseline ordinal hiding rules changed unexpectedly"
        assert hidden["startsit"]["tablet_hidden"] and hidden["startsit"]["mobile_hidden"],hidden
        assert any(x["tablet_action_hidden"] and x["mobile_action_hidden"] for x in hidden["waivers"]),hidden
        assert any(x["mobile_faab_hidden"] for x in hidden["waivers"]),hidden
        assert any(x["Action"]>=9 for x in specialist["dst"]),"D/ST Action no longer at hidden ordinal baseline"
        assert any(x["Action"]>=9 for x in specialist["kicker"]),"Kicker Action no longer at hidden ordinal baseline"
        print("KNOWN_GAP_REPRODUCED ordinal responsive CSS hides primary decisions/actions")
    else:
        assert not nth1150 and not nth760,"target: generic ordinal column hiding must be removed"
    print(json.dumps({"mode":a.mode,"ordinal_rules":{"1150":nth1150,"760":nth760},"startSitLabels":start_labels,"waiverSchemas":waiver_schemas,"hidden":hidden,"specialist":specialist},sort_keys=True))
if __name__=="__main__":main()
