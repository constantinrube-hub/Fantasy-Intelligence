"""Deterministic serving adapter scope and non-promotion tests, no provider calls."""
import json,tempfile,sys,hashlib
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'tools'))
from build_waiver_ui_evidence import build,DOCS
with tempfile.TemporaryDirectory() as d:
 root=Path(d)/'source';dest=Path(d)/'dist';p=root/'data/research/evaluation/2026/weeks/week-3/waivers/portfolio-latest.json';p.parent.mkdir(parents=True)
 report={'season':2026,'week':3,'generated_at':'2026-09-20','capture_id':'archive','leagues':[{'league_id':'L','status':'BLOCKED_PROFILE_DRIFT','research_only':True}]};p.write_text(json.dumps(report));before=p.read_bytes()
 hp=root/'data/research/evaluation/2026/waivers/history/league-L.json';hp.parent.mkdir(parents=True);good={'source_league_id':'L','season':2026,'week':3,'winning_claim':{'bid':0}}
 hp.write_text(json.dumps({'portfolio_league_id':'L','target_season':2026,'bid_ledger':[good,{**good,'source_league_id':'prior'},{**good,'season':2025}]}))
 dp=root/'docs/audits'/f'{DOCS[0]}.md';dp.parent.mkdir(parents=True);dp.write_text('# Method\n<script>literal</script>')
 index=build(root,dest);assert index['portfolio_reports'][0]['league_statuses']['L']=='BLOCKED_PROFILE_DRIFT';data=json.loads((dest/index['leagues']['L']).read_text());assert data['reports'][0]['report']['status']=='BLOCKED_PROFILE_DRIFT';assert data['history'][0]['ledger']==[good];assert data['reporting_only'] is True;assert p.read_bytes()==before
 assert data['reports'][0]['source']['sha256']==hashlib.sha256(before).hexdigest();first=(dest/index['leagues']['L']).read_bytes();build(root,dest);assert first==(dest/index['leagues']['L']).read_bytes()
 public=Path(d)/'public';pi=build(root,public,'public');assert pi['leagues']=={};assert pi['portfolio_reports']==[];assert not(public/'data/ui/waivers/leagues').exists();assert pi['documents'];build(root,dest,'public');assert not(dest/'data/ui/waivers/leagues').exists()
print('PASS editorial waiver serving: scope, byte bindings, immutable source, deterministic derivative, public exclusion')
