#!/usr/bin/env python3
"""FIE V8.8-M6 runtime governance with League-ID namespace isolation.

AUTO promotes only when every required artifact is compatible, fresh, hashable,
and scoped to the same League ID/profile. CONTROL hard-disables all M5/M6
overrides. A global CONTROL switch remains available for emergency rollback across
all leagues; each league also has its own versioned operator override.
"""
from __future__ import annotations
import argparse, hashlib, json
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional

ACTIVE_BUILD='V8.8-M6'; CONTROL_BUILD='V8.2.2'

def now(): return datetime.now(timezone.utc)
def iso(): return now().isoformat()
def load(path):
    if not path:return {}
    p=Path(path); return json.loads(p.read_text()) if p.exists() else {}
def write(path,obj):
    p=Path(path);p.parent.mkdir(parents=True,exist_ok=True);p.write_text(json.dumps(obj,indent=2,allow_nan=False)+'\n')
def sha256_file(path):
    p=Path(path)
    if not p.exists():return None
    h=hashlib.sha256()
    with p.open('rb') as f:
        for c in iter(lambda:f.read(1024*1024),b''):h.update(c)
    return h.hexdigest()
def parse_time(v):
    if not v:return None
    try:return datetime.fromisoformat(str(v).replace('Z','+00:00')).astimezone(timezone.utc)
    except Exception:return None
def snapshot_age_hours(cur):
    t=parse_time(cur.get('generated_at'));return (now()-t).total_seconds()/3600 if t else None

def override_mode(obj,default='AUTO'):
    m=str((obj or {}).get('mode') or default).upper();return m if m in {'AUTO','CONTROL'} else 'CONTROL'

def namespace_ok(path: str, league_id: str) -> bool:
    if not league_id or not path:return False
    try: parts=Path(path).as_posix().split('/')
    except Exception:return False
    needle=['data','research','leagues',str(league_id)]
    return len(parts)>=len(needle) and parts[:len(needle)]==needle

def build(args):
    m4=load(args.m4_bundle);m5=load(args.m5_bundle);m6=load(args.m6_bundle);cur=load(args.current_snapshot)
    profile=load(getattr(args,'league_profile',None)); local=load(args.operator_override); global_ov=load(getattr(args,'global_operator_override',None))
    cli=getattr(args,'mode','KEEP')
    local_mode=cli if cli in {'AUTO','CONTROL'} else override_mode(local)
    global_mode=override_mode(global_ov)
    mode='CONTROL' if global_mode=='CONTROL' or local_mode=='CONTROL' else 'AUTO'
    league_id=str(getattr(args,'league_id',None) or profile.get('league_id') or m5.get('league_id') or cur.get('league_id') or '')
    profile_fp=profile.get('profile_fingerprint'); profile_sig=profile.get('scoring_signature'); profile_fmt=profile.get('format')
    age=snapshot_age_hours(cur);max_age=float(cur.get('snapshot_max_age_hours') or getattr(args,'max_age_hours',18.0))
    sig5=m5.get('scoring_signature');sigc=cur.get('scoring_signature');sig6=m6.get('scoring_signature')
    ids=[str(x.get('league_id') or '') for x in (m4,m5,m6,cur)]
    fps=[x.get('profile_fingerprint') for x in (m4,m5,m6,cur)]
    fmts=[x.get('league_format') for x in (m4,m5,m6,cur) if x.get('league_format') is not None]
    paths=[args.m4_bundle,args.m5_bundle,args.m6_bundle,args.current_snapshot,args.operator_override,getattr(args,'output','')]
    checks={
      'global_operator_auto':global_mode=='AUTO',
      'operator_auto':mode=='AUTO',
      'league_id_match':bool(league_id and profile and all(x==league_id for x in ids)),
      'profile_fingerprint_match':bool(profile_fp and all(x==profile_fp for x in fps)),
      'current_profile_live_match':cur.get('profile_current_match') is True and cur.get('live_profile_fingerprint')==profile_fp,
      'format_match':bool(profile_fmt and (not fmts or all(x==profile_fmt for x in fmts))),
      'artifact_scope_match':bool(league_id and all(namespace_ok(x,league_id) for x in paths)),
      'm4_complete':m4.get('status')=='complete','m5_complete':m5.get('status')=='complete','m6_complete':m6.get('status')=='complete',
      'current_complete':str(cur.get('status') or '').lower() in {'complete','ready','active'},
      'current_producer':cur.get('producer_build')==ACTIVE_BUILD,'current_contract':cur.get('m5_build')=='V8.7-M5',
      'scoring_signature_match':bool(profile_sig and sig5 and sigc and profile_sig==sig5==sigc and (not sig6 or sig6==sig5)),
      'fresh_snapshot':age is not None and age>=0 and age<=max_age,
      'target_week_leakage_guard':cur.get('target_week_realised_stats_excluded') is True,
      'eligible_players':int((cur.get('summary') or {}).get('activation_eligible') or 0)>0,
    }
    enabled=all(checks.values());reason='all promotion checks passed' if enabled else '; '.join(k for k,v in checks.items() if not v)
    gates=(m5.get('activation') or {}).get('decision_gates') or {}
    artifact_paths={'milestone4':args.m4_bundle,'milestone5':args.m5_bundle,'milestone6':args.m6_bundle,'current_snapshot':args.current_snapshot}
    return {
      'schema_version':2,'active_build':ACTIVE_BUILD,'control_build':CONTROL_BUILD,'generated_at':iso(),
      'league_id':league_id or None,'league_format':profile_fmt,'profile_fingerprint':profile_fp,'profile_scoring_signature':profile_sig,
      'operator_mode':mode,'global_operator_mode':global_mode,'league_operator_mode':local_mode,
      'runtime_enabled':bool(enabled),'runtime_allow_m5':bool(enabled),'fallback':CONTROL_BUILD,'reason':reason,'checks':checks,
      'current_snapshot':{'path':args.current_snapshot,'season':cur.get('season'),'week':cur.get('week'),'generated_at':cur.get('generated_at'),'age_hours':age,'max_age_hours':max_age,'eligible_players':int((cur.get('summary') or {}).get('activation_eligible') or 0)},
      'scoring_signature':sig5,'decision_gates':gates,
      'model_lineage':{
        'research_window':str((m4.get('methodology') or {}).get('research_window') or 'rollover-safe historical window; see milestone bundles'),
        'time_safe_folds':(m4.get('methodology') or {}).get('time_safe_folds',[]),'m4_research_build':m4.get('research_build'),'m5_research_build':m5.get('research_build'),'m6_research_build':m6.get('research_build'),
        'm4_validated_positions':[r.get('position') for r in (m4.get('final_position_models') or {}).get('aggregate',[]) if r.get('status')=='validated_candidate'],
        'm6_validated_candidate_positions':(m6.get('advanced_second_wave') or {}).get('validated_candidate_positions',[]),
        'artifact_paths':artifact_paths,
        'artifact_sha256':{k:sha256_file(v) for k,v in artifact_paths.items()},
        'audit_rule':'Feature lists, coefficients, sample sizes and holdout metrics remain versioned in the league-scoped milestone bundles; promotion requires matching League ID, profile fingerprint, scoring and hashes.'
      },
      'rollback':{'mode':'CONTROL','operator_override':args.operator_override,'global_operator_override':getattr(args,'global_operator_override',None),'effect':'All M5/M6 decision overrides disabled; V8.2.2 remains live fallback.','code_change_required':False},
      'promotion':{'mode':'AUTO','rule':'Every namespace, scoring, freshness and decision-gate check must pass on each rebuild; failure automatically falls back.'},
    }

def parse_args(argv=None):
    p=argparse.ArgumentParser(description='Build FIE permanent runtime governance manifest')
    p.add_argument('--league-id',default=None);p.add_argument('--league-profile',default=None)
    p.add_argument('--m4-bundle',default='data/research/milestone4.json');p.add_argument('--m5-bundle',default='data/research/milestone5.json');p.add_argument('--m6-bundle',default='data/research/milestone6.json')
    p.add_argument('--current-snapshot',default='data/research/current/milestone5_current.json');p.add_argument('--operator-override',default='data/research/governance/operator_override.json');p.add_argument('--global-operator-override',default='data/research/governance/operator_override.json');p.add_argument('--output',default='data/research/governance/active_release.json')
    p.add_argument('--mode',choices=['KEEP','AUTO','CONTROL'],default='KEEP');p.add_argument('--max-age-hours',type=float,default=18.0);p.add_argument('--persist-mode',action='store_true')
    return p.parse_args(argv)

def main(argv=None):
    a=parse_args(argv)
    if a.persist_mode and a.mode in {'AUTO','CONTROL'}:
        write(a.operator_override,{'schema_version':1,'mode':a.mode,'updated_at':iso(),'note':'League-specific runtime override. Global CONTROL still wins.'})
    b=build(a);write(a.output,b);print(f"Wrote {a.output} league={b['league_id']} mode={b['operator_mode']} runtime_enabled={b['runtime_enabled']} reason={b['reason']}")
if __name__=='__main__':main()
