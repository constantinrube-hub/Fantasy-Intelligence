"""Additional consumed PBP fields for certified C2 event-zero denominators."""
from __future__ import annotations
import argparse
from concurrent.futures import ThreadPoolExecutor, as_completed
import hashlib
import io
import json
from pathlib import Path
from urllib.request import urlopen
import pandas as pd
import pyarrow.parquet as pq
from build_component_outcomes import csv, verified
from prospective_research_io import now, write, sha

ROOT=Path(__file__).resolve().parents[1]
BASE=Path('data/research/components/2026-10-14/c2-c4-v1/priors/sources')
FIELDS={
 'season','week','game_id','play_id','season_type','home_team','away_team','posteam','defteam',
 'play_type','play_type_nfl','play_deleted','desc','down','game_seconds_remaining',
 'total_home_score','total_away_score','posteam_score_post','defteam_score_post',
 'pass_attempt','rush_attempt','complete_pass','interception','fumble','fumble_lost',
 'fumble_forced','fumble_out_of_bounds','touchdown','pass_touchdown','rush_touchdown',
 'return_touchdown','special_teams_play','two_point_attempt','two_point_conv_result',
 'field_goal_attempt','field_goal_result','extra_point_attempt','extra_point_result',
 'kick_distance','punt_blocked','safety','tackled_for_loss','qb_hit','solo_tackle',
 'assist_tackle','tackle_with_assist','fourth_down_failed','fourth_down_converted',
 'first_down_pass','first_down_rush','passing_yards','receiving_yards','rushing_yards',
 'lateral_receiving_yards','lateral_rushing_yards','return_yards','return_team',
 'fumble_recovery_1_team','fumble_recovery_2_team','fumble_recovery_1_yards','fumble_recovery_2_yards',
 'forced_fumble_player_1_team','forced_fumble_player_2_team','sack',
}

def capture(root,folder,year):
    receipt=folder/f'pbp-{year}.receipt.json'
    if receipt.exists():
        ref=json.loads(receipt.read_text()); verified(root,ref); return ref
    url=f'https://github.com/nflverse/nflverse-data/releases/download/pbp/play_by_play_{year}.parquet'
    with urlopen(url,timeout=180) as response:raw=response.read()
    observed=now(); original=hashlib.sha256(raw).hexdigest()
    parquet=pq.ParquetFile(io.BytesIO(raw))
    names=parquet.schema_arrow.names
    required=FIELDS | {n for n in names if n.endswith('_player_id')}
    if FIELDS-set(names):
        raise ValueError('COMPONENT_PRIOR_PBP_SCHEMA_MISSING:'+','.join(sorted(FIELDS-set(names))))
    frame=parquet.read(columns=[n for n in names if n in required]).to_pandas()
    path=folder/f'pbp-{year}.csv.gz'; csv(frame,path)
    ref={'season':year,'path':path.relative_to(root).as_posix(),'sha256':sha(path),'endpoint':url,
         'observed_at':observed,'original_download_sha256':original,'original_download_size':len(raw),
         'snapshot_kind':'CONSUMED_FIELD_PROJECTION','columns':list(frame),
         'original_publication_time_verified':False}
    write(receipt,ref); return ref

def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--root',type=Path,default=ROOT)
    p.add_argument('--folder',type=Path,default=BASE);a=p.parse_args()
    root=a.root.resolve();folder=root/a.folder;folder.mkdir(parents=True,exist_ok=True)
    refs=[]
    with ThreadPoolExecutor(max_workers=2) as pool:
        futures={pool.submit(capture,root,folder,year):year for year in range(2021,2026)}
        for f in as_completed(futures):
            ref=f.result();refs.append(ref);print('C2_PRIOR_SOURCE',ref['season'],flush=True)
    write(folder/'manifest.json',{'schema':'fie-component-prior-sources-v1','sources':sorted(refs,key=lambda r:r['season']),
                                 'purpose':'EVENT_ZERO_EXPOSURE_CERTIFICATION','original_publication_time_verified':False})

if __name__=='__main__':main()
