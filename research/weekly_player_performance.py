#!/usr/bin/env python3
"""All-game retrospective raw player report from immutable nflverse responses.

The stored schedule and existing outcome stabilization buffer select eligibility.
This is descriptive provider evidence, never a pregame feature or league score.
"""
from __future__ import annotations
import argparse
import csv
import gzip
import hashlib
import io
import json
from datetime import datetime, timedelta, timezone
from pathlib import Path
from capture_in_season_pr2_lineup_nflverse_outcomes import STATS_URL, fetch_bytes, canonical_team
from resolve_in_season_pr2_lineup_outcome_target import STABILIZATION_HOURS
from point_in_time_capture import build_envelope, validate_envelope, first_write_json, compact_timestamp, canonical_bytes
from weekly_evidence_audit import schedule, stamp, digest
from weekly_lineup_decision_support import numeric

METRICS = ('completions','attempts','passing_yards','passing_tds','passing_interceptions','sacks_suffered',
           'carries','rushing_yards','rushing_tds','rushing_first_downs','targets','receptions','receiving_yards',
           'receiving_tds','receiving_air_yards','target_share','air_yards_share','receiving_first_downs',
           'fg_made','fg_att','fg_missed','pat_made','kickoff_return_yards','punt_return_yards',
           'fantasy_points','fantasy_points_ppr')


def target_rows(raw: bytes, season: int, week: int) -> list[dict]:
    result = []
    for row in csv.DictReader(io.StringIO(raw.decode('utf-8-sig'))):
        if str(row.get('season'))==str(season) and str(row.get('week'))==str(week) and row.get('season_type')=='REG':
            result.append(row)
    return result


def capture(root: Path, season: int, week: int, as_of: datetime) -> Path:
    games,_=schedule(root,season,week,as_of)
    due=max(stamp(game['kickoff_at']) for game in games)+timedelta(hours=STABILIZATION_HOURS)
    if as_of < due:
        raise ValueError('PERFORMANCE_OUTCOMES_NOT_DUE')
    endpoint=STATS_URL.format(season=season)
    raw=fetch_bytes(endpoint)
    observed=datetime.now(timezone.utc).isoformat()
    rows=target_rows(raw,season,week)
    if not rows:
        raise ValueError('PERFORMANCE_PROVIDER_TARGET_ROWS_UNAVAILABLE')
    base=root/f'data/operations/weekly-performance/{season}/week_{week:02d}/sources'/compact_timestamp(observed)
    raw_path=base/'player-stats.csv.gz';base.mkdir(parents=True,exist_ok=True)
    with raw_path.open('xb') as stream:
        stream.write(gzip.compress(raw,mtime=0))
    value=build_envelope(capture_id=f'weekly-performance-{season}-{week}-{compact_timestamp(observed)}',
        capture_intent='OTHER_GOVERNED',provider='nflverse',endpoint=endpoint,observed_at=observed,
        as_of_semantics='Retrospective player-week provider response observed now; never a prospective forecast or proof of official finality.',
        payload={'season':season,'week':week,'target_row_count':len(rows),
                 'target_rows_sha256':hashlib.sha256(canonical_bytes(rows)).hexdigest(),'raw_path':raw_path.relative_to(root).as_posix(),
                 'raw_response_sha256':hashlib.sha256(raw).hexdigest(),'raw_archive_sha256':digest(raw_path)})
    path=base/'source-envelope.json';first_write_json(path,value);return path


def build(root: Path, source_path: Path, season: int, week: int, as_of: datetime) -> dict:
    games,binding=schedule(root,season,week,as_of)
    due=max(stamp(game['kickoff_at']) for game in games)+timedelta(hours=STABILIZATION_HOURS)
    result={'producer':{'module':'research/weekly_player_performance.py','version':'1.0.0','sha256':digest(Path(__file__))},'schema':'fie-weekly-player-performance-v1','season':season,'week':week,'as_of_utc':as_of.isoformat(),
            'schedule_source':binding,'outcomes_eligible_at':due.isoformat(),'games':[],
            'governance':{'retrospective_only':True,'pregame_feature_eligible':False,'model_changed':False,
                          'league_scoring_replay':False,'official_game_finality_certified':False}}
    if as_of < due:
        return {**result,'status':'NOT_DUE','reason':'Existing PR2 outcome stabilization buffer has not elapsed.'}
    source_path=source_path.resolve()
    if not source_path.is_relative_to(root):
        raise ValueError('PERFORMANCE_SOURCE_OUTSIDE_ROOT')
    source=json.loads(source_path.read_text(encoding='utf-8'));validate_envelope(source)
    if stamp(source['observed_at'])>as_of:
        raise ValueError('PERFORMANCE_SOURCE_AFTER_AS_OF')
    payload=source['payload']
    if (payload['season'],payload['week'])!=(season,week):
        raise ValueError('PERFORMANCE_SOURCE_TARGET_MISMATCH')
    raw_path=(root/payload['raw_path']).resolve()
    if not raw_path.is_relative_to(root) or digest(raw_path)!=payload['raw_archive_sha256']:
        raise ValueError('PERFORMANCE_RAW_ARCHIVE_HASH_MISMATCH')
    raw=gzip.decompress(raw_path.read_bytes())
    selected=target_rows(raw,season,week)
    if hashlib.sha256(raw).hexdigest()!=payload['raw_response_sha256']:
        raise ValueError('PERFORMANCE_NORMALIZED_SOURCE_MISMATCH')
    if 'rows' in payload:
        if selected!=payload['rows']:raise ValueError('PERFORMANCE_NORMALIZED_SOURCE_MISMATCH')
    elif len(selected)!=payload['target_row_count'] or hashlib.sha256(canonical_bytes(selected)).hexdigest()!=payload['target_rows_sha256']:
        raise ValueError('PERFORMANCE_NORMALIZED_SOURCE_MISMATCH')
    known={game['game_id']:game for game in games}
    indexed={};seen=set();unresolved=[]
    for source_index, row in enumerate(selected):
        gid=row.get('game_id');team=canonical_team(row.get('team'));pid=row.get('player_id')
        if gid not in known or team not in {canonical_team(known[gid]['home_team']),canonical_team(known[gid]['away_team'])}:
            raise ValueError('PERFORMANCE_GAME_TEAM_OR_PLAYER_ID_MISMATCH')
        if pid and (gid,team,pid) in seen:
            raise ValueError('PERFORMANCE_DUPLICATE_PLAYER_GAME')
        seen.add((gid,team,pid or f'UNRESOLVED_SOURCE_ROW_{source_index}'))
        if not pid:unresolved.append(source_index)
        item={'player_id':f'gsis:{pid}' if pid else None,'identity_status':'SOURCE_GSIS_ID' if pid else 'UNRESOLVED_SOURCE_PLAYER',
              'source_row_index':source_index,'player_name':row.get('player_display_name') or row.get('player_name') or 'Unattributed provider row',
              'position':row.get('position'),'team':team,'game_id':gid,'metrics':{key:numeric(row.get(key)) for key in METRICS}}
        item['unsupported_fields']=['snaps','routes','route_participation','alignment']
        indexed.setdefault((gid,team),[]).append(item)
    missing=[]
    for game in sorted(games,key=lambda row:row['kickoff_at']):
        teams=[]
        for raw_team in (game['away_team'],game['home_team']):
            team=canonical_team(raw_team);players=indexed.get((game['game_id'],team),[])
            if not players:missing.append(f"{game['game_id']}:{team}")
            # Provider rows are sorted by observed opportunity, not by a new model score.
            players.sort(key=lambda row:(-(row['metrics'].get('targets') or 0)-(row['metrics'].get('carries') or 0)-(row['metrics'].get('attempts') or 0),str(row['player_id'])))
            teams.append({'team':team,'status':'RAW_ROWS_AVAILABLE' if players else 'MISSING_TEAM_ROWS','players':players})
        result['games'].append({'game_id':game['game_id'],'kickoff_at':game['kickoff_at'],'teams':teams})
    result.update(status='PARTIAL_MISSING_TEAM_ROWS' if missing else 'PARTIAL_UNRESOLVED_SOURCE_PLAYERS' if unresolved else 'AVAILABLE_PROVIDER_ROWS',
                  source={'path':source_path.relative_to(root).as_posix(),'sha256':digest(source_path),'observed_at':source['observed_at']},
                  missing_team_games=missing,unresolved_source_row_indices=unresolved,game_count=len(games),player_game_count=len(seen),
                  note='All scheduled games are listed. Provider fantasy points are standard/PPR diagnostics, not exact league scoring. Missing metrics stay null. Markdown focuses on offense/kickers; JSON preserves all observed provider rows. Availability of rows does not certify official finality or complete snap/route coverage.')
    return result


def markdown(report: dict) -> str:
    def show(value):return '—' if value is None else f'{value:g}'
    lines=[f"# Player performance — {report['season']} Week {report['week']}",f"Status: **{report['status']}**",'',report.get('note') or report.get('reason',''),'']
    for game in report['games']:
        lines += [f"## {game['game_id']}",'']
        for team in game['teams']:
            lines += [f"### {team['team']} — {team['status']}",'',
                '| Player | Pos | Pass C/A–Yds–TD–INT | Rush C–Yds–TD | Rec/Tgt–Yds–TD | Std / PPR |',
                '|---|---|---|---|---|---|']
            for player in team['players']:
                if player['position'] not in {'QB','RB','WR','TE','K'} and player['identity_status'] != 'UNRESOLVED_SOURCE_PLAYER':continue
                m=player['metrics']
                passing='/'.join(show(m[k]) for k in ('completions','attempts'))+'–'+'–'.join(show(m[k]) for k in ('passing_yards','passing_tds','passing_interceptions'))
                rushing='–'.join(show(m[k]) for k in ('carries','rushing_yards','rushing_tds'))
                receiving='/'.join(show(m[k]) for k in ('receptions','targets'))+'–'+'–'.join(show(m[k]) for k in ('receiving_yards','receiving_tds'))
                lines.append(f"| {player['player_name']} | {player['position']} | {passing} | {rushing} | {receiving} | {show(m['fantasy_points'])} / {show(m['fantasy_points_ppr'])} |")
            lines.append('')
    return '\n'.join(line.rstrip() for line in lines).rstrip()+'\n'


def replay_matches(published: dict, replayed: dict) -> bool:
    # Display wording and producer revision are preserved in the published
    # object; raw/source/target and derived rows must replay exactly.
    def semantic(value):return {key:item for key,item in value.items() if key not in {'note','producer'}}
    return semantic(published)==semantic(replayed)


def ensure_completed(root: Path, season: int, current_week: int, as_of: datetime) -> dict:
    """Publish once for the newest stored, completed schedule; no forecast reads."""
    if as_of.tzinfo is None or not 1<=current_week<=18:raise ValueError('PERFORMANCE_TARGET_OR_TIME_INVALID')
    completed = []
    for week in range(1,current_week+1):
        if not (root/f'data/research/context/weather/{season}/week_{week:02d}').is_dir():
            continue
        games,_=schedule(root,season,week,as_of)
        due=max(stamp(game['kickoff_at']) for game in games)+timedelta(hours=STABILIZATION_HOURS)
        if as_of>=due:completed.append(week)
    if not completed:
        return {'status':'NO_OP_NO_STORED_COMPLETED_WEEK','season':season}
    week=max(completed);base=root/f'data/operations/weekly-performance/{season}/week_{week:02d}'
    existing=[]
    for path in (base/'reports').glob('*.json'):
        report=json.loads(path.read_text(encoding='utf-8'))
        if stamp(report['as_of_utc'])<=as_of:existing.append((stamp(report['as_of_utc']),path,report))
    if existing:
        _,path,report=max(existing,key=lambda row:(row[0],str(row[1])))
        replay=build(root,root/report['source']['path'],season,week,stamp(report['as_of_utc']))
        if not replay_matches(report,replay):raise ValueError('PERFORMANCE_EXISTING_REPORT_REPLAY_MISMATCH')
        return {'status':'NO_OP_EXISTING_VALIDATED_REPORT','season':season,'week':week,'report':path.relative_to(root).as_posix()}
    sources=[]
    for path in (base/'sources').glob('*/source-envelope.json'):
        value=json.loads(path.read_text(encoding='utf-8'))
        if stamp(value['observed_at'])<=as_of:sources.append((stamp(value['observed_at']),path))
    source=max(sources,key=lambda row:(row[0],str(row[1])))[1] if sources else capture(root,season,week,as_of)
    now=max(as_of,datetime.now(timezone.utc))
    report=build(root,source,season,week,now)
    output=base/'reports'/f'performance-{compact_timestamp(now.isoformat())}.json';output.parent.mkdir(parents=True,exist_ok=True)
    with output.open('x',encoding='utf-8') as stream:stream.write(json.dumps(report,separators=(',',':'),sort_keys=True,allow_nan=False)+'\n')
    with output.with_suffix('.md').open('x',encoding='utf-8') as stream:stream.write(markdown(report))
    return {'status':'REPORT_CREATED','owner_status':report['status'],'season':season,'week':week,'report':output.relative_to(root).as_posix()}


def main():
    parser=argparse.ArgumentParser();parser.add_argument('--root',default=str(Path(__file__).resolve().parents[1]))
    parser.add_argument('--season',type=int,required=True);parser.add_argument('--week',type=int,required=True)
    parser.add_argument('--source',type=Path);parser.add_argument('--capture-live',action='store_true');parser.add_argument('--output',type=Path)
    parser.add_argument('--ensure-completed',action='store_true')
    args=parser.parse_args();root=Path(args.root).resolve();now=datetime.now(timezone.utc)
    if args.ensure_completed:
        if args.source or args.capture_live or args.output:raise ValueError('ensure-completed owns its output identity.')
        print(json.dumps(ensure_completed(root,args.season,args.week,now),sort_keys=True));return
    if not args.output:raise ValueError('Explicit output required for manual reporting.')
    if bool(args.source)==args.capture_live:raise ValueError('Choose exactly one stored source or live retrospective capture.')
    source=capture(root,args.season,args.week,now) if args.capture_live else args.source
    report=build(root,source,args.season,args.week,datetime.now(timezone.utc));output=args.output.resolve()
    if output.is_relative_to(root/'data/research'):raise ValueError('PERFORMANCE_REPORT_MUST_NOT_OVERWRITE_RESEARCH')
    output.parent.mkdir(parents=True,exist_ok=True)
    with output.open('x',encoding='utf-8') as stream:stream.write(json.dumps(report,separators=(',',':'),sort_keys=True,allow_nan=False)+'\n')
    with output.with_suffix('.md').open('x',encoding='utf-8') as stream:stream.write(markdown(report))
    print(f"Player performance: {report['status']} — {output}")

if __name__=='__main__':main()
