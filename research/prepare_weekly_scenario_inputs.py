"""Source-bound submitted intent; no probability or synthetic scenario bank."""
import io,json
import pandas as pd
from prospective_research_io import binding,gates,now,replay_response
from capture_week6_research_sources import validate_manifest
from capture_m10_prospective_weekly_raw import normalize_sleeper_id
from prepare_league_research_evidence import managed_roster
from league_profile import infer_format
from fie_research import build_identity
from weekly_portfolio_surface import identity_only_projection


def build(root,envelope):
    source=validate_manifest(root,envelope);refs={r['name']:r for r in source['responses']};at=source['captured_at']
    def load(name):return json.loads(replay_response(root,refs[name],at))
    identity,_=build_identity(pd.read_csv(io.BytesIO(replay_response(root,refs['players'],at)),low_memory=False),
                              pd.read_csv(io.BytesIO(replay_response(root,refs['ff_playerids'],at)),low_memory=False))
    crosswalk={}
    for _,r in identity.dropna(subset=['canonical_player_id','sleeper_id']).iterrows():
        crosswalk.setdefault(normalize_sleeper_id(r.sleeper_id),set()).add(str(r.canonical_player_id))
    catalog=load('sleeper_players');username=json.loads((root/'config/league-portfolio.json').read_text())['sleeper_username']
    leagues=[]
    for lid in source['league_ids']:
        try:
            profile=load(lid+'-profile');rosters=load(lid+'-rosters');users=load(lid+'-users');matchups=load(lid+'-matchups')
            if str(profile.get('season'))!=str(source['season']):raise ValueError('SCENARIO_PROFILE_SEASON')
            managed=managed_roster(users,rosters,username);fmt=infer_format(profile,'AUTO')
            if not isinstance(matchups,list) or len({m['roster_id'] for m in matchups})!=len(matchups):raise ValueError('SCENARIO_MATCHUP_DUPLICATE')
            automatic='BESTBALL' in fmt or fmt=='BEST_BALL'
            rows=[]
            for roster in rosters:
                matches=[m for m in matchups if m['roster_id']==roster['roster_id']]
                excluded={str(x) for x in (roster.get('reserve') or [])+(roster.get('taxi') or [])}
                selected=[str(x) for x in roster.get('players') or [] if str(x) not in excluded] if automatic else [str(x) for x in (matches[0].get('starters') or []) if str(x)!='0'] if len(matches)==1 else []
                if len(selected)!=len(set(selected)):raise ValueError('SCENARIO_DUPLICATE_SELECTED_PLAYER')
                canonical=[];blocked=[]
                for sid in selected:
                    sid=normalize_sleeper_id(sid);ids=set(crosswalk.get(sid,set()))
                    provider=identity_only_projection(sid,catalog)
                    if provider and provider.get('canonical_player_id'):ids.add(provider['canonical_player_id'])
                    if len(ids)==1:canonical.append({'sleeper_id':sid,'canonical_player_id':next(iter(ids))})
                    else:blocked.append({'sleeper_id':sid,'reason':'MISSING_OR_AMBIGUOUS_CANONICAL_ID'})
                if len({p['canonical_player_id'] for p in canonical})!=len(canonical):raise ValueError('SCENARIO_CANONICAL_COLLISION')
                rows.append({'roster_id':roster['roster_id'],'matchup_id':matches[0].get('matchup_id') if len(matches)==1 else None,
                             'basis':'AUTOMATIC_ACTIVE_ROSTER' if automatic else 'OBSERVED_SUBMITTED_INTENT',
                             'canonical_inputs':canonical,'blocked_identities':blocked,'selected_source_count':len(selected),
                             'complete_selected_identity':bool(selected) and not blocked,'locked_lineup_proven':False,'adoption':'UNKNOWN'})
            own=next(r for r in rows if r['roster_id']==managed['roster_id'])
            pair=[r['roster_id'] for r in rows if own['matchup_id'] is not None and r['matchup_id']==own['matchup_id'] and r['complete_selected_identity']]
            direct=pair if len(pair)==2 and managed['roster_id'] in pair and fmt not in {'CHOPPED','CHOPPED_BESTBALL'} else None
            leagues.append({'league_id':lid,'format':fmt,'rosters':rows,'direct_h2h_pair':direct,
                            'bank':None,'calibration':None,'win_probability':None,'survival_probability':None,'draft_request':None,
                            'chopped_field_status':'BLOCKED_VERIFIED_FIELD_TIE_ELIMINATION_PROOF' if 'CHOPPED' in fmt else 'NOT_APPLICABLE',
                            'source_bindings':{role:refs[lid+'-'+role] for role in ['profile','rosters','users','matchups']},
                            **gates(['BLOCKED_REAL_JOINT_BANK_AND_CALIBRATION','BLOCKED_LOCKED_LINEUP_AND_RULES'])})
        except (ValueError,KeyError,TypeError) as error:
            leagues.append({'league_id':lid,'status':'BLOCKED_SCENARIO_INPUTS','reason':str(error),**gates(['BLOCKED_SOURCE_OR_IDENTITY'])})
    return {'schema':'fie-weekly-scenario-inputs-v1','season':source['season'],'week':source['week'],'prepared_at':now(),
            'source_envelope':binding(root,envelope,at),'leagues':leagues,'distribution_owner':'research/joint_scenario_engine.py',
            **gates(['BLOCKED_REAL_BANK_CALIBRATION_AND_PROMOTION'])}
