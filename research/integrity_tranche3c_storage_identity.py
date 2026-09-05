#!/usr/bin/env python3
"""Permanent Tranche 3C governed current-snapshot identity mirror."""
from current_snapshot_storage import player_id

assert player_id({'sleeper_id':'123','canonical_player_id':'abc'}) == '123'
assert player_id({'canonical_player_id':'abc'}) == 'canonical:abc'
assert player_id({'internal_id':'abc'}) == 'canonical:abc'
assert player_id({'gsis_id':'00-001'}) == 'gsis:00-001'
assert player_id({'pfr_id':'AbcdJo00'}) == 'pfr:AbcdJo00'
assert player_id({'fantasypros_id':'9876'}) == 'fantasypros:9876'
try:
    player_id({'full_name':'Name Only','position_model':'WR'})
except ValueError as exc:
    assert 'governed Sleeper/canonical crosswalk identity' in str(exc)
else:
    raise AssertionError('display-name-only current row must fail closed')
print('PASS Tranche 3C current-snapshot governed identity storage contract')
