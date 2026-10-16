#!/usr/bin/env python3
"""Deterministic, research-only prospective lineup traces."""
from __future__ import annotations
from typing import Any
from m10_prospective_capture_contract import MODELS

def trace_rows(rows:list[dict[str,Any]], league_id:str, domain:str, slots:int)->list[dict[str,Any]]:
    assert domain in {"start_sit","best_ball","chopped"} and slots>0
    by_model={m:[r for r in rows if r["model"]==m] for m in MODELS}
    legal={m:tuple(sorted(str(r["forecast_id"]) for r in values)) for m,values in by_model.items()}
    assert all(legal[m]==legal["M9"] for m in MODELS), "model-specific eligibility is prohibited"
    out=[]
    for model,values in by_model.items():
        key="p10" if domain=="chopped" else "mean"
        chosen=sorted(values,key=lambda r:(-float(r[key]),str(r["canonical_player_id"])))[:slots]
        out.append({"league_id":league_id,"domain":domain,"model":model,"legal_forecast_ids":list(legal[model]),"selected_forecast_ids":[r["forecast_id"] for r in chosen],"predicted_utility":sum(float(r[key]) for r in chosen),"research_only":True,"production_recommendation_changed":False})
    return out
