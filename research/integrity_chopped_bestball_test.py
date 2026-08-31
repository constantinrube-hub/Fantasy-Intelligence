#!/usr/bin/env python3
from __future__ import annotations
import json
from pathlib import Path

from league_profile import FORMATS, infer_format
from validate_m5_bundle import CURRENT_FORMATS, LEGACY_FORMATS

ROOT = Path(__file__).resolve().parents[1]
HYBRID = "CHOPPED_BESTBALL"

assert HYBRID in FORMATS
assert HYBRID in CURRENT_FORMATS
assert HYBRID not in LEGACY_FORMATS

fixture = {
    "league_id": "1399318410818519040",
    "name": "Hybrid fixture",
    "type": "redraft",
    "settings": {"type": 3, "best_ball": 1},
}
assert infer_format(fixture, "AUTO") == HYBRID
assert infer_format(fixture, HYBRID) == HYBRID
assert infer_format({**fixture, "settings": {"type": 3, "best_ball": 0}}, "AUTO") == "CHOPPED"
assert infer_format({**fixture, "settings": {"type": 0, "best_ball": 1}}, "AUTO") == "REDRAFT_BESTBALL"

cfg = json.loads((ROOT / "config" / "league-portfolio.json").read_text())
by_id = {str(x["league_id"]): x for x in cfg["leagues"]}
expected = {
    "1399128582088835072": "REDRAFT",
    "1399318410818519040": HYBRID,
    "1396507356048658438": "CHOPPED",
}
for lid, fmt in expected.items():
    assert by_id[lid]["format"] == fmt, (lid, by_id[lid])
assert len(by_id) == len(cfg["leagues"])
assert len(cfg["leagues"]) >= 22

m5 = (ROOT / "research" / "fie_m5.py").read_text()
for token in ['"CHOPPED_BESTBALL": {', '"contract_revision": 5', 'set(chopped_positions) & set(bb_positions)']:
    assert token in m5, token
assert '"CHOPPED_BESTBALL": sorted(set(runtime_positions) & set(risk_positions) & set(chopped_positions) & set(bb_positions))' in m5
assert '"CHOPPED_BESTBALL": sorted(set(weekly_positions) & set(risk_positions) & set(chopped_positions) & set(bb_positions))' in m5
assert '"CHOPPED_BESTBALL": sorted(set(draft_positions) & set(risk_positions) & set(chopped_positions) & set(bb_positions))' in m5
assert '"CHOPPED_BESTBALL": sorted(set(waiver_positions) & set(chopped_positions) & set(bb_positions))' in m5

js = (ROOT / "app" / "decision-model-v9.js").read_text()
assert "fmt==='CHOPPED_BESTBALL'" in js
assert "chopped_bestball_utility_weights" in js
assert "lower_tail_surplus" in js and "spike_surplus" in js

portfolio_js = (ROOT / "app" / "portfolio-config.js").read_text()
assert "CHOPPED_BESTBALL:'Chopped + Best Ball'" in portfolio_js


print("PASS: CHOPPED_BESTBALL auto-detection, portfolio registration, M5 fail-closed intersections, workflow and browser utility")
