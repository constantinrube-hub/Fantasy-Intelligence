#!/usr/bin/env python3
"""Build the current M9 season projection board from validated preseason specs.

Validated FIE year-to-year raw-stat specs are preferred.  Players/positions without a
cleared FIE preseason gate fall back to the frozen Sleeper season projection and are
labelled MARKET_FALLBACK.  This produces a complete board without pretending an
unvalidated model is production-ready.
"""
from __future__ import annotations

import argparse
import gzip
import json
import math
import re
from pathlib import Path
from typing import Dict, List, Optional

import numpy as np
import pandas as pd

from fie_research import BONUS_RULES, SCORING_MAP, score_rows
from fie_m9 import RETURN_SCORING_ALIASES, score_return_stats, simulate_player_season


def load_json(path: str) -> dict:
    return json.loads(Path(path).read_text())


def load_market(path: str) -> List[dict]:
    p=Path(path); rows=[]
    opener=gzip.open if p.suffix=='.gz' else open
    with opener(p,'rt',encoding='utf-8') as h:
        for line in h:
            line=line.strip()
            if line: rows.append(json.loads(line))
    return rows


def predict_spec(spec: dict, values: dict, with_contrib: bool=False):
    fs=spec.get('features') or []; med=spec.get('imputer_medians') or []; mu=spec.get('scaler_mean') or []; sd=spec.get('scaler_scale') or []; co=spec.get('coefficients') or []
    if not (len(fs)==len(med)==len(mu)==len(sd)==len(co)): raise ValueError('invalid preseason target spec')
    y=float(spec.get('intercept') or 0); contrib={}
    for i,f in enumerate(fs):
        v=values.get(f)
        try: x=float(v) if v is not None and math.isfinite(float(v)) else float(med[i])
        except Exception: x=float(med[i])
        c=((x-float(mu[i]))/(float(sd[i]) if float(sd[i]) else 1.0))*float(co[i]); y += c; contrib[f]=float(c)
    pred=max(float(spec.get('prediction_floor') or 0),y)
    return (pred,contrib) if with_contrib else pred


def target_point_weight(target: str, scoring: dict, pos: str) -> float:
    w=0.0
    for key,aliases in SCORING_MAP.items():
        if target in aliases:
            try: w += float(scoring.get(key) or 0)
            except Exception: pass
    if target=='receptions':
        pkey={'RB':'bonus_rec_rb','WR':'bonus_rec_wr','TE':'bonus_rec_te'}.get(pos)
        alt={'RB':'rec_rb','WR':'rec_wr','TE':'rec_te'}.get(pos)
        for k in [pkey,alt]:
            if k:
                try: w += float(scoring.get(k) or 0)
                except Exception: pass
    return float(w)


def market_points(stats: dict, scoring: dict, position: str) -> Optional[float]:
    pts=0.0; used=0
    for key,w in scoring.items():
        try: weight=float(w)
        except Exception: continue
        if not weight: continue
        if key in {'bonus_rec_te','rec_te','bonus_rec_rb','rec_rb','bonus_rec_wr','rec_wr'}:
            target='TE' if '_te' in key else ('RB' if '_rb' in key else 'WR')
            if position==target and stats.get('rec') is not None:
                pts += float(stats.get('rec') or 0)*weight; used+=1
            continue
        v=stats.get(key)
        try:
            if v is not None and math.isfinite(float(v)):
                pts += float(v)*weight; used+=1
        except Exception: pass
    if used: return float(pts)
    for key in ('pts_ppr','pts_half_ppr','pts_std','pts'):
        try:
            x=float(stats.get(key));
            if math.isfinite(x): return x
        except Exception: pass
    return None


def active_return_scoring(scoring: dict) -> List[str]:
    out=[]
    for k,v in (scoring or {}).items():
        if k not in RETURN_SCORING_ALIASES:
            continue
        try:
            if math.isfinite(float(v)) and float(v) != 0:
                out.append(str(k))
        except Exception:
            pass
    return sorted(out)


def return_profile_index(m9: dict) -> Dict[str, dict]:
    rows=(m9.get('returner_intelligence',{}).get('season_projection',{}).get('latest_profiles') or [])
    return {str(r.get('canonical_player_id')): r for r in rows if r.get('canonical_player_id')}


def predict_validated_returns(m9: dict, cid: str, current_team: str) -> dict:
    season=m9.get('returner_intelligence',{}).get('season_projection',{}) or {}
    specs=season.get('model_specs') or {}; prof=return_profile_index(m9).get(str(cid))
    if not prof or not specs:
        return {'raw':{},'profile':prof,'eligible_targets':[], 'team_changed':False}
    old_team=str(prof.get('profile_team') or '')
    changed=bool(current_team and old_team and current_team != old_team)
    if changed:
        return {'raw':{},'profile':prof,'eligible_targets':[], 'team_changed':True}
    raw={}; eligible=[]
    for target,spec in specs.items():
        try:
            raw[str(target)]=float(predict_spec(spec,prof)); eligible.append(str(target))
        except Exception:
            continue
    return {'raw':raw,'profile':prof,'eligible_targets':sorted(eligible),'team_changed':False}


def model_scoring_coverage(targets: List[str], scoring: dict, pos: str, return_targets: Optional[List[str]]=None) -> dict:
    # Nonlinear per-game bonuses need explicit occurrence models, not an average-stat threshold.
    nonlinear=[k for k,v in scoring.items() if k in BONUS_RULES and float(v or 0)!=0]
    relevant={
        'QB': {'pass_yd','pass_td','pass_int','pass_cmp','pass_att','pass_2pt','pass_fd','rush_yd','rush_td','rush_att','rush_2pt','rush_fd','fum_lost'},
        'RB': {'rush_yd','rush_td','rush_att','rush_2pt','rush_fd','rec','rec_yd','rec_td','rec_tgt','rec_2pt','rec_fd','fum_lost','bonus_rec_rb','rec_rb'},
        'WR': {'rush_yd','rush_td','rush_att','rush_2pt','rush_fd','rec','rec_yd','rec_td','rec_tgt','rec_2pt','rec_fd','fum_lost','bonus_rec_wr','rec_wr'},
        'TE': {'rush_yd','rush_td','rush_att','rush_2pt','rush_fd','rec','rec_yd','rec_td','rec_tgt','rec_2pt','rec_fd','fum_lost','bonus_rec_te','rec_te'},
    }.get(pos,set())
    active=[]
    for k,v in scoring.items():
        try: nz=float(v or 0)!=0
        except Exception: nz=False
        if k in relevant and nz: active.append(k)
    supported=[]; unsupported=[]
    targetset=set(targets)
    for key in active:
        if key in {'bonus_rec_te','rec_te','bonus_rec_rb','rec_rb','bonus_rec_wr','rec_wr'}:
            (supported if 'receptions' in targetset else unsupported).append(key); continue
        aliases=SCORING_MAP.get(key) or []
        if any(a in targetset for a in aliases): supported.append(key)
        else: unsupported.append(key)
    return_targets=set(return_targets or [])
    for key in active_return_scoring(scoring):
        active.append(key)
        raw=RETURN_SCORING_ALIASES[key]
        # Generic ret_yd/ret_td can be reconstructed when both component targets exist.
        ok = raw in return_targets or (raw=='return_yd' and {'kr_yd','pr_yd'}.issubset(return_targets)) or (raw=='return_td' and {'kr_td','pr_td'}.issubset(return_targets))
        (supported if ok else unsupported).append(key)
    unsupported=sorted(set(unsupported+nonlinear))
    return {'active_keys':sorted(set(active)),'supported_keys':sorted(set(supported)),'unsupported_keys':unsupported,
            'coverage_rate':len(supported)/(len(supported)+len(unsupported)) if supported or unsupported else 1.0,
            'exact_linear_replay':not unsupported}


def norm_name(value: object) -> str:
    return re.sub(r"[^a-z0-9]+", "", str(value or "").lower())


def norm_sleeper_id(value: object) -> str:
    """Normalize Sleeper IDs read through pandas without changing non-numeric IDs."""
    if value is None:
        return ""
    s = str(value).strip()
    if not s or s.lower() in {"nan", "none"}:
        return ""
    if re.fullmatch(r"\d+\.0", s):
        s = s[:-2]
    return s


def board(args) -> pd.DataFrame:
    m1=load_json(args.m1_bundle); m9=load_json(args.m9_bundle); scoring=m1.get('scoring',{}).get('settings',{})
    market=load_market(args.market_snapshot)
    prof_path=Path(args.profile_table or m9.get('preseason_season_projection',{}).get('latest_profiles_derived_table') or '')
    profiles=pd.read_csv(prof_path,low_memory=False) if prof_path.is_file() else pd.DataFrame()
    by_pid={str(r.canonical_player_id):r._asdict() for r in profiles.itertuples(index=False)} if not profiles.empty else {}

    # Preserve the immutable market snapshot and repair only identity at read time.
    # Pandas can deserialize numeric Sleeper IDs as floats (e.g. 6786.0), which must
    # be normalized before matching the string IDs returned by the Sleeper endpoint.
    identity_path = prof_path.parent / "player_identity.csv.gz"
    identity = pd.read_csv(identity_path, low_memory=False) if identity_path.is_file() else pd.DataFrame()
    by_sid={}
    if not identity.empty and {"sleeper_id","canonical_player_id"}.issubset(identity.columns):
        for r in identity.dropna(subset=["sleeper_id","canonical_player_id"]).to_dict("records"):
            sid=norm_sleeper_id(r.get("sleeper_id"))
            if sid:
                by_sid[sid]=r

    by_name={}
    if not profiles.empty and {'full_name','position_model'}.issubset(profiles.columns):
        tmp=profiles.copy(); tmp['_name_key']=tmp.full_name.map(norm_name); tmp['_pos_key']=tmp.position_model.astype(str).str.upper()
        counts=tmp.groupby(['_name_key','_pos_key']).size()
        for r in tmp.to_dict('records'):
            k=(r.get('_name_key'),r.get('_pos_key'))
            if k[0] and counts.get(k,0)==1: by_name[k]=r
    specs=m9.get('preseason_season_projection',{}).get('model_specs',{}) or {}
    weekly_cal=m9.get('projection_distribution',{}).get('position_calibration',{}) or {}
    rows=[]
    for rec in market:
        pos=str(rec.get('position_model') or '').upper();
        if pos not in {'QB','RB','WR','TE'}: continue
        cid=str(rec.get('canonical_player_id') or ''); stats=rec.get('stats') or {}; adps=rec.get('adp') or {}
        mkt=market_points(stats,scoring,pos)
        p=by_pid.get(cid) if cid else None; join_method='canonical_id' if p is not None else 'unmatched'
        identity_row=None
        if p is None:
            sid=norm_sleeper_id(rec.get('sleeper_id'))
            identity_row=by_sid.get(sid)
            identity_cid=str((identity_row or {}).get('canonical_player_id') or '')
            if identity_cid:
                p=by_pid.get(identity_cid)
                cid=identity_cid
                if p is not None:
                    join_method='sleeper_id_to_canonical'
        if p is None:
            p=by_name.get((norm_name(rec.get('full_name')),pos))
            if p is not None: join_method='unique_name_position'
        matched_cid=str((p or {}).get('canonical_player_id') or cid or '')
        pspec=specs.get(pos); raw={}; coverage={'exact_linear_replay':False,'coverage_rate':0.0,'unsupported_keys':['no_validated_preseason_spec']}
        source='MARKET_FALLBACK'; ppg=None; team_changed=False
        driver_contrib={}
        current_team=str(rec.get('team') or '')
        ret = predict_validated_returns(m9, matched_cid, current_team) if active_return_scoring(scoring) else {'raw':{},'profile':None,'eligible_targets':[],'team_changed':False}
        if p and pspec:
            targets=[]
            for ts in pspec.get('targets') or []:
                try:
                    target=str(ts.get('target')); pred,fc=predict_spec(ts,p,with_contrib=True); raw[target]=pred; targets.append(target)
                    weight=target_point_weight(target,scoring,pos)
                    for f,c in fc.items(): driver_contrib[f]=driver_contrib.get(f,0.0)+float(c)*weight
                except Exception: pass
            return_raw=dict(ret.get('raw') or {})
            if return_raw:
                return_raw['return_yd']=float(return_raw.get('kr_yd',0) or 0)+float(return_raw.get('pr_yd',0) or 0)
                return_raw['return_td']=float(return_raw.get('kr_td',0) or 0)+float(return_raw.get('pr_td',0) or 0)
            coverage=model_scoring_coverage(targets,scoring,pos,return_targets=list(return_raw))
            old_team=str(p.get('profile_team') or '')
            team_changed=bool(current_team and old_team and current_team!=old_team) or bool(ret.get('team_changed'))
            # Role/team transfer is not learned by either year-to-year model; changed-team players fail closed.
            if raw and coverage.get('exact_linear_replay') and not team_changed:
                f=pd.DataFrame([{**raw,'position_model':pos}]); offense_ppg=float(score_rows(f,scoring).iloc[0])
                return_ppg=float(score_return_stats(return_raw,scoring).get('points') or 0.0)
                ppg=offense_ppg+return_ppg
                raw.update({f'return__{k}':v for k,v in return_raw.items() if k in {'kr_yd','pr_yd','kr_td','pr_td'}})
                source='FIE_M9_VALIDATED_PRESEASON_RETURN' if active_return_scoring(scoring) else 'FIE_M9_VALIDATED_PRESEASON'
        if ppg is not None:
            mean=float(ppg)*args.games
        else:
            mean=float(mkt) if mkt is not None else None
            ppg=(mean/args.games) if mean is not None and args.games else None
        cal=weekly_cal.get(pos,{})
        dist=simulate_player_season(ppg or 0,args.games,cal,n=args.simulations,seed=args.seed+len(rows),active_probability=args.active_probability) if mean is not None else {}
        # Anchor simulated mean to the board mean while retaining the empirically calibrated spread.
        sim_mean=dist.get('mean') or 0; shift=(mean-sim_mean) if mean is not None else 0
        q={k:(float(dist[k]+shift) if k in dist else None) for k in ['p10','p25','p50','p75','p90']}
        adp=adps.get(args.adp_key)
        try: adp=float(adp) if adp is not None and 0<float(adp)<999 else None
        except Exception: adp=None
        conf=90 if source.startswith('FIE') else (62 if mkt is not None else 10)
        if p: conf+=min(5,int(p.get('prev_games') or 0)//4)
        if team_changed: conf=min(conf,55)
        display_name=(p or {}).get('full_name') or (identity_row or {}).get('full_name') or rec.get('full_name')
        rows.append({'sleeper_id':rec.get('sleeper_id'),'canonical_player_id':matched_cid or None,'full_name':display_name,
                     'identity_join_method':join_method,
                     'position_model':pos,'team':rec.get('team'),'profile_team':p.get('profile_team') if p else None,
                     'team_changed':team_changed,'market_adp':adp,'market_adp_key':args.adp_key,'sleeper_market_projection':mkt,
                     'fie_season_mean':mean,'fie_ppg':ppg,**q,'confidence':min(95,conf),'projection_source':source,
                     'scoring_coverage':coverage.get('coverage_rate'),'scoring_unsupported':'|'.join(coverage.get('unsupported_keys',[])),
                     'raw_projected_stats_per_game':json.dumps(raw,separators=(',',':')) if raw else '{}',
                     'active_return_scoring':'|'.join(active_return_scoring(scoring)),
                     'validated_return_targets':'|'.join(ret.get('eligible_targets') or []),
                     'driver_contributions_ppg':json.dumps(dict(sorted(driver_contrib.items(),key=lambda kv:abs(kv[1]),reverse=True)[:8]),separators=(',',':')) if driver_contrib else '{}'})
    out=pd.DataFrame(rows)
    if not out.empty:
        out['fie_position_rank']=out.groupby('position_model').fie_season_mean.rank(method='min',ascending=False)
        out['market_position_rank']=out.groupby('position_model').market_adp.rank(method='min',ascending=True)
        out['comparison_eligible']=out.projection_source.astype(str).str.startswith('FIE')
        out['rank_edge']=np.where(out.comparison_eligible,out.market_position_rank-out.fie_position_rank,np.nan)
    return out


def parse_args(argv=None):
    p=argparse.ArgumentParser()
    p.add_argument('--m1-bundle',required=True);p.add_argument('--m9-bundle',required=True);p.add_argument('--market-snapshot',required=True)
    p.add_argument('--profile-table',default='');p.add_argument('--adp-key',default='adp_ppr');p.add_argument('--games',type=int,default=17)
    p.add_argument('--simulations',type=int,default=10000);p.add_argument('--seed',type=int,default=9409);p.add_argument('--active-probability',type=float,default=1.0)
    p.add_argument('--output',required=True);return p.parse_args(argv)


def main(argv=None):
    a=parse_args(argv); df=board(a); out=Path(a.output);out.parent.mkdir(parents=True,exist_ok=True)
    df.to_csv(out,index=False); meta=out.with_suffix(out.suffix+'.meta.json')
    meta.write_text(json.dumps({'rows':len(df),'adp_key':a.adp_key,'games':a.games,'market_snapshot':a.market_snapshot,
                                'fie_validated':int(df.projection_source.str.startswith('FIE').sum()) if not df.empty else 0,
                                'market_fallback':int(df.projection_source.eq('MARKET_FALLBACK').sum()) if not df.empty else 0},indent=2))
    print(f'Wrote {out} rows={len(df)} FIE={int(df.projection_source.str.startswith("FIE").sum()) if not df.empty else 0}')

if __name__=='__main__':main()
