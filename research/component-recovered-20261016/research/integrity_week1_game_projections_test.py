#!/usr/bin/env python3
"""No-network regression gates for Week 1 game-level projection semantics."""
from week1_game_projections import availability_state, canonical_team, identity_match, readiness
from nfl_schedule_time import kickoff_iso
import pandas as pd

assert kickoff_iso("2026-09-09", "20:20") == "2026-09-10T00:20:00+00:00"
assert readiness("2026-09-10T00:20:00+00:00", "2026-09-09T20:00:00+00:00") == "READY_PREGAME_FINAL"
assert readiness("2026-09-10T00:20:00+00:00", "2026-09-10T00:20:00+00:00") == "BLOCKED_KICKOFF_PASSED"
assert availability_state({"status": "Active", "injury_status": "Out"}) == "OUT"
assert availability_state({"status": "Active", "injury_status": "Questionable"}) == "QUESTIONABLE"
assert canonical_team("LA") == "LAR" and canonical_team("JAC") == "JAX"
identity = pd.DataFrame([{"canonical_player_id": "one", "full_name": "Jane Player", "position": "WR"}, {"canonical_player_id": "two", "full_name": "Twin Player", "position": "WR"}, {"canonical_player_id": "three", "full_name": "Twin Player", "position": "WR"}])
mapped, blocked = identity_match(identity, [{"sleeper_id": "a", "full_name": "Jane Player", "position_model": "WR"}, {"sleeper_id": "b", "full_name": "Twin Player", "position_model": "WR"}])
assert mapped["a"]["canonical_player_id"] == "one" and "b" in blocked
print("PASS week1 game-level projection semantics")
