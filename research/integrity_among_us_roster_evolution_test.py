#!/usr/bin/env python3
"""Regression contract for the declared Among Us Guillotine roster schedule."""
from __future__ import annotations

import json
from pathlib import Path

from league_profile import research_roster_positions_for_live_state, roster_evolution_status
from portfolio_rules import entry_for, load_portfolio_config

ROOT = Path(__file__).resolve().parents[1]
LEAGUE_ID = "1402643913583398912"


def main() -> int:
    config = load_portfolio_config(ROOT / "config/league-portfolio.json")
    entry = entry_for(config, LEAGUE_ID)
    assert entry is not None
    profile = json.loads((ROOT / f"data/research/leagues/{LEAGUE_ID}/profile.json").read_text())
    assert profile.get("roster_evolution") == entry.get("roster_evolution")
    assert profile.get("operational_rules") == entry.get("operational_rules") == {
        "faab_budget": 1000, "trading_allowed": False, "draft_lottery_draws": 3,
    }

    base = list(profile["roster_positions"])
    # Between Monday Night Football and Tuesday's commissioner update, the
    # most recently realized stage remains approved—not a workflow blocker.
    pending = roster_evolution_status(profile, base, 2026, 4)
    assert pending["recognized"] and pending["matched_stage"] == 0
    assert pending["scheduled_addition_pending"] is True
    assert pending["next_scheduled_change"] == {"week": 1, "slots": ["BN"]}

    week_one = base + ["BN"]
    stage_one = roster_evolution_status(profile, week_one, 2026, 4)
    assert stage_one["recognized"] and stage_one["matched_stage"] == 1
    assert stage_one["scheduled_addition_pending"] is True
    positions, evidence = research_roster_positions_for_live_state(profile, week_one, 2026, 4)
    assert positions == base and evidence["recognized"]

    through_week_five = week_one + ["BN", "BN", "BN", "FLEX"]
    stage_five = roster_evolution_status(profile, through_week_five, 2026, 5)
    assert stage_five["recognized"] and stage_five["matched_stage"] == 5
    assert stage_five["scheduled_addition_pending"] is False
    assert not roster_evolution_status(profile, base + ["SUPER_FLEX"], 2026, 4)["recognized"]
    assert stage_five["season_complete_week"] == 17
    assert roster_evolution_status(profile, through_week_five, 2026, 17)["season_complete"] is True
    print("PASS Among Us roster evolution: Tuesday pending stages accepted; unplanned slots fail closed")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
