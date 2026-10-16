"""Compare two complete issuances, independent of output location and ZIP codec."""
import argparse,gzip,json,math
from pathlib import Path
import numpy as np
from recovery_common import ROOT,sha
def equal(a,b):
    if isinstance(a,bool) or isinstance(b,bool):return a==b
    if isinstance(a,(int,float)) and isinstance(b,(int,float)):return math.isclose(a,b,rel_tol=0,abs_tol=1e-10)
    if isinstance(a,dict) and isinstance(b,dict):return set(a)==set(b) and all(equal(a[k],b[k]) for k in a)
    if isinstance(a,list) and isinstance(b,list):return len(a)==len(b) and all(equal(x,y) for x,y in zip(a,b))
    return a==b
def compare(expected,actual,root=ROOT):
    e=root/expected/'issuance';a=root/actual/'issuance';errors=[];checked=0;json_rows=0
    for name in ['weekly-components','weekly-league-scores','team-ledgers','allocation','three-week-summaries']:
        ep=e/(name+'.jsonl.gz');ap=a/(name+'.jsonl.gz');checked+=1
        if sha(ep)==sha(ap):
            with gzip.open(ep) as f:json_rows+=sum(1 for _ in f)
            continue
        with gzip.open(ep,'rt') as ef,gzip.open(ap,'rt') as af:
            import itertools
            for x,y in itertools.zip_longest(ef,af):
                json_rows+=1
                if x is None or y is None or not equal(json.loads(x),json.loads(y)):errors.append(name+':row'+str(json_rows))
    names={p.name for p in (e/'draws').glob('*.npz')}
    if names!={p.name for p in (a/'draws').glob('*.npz')}:errors.append('DRAW_POPULATION_MISMATCH')
    for name in sorted(names):
        ep=e/'draws'/name;ap=a/'draws'/name;checked+=1
        if sha(ep)==sha(ap):continue
        with np.load(ep) as ez,np.load(ap) as az:
            if set(ez.files)!=set(az.files):errors.append(name+':fields');continue
            for key in ez.files:
                if not np.array_equal(ez[key],az[key]):errors.append(name+':'+key)
    result={'status':'EXACT_REPLAY' if not errors else 'FAIL','artifacts_compared':checked,'table_rows_compared':json_rows,'games':len(names),'errors':errors[:30],'error_count':len(errors)}
    print(json.dumps(result));return result
if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--expected',type=Path,required=True);p.add_argument('--actual',type=Path,required=True);a=p.parse_args();raise SystemExit(compare(a.expected,a.actual)['status']!='EXACT_REPLAY')
