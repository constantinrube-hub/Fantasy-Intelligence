"""Deterministic prior-week PBP, snap and role diagnostics, research only."""
from __future__ import annotations

import argparse
from collections import Counter, defaultdict
import json
from pathlib import Path
from statistics import mean

from point_in_time_capture import first_write_json
from research_source_archive import read
from strict_sleeper_baseline import finite
from weekly_evidence_audit import stamp, digest


def integer(value):
    number = finite(value)
    return int(number) if number is not None and number == int(number) else None


def prior_rows(rows, season, target_week, *, season_type='season_type'):
    if isinstance(target_week,bool) or not 1 <= target_week <= 18:
        raise ValueError('FEATURE_TARGET_WEEK_INVALID')
    out = []
    excluded = Counter()
    for row in rows:
        if integer(row.get('season')) != season:
            excluded['OTHER_SEASON'] += 1
            continue
        if row.get(season_type) != 'REG':
            excluded['NON_REGULAR_OR_UNDECLARED'] += 1
            continue
        week = integer(row.get('week'))
        if week is None or not 1 <= week <= 18:
            raise ValueError('FEATURE_SOURCE_WEEK_INVALID')
        if week >= target_week:
            excluded['TARGET_OR_FUTURE_WEEK'] += 1
            continue
        out.append(row)
    return out, dict(sorted(excluded.items()))


def pbp_tables(rows, season, target_week):
    rows, excluded = prior_rows(rows,season,target_week)
    teams, drives, players = defaultdict(list), defaultdict(list), defaultdict(lambda: Counter())
    seen, skipped = set(), Counter()
    for row in rows:
        gid, pid, team = row.get('game_id'), row.get('play_id'), row.get('posteam')
        if not gid or not pid:
            raise ValueError('PBP_PLAY_ID_MISSING')
        key = (gid,pid)
        if key in seen:
            raise ValueError('PBP_DUPLICATE_PLAY_ID')
        seen.add(key)
        # nflverse CSV commonly publishes play_type rather than no_play.
        # Only explicit run/pass plays qualify through that schema.
        no_play = finite(row.get('no_play')) if 'no_play' in row else (0 if row.get('play_type') in {'run','pass'} else None)
        if not team or no_play != 0 or row.get('play_type') == 'no_play':
            skipped['NO_TEAM_OR_NO_PLAY_UNVERIFIED'] += 1
            continue
        passed, rushed = finite(row.get('pass_attempt')), finite(row.get('rush_attempt'))
        if passed not in (0,1) or rushed not in (0,1):
            skipped['ATTEMPT_FLAGS_MISSING'] += 1
            continue
        if passed+rushed>1:
            raise ValueError('PBP_CONTRADICTORY_ATTEMPT_FLAGS')
        if not passed and not rushed:
            continue
        week = integer(row['week'])
        teams[(week,gid,team)].append(row)
        drive = row.get('fixed_drive')
        if integer(drive) is not None:
            drives[(week,gid,team,int(float(drive)))].append(row)
        else:
            skipped['FIXED_DRIVE_MISSING'] += 1
        yardline = finite(row.get('yardline_100'))
        if yardline is None or not 0 <= yardline <= 100:
            skipped['RED_ZONE_YARDLINE_MISSING'] += 1
            continue
        for field, flag, role in [('rusher_player_id',rushed,'carries'),('receiver_player_id',passed,'targets')]:
            sid = row.get(field)
            if not flag or not sid:
                continue
            count = players[(week,gid,team,'gsis:'+sid)]
            count[role] += 1
            if yardline <=20:
                count['red_zone_'+role] += 1
            if yardline <=5:
                count['goal_line_'+role] += 1
    team_rows = []
    for (week,gid,team), plays in sorted(teams.items()):
        epa = [finite(p.get('epa')) for p in plays]
        success = [finite(p.get('success')) for p in plays]
        neutral = [p for p in plays if finite(p.get('qtr')) is not None and 1 <= float(p['qtr']) <=3 and
                   finite(p.get('score_differential')) is not None and abs(float(p['score_differential'])) <=7]
        passes = sum(float(p['pass_attempt']) for p in plays)
        team_rows.append({'season':season,'week':week,'game_id':gid,'team':team,'scrimmage_plays':len(plays),
            'pass_attempts':passes,'rush_attempts':sum(float(p['rush_attempt']) for p in plays),
            'pass_rate':passes/len(plays),'neutral_plays':len(neutral),
            'neutral_pass_rate':sum(float(p['pass_attempt']) for p in neutral)/len(neutral) if neutral else None,
            'epa_per_observed_play':mean(v for v in epa if v is not None) if any(v is not None for v in epa) else None,
            'epa_observed_plays':sum(v is not None for v in epa),
            'success_rate_observed':mean(v for v in success if v is not None) if any(v is not None for v in success) else None,
            'success_observed_plays':sum(v is not None for v in success), 'proe':None,'pressure_rate':None})
    drive_rows = []
    for (week,gid,team,drive), plays in sorted(drives.items()):
        plays.sort(key=lambda p: float(p['play_id']))
        start = plays[0]
        yards = [finite(p.get('yards_gained')) for p in plays]
        first_downs = [finite(p.get('first_down')) for p in plays]
        touchdowns = [finite(p.get('touchdown')) for p in plays]
        td_teams_known = all(p.get('td_team') for p in plays if finite(p.get('touchdown')) == 1)
        drive_rows.append({'season':season,'week':week,'game_id':gid,'team':team,'fixed_drive':drive,
            'start_reason': start.get('drive_start_transition') or 'UNKNOWN',
            'first_scrimmage_yardline_100':finite(start.get('yardline_100')),
            'scrimmage_yards':sum(yards) if all(v is not None for v in yards) else None,
            'first_downs':sum(first_downs) if all(v is not None for v in first_downs) else None,
            'offensive_touchdown_observed':any(finite(p.get('touchdown')) == 1 and p.get('td_team') == team for p in plays)
                if all(v is not None for v in touchdowns) and td_teams_known else None,
            'scope':'SCRIMMAGE_PLAYS_ONLY_NOT_COMPLETE_DRIVE_ORIGIN'})
    player_rows = [{'season':season,'week':k[0],'game_id':k[1],'team':k[2],'source_gsis_player_id':k[3],
                    'canonical_player_id':None, 'metrics':{field: counts.get(field,0) for field in
                    ('carries','targets','red_zone_carries','red_zone_targets','goal_line_carries','goal_line_targets')},
                    'routes':None,'charted_end_zone_targets':None} for k,counts in sorted(players.items())]
    return {'team_games':team_rows,'drive_scrimmage_summaries':drive_rows,'red_zone_players':player_rows,
            'excluded_rows':excluded,'missing_or_skipped_rows':dict(sorted(skipped.items()))}


def snap_table(rows,season,target_week):
    rows, excluded = prior_rows(rows,season,target_week,season_type='game_type')
    out, seen = [], set()
    for row in rows:
        sid, gid, team = row.get('pfr_player_id'),row.get('game_id'),row.get('team')
        key = (gid,team,sid)
        if not all(key) or key in seen:
            raise ValueError('SNAP_ID_MISSING_OR_DUPLICATE')
        seen.add(key)
        values = {}
        for field in ('offense_snaps','defense_snaps','st_snaps'):
            value = integer(row.get(field))
            if row.get(field) not in (None,'') and (value is None or value <0):
                raise ValueError('SNAP_COUNT_INVALID')
            values[field] = value
        for field in ('offense_pct','defense_pct','st_pct'):
            value = finite(row.get(field))
            if row.get(field) not in (None,'') and (value is None or not 0 <= value <=100):
                raise ValueError('SNAP_PROVIDER_PERCENTAGE_INVALID')
            values[field+'_provider_units'] = value
        out.append({'season':season,'week':integer(row['week']),'game_id':gid,'team':team,
                    'source_pfr_player_id':'pfr:'+sid,'canonical_player_id':None,**values,
                    'offense_snap_share':None,'percentage_scale':'UNVERIFIED','routes':None})
    return {'rows':out,'excluded_rows':excluded}


def role_changes(rows,*,target_week,cutoff,minimum_opportunities=5):
    grouped, seen = defaultdict(list), set()
    for row in rows:
        if stamp(row['observed_at']) > stamp(cutoff) or row['week'] >=target_week:
            continue
        key = (row['season'],row['source_gsis_player_id'],row['metric'])
        obskey = (*key,row['week'],row['game_id'])
        if obskey in seen:
            raise ValueError('ROLE_DUPLICATE_PLAYER_GAME_METRIC')
        seen.add(obskey)
        numerator, denominator = finite(row.get('numerator')),finite(row.get('denominator'))
        if numerator is None or denominator is None or numerator <0 or denominator <minimum_opportunities or numerator>denominator:
            grouped[key].append({**row,'share':None})
        else:
            grouped[key].append({**row,'share':numerator/denominator})
    out = []
    for key, history in sorted(grouped.items()):
        history.sort(key=lambda r:(r['week'],r['game_id']))
        window=history[-5:]
        base={'season':key[0],'source_gsis_player_id':key[1],'metric':key[2],
              'target_week':target_week,'history_games':len(history),'production_authorized':False}
        if len(window)<5 or any(r['share'] is None for r in window):
            out.append({**base,'status':'BLOCKED_HISTORY_OR_OPPORTUNITIES','delta':None})
        elif len({r['team'] for r in window}) !=1:
            out.append({**base,'status':'BLOCKED_TEAM_CHANGE','delta':None})
        else:
            baseline=mean(r['share'] for r in window[:3]);recent=mean(r['share'] for r in window[3:])
            deltas=[r['share']-baseline for r in window[3:]]
            out.append({**base,'status':'DESCRIPTIVE_ROLE_CHANGE','baseline_share':baseline,
                        'recent_share':recent,'delta':recent-baseline,
                        'same_direction_recent_games':all(d>0 for d in deltas) or all(d<0 for d in deltas),
                        'input_game_ids':[r['game_id'] for r in window]})
    return out


def build(root,receipt_path,*,kind,season,target_week,cutoff):
    rows,source=read(root,receipt_path,kind=kind,season=season,cutoff=cutoff)
    if kind not in {'pbp','snaps'}:
        raise ValueError('FEATURE_KIND_NOT_IMPLEMENTED')
    table=pbp_tables(rows,season,target_week) if kind=='pbp' else snap_table(rows,season,target_week)
    return {'schema':'fie-research-feature-tables-v1','kind':kind,'season':season,'target_week':target_week,
            'cutoff':stamp(cutoff).isoformat(),'source':source,'tables':table,'retrospective_only':True,
            'producer':{'module':'research/research_feature_tables.py','sha256':digest(Path(__file__))},
            'production_authorized':False,'official_finality_certified':False}


def main():
    ap=argparse.ArgumentParser()
    ap.add_argument('--root',type=Path,default=Path(__file__).resolve().parents[1])
    ap.add_argument('--receipt',type=Path,required=True)
    ap.add_argument('--kind',choices=['pbp','snaps'],required=True)
    ap.add_argument('--season',type=int,required=True)
    ap.add_argument('--target-week',type=int,required=True)
    ap.add_argument('--cutoff',required=True)
    ap.add_argument('--output',type=Path,required=True)
    args=ap.parse_args()
    report=build(args.root,args.receipt,kind=args.kind,season=args.season,target_week=args.target_week,cutoff=args.cutoff)
    print(first_write_json(args.output,report))


if __name__=='__main__':
    main()
