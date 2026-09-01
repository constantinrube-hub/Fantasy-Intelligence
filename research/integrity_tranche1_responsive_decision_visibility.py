#!/usr/bin/env python3
"""Tranche 1 responsive primary-decision visibility characterization."""
from __future__ import annotations
import argparse,json,re
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]

def between(src,start,end):
    i=src.index(start)
    j=src.index(end,i)
    return src[i:j]

def schema_keys(chunk:str):
    """Return schema object order from `key:'...'`.

    Keys are stable even when a column label is a JS expression such as
    `label: calibrated ? 'P10' : 'Low · Estimate'`.  The original harness used
    only literal label strings and therefore shifted later column ordinals.
    """
    return re.findall(r"\{key:'([^']+)'",chunk)

def pos(keys,name):
    return keys.index(name)+1 if name in keys else None

def main():
    ap=argparse.ArgumentParser()
    ap.add_argument("--mode",choices=["baseline","target"],default="baseline")
    a=ap.parse_args()

    css=(ROOT/"app/decision-ui.css").read_text(encoding="utf-8")
    ui=(ROOT/"app/decision-ui.js").read_text(encoding="utf-8")

    nth1150="th:nth-child(n+9)" in css and "td:nth-child(n+9)" in css
    nth760="th:nth-child(n+7)" in css and "td:nth-child(n+7)" in css

    start_chunk=between(ui,"function renderStartSit()","renderTable('startsit'")
    start_keys=schema_keys(start_chunk)
    assert start_keys==[
        "slot","player","opp","week","low","high","match","bench","decision","posrank"
    ], f"unexpected Start/Sit schema order: {start_keys}"

    wchunk=between(ui,"function renderWaivers()","function renderTargets()")
    waiver_chunks=re.findall(r"schema=\[(.*?)\];",wchunk,re.S)
    waiver_schemas=[schema_keys(x) for x in waiver_chunks]
    assert len(waiver_schemas)==3, f"expected 3 waiver schemas, got {waiver_schemas}"
    for keys in waiver_schemas:
        assert keys[-2:]==["faab","action"], f"unexpected waiver tail: {keys}"

    decision_col=pos(start_keys,"decision")
    hidden={
      "startsit":{
        "Decision":decision_col,
        "tablet_hidden":decision_col is not None and decision_col>=9,
        "mobile_hidden":decision_col is not None and decision_col>=7
      },
      "waivers":[
        {
          "keys":keys,
          "FAAB":pos(keys,"faab"),
          "Action":pos(keys,"action"),
          "tablet_action_hidden":pos(keys,"action") is not None and pos(keys,"action")>=9,
          "mobile_faab_hidden":pos(keys,"faab") is not None and pos(keys,"faab")>=7,
          "mobile_action_hidden":pos(keys,"action") is not None and pos(keys,"action")>=7
        } for keys in waiver_schemas
      ]
    }

    specialist={}
    for name,path in [
        ("dst","app/dst-intelligence.js"),
        ("kicker","app/kicker-intelligence.js")
    ]:
        s=(ROOT/path).read_text(encoding="utf-8")
        tables=re.findall(r"<thead><tr>(.*?)</tr></thead>",s,re.S)
        parsed=[]
        for t in tables:
            labels=re.findall(r"<th>(.*?)</th>",t)
            if "Action" in labels:
                parsed.append({"labels":labels,"Action":labels.index("Action")+1})
        specialist[name]=parsed

    if a.mode=="baseline":
        assert nth1150 and nth760, "baseline ordinal hiding rules changed unexpectedly"
        assert hidden["startsit"]["Decision"]==9, hidden
        assert hidden["startsit"]["tablet_hidden"], hidden
        assert hidden["startsit"]["mobile_hidden"], hidden
        assert all(x["Action"]==9 for x in hidden["waivers"]), hidden
        assert all(x["FAAB"]==8 for x in hidden["waivers"]), hidden
        assert all(x["tablet_action_hidden"] for x in hidden["waivers"]), hidden
        assert all(x["mobile_faab_hidden"] for x in hidden["waivers"]), hidden
        assert all(x["mobile_action_hidden"] for x in hidden["waivers"]), hidden
        assert any(x["Action"]>=9 for x in specialist["dst"]), (
            "D/ST Action no longer at hidden ordinal baseline"
        )
        assert any(x["Action"]>=9 for x in specialist["kicker"]), (
            "Kicker Action no longer at hidden ordinal baseline"
        )
        print(
            "KNOWN_GAP_REPRODUCED ordinal responsive CSS hides "
            "Start/Sit Decision and Waiver/DST/Kicker primary actions"
        )
    else:
        assert not nth1150 and not nth760, (
            "target: generic ordinal column hiding must be removed"
        )

    print(json.dumps({
        "mode":a.mode,
        "ordinal_rules":{"1150":nth1150,"760":nth760},
        "startSitKeys":start_keys,
        "waiverSchemas":waiver_schemas,
        "hidden":hidden,
        "specialist":specialist
    },sort_keys=True))

if __name__=="__main__":
    main()
