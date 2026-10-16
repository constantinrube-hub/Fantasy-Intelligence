"""Read-only live C4 observation bundle; all three Sleeper endpoints are attempted."""
from __future__ import annotations
import argparse
from concurrent.futures import ThreadPoolExecutor,as_completed
import hashlib
import json
from pathlib import Path
from urllib.request import Request,urlopen
from urllib.error import HTTPError
from prospective_research_io import now,clock,response,write,gates

ROOT=Path(__file__).resolve().parents[1]
BASE=Path('data/research/components/2026-10-14/c2-c4-v1/captures')
NFL='https://github.com/nflverse/nflverse-data/releases/download/'
GLOBALS={
 'schedule':('https://raw.githubusercontent.com/nflverse/nfldata/master/data/games.csv','csv'),
 'players':(NFL+'players/players.csv','csv'),
 'ff_playerids':('https://raw.githubusercontent.com/dynastyprocess/data/master/files/db_playerids.csv','csv'),
 'player_week':(NFL+'stats_player/stats_player_week_2026.csv','csv'),
 'weekly_rosters':(NFL+'weekly_rosters/roster_weekly_2026.csv','csv'),
 'pbp':(NFL+'pbp/play_by_play_2026.csv','csv'),
 'snaps':(NFL+'snap_counts/snap_counts_2026.csv','csv'),
 'sleeper_players':('https://api.sleeper.app/v1/players/nfl','json'),
}

def fetch_one(root,folder,name,url,kind,metadata):
    request=Request(url,headers={'User-Agent':'FIE-Component-Forecast-Research/1.0'})
    with urlopen(request,timeout=120 if kind=='csv' else 45) as r:raw=r.read()
    observed=now()
    if kind=='json':json.loads(raw)
    elif b',' not in raw.splitlines()[0] or raw.lstrip().startswith(b'<'):
        raise ValueError('COMPONENT_OBSERVATION_INVALID_CSV')
    raw_folder=folder/'raw'/hashlib.sha256(raw).hexdigest()
    ref={'name':name,**metadata,**response(root,raw_folder,name,url,raw,observed,kind)}
    write(folder/'receipts'/(name+'.json'),ref);return ref

def capture(root,output=None):
    started=now();stamp=clock(started).strftime('%Y%m%dT%H%M%S%fZ')
    folder=root/(output or BASE/stamp);folder.mkdir(parents=True,exist_ok=True)
    if (folder/'observation-bundle.json').exists():raise ValueError('C4_NEW_OBSERVATION_DIRECTORY_REQUIRED')
    registry=json.loads((root/'data/research/leagues/registry.json').read_text())['leagues']
    leagues=sorted(k for k,v in registry.items() if v.get('enabled') is True)
    if len(leagues)!=23:raise ValueError('C4_LEAGUE_COUNT_DRIFT')
    jobs=[(n,u,k,{}) for n,(u,k) in GLOBALS.items()]
    for week in [6,7,8]:
        name='sleeper_projections' if week==6 else 'sleeper_projections_week_'+str(week)
        jobs.append((name,f'https://api.sleeper.com/projections/nfl/2026/{week}?season_type=regular','json',{'target_week':week}))
    for lid in leagues:
        for role,suffix in [('profile',''),('rosters','/rosters'),('users','/users'),('matchups','/matchups/6'),('transactions','/transactions/6')]:
            jobs.append((lid+'-'+role,'https://api.sleeper.app/v1/league/'+lid+suffix,'json',{'league_id':lid,'role':role}))
    refs=[];failures=[]
    write(folder/'capture-start.json',{'started_at':started,'target_weeks':[6,7,8],'status':'OBSERVING','research_only':True})
    with ThreadPoolExecutor(max_workers=6) as pool:
        futures={pool.submit(fetch_one,root,folder,*job):job[0] for job in jobs}
        for f in as_completed(futures):
            try:refs.append(f.result())
            except Exception as exc:failures.append({'name':futures[f],'error':str(exc),'observed_at':now()})
            if (len(refs)+len(failures))%20==0:print('C4_OBSERVATIONS',len(refs),'observed',len(failures),'unavailable',flush=True)
    cutoff=now();refs.sort(key=lambda r:r['name'])
    value={'schema':'fie-component-observation-bundle-v1','season':2026,'target_weeks':[6,7,8],
           'capture_started_at':started,'observation_cutoff':cutoff,'league_ids':leagues,
           'responses':refs,'failures':failures,'future_projection_policy':'MISSING_RECORDED_NO_EXTRAPOLATION',
           'source_registry_sha256':hashlib.sha256((root/'data/research/leagues/registry.json').read_bytes()).hexdigest(),
           'research_only':True,'transaction_eligible':False}
    write(folder/'observation-bundle.json',value)
    # The unchanged direct-owner validator consumes this canonical subset.
    env={'schema':'fie-weekly-research-source-envelope-v1','season':2026,'week':6,'capture_started_at':started,
         'captured_at':cutoff,'league_ids':leagues,'responses':[r for r in refs if r.get('target_week',6)==6],
         'failures':[f for f in failures if not f['name'].endswith(('_week_7','_week_8'))],
         'status':'RAW_CAPTURED' if not failures else 'PARTIAL','history_weeks_requested':[1,2,3,4,5],
         **gates(['BLOCKED_RESEARCH_ONLY'])}
    write(folder/'source-envelope.json',env)
    print('C4_OBSERVATION_BUNDLE',str((folder/'observation-bundle.json').relative_to(root)),flush=True)
    return folder/'observation-bundle.json'

def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--root',type=Path,default=ROOT)
    p.add_argument('--output',type=Path);a=p.parse_args();capture(a.root.resolve(),a.output)

if __name__=='__main__':main()
