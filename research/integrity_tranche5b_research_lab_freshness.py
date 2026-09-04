#!/usr/bin/env python3
"""Tranche 5B Research/Lab IA and freshness characterization."""
from __future__ import annotations

import argparse
import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SHELL = (ROOT / "index.html").read_text(encoding="utf-8")
REPORT = (ROOT / "app/research-report-ui.js").read_text(encoding="utf-8")
EVIDENCE = (ROOT / "app/core/evidence-semantics.js").read_text(encoding="utf-8")
RUNTIME = (ROOT / "app/runtime-foundation.js").read_text(encoding="utf-8")


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--mode", choices=("baseline", "target"), default="baseline")
    args = ap.parse_args()

    lab_match = re.search(r"lab:\{title:'Lab'.*?\}\n", SHELL)
    assert lab_match, "Lab navigation contract not found"
    tabs_match = re.search(r"tabs:\[(.*?)\](?:,routes:|\})", lab_match.group(0))
    assert tabs_match, "Lab visible tabs not found"
    lab_tabs = re.findall(r"\['([^']+)','([^']+)'\]", tabs_match.group(1))
    milestone_panels = [f"research{i}Panel" if i > 1 else "researchPanel" for i in range(1, 7)]
    facts = {
        "lab_tab_count": len(lab_tabs),
        "lab_tabs": [label for _, label in lab_tabs],
        "milestone_panel_count": sum(f'id="{panel}"' in SHELL for panel in milestone_panels),
        "standalone_research_report_overlay": "fieResearchOverlay" in REPORT,
        "standalone_research_report_launcher": "fieResearchLauncher" in REPORT,
        "integrated_research_report_entry": "data-fie-research-report" in SHELL and "data-fie-research-report" in REPORT,
        "lab_overview": 'id="labOverviewPanel"' in SHELL,
        "legacy_routes_preserved": all(f"'{route}'" in lab_match.group(0) for route in ("research", "research2", "research3", "research4", "features", "model")),
        "typed_as_of_available": "function firstAsOf" in EVIDENCE and "asOf:" in EVIDENCE,
        "m5_week_only_badge": "Current ${c?.season||''} W${c?.week||'?'}" in SHELL,
        "m6_boolean_freshness": "function m6Fresh" in SHELL,
        "raw_build_timestamp": "BUILD_MANIFEST.generated_at" in RUNTIME or "BUILD_MANIFEST?.generated_at" in RUNTIME,
        "shared_freshness_presenter": "FIEFreshness" in "\n".join((SHELL, REPORT, RUNTIME)),
    }

    assert facts["milestone_panel_count"] == 6, facts
    assert facts["standalone_research_report_overlay"], facts
    assert facts["typed_as_of_available"], facts
    assert facts["m6_boolean_freshness"], facts
    assert facts["raw_build_timestamp"], facts

    if args.mode == "baseline":
        assert facts["lab_tab_count"] == 9, facts
        assert facts["standalone_research_report_launcher"], facts
        assert facts["m5_week_only_badge"], facts
        assert not facts["shared_freshness_presenter"], facts
        print("KNOWN_GAP_REPRODUCED Research/Lab navigation and freshness presentation remain fragmented")
    else:
        contract_path = ROOT / "config/research-lab-ux-contract.json"
        assert contract_path.is_file(), "target Research/Lab UX contract missing"
        contract = json.loads(contract_path.read_text(encoding="utf-8"))
        assert contract.get("schema") == "fie-research-lab-ux-v1"
        assert contract.get("navigation_groups") and contract.get("freshness_states")
        assert facts["lab_tab_count"] == 4, facts
        assert facts["lab_overview"], facts
        assert facts["integrated_research_report_entry"], facts
        assert facts["legacy_routes_preserved"], facts
        assert not facts["m5_week_only_badge"], facts
        assert facts["shared_freshness_presenter"], facts
        print("TARGET_GAP_CLOSED Research/Lab navigation grouped and freshness presentation unified")
    print(json.dumps({"mode": args.mode, **facts}, sort_keys=True))


if __name__ == "__main__":
    main()
