"""Additional profile source scope: uncertain events stay null locally."""
from __future__ import annotations
import copy,hashlib
import numpy as np
import pandas as pd
from build_waiver_v2_outcome_ledger import scoring_signature
from waiver_v2_outcomes import EVENT_WEEKLY_RULES,build_dense_offensive_outcome_ledger
from waiver_v2_population import certify,extend,close_identity_calendar
from waiver_v2_event_ledger import _event_weekly_stats,E2_RULE_FIELDS,E3_RULE_FIELDS,E4_RULE_FIELDS,E5_RULE_FIELDS
from waiver_v2_validation import KEYS
from scoring_relevance import position_relevant
from week1_game_projections import canonical_team

SCOPED={'fum_rec_td':'fumble_recovery_td','kr_yd':'kick_return_yards','pr_yd':'punt_return_yards',
        'rec_40p':'reception_40','rec_td_40p':'reception_td_40','rec_td_50p':'reception_td_50'}
FIELDS={**E2_RULE_FIELDS,**E3_RULE_FIELDS,**E4_RULE_FIELDS,**E5_RULE_FIELDS}

def component_sources(pbp,stats,events,report,blockers,reconciliation_stats):
    original=copy.deepcopy(report['rule_support']);support=copy.deepcopy(original);exclusions=[]
    covered=set(map(tuple,pbp.loc[pbp.season_type.eq('REG'),['season','week']].drop_duplicates().to_numpy()))
    if not report['source_inventory']['pbp_source_complete']:raise ValueError('SCOPED_PBP_INCOMPLETE')
    for rule,event in SCOPED.items():
        status=original[rule]['support_status'];unresolved=[b for b in blockers if b['event_type']==event]
        if status=='EXACT_EVENT_READY' or set(FIELDS[rule])-set(pbp) or not unresolved:continue
        if status not in {'BLOCKED_EVENT_IDENTITY','BLOCKED_EVENT_SEMANTICS','BLOCKED_RECONCILIATION_MISMATCH','BLOCKED_SOURCE_INCOMPLETE'}:continue
        if not original[rule].get('reason','').startswith(f'{len(unresolved)} {event} PBP events lack exact'):continue
        support[rule]={'support_status':'EXACT_EVENT_READY','reason':'Scoped rows only; uncertain observations retain null components'}
        for b in unresolved:
            exclusions.append({'rule':rule,'season':int(b['season']),'week':int(b['week']),'game_id':str(b['game_id']),
                               'canonical_player_id':None,'basis':'UNRESOLVED_EVENT_BOTH_GAME_TEAMS','play_id':b['play_id'],'reason':b['reason']})
    weekly=_event_weekly_stats(events)
    joined=stats[KEYS].drop_duplicates().merge(weekly,on=KEYS,how='left',validate='one_to_one')
    valid=np.array([tuple(x) in covered for x in joined[['season','week']].to_numpy()])
    for rule,column in EVENT_WEEKLY_RULES.items():
        if column not in joined:joined[column]=np.nan
        if support.get(rule,{}).get('support_status')=='EXACT_EVENT_READY':
            joined.loc[valid,column]=pd.to_numeric(joined.loc[valid,column],errors='coerce').fillna(0)
    for rule,rawcol in [('kr_yd','kickoff_return_yards'),('pr_yd','punt_return_yards')]:
        if support.get(rule,{}).get('support_status')!='EXACT_EVENT_READY':continue
        if rawcol not in reconciliation_stats:support[rule]=original[rule];continue
        col=EVENT_WEEKLY_RULES[rule]
        totals=weekly[KEYS+[col]].merge(reconciliation_stats[KEYS+[rawcol]],on=KEYS,how='outer',validate='one_to_one')
        a=pd.to_numeric(totals[col],errors='coerce').fillna(0);b=pd.to_numeric(totals[rawcol],errors='coerce')
        for row in totals.loc[b.isna()|~np.isclose(a,b,rtol=0,atol=1e-9)].itertuples(index=False):
            exclusions.append({'rule':rule,'season':int(row.season),'week':int(row.week),'game_id':None,
                               'canonical_player_id':str(row.canonical_player_id),'basis':'RETURN_AGGREGATE_MISMATCH_OR_MISSING',
                               'play_id':None,'reason':'Exact PBP/player-week return reconciliation failed'})
    joined=joined.merge(stats[KEYS+['game_id']].drop_duplicates(KEYS),on=KEYS,how='left',validate='one_to_one')
    for x in exclusions:
        mask=joined.season.eq(x['season'])&joined.week.eq(x['week'])
        mask &= joined.canonical_player_id.eq(x['canonical_player_id']) if x['canonical_player_id'] else joined.game_id.eq(x['game_id'])
        joined.loc[mask,EVENT_WEEKLY_RULES[x['rule']]]=np.nan
    return joined.drop(columns='game_id'),support,exclusions

def mask_outcomes(outcomes,scoring,exclusions,games):
    result=outcomes.copy();blocked=np.zeros(len(result),dtype=bool);codes=[set() for _ in range(len(result))]
    schedule={str(r.game_id):{canonical_team(r.home_team),canonical_team(r.away_team)} for r in games.itertuples()}
    for item in exclusions:
        if not float(scoring.get(item['rule'],0)):continue
        relevant=result.position_model.map(lambda p:position_relevant(item['rule'],str(p)) if pd.notna(p) else any(position_relevant(item['rule'],q) for q in ['QB','RB','WR','TE']))
        mask=result.season.eq(item['season'])&result.week.eq(item['week'])&relevant;unknown=result.team.isna()
        if item['canonical_player_id']:mask &= result.canonical_player_id.eq(item['canonical_player_id'])|unknown
        else:
            teams=schedule.get(item['game_id'])
            if not teams:raise ValueError('SCOPED_UNBOUND_EVENT_GAME')
            mask &= result.team.map(canonical_team).isin(teams)|unknown
        for i in np.flatnonzero(mask.to_numpy()):codes[i].add('SCOPED_UNCERTAIN_'+item['rule'])
        blocked |= mask.to_numpy()
    result.loc[blocked,'fantasy_points_exact']=np.nan;result.loc[blocked,'outcome_complete']=False;result.loc[blocked,'exact_scoring']=False
    result.loc[blocked,'outcome_status']='BLOCKED_SCOPED_EVENT_ATTRIBUTION'
    result.loc[blocked,'outcome_blocker_codes']=[';'.join(sorted(codes[i])) for i in np.flatnonzero(blocked)]
    return result

def slow_profile_outcomes(pbp,stats,roster,games,identity,weekly,support,exclusions,scoring):
    from waiver_v2_source_adapter import normalize_team_schedule
    combined=stats.merge(weekly,on=KEYS,how='left',validate='one_to_one')
    ledger=build_dense_offensive_outcome_ledger(combined,roster,normalize_team_schedule(games,roster),scoring,
        scoring_signature=scoring_signature(scoring),player_stats_complete=False,event_rule_support=support)
    cert,audit,actors,missing=certify(pbp,games,roster,stats,identity,support,sorted(pbp.season.unique()))
    ledger,_=extend(ledger,cert,hashlib.sha256(cert.to_csv(index=False).encode()).hexdigest())
    ledger,proofs=close_identity_calendar(ledger,stats,weekly,audit,actors,games,scoring,support)
    extra=list(exclusions)
    for row in audit[~audit.proof_ready].itertuples(index=False):
        for rule in EVENT_WEEKLY_RULES:
            if float(scoring.get(rule,0)):extra.append({'rule':rule,'season':int(row.season),'week':int(row.week),'game_id':str(row.game_id),'canonical_player_id':None})
    return mask_outcomes(ledger,scoring,extra,games),audit,proofs

_PROOF_CACHE=None
def profile_outcomes(pbp,stats,roster,games,identity,weekly,support,exclusions,scoring):
    """Reuse source proofs; original roster position and scoring rules govern."""
    global _PROOF_CACHE
    from waiver_v2_outcomes import build_offensive_scoring_inventory,EXACT_WEEKLY_STAT_RULES,POSITION_RECEPTION_RULES,THRESHOLD_BONUS_RULES
    refs=(pbp,stats,roster,games,identity,weekly);key=tuple(id(x) for x in refs)
    if _PROOF_CACHE is None or _PROOF_CACHE[0]!=key:
        template,audit,proofs=slow_profile_outcomes(pbp,stats,roster,games,identity,weekly,support,[],{'pass_yd':.04,'rush_yd':.1,'rec_yd':.1})
        joined=stats.merge(weekly,on=KEYS,how='left',validate='one_to_one').drop(columns='position_model')
        joined=joined.merge(template[KEYS+['position_model']],on=KEYS,how='inner',validate='one_to_one')
        _PROOF_CACHE=(key,refs,template,audit,proofs,joined)
    _,_,template,audit,proofs,joined=_PROOF_CACHE;values=[]
    for pos,frame in joined.groupby('position_model',sort=False):
        inv=build_offensive_scoring_inventory(scoring,position=pos,available_columns=set(joined),event_rule_support=support)
        scores=np.zeros(len(frame));valid=np.ones(len(frame),dtype=bool)&inv['exact_replay_eligible']
        for rule in inv['relevant_nonzero_rules']:
            k=rule['key'];weight=rule['weight'];col=EXACT_WEEKLY_STAT_RULES.get(k) or EVENT_WEEKLY_RULES.get(k);threshold=None
            if k in POSITION_RECEPTION_RULES:
                if POSITION_RECEPTION_RULES[k]!=pos:continue
                col='receptions'
            elif k in THRESHOLD_BONUS_RULES:col,threshold=THRESHOLD_BONUS_RULES[k]
            if col is None or col not in frame:valid[:]=False;continue
            raw=pd.to_numeric(frame[col],errors='coerce').to_numpy(float);valid &= np.isfinite(raw)
            scores += weight*(raw if threshold is None else (raw>=threshold).astype(float))
        f=frame[KEYS].copy();f['published_score']=np.where(valid,scores,np.nan);f['published_present']=True;values.append(f)
    result=template.merge(pd.concat(values,ignore_index=True),on=KEYS,how='left',validate='one_to_one')
    published=result.published_present.eq(True)&result.outcome_status.isin(['COMPLETE_EXACT','COMPLETE_PUBLISHED_SOURCE_WITHOUT_ROSTER'])
    ready=result.outcome_complete.map(lambda x:str(x).lower()=='true')
    result.loc[published&ready,'fantasy_points_exact']=result.loc[published&ready,'published_score']
    missing=published&result.published_score.isna()
    result.loc[missing,'outcome_complete']=False;result.loc[missing,'exact_scoring']=False;result.loc[missing,'fantasy_points_exact']=np.nan
    result.loc[missing,'outcome_status']='BLOCKED_SCOPED_COMPONENT_OR_SOURCE';result.loc[missing,'outcome_blocker_codes']='BLOCKED_SCOPED_COMPONENT_OR_SOURCE'
    result['scoring_signature']=scoring_signature(scoring)
    for pos in ['QB','RB','WR','TE']:
        inv=build_offensive_scoring_inventory(scoring,position=pos,available_columns=set(joined),event_rule_support=support)
        if not inv['exact_replay_eligible']:
            mask=result.position_model.eq(pos)|result.position_model.isna()
            result.loc[mask,'outcome_complete']=False;result.loc[mask,'exact_scoring']=False;result.loc[mask,'fantasy_points_exact']=np.nan
            result.loc[mask,'outcome_status']='BLOCKED_UNSUPPORTED_EXACT_SCORING'
    extra=list(exclusions)
    for row in audit[~audit.proof_ready].itertuples(index=False):
        for rule in EVENT_WEEKLY_RULES:
            if float(scoring.get(rule,0)):extra.append({'rule':rule,'season':int(row.season),'week':int(row.week),'game_id':str(row.game_id),'canonical_player_id':None})
    return mask_outcomes(result.drop(columns=['published_score','published_present']),scoring,extra,games),audit,proofs
