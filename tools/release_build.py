#!/usr/bin/env python3
"""One-command deterministic FIE release build."""
from __future__ import annotations
import argparse,os,subprocess,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
def normalize_deployment_code(root:Path=ROOT)->None:
 """Finalize mutable deployment code bytes before generation and hashing."""
 paths=[root/name for name in ('index.html','_headers','_routes.json')]
 paths.extend(p for p in sorted((root/'app').rglob('*')) if p.is_file() and p.suffix in {'.js','.css'})
 changed=[]
 for path in paths:
  if not path.exists():continue
  raw=path.read_bytes();canonical=raw.replace(b'\r\n',b'\n')
  if raw!=canonical:
   path.write_bytes(canonical);changed.append(str(path.relative_to(root)))
 if changed:print(f'Normalized {len(changed)} deployment code files to LF before hashing',flush=True)
def run(*args:str)->None:
 cmd=[sys.executable if args[0]=='python' else args[0],*args[1:]]
 print('+',' '.join(map(str,cmd)),flush=True)
 env={**os.environ,'PYTHONDONTWRITEBYTECODE':'1'}
 subprocess.run(cmd,cwd=ROOT,env=env,check=True)
def main()->None:
 ap=argparse.ArgumentParser();ap.add_argument('--mode',choices=['personal','public'],default='personal');ns=ap.parse_args()
 normalize_deployment_code()
 run('python','research/integrity_app_shell_test.py','--source-only')
 run('python','research/generate_runtime_contracts.py')
 run('python','research/generate_model_config.py')
 run('python','research/generate_release_descriptor.py')
 run('python','research/build_app_manifest.py')
 run('python','tools/build_dist.py','--mode',ns.mode)
 run('python','tools/sync_league_app_snapshots.py')
 run('python','research/release_gate.py')
 print(f'RELEASE BUILD COMPLETE: mode={ns.mode} output=dist/')
if __name__=='__main__':main()
