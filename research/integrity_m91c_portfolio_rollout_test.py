#!/usr/bin/env python3
"""Portfolio rollout invariants for official M9.1c challenger integration."""
from build_fie_portfolio_research_report import _audit_row, _status

readiness={
    "pipeline":{"status":"complete_research_only"},
    "league":{"name":"Fixture","format":"REDRAFT","teams":12},
    "market":{"adp_key":"adp_ppr"},
    "league_value":{"replacement":{"QB":220}},
    "preseason_projection_challenger":{
        "model":"M9.1c",
        "status":"RESEARCH_ONLY_BLOCKED_PROMOTION",
        "production_eligible":False,
        "automatic_promotion":False,
        "residual_model_gate":{"status":"BLOCKED_MISSING_HISTORICAL_SLEEPER_BASELINE"},
    },
    "positions":{
        "QB":{
            "selected_production_model":"M9",
            "decision":"BLOCKED_STATISTICS",
            "preseason_projection_challenger":{
                "model":"M9.1c","exact_rows":50,"adjusted_rows":45,
                "median_abs_adjustment":2.0,"p90_abs_adjustment":8.0,
                "max_abs_adjustment":20.0,"median_total_reliability":.55,
            }
        },
        "RB":{"selected_production_model":"M9","decision":"BLOCKED_STATISTICS"},
        "WR":{"selected_production_model":"M9","decision":"BLOCKED_STATISTICS"},
        "TE":{"selected_production_model":"M9","decision":"BLOCKED_STATISTICS"},
    },
}
summary={"headline":{"actionable_top100_positive":1,"actionable_top100_negative":2,"positive_sleepers_gt100":3}}
matrix={
    "outcome":"success",
    "stages":{"m1_m9":"reused_valid"},
    "m91c_integration_status":"complete_research_only",
    "app_publish_complete":False,
}
registry={"league_name":"Fixture","research_format":"REDRAFT"}

assert _status("1",2026,readiness,summary,matrix)==("completed","")
audit=_audit_row("1",registry,2026,readiness,summary,matrix)
assert audit["M91c_model"]=="M9.1c"
assert audit["M91c_production_eligible"] is False
assert audit["M91c_residual_gate_status"]=="BLOCKED_MISSING_HISTORICAL_SLEEPER_BASELINE"
assert audit["QB_selected_model"]=="M9"
assert audit["QB_M91c_median_abs_adjustment"]==2.0

missing=dict(readiness)
missing.pop("preseason_projection_challenger")
assert _status("1",2026,missing,summary,matrix)[0]=="blocked"

bad_matrix=dict(matrix)
bad_matrix["m91c_integration_status"]="failed"
assert _status("1",2026,readiness,summary,bad_matrix)[0]=="blocked"

print("PASS M9.1c portfolio rollout: completed requires official challenger integration while production remains M9")
