"""Current-week exact-ID population; preserved identity logic with a parameterized cutoff."""
import re
import pandas as pd
from component_source_contract import position,team
from issue_component_forecasts import GSIS,ALLOWED,as_id,entry_season

def universe(catalog,roster,players,bridge,owned,target_week=6):
    """Exact NFL IDs or explicitly separated provider-only identities; no names."""
    owned=set(owned)|{sid for sid,meta in catalog.items() if meta.get('position')=='K' and meta.get('team') and meta.get('status')=='Active'}
    roster=roster[roster.season.eq(2026)&roster.week.le(target_week)].copy()
    latest=int(roster.week.max())
    # NFLverse need not publish a target-week roster for a club on bye.
    # Retain the latest observed club roster, including the prior week for byes.
    latest_club_week=roster.groupby('team',dropna=False).week.transform('max')
    roster=roster[roster.week.eq(latest_club_week)]
    membership=roster.status.isin({'ACT','DEV','E14','EXE','INA','PUP','RES','RSN','SUS'})
    if 'status_description_abbr' in roster:membership|=roster.status_description_abbr.eq('A01')
    roster=roster[membership & roster.gsis_id.astype(str).str.strip().str.fullmatch(GSIS.pattern)].copy()
    rows={};audit=[]
    exact=bridge[bridge.identity_status.eq('EXACT_ONE_TO_ONE')].copy()
    gsis_to_sid=dict(zip(exact.canonical_player_id.astype(str),exact.sleeper_id.astype(str)))
    sid_to_gsis={sid:gsis for gsis,sid in gsis_to_sid.items()}
    players_map={str(r.gsis_id).strip():r._asdict() for r in players.itertuples(index=False) if pd.notna(r.gsis_id)}
    def add(sid,cid,raw_roster=None):
        meta=catalog.get(sid,{})
        p=position(meta.get('position') or (raw_roster or {}).get('position',''))
        eligible=sorted({position(x) for x in meta.get('fantasy_positions',[]) if position(x) in ALLOWED}|({p} if p in ALLOWED else set()))
        if p not in ALLOWED:
            if eligible:p=eligible[0]
            else:return
        gsis=cid if GSIS.fullmatch(cid) else None
        nfl=players_map.get(gsis,{})
        observed=(raw_roster or {})
        meta_team=meta.get('team');observed_team=observed.get('team')
        club=team(meta_team) if meta_team else team(observed_team) if observed_team else None
        nfl_clubs={team(v) for v in roster.team.dropna()}
        if club not in nfl_clubs:club=None
        nfl_pos=position(observed.get('position',p))
        model_pos=nfl_pos if nfl_pos in ALLOWED else p
        rookie=entry_season(nfl.get('rookie_season'),observed.get('rookie_year'),observed.get('entry_year'))
        identity_status='EXACT_GSIS_PROVIDER_BINDING' if gsis else 'EXACT_PROVIDER_ID_GSIS_UNRESOLVED'
        rows[cid]={'canonical_player_id':cid,'gsis_id':gsis,'sleeper_id':sid,
          'name':meta.get('full_name') or observed.get('full_name') or nfl.get('display_name') or sid,
          'position_model':p,'model_position':model_pos,'fantasy_positions':eligible,'team':club,
          'entry_season':rookie,'identity_status':identity_status,'current_roster_week':int(observed['week']) if raw_roster else None,
          'injury_status':meta.get('injury_status'),'provider_status':meta.get('status'),
          'source_roster_status':observed.get('status'),'position_source_disagreement':p!=model_pos}
    for gsis,group in roster.groupby(roster.gsis_id.astype(str).str.strip(),sort=True):
        candidates={as_id(v) for v in group.sleeper_id.dropna()} if 'sleeper_id' in group else set()
        candidates.discard(None)
        mapped=gsis_to_sid.get(gsis)
        if mapped:candidates.add(mapped)
        if len(candidates)!=1:
            audit.append({'canonical_player_id':gsis,'status':'UNRESOLVED_CURRENT_PROVIDER_BINDING','candidates':sorted(candidates)});continue
        sid=next(iter(candidates));meta=catalog.get(sid,{})
        pg=str(meta.get('gsis_id') or '').strip()
        if pg and pg!=gsis:
            audit.append({'canonical_player_id':gsis,'sleeper_id':sid,'status':'CONFLICTING_FRESH_PROVIDER_GSIS'});continue
        teams=set(group.team.dropna().map(team));meta_team=team(meta['team']) if meta.get('team') else None
        selected=group
        if len(teams)>1:
            if meta_team in teams:selected=group[group.team.map(team).eq(meta_team)]
            else:
                audit.append({'canonical_player_id':gsis,'sleeper_id':sid,'status':'AMBIGUOUS_CUTOFF_TEAM'});continue
        add(sid,gsis,selected.iloc[0].to_dict())
    existing={r['sleeper_id']:cid for cid,r in rows.items()}
    for sid in sorted(owned):
        if sid in existing or re.fullmatch(r'[A-Z]{2,3}',sid):continue
        meta=catalog.get(sid)
        if not meta:
            audit.append({'sleeper_id':sid,'status':'OWNED_ID_ABSENT_FROM_FRESH_CATALOG'});continue
        gsis=sid_to_gsis.get(sid)
        pg=str(meta.get('gsis_id') or '').strip()
        if gsis and pg and pg!=gsis:gsis=None
        cid=gsis if gsis and gsis not in rows else 'SLEEPER:'+sid
        add(sid,cid)
    clubs=sorted(set(team(v) for v in roster.team.dropna()))
    for club in clubs:
        candidates=[sid for sid,m in catalog.items() if position(m.get('position'))=='DEF' and team(sid)==club]
        sid=club if club in candidates else candidates[0] if len(candidates)==1 else club
        rows['TEAM:'+club]={'canonical_player_id':'TEAM:'+club,'gsis_id':None,'sleeper_id':sid,'name':club+' D/ST',
             'position_model':'DEF','model_position':'DEF','fantasy_positions':['DEF'],'team':club,
             'entry_season':None,'identity_status':'CANONICAL_TEAM_DEFENSE','current_roster_week':latest,
             'injury_status':None,'provider_status':'TEAM','source_roster_status':'TEAM','position_source_disagreement':False}
    if len([r for r in rows.values() if r['position_model']=='DEF'])!=32:raise ValueError('C4_TEAM_UNIVERSE_NOT_32')
    if len({r['sleeper_id'] for r in rows.values()})!=len(rows):raise ValueError('C4_PROVIDER_FORECAST_UNIVERSE_COLLISION')
    return sorted(rows.values(),key=lambda r:(r['position_model'],r['canonical_player_id'])),audit

