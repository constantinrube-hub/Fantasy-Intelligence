"""Prepare a reviewable hash commitment; remote publication requires --publish."""
from __future__ import annotations
import argparse
from email.utils import parsedate_to_datetime
import hashlib
import json
import os
from pathlib import Path
import subprocess
import tempfile
from urllib.request import Request,urlopen
import uuid
from prospective_research_io import sha,write,clock,now
from validate_component_forecasts import DEFAULT,ROOT

REPO='constantinrube-hub/Fantasy-Intelligence'
BASE_COMMIT='07adf186fb6cbcd8a8492d1f270783da1e035c20'

def prepare(root,capture):
    manifest=json.loads(capture.read_text());folder=capture.parent.parent;output=folder/'publication/approved-payload-v3.json'
    if output.exists():
        value=json.loads(output.read_text())
        verify(root,value);return output
    closure=folder/'local-closure.json';closed=json.loads(closure.read_text())
    if closed['status']!='C2_C3_C4_LOCAL_CLOSURE_PASSED' or closed['capture_manifest_sha256']!=sha(capture):raise ValueError('PUBLICATION_CLOSURE_REQUIRED')
    base=(root/manifest['model_lock']['path']).parent.parent
    files={p.relative_to(root).as_posix():{'sha256':sha(p),'bytes':p.stat().st_size} for p in sorted(base.rglob('*'))
           if p.is_file() and 'publication' not in p.relative_to(base).parts}
    direct=json.loads((folder/'comparisons/direct-comparator-attempt.json').read_text())
    owners={rel:sha(root/rel) for rel in ['research/publish_component_commitment.py','research/build_component_forecast_board.py',
        'research/validate_component_forecasts.py','research/capture_component_direct_comparison.py',
        'research/integrity_component_baselines_test.py','research/integrity_component_issuance_test.py',
        'research/requirements-components.txt']}
    payload={'schema':'fie-component-c4-remote-hash-commitment-v2','prepared_at':now(),'repository':REPO,
        'purpose':'Pregame SHA256 commitment to complete locally archived forecasts and source/model/validation evidence',
        'full_forecast_and_raw_payloads_uploaded':False,'private_metadata_included':['league IDs','coverage counts','capture clocks','artifact paths and hashes','scoring/model owner hashes'],
        'capture_manifest':manifest,'capture_manifest_sha256':sha(capture),'local_closure_sha256':sha(closure),
        'league_coverage':closed['league_rows'],'user_owned_coverage':closed['user_owned_rows'],
        'provider_comparison_coverage':closed['sleeper_coverage'],
        'direct_comparison':{'status':direct['status'],'rows':direct['rows'],'numeric_rows':direct['numeric_rows'],'same_cutoff':direct['same_cutoff']},
        'files':files,'implementation_owners':owners,'research_only':True,'C5_started':False,'app_integration':False,
        'provider_scoring_certified':False,'review_status':'READY_FOR_EXPLICIT_REPOSITORY_PUBLICATION_APPROVAL'}
    write(output,payload);return output

def verify(root,value):
    for rel,item in value['files'].items():
        path=root/rel
        if Path(rel).is_absolute() or '..' in Path(rel).parts or not path.resolve().is_relative_to(root.resolve()):raise ValueError('PUBLICATION_UNSAFE_PATH')
        if sha(path)!=item['sha256']:raise ValueError('PUBLICATION_DIVERGENT_ARTIFACT:'+rel)
    for rel,expected in value['implementation_owners'].items():
        if sha(root/rel)!=expected:raise ValueError('PUBLICATION_OWNER_DRIFT:'+rel)

def publish(root,payload):
    value=json.loads(payload.read_text());verify(root,value);first=value['capture_manifest']['first_target_kickoff']
    if clock(now())>=clock(first):raise ValueError('PUBLICATION_WINDOW_MISSED_CANNOT_CLAIM_PREGAME_REMOTE_CONFIRMATION')
    def git(*args,env=None):return subprocess.check_output(['git','-C',str(root),*args],env=env,text=True).strip()
    origin=git('remote','get-url','origin').removesuffix('.git').rstrip('/')
    if origin not in {'https://github.com/'+REPO,'git@github.com:'+REPO}:raise ValueError('PUBLICATION_ORIGIN_NOT_APPROVED_REPOSITORY')
    branch='research/component-c4-'+clock(now()).strftime('%Y%m%d-%H%M%S')
    with tempfile.TemporaryDirectory(prefix='fie-component-publication-') as d:
        env={**os.environ,'GIT_INDEX_FILE':str(Path(d)/'index'),'GIT_TERMINAL_PROMPT':'0'}
        rel=payload.relative_to(root).as_posix();blob=git('hash-object','-w',rel,env=env)
        git('read-tree',BASE_COMMIT,env=env);git('update-index','--add','--cacheinfo','100644,'+blob+','+rel,env=env)
        tree=git('write-tree',env=env);commit=git('-c','commit.gpgSign=false','commit-tree',tree,'-p',BASE_COMMIT,
            '-m','research: freeze pregame all-23 component forecast hashes for Weeks 6-8',env=env)
        # This is the only remote mutation. Main and all production pointers stay intact.
        subprocess.run(['git','-C',str(root),'push','origin',commit+':refs/heads/'+branch],env=env,check=True)
        remote=git('ls-remote','origin','refs/heads/'+branch,env=env).split()[0]
        if remote!=commit:raise ValueError('PUBLICATION_REMOTE_HEAD_MISMATCH')
        git('fetch','--no-tags','origin','refs/heads/'+branch,env=env)
        raw=subprocess.check_output(['git','-C',str(root),'show','FETCH_HEAD:'+rel],env=env)
        if hashlib.sha256(raw).hexdigest()!=sha(payload):raise ValueError('PUBLICATION_REMOTE_PAYLOAD_HASH_MISMATCH')
        # Read an independent, uncached GitHub server clock after successful readback.
        request=Request('https://api.github.com/?component_receipt='+uuid.uuid4().hex,method='HEAD',headers={'User-Agent':'FIE-Component-Receipt/1.0','Cache-Control':'no-cache'})
        with urlopen(request,timeout=30) as r:remote_date=r.headers['Date']
        remote_time=parsedate_to_datetime(remote_date).isoformat();local_time=now()
        if abs((clock(local_time)-clock(remote_time)).total_seconds())>300:raise ValueError('PUBLICATION_SERVER_CLOCK_NOT_CURRENT')
        before=clock(remote_time)<clock(first) and clock(local_time)<clock(first)
        receipt={'schema':'fie-component-c4-publication-receipt-v1','status':'PUBLISHED_PRE_KICKOFF_HASH_COMMITMENT' if before else 'PUBLISHED_LATE_NOT_PREGAME_CONFIRMED',
            'repository':REPO,'branch':branch,'commit_sha':commit,'commit_url':'https://github.com/'+REPO+'/commit/'+commit,
            'remote_payload_path':rel,'payload_sha256':sha(payload),'capture_manifest_sha256':value['capture_manifest_sha256'],
            'remote_head_and_payload_readback_verified':True,'github_server_date':remote_time,'observed_at':local_time,
            'first_target_kickoff':first,'pregame_remote_confirmation':before,'full_payloads_uploaded':False,
            'research_only':True,'C5_started':False}
        write(payload.parent/'receipts'/commit/'receipt.json',receipt);return receipt

if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--root',type=Path,default=ROOT)
    p.add_argument('--capture',type=Path,default=DEFAULT);p.add_argument('--publish',action='store_true',help='Explicitly authorize sharing the prepared hash commitment with the fixed repository')
    a=p.parse_args();root=a.root.resolve();payload=prepare(root,a.capture.resolve())
    print(json.dumps(publish(root,payload) if a.publish else {'status':'PREPARED_ONLY_NOT_PUBLISHED','path':str(payload),'sha256':sha(payload),'repository':REPO}))
