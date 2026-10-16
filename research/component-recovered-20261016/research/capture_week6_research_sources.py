"""Prospective raw football, league, specialist and auction evidence capture."""
from __future__ import annotations
import argparse
import hashlib
import io
import json
from pathlib import Path
import pandas as pd
import requests
from prospective_research_io import now, clock, response, replay_response, write, gates

ROOT = Path(__file__).resolve().parents[1]
NFLVERSE = 'https://github.com/nflverse/nflverse-data/releases/download/'
SOURCES = {
    'schedule': ('https://raw.githubusercontent.com/nflverse/nfldata/master/data/games.csv', 'csv'),
    'players': (NFLVERSE+'players/players.csv', 'csv'),
    'ff_playerids': ('https://raw.githubusercontent.com/dynastyprocess/data/master/files/db_playerids.csv', 'csv'),
    'player_week': (NFLVERSE+'stats_player/stats_player_week_{season}.csv', 'csv'),
    'weekly_rosters': (NFLVERSE+'weekly_rosters/roster_weekly_{season}.csv', 'csv'),
    'pbp': (NFLVERSE+'pbp/play_by_play_{season}.csv', 'csv'),
    'snaps': (NFLVERSE+'snap_counts/snap_counts_{season}.csv', 'csv'),
    'sleeper_players': ('https://api.sleeper.app/v1/players/nfl', 'json'),
}


def fetch(url):
    r = requests.get(url, timeout=(20,180) if url.endswith('.csv') else (10,35), headers={'User-Agent':'FIE-Prospective-Research/1.0'})
    r.raise_for_status()
    return r.content, now()


def validate_manifest(root, manifest_path):
    manifest = json.loads(Path(manifest_path).read_text())
    if manifest.get('schema') != 'fie-weekly-research-source-envelope-v1':
        raise ValueError('RESEARCH_SOURCE_ENVELOPE_SCHEMA')
    cutoff = manifest['captured_at']
    if not manifest.get('research_only') or manifest.get('transaction_eligible') is not False:
        raise ValueError('RESEARCH_SOURCE_AUTHORITY')
    seen = set()
    for item in manifest['responses']:
        if item['name'] in seen:
            raise ValueError('RESEARCH_RESPONSE_DUPLICATE')
        seen.add(item['name'])
        if item['name'] in SOURCES:
            expected = SOURCES[item['name']][0].format(season=manifest['season'])
        elif item['name'] == 'sleeper_projections':
            expected = f"https://api.sleeper.com/projections/nfl/{manifest['season']}/{manifest['week']}?season_type=regular"
        else:
            league = item.get('league_id')
            if league not in manifest['league_ids']:
                raise ValueError('RESEARCH_RESPONSE_LEAGUE_DRIFT')
            role = item.get('role')
            if role not in {'profile','rosters','users','matchups','transactions'}:
                raise ValueError('RESEARCH_RESPONSE_ROLE_DRIFT')
            suffix = {'profile':'','rosters':'/rosters','users':'/users','matchups':f"/matchups/{manifest['week']}",
                      'transactions':f"/transactions/{manifest['week']}"}[role]
            expected = f'https://api.sleeper.app/v1/league/{league}{suffix}'
        if item['endpoint'] != expected:
            raise ValueError('RESEARCH_ENDPOINT_DRIFT')
        replay_response(root, item, cutoff)
    return manifest


def capture(root, season, week, *, fetcher=fetch, league_ids=None):
    if not 1 <= week <= 18 or season < 2026:
        raise ValueError('RESEARCH_CAPTURE_TARGET')
    if league_ids is None:
        registry = json.loads((root/'data/research/leagues/registry.json').read_text())['leagues']
        league_ids = sorted(k for k,v in registry.items() if v.get('enabled') is True)
    if len(set(league_ids)) != len(league_ids) or any(not str(x).isdigit() for x in league_ids):
        raise ValueError('RESEARCH_CAPTURE_LEAGUE_IDS')
    started = now()
    stamp = clock(started).strftime('%Y%m%dT%H%M%S%fZ')
    folder = root/f'data/research/prospective/weekly-sources/{season}/week_{week:02d}/{stamp}'
    write(folder/'capture-start.json',{'season':season,'week':week,'started_at':started,'league_ids':league_ids,
                                      'status':'IN_PROGRESS','research_only':True})
    responses, failures = [], []
    def get(name, url, kind, **metadata):
        try:
            raw, observed = fetcher(url)
            if not raw:
                raise ValueError('EMPTY_RESPONSE')
            if kind == 'json':
                json.loads(raw)
            else:
                header = raw.decode('utf-8-sig').splitlines()[0]
                if ',' not in header or header.lstrip().startswith('<'):
                    raise ValueError('INVALID_CSV_RESPONSE')
            raw_folder=root/f'data/research/prospective/weekly-sources/raw/{season}/{hashlib.sha256(raw).hexdigest()}'
            item={'name':name, **metadata, **response(root,raw_folder,name,url,raw,observed,kind)}
            write(folder/(name+'-response-receipt.json'),item)
            responses.append(item)
        except (requests.RequestException, ValueError, UnicodeError) as error:
            failures.append({'name':name, 'reason':type(error).__name__+':'+str(error)[:250]})
    for name,(url,kind) in SOURCES.items():
        get(name,url.format(season=season),kind)
    get('sleeper_projections',f'https://api.sleeper.com/projections/nfl/{season}/{week}?season_type=regular','json')
    for league in league_ids:
        for role,suffix in [('profile',''),('rosters','/rosters'),('users','/users'),('matchups',f'/matchups/{week}'),('transactions',f'/transactions/{week}')]:
            get(league+'-'+role,f'https://api.sleeper.app/v1/league/{league}{suffix}','json',league_id=league,role=role)
    # The response itself proves only exposed transactions. Failed private bids,
    # availability/intent, and final Best Ball starters remain unverified.
    report = {'schema':'fie-weekly-research-source-envelope-v1','season':season,'week':week,
              'capture_started_at':started,'captured_at':now(),'league_ids':league_ids,
              'responses':responses,'failures':failures,
              'status':'PARTIAL' if failures else 'RAW_CAPTURED',
              'auction_completeness':'EXPOSED_PAYLOAD_ONLY_PRIVATE_FAILED_BIDS_UNVERIFIED',
              'history_weeks_requested':list(range(1,week)),
              'history_completeness':'REQUIRES_GAME_EVENT_AND_SCORING_REPLAY',
              'specialist_strategy_basis':'MIDSEASON_FROZEN_CAPTURE_NOT_PRESEASON_RANK',
              **gates(['BLOCKED_NORMALIZED_SOURCE_REPLAY_REQUIRED','BLOCKED_CALIBRATION_REQUIRED','BLOCKED_PROMOTION_REVIEW_REQUIRED'])}
    path = folder/'source-envelope.json'
    write(path,report)
    validate_manifest(root,path)
    return path


def resolve_target(season, fetcher=fetch):
    from build_current_snapshot import first_kickoff_utc
    raw,_ = fetcher(SOURCES['schedule'][0])
    games = pd.read_csv(io.BytesIO(raw))
    weeks = sorted(set(int(x) for x in games.loc[(games.season==season)&games.game_type.eq('REG'),'week']))
    future = [w for w in weeks if first_kickoff_utc(games,season,w)>clock(now())]
    if not future:
        raise ValueError('NO_FUTURE_REGULAR_SEASON_WEEK')
    return future[0]


def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--root',type=Path,default=ROOT);p.add_argument('--season',type=int,default=2026)
    p.add_argument('--week',type=int);a=p.parse_args()
    week=a.week or resolve_target(a.season)
    path=capture(a.root,a.season,week)
    print(json.dumps({'source_envelope':path.relative_to(a.root).as_posix(),'week':week,'research_only':True}))


if __name__=='__main__': main()
