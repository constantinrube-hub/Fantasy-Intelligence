#!/usr/bin/env python3
from __future__ import annotations
import json, re
from fie_research_pipeline_contract import ROOT
WORKFLOW="validate-fie-tranche7cr-source-bundle.yml"
def main() -> int:
 t=json.loads((ROOT/"config/tranche7cr-source-bundle-target.json").read_text()); assert t["tranche"]=="7C-R2" and t["research_only"] and t["production_model"]=="M9"; assert not any(t[k] for k in ("production_activation","app_integration","runtime_integration","shadow_integration","scheduled_collection","live_provider_request","historical_reconstruction"))
 w=(ROOT/".github/workflows"/WORKFLOW).read_text(); assert re.search(r"(?m)^  push:",w) and not re.search(r"(?m)^  schedule:",w)
 print("PASS Tranche 7C-R2: fixture-only source bundle; no schedule, provider, or production writer")
 return 0
if __name__=="__main__": raise SystemExit(main())
