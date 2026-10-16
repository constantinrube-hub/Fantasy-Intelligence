"""C2 source-certified exposures and a separate, versioned specialist target view."""
from __future__ import annotations
import argparse
from collections import defaultdict
import gzip
import json
from pathlib import Path
import re
import numpy as np
import pandas as pd
from build_component_outcomes import BASE as C1, HISTORY, ENVELOPE, KEYS, regular, csv, verified, additive, missed_distance_counts
from component_source_contract import PLAYER_FIELDS, EVENT_FIELDS, position, team
from component_registry import ROOT, build
from prospective_research_io import write, sha, now
from waiver_v2_population import certify
from week1_game_projections import canonical_team

BASE=Path('data/research/components/2026-10-14/c2-c4-v1/priors')
GSIS=re.compile(r'^00-\d{7}$')
IDP_ROLES={
 'idp_tackles_solo':['solo_tackle_1_player_id','solo_tackle_2_player_id','tackle_with_assist_1_player_id','tackle_with_assist_2_player_id'],
 'idp_tackles_assisted':[f'assist_tackle_{i}_player_id' for i in range(1,5)],
 'idp_tackles_for_loss':['tackle_for_loss_1_player_id','tackle_for_loss_2_player_id'],
 'idp_sacks':['sack_player_id','half_sack_1_player_id','half_sack_2_player_id'],
 'idp_sack_yards':['sack_player_id','half_sack_1_player_id','half_sack_2_player_id'],
 'idp_quarterback_hits':['qb_hit_1_player_id','qb_hit_2_player_id'],
 'idp_interceptions':['interception_player_id','lateral_interception_player_id'],
 'idp_interception_return_yards':['interception_player_id','lateral_interception_player_id'],
 'idp_passes_defended':['pass_defense_1_player_id','pass_defense_2_player_id'],
 'idp_forced_fumbles':['forced_fumble_player_1_player_id','forced_fumble_player_2_player_id'],
 'idp_fumble_recoveries':['fumble_recovery_1_player_id','fumble_recovery_2_player_id'],
 'idp_fumble_return_yards':['fumble_recovery_1_player_id','fumble_recovery_2_player_id'],
 'idp_safeties':['safety_player_id'], 'idp_blocked_kicks':['blocked_player_id'],
 'idp_defensive_touchdowns':['td_player_id'],
}
IDP_ROLES['idp_tackles_total']=IDP_ROLES['idp_tackles_solo']+IDP_ROLES['idp_tackles_assisted']
EXTRA=['targets','kick_returns','punt_returns','kicker_field_goal_attempts','kicker_extra_point_attempts',
       'kicker_fgm','kicker_fgmiss_50_59','kicker_fgmiss_60p',
       'dst_points_allowed','dst_net_yards_allowed','dst_prob_pts_allow_21_27']

def valid_actors(frame,columns):
    return set(str(x).strip() for x in frame.reindex(columns=columns).to_numpy().ravel()
               if pd.notna(x) and GSIS.fullmatch(str(x).strip()) and str(x).strip()!='00-0000000')

def negative_events(game):
    """Conservative all-team negatives; a possible candidate never proves zero."""
    needed=['special_teams_play','fumble','fumble_forced','touchdown','safety','field_goal_attempt',
            'punt_blocked','fourth_down_failed','two_point_attempt','complete_pass','rush_attempt',
            'interception','return_touchdown']
    action=game[game.play_type.notna() & ~game.play_type.isin(['no_play','nan'])]
    complete=not action.empty and set(needed)<=set(action)
    if complete:
        complete=all(pd.to_numeric(action[c],errors='coerce').isin([0,1]).all() for c in needed)
    if not complete:
        return {},'BLOCKED_EVENT_FLAGS'
    st=action.special_teams_play.eq(1); fum=action.fumble.eq(1);td=action.touchdown.eq(1)
    blocked=(action.punt_blocked.eq(1)|action.field_goal_result.eq('blocked')|
             action.extra_point_result.eq('blocked')|action.blocked_player_id.notna()|
             action.desc.fillna('').str.contains(r'\bBLOCKED\b',case=False,regex=True))
    missed_fg=action.field_goal_attempt.eq(1)&~action.field_goal_result.eq('made')
    result={
      'dst_forced_fumbles':not action.fumble_forced.eq(1).any(),
      'dst_fumble_recoveries':not fum.any(), 'dst_fumble_return_yards':not fum.any(),
      'dst_special_teams_forced_fumbles':not (st&action.fumble_forced.eq(1)).any(),
      'dst_special_teams_fumble_recoveries':not (st&fum).any(),
      'dst_special_teams_touchdowns':not (st&td).any(),
      'dst_blocked_kicks':not blocked.any(),'dst_blocked_kick_return_yards':not blocked.any(),
      'dst_field_goal_return_yards':not missed_fg.any(),
      'dst_fourth_down_stops':not action.fourth_down_failed.eq(1).any(),
      'dst_safeties':not action.safety.eq(1).any(),
      'individual_special_teams_touchdowns':not (st&td).any(),
      'individual_special_teams_forced_fumbles':not (st&action.fumble_forced.eq(1)).any(),
      'individual_special_teams_fumble_recoveries':not (st&fum).any(),
      'offensive_fumble_recovery_touchdowns':not (fum&td).any(),
      'passing_pick_sixes':not (action.interception.eq(1)&action.return_touchdown.eq(1)).any(),
    }
    ordinary=~action.two_point_attempt.eq(1)
    for kind,yard,qualifier,names in [
      ('pass','passing_yards',action.complete_pass.eq(1),['passing_completions_40_plus','passing_touchdowns_40_plus','passing_touchdowns_50_plus']),
      ('rush','rushing_yards',action.rush_attempt.eq(1),['rushes_40_plus','rushing_touchdowns_40_plus','rushing_touchdowns_50_plus']),
      ('rec','receiving_yards',action.complete_pass.eq(1),['receptions_40_plus','receiving_touchdowns_40_plus','receiving_touchdowns_50_plus'])]:
        qualifying=action[ordinary & qualifier]
        numbers=pd.to_numeric(qualifying[yard],errors='coerce')
        # Lateral values may be attributed separately. A nonzero lateral or
        # missing official yard value keeps the game unknown for that family.
        lateral='lateral_rushing_yards' if kind=='rush' else 'lateral_receiving_yards'
        lateral_present=kind!='pass' and pd.to_numeric(qualifying[lateral],errors='coerce').fillna(0).ne(0).any()
        if numbers.notna().all() and not lateral_present:
            for c in names:
                threshold=50 if '50_plus' in c else 40
                result[c]=not numbers.ge(threshold).any()
    return result,None

def provider_rows(root,bridge,sources):
    lookup=dict(zip(bridge.dropna(subset=['sleeper_id']).sleeper_id.astype(str),
                    bridge.dropna(subset=['sleeper_id']).canonical_player_id.astype(str)))
    rows=[]
    for ref in sources:
        if ref['week'] is None:continue
        payload=json.loads(gzip.decompress(verified(root,ref).read_bytes()))
        for sid,st in payload.items():
            if sid.startswith('TEAM_'):continue
            cid='TEAM:'+team(sid) if re.fullmatch(r'[A-Z]{2,3}',sid) else lookup.get(sid)
            if cid is None:continue
            numeric={k:float(v) for k,v in st.items() if not isinstance(v,bool) and isinstance(v,(float,int)) and np.isfinite(v)}
            rows.append({**numeric,'canonical_player_id':cid,'season':ref['season'],'week':ref['week']})
    out=pd.DataFrame(rows)
    if out.duplicated(KEYS).any():raise ValueError('C2_PROVIDER_CANONICAL_DUPLICATE')
    return out

def build_year(c1,raw,pbp,games,provider,components,rulekeys):
    season=int(c1.season.iloc[0]);limit=5 if season==2026 else 18
    raw=regular(raw,limit);raw=raw[raw.player_id.astype(str).str.fullmatch(GSIS.pattern)].copy()
    raw['canonical_player_id']=raw.player_id.astype(str);raw['position_model']=raw.position.map(position)
    raw['team']=raw.team.map(canonical_team)
    if raw.duplicated(KEYS).any():raise ValueError('C2_DUPLICATE_RAW_WEEK')
    roster=c1[c1.position_model.ne('DEF') & c1.membership_team_count.eq(1)].copy()
    roster['team']=roster.team.map(canonical_team);roster['roster_complete']=True
    roster=roster[KEYS+['team','position_model','roster_complete']]
    identity=pd.DataFrame({'gsis_id':sorted(set(raw.canonical_player_id)|set(roster.canonical_player_id))})
    identity['canonical_player_id']=identity.gsis_id
    support={k:{'support_status':'EXACT_EVENT_READY'} for k in ['fum','fum_lost','pass_int_td']}
    certificates,audit,actors,missing=certify(pbp,games,roster,raw,identity,support,[season])
    # Extend the closed offensive audit conservatively to full specialist flags.
    negatives={};roles={};extra_bad=set()
    valid=pbp[~pd.to_numeric(pbp.play_deleted,errors='coerce').fillna(1).eq(1)].copy()
    for gid,game in valid.groupby('game_id',sort=False):
        neg,blocked=negative_events(game);negatives[gid]=neg
        if blocked:extra_bad.add(gid)
        roles[gid]={c:valid_actors(game,fields) for c,fields in IDP_ROLES.items()}
        for flag,fields in [('sack',IDP_ROLES['idp_sacks']),('fumble_forced',IDP_ROLES['idp_forced_fumbles']),
                            ('tackled_for_loss',IDP_ROLES['idp_tackles_for_loss']),('qb_hit',IDP_ROLES['idp_quarterback_hits'])]:
            candidates=game[game[flag].eq(1)]
            for _,row in candidates.iterrows():
                if not valid_actors(pd.DataFrame([row]),fields):extra_bad.add(gid)
    audit.loc[audit.game_id.isin(extra_bad),'proof_ready']=False
    audit.loc[audit.game_id.isin(extra_bad),'blockers']=audit.loc[audit.game_id.isin(extra_bad),'blockers'].astype(str)+';BLOCKED_SPECIALIST_EVENT_PROOF'
    ready_games=set(audit.loc[audit.proof_ready,'game_id'])
    ready_weeks=set(audit.groupby(['season','week']).proof_ready.all().loc[lambda s:s].index)
    certificates=certificates[certificates.game_id.isin(ready_games)]
    certificates=certificates[np.array([tuple(x) in ready_weeks for x in certificates[['season','week']].to_numpy()],dtype=bool)]
    zero_keys=set(map(tuple,certificates[KEYS].to_numpy()))
    base=c1[['canonical_player_id','season','week','game_id','team','opponent','position_model',
             'published_stat_row','week_state','membership_team_count']].copy()
    raw_columns=set(sum((list(v) for v in PLAYER_FIELDS.values()),[]))|{'def_qb_hits','special_teams_tds',
         'fg_missed','fg_blocked','fg_missed_list','fg_blocked_list'}
    native=raw[KEYS+sorted(raw_columns & set(raw))]
    joined=base.merge(native,on=KEYS,how='left',validate='one_to_one')
    pr=provider.rename(columns={c:'provider_'+c for c in provider if c not in KEYS})
    joined=joined.merge(pr,on=KEYS,how='left',validate='one_to_one')
    byes=joined.week_state.eq('PROVEN_BYE')
    valid_games=joined.game_id.isin(ready_games)&joined.week_state.eq('COMPLETED_GAME')
    absent_zero=pd.Series([tuple(x) in zero_keys for x in joined[KEYS].to_numpy()],index=joined.index)
    out={};rows=[]
    for comp in components:
        value=pd.to_numeric(c1.get(comp,pd.Series(np.nan,index=c1.index)),errors='coerce').copy()
        basis=pd.Series('UNKNOWN',index=c1.index,dtype=object)
        old_eligible=c1.get(comp+'__score_target_eligible',pd.Series(False,index=c1.index)).eq(True)
        value=value.where(old_eligible);basis.loc[value.notna()]='C1_SOURCE_BOUND_OUTCOME'
        human=joined.position_model.ne('DEF');relevant=~human if comp.startswith('dst_') else human
        if comp in PLAYER_FIELDS:
            raw_value=additive(joined,PLAYER_FIELDS[comp])
            if comp in {'passing_first_downs','rushing_first_downs','receiving_first_downs'}:
                # C1 is the frozen adjusted first-down owner; do not replace it.
                raw_value=pd.Series(np.nan,index=joined.index)
            fill=value.isna()&raw_value.notna()&human&joined.published_stat_row.eq(True)
            old_mismatch=c1.get(comp+'__status',pd.Series('',index=c1.index)).eq('OBSERVED_SOURCE_PROVIDER_MISMATCH')
            fill &= ~old_mismatch
            value.loc[fill]=raw_value.loc[fill];basis.loc[fill]='NFL_PUBLISHED_STAT_PROXY'
        if comp=='idp_quarterback_hits':
            native_hits=pd.to_numeric(joined.get('def_qb_hits',pd.Series(np.nan,index=joined.index)),errors='coerce')
            fill=value.isna()&native_hits.notna()&human&joined.published_stat_row.eq(True)
            value.loc[fill]=native_hits.loc[fill];basis.loc[fill]='NFL_NATIVE_HIT_PROXY_CONVENTION_UNVERIFIED'
        if comp.startswith('kicker_fgmiss_'):
            token=comp.removeprefix('kicker_fgmiss_')
            bounds=(int(token[:-1]),None) if token.endswith('p') else tuple(map(int,token.split('_')))
            raw_misses=missed_distance_counts(joined,*bounds)
            fill=value.isna()&raw_misses.notna()&human&joined.published_stat_row.eq(True)
            value.loc[fill]=raw_misses.loc[fill];basis.loc[fill]='NFL_MISSED_BLOCKED_DISTANCE_LISTS'
        # Explicit provider keys define their own specialist target convention.
        # This is label reconciliation, never a Sleeper forecast feature.
        if comp.startswith(('idp_','dst_')) or comp.startswith('individual_special_teams'):
            keys=rulekeys.get(comp,[])
            for key in keys:
                col='provider_'+key
                if col not in joined:continue
                explicit=pd.to_numeric(joined[col],errors='coerce')
                use=explicit.notna()&relevant&joined.week_state.eq('COMPLETED_GAME')
                value.loc[use]=explicit.loc[use];basis.loc[use]='EXPLICIT_SLEEPER_ACTUAL_TARGET'
        # Prove only true negatives; a candidate retains an unknown outcome.
        negative=pd.Series([bool(negatives.get(gid,{}).get(comp,False)) for gid in joined.game_id],index=joined.index)
        fill=value.isna()&negative&valid_games&relevant
        value.loc[fill]=0.;basis.loc[fill]='COMPLETE_GAME_NEGATIVE_EVENT_CERTIFICATE'
        # Exact absence is stronger than an inactive/IR tag or an omitted stat.
        fill=value.isna()&absent_zero&human&relevant
        value.loc[fill]=0.;basis.loc[fill]='WHOLE_WEEK_NO_ACTOR_NO_STAT_ZERO_CERTIFICATE'
        value.loc[byes&relevant]=0.;basis.loc[byes&relevant]='PROVEN_BYE_ZERO'
        bad=~joined.week_state.isin(['COMPLETED_GAME','PROVEN_BYE'])|~relevant
        value.loc[bad]=np.nan;basis.loc[bad]='UNKNOWN_OR_OTHER_ENTITY'
        out[comp]=value;out[comp+'__basis']=basis
        for label,indices in basis.groupby(basis).groups.items():
            rows.append({'season':season,'component':comp,'basis':label,'rows':len(indices),
                         'known_rows':int(value.loc[indices].notna().sum()),
                         'zero_rows':int(value.loc[indices].eq(0).sum()),
                         'nonzero_rows':int(value.loc[indices].notna().sum()-value.loc[indices].eq(0).sum())})
    result=pd.concat([base,pd.DataFrame(out,index=base.index)],axis=1)
    activity_cols=[c for c in components if not c.startswith(('dst_','prob_'))]
    values=result[activity_cols]
    # Any source-observed positive/signed scoreable production proves activity;
    # only full source absence/observed complete zeros prove inactivity.
    nonzero=values.fillna(0).ne(0).any(axis=1)&human
    all_known=values.notna().all(axis=1)&human
    result['stat_activity']=pd.Series(np.nan,index=result.index)
    result.loc[nonzero,'stat_activity']=1.
    result.loc[(all_known&~nonzero)|absent_zero|byes,'stat_activity']=0.
    result.loc[~human&result.week_state.eq('COMPLETED_GAME'),'stat_activity']=1.
    result['activity_basis']=np.select([nonzero,absent_zero,byes,all_known],
        ['SOURCE_NONZERO_PRODUCTION','NO_EVENT_CERTIFICATE','BYE','FULL_OBSERVED_ZERO'],default='UNKNOWN')
    return result,audit,certificates,pd.DataFrame(rows)

def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--root',type=Path,default=ROOT)
    p.add_argument('--output',type=Path,default=BASE);a=p.parse_args();root=a.root.resolve();folder=root/a.output
    folder.mkdir(parents=True,exist_ok=True)
    closure=folder/'training-view.json'
    if closure.exists():
        old=json.loads(closure.read_text())
        if sha(Path(__file__))!=old['owner_sha256']:raise ValueError('C2_TRAINING_VIEW_OWNER_CHANGED_NEW_REVISION_REQUIRED')
        for rel,h in old['artifacts'].items():
            if sha(root/rel)!=h:raise ValueError('C2_TRAINING_VIEW_DRIFT')
        print('C2_TRAINING_VIEW_PRESERVED_VERIFIED');return
    demand=build(root);components=sorted({c['component'] for c in demand['required_components']}|set(EXTRA)|set(PLAYER_FIELDS))
    rulekeys=defaultdict(list)
    for r in demand['rules']:
        if r['scoring_key'] not in rulekeys[r['component']]:rulekeys[r['component']].append(r['scoring_key'])
    current=json.loads((root/ENVELOPE).read_text());refs={r['name']:r for r in current['responses']}
    game_ref=refs['schedule'];games=pd.read_csv(verified(root,game_ref),low_memory=False)
    source_manifest=json.loads((folder/'sources/manifest.json').read_text())
    historical={r['season']:r for r in source_manifest['sources']}
    archive=json.loads((root/HISTORY/'sources/source-receipts.json').read_text())
    rawrefs={r['season']:r for r in archive['raw_player_stats']}
    captured=json.loads((root/C1/'sources/manifest.json').read_text())['sources']
    bridge=pd.read_csv(root/C1/'identity-bridge.csv.gz',dtype={'sleeper_id':'string'})
    provider=provider_rows(root,bridge,captured)
    all_support=[];scope=[];binding_refs=[]
    for year in range(2021,2027):
        c1=pd.read_csv(root/C1/f'component-week-{year}.csv.gz',low_memory=False)
        rawref=refs['player_week'] if year==2026 else rawrefs[year]
        raw=pd.read_csv(verified(root,rawref),low_memory=False)
        pbpref=refs['pbp'] if year==2026 else historical[year]
        pbp=regular(pd.read_csv(verified(root,pbpref),low_memory=False),5 if year==2026 else 18)
        selected=games[games.season.eq(year)&games.game_type.eq('REG')&games.week.le(5 if year==2026 else 18)]
        frame,audit,cert,support=build_year(c1,raw,pbp,selected,provider[provider.season.eq(year)],components,rulekeys)
        csv(frame,folder/f'training-{year}.csv.gz');csv(audit,folder/f'game-audit-{year}.csv.gz');csv(cert,folder/f'absence-certificates-{year}.csv.gz')
        all_support.append(support);binding_refs += [rawref,pbpref]
        scope.append({'season':year,'rows':len(frame),'ready_games':int(audit.proof_ready.sum()),'blocked_games':int((~audit.proof_ready).sum()),
                      'absent_zero_certificates':len(cert),'observed_activity_rows':int(frame.stat_activity.notna().sum())})
        print('C2_TRAINING_VIEW',year,scope[-1],flush=True)
    csv(pd.concat(all_support,ignore_index=True),folder/'target-support.csv.gz')
    artifacts={p.relative_to(root).as_posix():sha(p) for p in sorted(folder.glob('*.csv.gz'))}
    write(closure,{'schema':'fie-component-training-view-v2','built_at':now(),'owner_sha256':sha(Path(__file__)),
        'methodology_sha256':sha(root/'config/component-baseline-methodology-v1.json'),
        'C1_closure_sha256':sha(root/C1/'closure.json'),'components':components,'seasons':scope,
        'sources':binding_refs,'source_manifest_sha256':sha(folder/'sources/manifest.json'),
        'target_convention':'EXPLICIT_PROVIDER_SPECIALISTS_WITH_NFL_NATIVE_PROXY_AND_CERTIFIED_NEGATIVES',
        'source_semantics_fully_certified':False,'sleeper_forecasts_used':False,'artifacts':artifacts,
        'research_only':True,'transaction_eligible':False})

if __name__=='__main__':main()
