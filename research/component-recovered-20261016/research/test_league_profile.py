#!/usr/bin/env python3
import json, subprocess, sys, tempfile
from pathlib import Path

HERE=Path(__file__).resolve().parent
with tempfile.TemporaryDirectory() as td:
    td=Path(td); out=td/'profile.json'; reg=td/'registry.json'
    subprocess.run([sys.executable,str(HERE/'league_profile.py'),'fixture','--league-id','123456789012345678','--format','REDRAFT','--output',str(out),'--registry',str(reg)],check=True,stdout=subprocess.DEVNULL)
    p=json.loads(out.read_text()); r=json.loads(reg.read_text())
    assert p['league_id']=='123456789012345678'
    assert p['format']=='REDRAFT'
    assert len(p['scoring_signature'])==16
    assert len(p['profile_fingerprint'])==64
    assert r['leagues'][p['league_id']]['profile_fingerprint']==p['profile_fingerprint']
print('league profile fixture: PASS')
