"""Archive consumed historical fields and exact provider scoring-scope evidence."""
from __future__ import annotations
import argparse,ast,gc,gzip,hashlib,io,json,re,tempfile,uuid
from pathlib import Path
import pandas as pd,requests
from prospective_research_io import sha,write,now,verified
from waiver_v2_source_adapter import normalize_player_stats

ROOT=Path(__file__).resolve().parents[1]
BASE='data/research/waiver-expanded/2026/recovery-1'
YEARS=[2018,2021,2022,2023,2024,2025]
PREFIX='https://github.com/nflverse/nflverse-data/releases/download/'
def get(url):
    r=requests.get(url,timeout=(20,180));r.raise_for_status();return r.content,now()
def csv(frame,path):
    path.parent.mkdir(parents=True,exist_ok=True)
    temp=path.with_name(path.name+'.writing-'+uuid.uuid4().hex)
    with temp.open('wb') as binary:
        with gzip.GzipFile(filename='',mode='wb',fileobj=binary,mtime=0) as compressed:
            with io.TextIOWrapper(compressed,encoding='utf-8',newline='') as text:
                frame.to_csv(text,index=False)
    with gzip.open(temp,'rb') as check:
        while check.read(1024*1024):pass
    temp.replace(path)

def archive(root):
    folder=root/BASE/'sources';folder.mkdir(parents=True,exist_ok=True);receipts=[];rawstats=[]
    manifest=folder/'source-receipts.json'
    if manifest.exists():
        prior=json.loads(manifest.read_text())
        for ref in prior['pbp_sources']+prior['raw_player_stats']+prior['scoring_scope']+[prior['games'],prior['field_goal_return_audit']]:verified(root,ref,now())
        for path in folder.glob('*.gz'):
            with gzip.open(path,'rb') as stream:
                while stream.read(1024*1024):pass
        print('ARCHIVE_PRESERVED_VERIFIED',flush=True);return prior
    strings=set()
    for name in ['waiver_v2_event_ledger.py','waiver_v2_population.py','waiver_v2_source_adapter.py','waiver_v2_scoped_sources.py']:
        for node in ast.walk(ast.parse((root/'research'/name).read_text())):
            if isinstance(node,ast.Constant) and isinstance(node.value,str):strings.add(node.value)
    strings.update(['field_goal_attempt','field_goal_result','play_type_nfl','desc'])
    for year in YEARS:
        path=folder/f'pbp-{year}.csv.gz';receipt=folder/f'pbp-{year}-receipt.json';url=PREFIX+f'pbp/play_by_play_{year}.parquet'
        if not receipt.exists():
            raw,at=get(url)
            with tempfile.TemporaryDirectory() as tmp:
                parquet=Path(tmp)/'pbp.parquet';parquet.write_bytes(raw);original=hashlib.sha256(raw).hexdigest();del raw
                frame=pd.read_parquet(parquet)
                columns=[c for c in frame if c in strings or c.endswith('_player_id')]
                csv(frame[columns],path);del frame;gc.collect()
            write(receipt,{'season':year,'url':url,'path':path.relative_to(root).as_posix(),'sha256':sha(path),'observed_at':at,
                           'original_download_sha256':original,'snapshot_kind':'CONSUMED_FIELD_PROJECTION','columns':columns})
        item=json.loads(receipt.read_text());assert sha(path)==item['sha256'];receipts.append(item)
        path=folder/f'player-stats-raw-{year}.csv.gz';receipt=folder/f'player-stats-raw-{year}-receipt.json';url=PREFIX+f'stats_player/stats_player_week_{year}.csv'
        if not receipt.exists():
            raw,at=get(url);frame=pd.read_csv(io.BytesIO(raw),low_memory=False);csv(frame,path);del raw,frame;gc.collect()
            write(receipt,{'season':year,'path':path.relative_to(root).as_posix(),'sha256':sha(path),'url':url,'observed_at':at})
        item=json.loads(receipt.read_text());assert sha(path)==item['sha256'];rawstats.append(item)
        print('ARCHIVED_SOURCE_YEAR',year,flush=True)
    raw=pd.concat([pd.read_csv(root/i['path'],low_memory=False) for i in rawstats],ignore_index=True)
    ids=sorted(set(raw.player_id.dropna().astype(str)));ids=[x for x in ids if re.fullmatch(r'00-\d{7}',x)]
    identity=pd.DataFrame({'gsis_id':ids,'canonical_player_id':ids})
    allstats,_=normalize_player_stats(raw,identity,offensive_only=False);stats=allstats[allstats.position_model.isin(['QB','RB','WR','TE'])].copy()
    csv(identity,folder/'identity.csv.gz');csv(allstats,folder/'all-position-stats.csv.gz');csv(stats,folder/'offensive-stats.csv.gz')
    games=folder/'games.csv.gz'
    if not games.exists():
        raw,at=get('https://raw.githubusercontent.com/nflverse/nfldata/master/data/games.csv');csv(pd.read_csv(io.BytesIO(raw)),games)
        write(folder/'games-receipt.json',{'path':games.relative_to(root).as_posix(),'sha256':sha(games),'observed_at':at,'url':'https://raw.githubusercontent.com/nflverse/nfldata/master/data/games.csv'})
    scope=[]
    for year,week in [(2018,16),(2021,3),(2021,17),(2023,12),(2023,17),(2024,4),(2024,10),(2024,13),(2024,15),(2025,6)]:
        path=folder/f'sleeper-fg-scope-{year}-{week:02d}.json.gz';receipt=path.with_suffix('.receipt.json')
        if not receipt.exists():
            url=f'https://api.sleeper.com/stats/nfl/{year}/{week}?season_type=regular';raw,at=get(url);payload=json.loads(raw)
            if not isinstance(payload,list):raise ValueError('SCORING_SCOPE_PROVIDER_SCHEMA')
            detected=[{'player_id':r['player_id'],'fg_ret_yd':float(r['stats']['fg_ret_yd'])} for r in payload if r.get('stats',{}).get('fg_ret_yd')]
            path.write_bytes(gzip.compress(raw,mtime=0));write(receipt,{'path':path.relative_to(root).as_posix(),'sha256':sha(path),
                'raw_sha256':hashlib.sha256(raw).hexdigest(),'observed_at':at,'endpoint':url,'nonzero_fg_ret_yd':detected})
        scope.append(json.loads(receipt.read_text()))
    if not any(r['nonzero_fg_ret_yd'] for r in scope) or any(not re.fullmatch(r'[A-Z]{2,3}',r['player_id']) for ref in scope for r in ref['nonzero_fg_ret_yd']):raise ValueError('FG_SCOPE_NOT_PROVEN_TEAM_ONLY')
    fg=[]
    for ref in receipts:
        f=pd.read_csv(root/ref['path'],usecols=['season','week','game_id','play_id','season_type','desc','return_yards'],low_memory=False)
        mask=f.season_type.eq('REG')&f.desc.str.contains('field goal',case=False,na=False)&f.desc.str.contains('No Good',case=False,na=False)&f.desc.str.contains('for [0-9]+ yards',case=False,na=False)&~f.desc.str.contains('BLOCKED',case=False,na=False)
        for row in f[mask].itertuples(index=False):fg.append({'season':int(row.season),'week':int(row.week),'game_id':row.game_id,'play_id':row.play_id,'description':row.desc,'description_yards':int(re.findall(r'for (\d+) yards',row.desc,re.I)[-1]),'structured_return_yards':row.return_yards})
    audit={'schema':'fie-field-goal-return-scope-audit-v1','event_count':len(fg),'description_yards':sum(r['description_yards'] for r in fg),'events':fg,'basis':'DESCRIPTION_CANDIDATES_NOT_EXACT_DST_SCORING_LEDGER','dst_reconciliation':'UNRESOLVED','offensive_scope':False}
    write(folder/'field-goal-return-audit.json',audit)
    write(folder/'source-receipts.json',{'training_seasons':YEARS,'publication_time_verified':False,'pbp_sources':receipts,'raw_player_stats':rawstats,
        'scoring_scope':scope,'games':json.loads((folder/'games-receipt.json').read_text()),'field_goal_return_audit':{'path':(folder/'field-goal-return-audit.json').relative_to(root).as_posix(),'sha256':sha(folder/'field-goal-return-audit.json'),'observed_at':now()}})
    print('ARCHIVE_COMPLETE',len(stats),'offensive rows',len(fg),'FG description candidates',flush=True)
if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--root',type=Path,default=ROOT);a=p.parse_args();archive(a.root)
