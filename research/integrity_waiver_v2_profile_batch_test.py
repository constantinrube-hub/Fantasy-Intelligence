#!/usr/bin/env python3
"""Profile grouping must preserve canonical scoring-signature isolation."""
from __future__ import annotations

import json
import tempfile
from pathlib import Path

from run_waiver_v2_profile_batch import load_profile_groups


with tempfile.TemporaryDirectory() as raw:
    root = Path(raw); profiles = root / "leagues"; profiles.mkdir()
    settings = {"rec": 1, "pass_yd": 0.04}
    from build_waiver_v2_outcome_ledger import scoring_signature
    for league_id, name, scoring in (("1", "One", settings), ("2", "Two", settings), ("3", "Three", {"rec": 0.5, "pass_yd": 0.04})):
        target = profiles / league_id; target.mkdir()
        target.joinpath("profile.json").write_text(json.dumps({"league_id": league_id, "league_name": name, "scoring_settings": scoring, "scoring_signature": scoring_signature(scoring)}), encoding="utf-8")
    overview = root / "overview.json"
    overview.write_text(json.dumps({"leagues": [{"league_id": "1"}, {"league_id": "2"}, {"league_id": "3"}]}), encoding="utf-8")
    groups = load_profile_groups(profiles, overview)
    assert len(groups) == 2
    grouped = {tuple(group["league_ids"]): group for group in groups}
    assert ("1", "2") in grouped and grouped[("1", "2")]["scoring_signature"] == scoring_signature(settings)
    assert ("3",) in grouped

    bad = json.loads((profiles / "3" / "profile.json").read_text(encoding="utf-8"))
    bad["scoring_signature"] = "wrong"
    (profiles / "3" / "profile.json").write_text(json.dumps(bad), encoding="utf-8")
    try:
        load_profile_groups(profiles, overview)
        raise AssertionError("profile signature mismatch must fail closed")
    except ValueError as error:
        assert "does not match" in str(error)

print("OK waiver-v2 profile batch signature isolation")
