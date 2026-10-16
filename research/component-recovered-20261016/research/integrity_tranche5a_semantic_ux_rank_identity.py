#!/usr/bin/env python3
"""Tranche 5A semantic-rank and research-surface characterization."""
from __future__ import annotations

import argparse
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
UI = (ROOT / "app/decision-ui.js").read_text(encoding="utf-8")
ENGINES = (ROOT / "app/decision-engines.js").read_text(encoding="utf-8")
VALUE = (ROOT / "app/value-finder.js").read_text(encoding="utf-8")
REPORT = (ROOT / "app/research-report-ui.js").read_text(encoding="utf-8")
SHELL = (ROOT / "index.html").read_text(encoding="utf-8")

CURRENT_LABELS = (
    "Draft Rank",
    "FIE Pos",
    "Asset Rank",
    "League Rank",
    "FIE League Rank",
    "Board Rank",
    "Decision Rank",
    "Market Rank",
)


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--mode", choices=("baseline", "target"), default="baseline")
    args = ap.parse_args()
    corpus = "\n".join((UI, ENGINES, VALUE, SHELL))
    present = [label for label in CURRENT_LABELS if label in corpus]
    facts = {
        "labels_present": present,
        "draft_board_rank_and_decision_rank_both_present": "Board Rank" in UI and "Decision Rank" in UI,
        "value_finder_declares_timing_not_second_board": "not a second Draft Board" in VALUE,
        "research_report_declares_no_rank_calculation": "no rank calculation" in REPORT,
        "parallel_research_panels": int('id="researchPanel"' in SHELL) + sum(f'research{i}Panel' in SHELL for i in range(2, 7)),
        "separate_research_overlay": "fieResearchOverlay" in REPORT,
    }
    assert facts["value_finder_declares_timing_not_second_board"], facts
    assert facts["research_report_declares_no_rank_calculation"], facts
    assert facts["parallel_research_panels"] >= 6, facts
    assert facts["separate_research_overlay"], facts
    if args.mode == "baseline":
        assert len(present) >= 7, facts
        assert facts["draft_board_rank_and_decision_rank_both_present"], facts
        print("KNOWN_GAP_REPRODUCED rank terminology and Research/Lab entry points lack one semantic UX contract")
    else:
        contract = ROOT / "config/semantic-ux-contract.json"
        assert contract.is_file(), "target semantic UX contract missing"
        data = json.loads(contract.read_text(encoding="utf-8"))
        assert data.get("schema") == "fie-semantic-ux-v1"
        assert data.get("rank_terms") and data.get("surface_roles")
        labels = {item["label"] for item in data["rank_terms"].values()}
        assert {"League Rank", "Position Rank", "Decision Rank", "Asset Rank", "Market Rank", "Weekly Position Rank", "Research Position Rank"} <= labels
        assert "'Draft Rank':'League Rank'" in UI
        assert "'Board Rank':'League Rank'" in UI
        assert "'FIE Pos':'Position Rank'" in UI
        assert "<th>League Rank</th><th>Decision Rank</th><th>Position Rank</th>" in UI
        assert "<th>Research Position Rank</th>" in REPORT
        assert "Research / Lab · evidence only" in REPORT
        assert "Does not change League Rank or Decision Rank" in REPORT
        assert "<span>FIE League Rank</span>" not in ENGINES
        assert "<th>FIE Pos</th>" not in VALUE
        assert "<th>Market Pos</th>" not in VALUE
        assert data["surface_roles"]["draft_board"]["owns_canonical_rank"] is True
        assert all(not role["owns_canonical_rank"] for key, role in data["surface_roles"].items() if key != "draft_board")
        print("TARGET_GAP_CLOSED canonical rank vocabulary and surface roles enforced")
    print(json.dumps({"mode": args.mode, **facts}, sort_keys=True))


if __name__ == "__main__":
    main()
