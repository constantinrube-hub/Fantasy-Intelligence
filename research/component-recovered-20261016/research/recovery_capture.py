"""Immutable, week-parameterized source capture for generation and actual review."""
import argparse,concurrent.futures,hashlib,json
from pathlib import Path
from urllib.request import Request,urlopen
from recovery_common import *
from prospective_research_io import response
def capture(output,start=6,through=None,root=ROOT,actual_week=None):
    through=start-1 if through is None else through
    if not 1<=start<=16 or not 0<=through<=18:raise ValueError('INVALID_CAPTURE_SCOPE')
    folder=root/output
    if folder.exists() and any(folder.iterdir()):raise ValueError('NEW_CAPTURE_DIRECTORY_REQUIRED')
    folder.mkdir(parents=True,exist_ok=True)
    registry=read(root/'data/research/leagues/registry.json')['leagues'];leagues=sorted(k for k,v in registry.items() if v.get('enabled') is True)
    if len(leagues)!=23:raise ValueError('REGISTRY_23_REQUIRED')
    nfl='https://github.com/nflverse/nflverse-data/releases/download/'
    jobs=[('schedule','https://raw.githubusercontent.com/nflverse/nfldata/master/data/games.csv','csv',{}),('players',nfl+'players/players.csv','csv',{}),('ff_playerids','https://raw.githubusercontent.com/dynastyprocess/data/master/files/db_playerids.csv','csv',{}),('player_week',nfl+'stats_player/stats_player_week_2026.csv','csv',{}),('weekly_rosters',nfl+'weekly_rosters/roster_weekly_2026.csv','csv',{}),('pbp',nfl+'pbp/play_by_play_2026.csv','csv',{}),('snaps',nfl+'snap_counts/snap_counts_2026.csv','csv',{}),('sleeper_players','https://api.sleeper.app/v1/players/nfl','json',{})]
    if actual_week is not None:jobs.append(('sleeper_actual',f'https://api.sleeper.app/v1/stats/nfl/regular/2026/{actual_week}','json',{'actual_week':actual_week}))
    for week in range(start,start+3):jobs.append((f'sleeper_projections_week_{week}',f'https://api.sleeper.com/projections/nfl/2026/{week}?season_type=regular','json',{'target_week':week}))
    for lid in leagues:
        for role,suffix in [('profile',''),('rosters','/rosters'),('users','/users'),('matchups',f'/matchups/{start}'),('transactions',f'/transactions/{start}')]:jobs.append((lid+'-'+role,'https://api.sleeper.app/v1/league/'+lid+suffix,'json',{'league_id':lid,'role':role}))
    started=now();refs=[];failed=[]
    def one(job):
        name,url,kind,meta=job
        with urlopen(Request(url,headers={'User-Agent':'FIE-Component-Recovery/2'}),timeout=90) as f:raw=f.read()
        observed=now()
        if kind=='json':json.loads(raw)
        elif not raw.splitlines() or b',' not in raw.splitlines()[0] or raw.lstrip().startswith(b'<'):raise ValueError('SOURCE_NOT_CSV')
        return {'name':name,**meta,**response(root,folder/'raw'/hashlib.sha256(raw).hexdigest(),name,url,raw,observed,kind)}
    with concurrent.futures.ThreadPoolExecutor(max_workers=6) as pool:
        tasks={pool.submit(one,job):job[0] for job in jobs}
        for f in concurrent.futures.as_completed(tasks):
            try:refs.append(f.result())
            except Exception as exc:failed.append({'name':tasks[f],'error':str(exc)})
    bundle={'schema':'fie-component-observation-bundle-v2','season':2026,'target_weeks':list(range(start,start+3)),'history_through_week':through,'capture_started_at':started,'observation_cutoff':now(),'league_ids':leagues,'responses':sorted(refs,key=lambda x:x['name']),'failures':failed,'research_only':True,'actual_week':actual_week}
    write(folder/'observation-bundle.json',bundle);print('CAPTURE',len(refs),'responses',len(failed),'unavailable');return bundle
if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--output',type=Path,required=True);p.add_argument('--start-week',type=int,default=6);p.add_argument('--actual-week',type=int);a=p.parse_args();capture(a.output,a.start_week,actual_week=a.actual_week)
