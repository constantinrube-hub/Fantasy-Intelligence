#!/usr/bin/env python3
"""Bounded final release gate for the browser repository."""
from __future__ import annotations
import argparse,json,subprocess,sys,os,shutil
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
def run(cmd,timeout=90):
 try:
  env={**os.environ,'PYTHONDONTWRITEBYTECODE':'1'};p=subprocess.run(cmd,cwd=ROOT,text=True,capture_output=True,timeout=timeout,env=env)
  return {'cmd':' '.join(cmd),'ok':p.returncode==0,'code':p.returncode,'stdout':p.stdout[-2500:],'stderr':p.stderr[-2500:]}
 except subprocess.TimeoutExpired:return {'cmd':' '.join(cmd),'ok':False,'timeout':True,'stdout':'','stderr':f'timeout after {timeout}s'}
def main():
 ap=argparse.ArgumentParser();ap.add_argument('--json-output',default='config/release-gate.json');a=ap.parse_args()
 for d in ROOT.rglob('__pycache__'):
  if d.is_dir(): shutil.rmtree(d,ignore_errors=True)
 checks=[
  run([sys.executable,'research/production_readiness.py']),
  run([sys.executable,'research/integrity_build_manifest_test.py']),
  run(['node','research/integrity_runtime_foundation_test.js']),
  run(['node','research/integrity_league_switch_runtime_test.js']),
  run(['node','research/integrity_v9_model_runtime_test.js']),
  run(['node','research/integrity_decision_service_test.js']),
  run([sys.executable,'research/integrity_structural_profile_test.py']),
  run([sys.executable,'research/integrity_release_versions_test.py']),
  run([sys.executable,'research/integrity_dist_hygiene_test.py']),
  run([sys.executable,'research/integrity_current_storage_test.py']),
  run(['node','research/integrity_monte_carlo_worker_test.js']),
  run([sys.executable,'research/integrity_decision_engines_test.py']),
  run([sys.executable,'research/integrity_v89_test.py']),
  run([sys.executable,'research/integrity_m5_test.py']),
  run([sys.executable,'research/integrity_m6_test.py']),
  run([sys.executable,'research/integrity_scoring_relevance_test.py']),
  run([sys.executable,'research/integrity_dst_test.py']),
  run([sys.executable,'research/integrity_kicker_test.py']),
  run([sys.executable,'research/integrity_value_finder_test.py']),
  run([sys.executable,'research/integrity_v93_decision_ux_test.py']),
  run(['node','research/integrity_v93_scarcity_runtime_test.js']),
  run(['node','research/integrity_v93_league_context_runtime_test.js']),
  run(['node','research/integrity_v93_decision_ui_runtime_test.js']),
  run(['node','research/integrity_value_finder_runtime_test.js']),
  run(['node','research/integrity_top100_optimizer_runtime_test.js']),
 ]
 # Hygiene: release output only and no backup/cache files.
 bad=[str(p.relative_to(ROOT)) for p in ROOT.rglob('*') if p.is_file() and ('.pre_' in p.name or p.suffix in {'.pyc','.pyo'} or '__pycache__' in p.parts)]
 checks.append({'cmd':'artifact hygiene','ok':not bad,'stderr':'\n'.join(bad[:100]),'stdout':''})
 dist=ROOT/'dist'; forbidden=[]
 if not dist.exists(): forbidden=['dist missing']
 else:
  for p in dist.rglob('*'):
   if not p.is_file():continue
   rel=str(p.relative_to(dist))
   if rel.startswith(('research/','docs/','.github/')) or p.suffix in {'.py','.pyc'}:forbidden.append(rel)
 checks.append({'cmd':'dist hygiene','ok':not forbidden,'stderr':'\n'.join(forbidden[:100]),'stdout':''})
 ok=all(c['ok'] for c in checks)
 result={'status':'DEPLOYABLE_SOURCE' if ok else 'BLOCKED','browser_preview_required':True,'checks':checks}
 out=ROOT/a.json_output;out.parent.mkdir(parents=True,exist_ok=True);out.write_text(json.dumps(result,indent=2)+'\n');print(json.dumps(result,indent=2));raise SystemExit(0 if ok else 1)
if __name__=='__main__':main()
