#!/usr/bin/env python3
"""Static/deterministic governance integrity for unified orchestration."""
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
contract=(ROOT/'research/fie_research_pipeline_contract.py').read_text(encoding='utf-8')
runner=(ROOT/'research/run_fie_league_research_pipeline.py').read_text(encoding='utf-8')
resolver=(ROOT/'research/resolve_fie_position_models.py').read_text(encoding='utf-8')
assert 'existing_resolver(profile, requested)' in contract
assert 'build_performance_research.py' in runner and 'build_fie_strategy_stack.py' in runner
assert 'preseason_projection_v4.py' in runner and 'preseason_projection_v5.py' in runner
assert 'statistical_gates_lowered": False' in runner
assert 'automatic_promotion": False' in resolver
assert 'current_challenger_projection_activated": False' in resolver
assert 'selected = override.get(pos, "M9")' in resolver
print('PASS unified pipeline governance/delegation integrity')
