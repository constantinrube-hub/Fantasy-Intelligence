#!/usr/bin/env python3
import json, sys
from pathlib import Path

p=Path(sys.argv[1] if len(sys.argv)>1 else 'data/research/milestone5.json')
if not p.exists():
    raise SystemExit(f'Missing {p}')
b=json.loads(p.read_text())
assert b.get('schema_version')==5
assert b.get('milestone')=='M5'
assert b.get('research_build')=='V8.7-M5'
assert b.get('control_build')=='V8.2.2'
assert b.get('steps_completed')==[24,25,26,27]
assert b.get('integration_mode')=='fail_closed_conditional'
a=b.get('activation',{})
assert a.get('policy')=='fail_closed'
assert a.get('requires_current_snapshot') is True
assert a.get('fallback')=='V8.2.2 live decision logic'
assert str(a.get('current_snapshot_path','')).endswith('milestone5_current.json')
assert isinstance(b.get('scoring_settings',{}),dict)
g=a.get('decision_gates',{})
for key in ['weekly_mean_positions','weekly_risk_positions','draft_policy_positions','waiver_policy_positions','validated_format_profiles']:
    assert isinstance(g.get(key,[]),list), key
assert set(g.get('weekly_risk_positions',[])).issubset(set(g.get('weekly_mean_positions',[])))
upstream=set(a.get('upstream_validated_positions',[]) or [])
assert set(g.get('weekly_mean_positions',[])).issubset(upstream)
assert set(g.get('draft_policy_positions',[])).issubset(upstream)
assert set(g.get('waiver_policy_positions',[])).issubset(upstream)
fg=g.get('format_position_gates',{})
assert set(fg)=={'REDRAFT','DYNASTY','REDRAFT_BESTBALL','DYNASTY_BESTBALL','CHOPPED'}
for key, vals in fg.items(): assert isinstance(vals,list), key

for section in ['draft_integration','waiver_integration','weekly_integration','format_strategy','runtime_contract']:
    assert section in b, section

profiles=b['format_strategy'].get('profiles',{})
expected={'REDRAFT','DYNASTY','REDRAFT_BESTBALL','DYNASTY_BESTBALL','CHOPPED'}
assert set(profiles)==expected
for k,v in profiles.items():
    for weight_key in ['draft_weights','waiver_weights']:
        w=v.get(weight_key,{})
        assert w and abs(sum(float(x) for x in w.values())-1.0)<1e-9, (k,weight_key,w)

for r in b['weekly_integration'].get('risk_bands',[]):
    vals=[r.get('q10'),r.get('q25'),r.get('q50'),r.get('q75'),r.get('q90')]
    if all(x is not None for x in vals):
        assert vals==sorted(vals), (r.get('position'),vals)

# M5 may conditionally activate players only through a separate current snapshot.
text=json.dumps(b)
assert 'activation_eligible=true' in text
assert 'unconditional_activation' not in text
print(f"OK {p}: M5 schema/guardrails validated")
