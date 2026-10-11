"""Source-observed kickoff gaps; no physiological or projection adjustment."""
from collections import defaultdict
from research_source_archive import read
from weekly_evidence_audit import stamp
from window2d_context_foundation import parse_schedule_csv


def rest_features(games,*,season,target_week,observed_at,cutoff):
    limit=stamp(cutoff)
    if stamp(observed_at)>limit:
        raise ValueError('REST_SCHEDULE_OBSERVED_AFTER_CUTOFF')
    histories=defaultdict(list);seen=set()
    for game in games:
        if game['season']!=season:
            continue
        gid=game['game_id']
        if gid in seen or game['home_team']==game['away_team']:
            raise ValueError('REST_SCHEDULE_DUPLICATE_OR_TEAM_INVALID')
        seen.add(gid)
        for team,home in ((game['home_team'],True),(game['away_team'],False)):
            histories[team].append({**game,'home':home})
    rows=[]
    for team,history in sorted(histories.items()):
        history.sort(key=lambda r:(stamp(r['kickoff']),r['game_id']))
        for index,game in enumerate(history):
            if game['week']!=target_week:
                continue
            base={'team':team,'game_id':game['game_id'],'kickoff':game['kickoff'],
                  'season':season,'target_week':target_week,'travel_distance':None,'time_zone_travel':None}
            if stamp(game['kickoff'])<=limit:
                rows.append({**base,'status':'BLOCKED_TARGET_GAME_ALREADY_STARTED','kickoff_gap_hours':None})
                continue
            previous=history[index-1] if index else None
            if previous is None:
                rows.append({**base,'status':'MISSING_PRIOR_GAME','kickoff_gap_hours':None})
                continue
            if previous['week']>=target_week or stamp(previous['kickoff'])>limit:
                raise ValueError('REST_PRIOR_GAME_TIME_INVALID')
            away_run=0
            for prior in reversed(history[:index+1]):
                if prior['home']:break
                away_run+=1
            rows.append({**base,'status':'DESCRIPTIVE_KICKOFF_GAP',
                         'prior_game_id':previous['game_id'],
                         'kickoff_gap_hours':(stamp(game['kickoff'])-stamp(previous['kickoff'])).total_seconds()/3600,
                         'consecutive_away_games':away_run,
                         'weeks_since_prior_game':target_week-previous['week'],
                         'production_authorized':False})
    return rows


def build(root,receipt_path,*,season,target_week,cutoff):
    _,source=read(root,receipt_path,kind='schedule',season=season,cutoff=cutoff)
    raw=(root/source['raw_path']).read_bytes()
    return {'schema':'fie-research-rest-context-v1','source':source,'season':season,'target_week':target_week,
            'rows':rest_features(parse_schedule_csv(raw,season),season=season,target_week=target_week,
                                 observed_at=source['observed_at'],cutoff=cutoff),'production_authorized':False}
