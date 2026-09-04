#!/usr/bin/env python3
"""Targeted regression contract for Tranche 6B."""
from build_fie_research_completeness_inventory import build_inventory
from validate_fie_research_completeness_inventory import validate

inventory = build_inventory()
validate(inventory)
assert inventory["governance"]["production_behavior_changed"] is False
assert inventory["summary"]["cell_states"].get("PRODUCTION_AUTHORIZED", 0) == 0
assert inventory["summary"]["blockers"].get("GOVERNANCE_BLOCKED", 0) > 0
assert inventory["summary"]["blockers"].get("INSUFFICIENT_HISTORY", 0) > 0
print("PASS Tranche 6B inventory: complete coverage remains evidence-incomplete and promotion-blocked")
