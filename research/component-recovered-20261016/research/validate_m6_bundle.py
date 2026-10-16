#!/usr/bin/env python3
import json,sys
from pathlib import Path

def fail(msg):
    raise SystemExit(f"M6 validation failed: {msg}")

def main():
    p=Path(sys.argv[1] if len(sys.argv)>1 else 'data/research/milestone6.json')
    if not p.exists():fail('bundle missing')
    b=json.loads(p.read_text())
    if b.get('schema_version')!=6:fail('schema_version must be 6')
    if b.get('milestone')!='M6':fail('milestone must be M6')
    if b.get('research_build')!='V8.8-M6':fail('research build mismatch')
    if b.get('steps_completed')!=[28,29,30]:fail('steps_completed mismatch')
    if b.get('status') not in {'complete','pipeline_ready_not_run'}:fail('invalid status')
    a=b.get('advanced_second_wave') or {}
    if a.get('activation_status')!='DIAGNOSTIC_ONLY':fail('Step 28 must remain diagnostic-only')
    cur=b.get('current_season_automation') or {}
    if cur.get('status')!='implemented' or cur.get('output')!='data/research/current/milestone5_current.json':fail('Step 29 contract missing')
    gov=b.get('governance') or {}
    if gov.get('status')!='implemented' or gov.get('control_fallback')!='V8.2.2':fail('Step 30 fallback contract missing')
    if b.get('status')=='complete':
        blocked=a.get('blocked_analyses') or []
        if not blocked:fail('complete M6 must surface blocked analyses')
        if not any('all_route' in str(x.get('analysis','')) for x in blocked):fail('route-tracking guardrail missing')
    print(f"M6 bundle valid: {p} status={b.get('status')}")
if __name__=='__main__':main()
