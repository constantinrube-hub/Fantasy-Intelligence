"""Versioned source-only refit replacing the unavailable historical WR fitter.

Preweek player estimates and usage ranks exclude the week being used to measure
defensive performance. This reconstructed method is not claimed to recreate the
original tier-fitting code or its coefficients.
"""
import argparse,collections,math
from pathlib import Path
import numpy as np
import pandas as pd
from recovery_common import *
from recovery_parameters import fit,individual,source_frames,pairs
from recovery_population import universe
from issue_component_forecasts import snapshot
from component_source_contract import team
def usage_roles(frame):
    cols=['canonical_player_id','season','week','team','opponent','position_model','targets','receptions','receiving_yards','receiving_touchdowns','rushing_attempts','rushing_yards','rushing_touchdowns','weight']
    f=frame.reindex(columns=cols).copy();f['team']=f.team.map(team);f['opponent']=f.opponent.map(team)
    key=['canonical_player_id','season','week'];past=f[key+['targets']];usage=np.zeros(len(f));count=np.zeros(len(f))
    for lag in range(1,5):
        p=past.copy();p.week+=lag;x=f[key].merge(p,on=key,how='left',validate='one_to_one').targets
        usage+=x.fillna(0).to_numpy();count+=x.notna().to_numpy()
    f['_prior_usage']=np.divide(usage,count,out=np.zeros_like(usage),where=count>0);f['receiving_role']=f.position_model
    wr=f[f.position_model.eq('WR')].sort_values(['season','week','team','_prior_usage','canonical_player_id'],ascending=[True,True,True,False,True])
    rank=wr.groupby(['season','week','team']).cumcount();f.loc[wr.index,'receiving_role']=np.where(rank.eq(0),'WR1',np.where(rank.eq(1),'WR2','WR3+'))
    return f
def refit(output,bundle_path,training_dir,through=5,root=ROOT):
    out=root/output
    if out.exists():raise ValueError('NEW_FIT_REVISION_REQUIRED')
    training=read(root/training_dir/'training-view.json')
    if training.get('through_week',5)!=through:raise ValueError('UPDATED_TRAINING_REVISION_REQUIRED')
    b=read(root/bundle_path);refs={r['name']:r for r in b['responses']};schedule=snapshot(root,refs['schedule'],b['observation_cutoff'])
    games=schedule[schedule.season.eq(2026)&schedule.game_type.eq('REG')&schedule.week.le(through)]
    if games[['home_score','away_score']].isna().any().any():raise ValueError('FIT_CONTAINS_UNFINISHED_WEEK')
    hist,current=source_frames(root,b,through)
    owned=set()
    for lid in b['league_ids']:
        for r in snapshot(root,refs[str(lid)+'-rosters'],b['observation_cutoff']):owned.update(str(x) for x in (r.get('players') or [])+(r.get('reserve') or [])+(r.get('taxi') or []))
    bridge=pd.read_csv(root/'data/research/components/2026-10-14/c0-c1-v1/identity-bridge.csv.gz',dtype={'sleeper_id':'string'})
    entities,_=universe(snapshot(root,refs['sleeper_players'],b['observation_cutoff']),snapshot(root,refs['weekly_rosters'],b['observation_cutoff']),snapshot(root,refs['players'],b['observation_cutoff']),bridge,owned,target_week=through+1)
    # Source historical priors are shared; this intermediate fit is retained.
    value=fit(root,bundle_path,output.with_name(output.stem+'-base.json'),through,True)
    value['players'],value['position_priors']=individual(hist,current,entities)
    h=usage_roles(hist);c=usage_roles(current);roles=['RB','TE','WR','WR1','WR2','WR3+'];prior={}
    for role in roles:
        g=h[h.position_model.eq('WR')] if role=='WR' else h[h.receiving_role.eq(role)]
        vals={k:float((pd.to_numeric(g[k],errors='coerce').fillna(0)*g.weight).sum()) for k in ['targets','receptions','receiving_yards','receiving_touchdowns']}
        prior[role]={'catch_probability':vals['receptions']/max(vals['targets'],1),'ypr':vals['receiving_yards']/max(vals['receptions'],1),'td_rate':vals['receiving_touchdowns']/max(vals['receptions'],1),'share':vals['targets']}
    total=sum(prior[x]['share'] for x in ['RB','TE','WR']);wr_total=prior['WR']['share']
    for role in roles:prior[role]['share']/=max(wr_total if role.startswith('WR') and role!='WR' else total,1)
    all_carries=float((h.rushing_attempts.fillna(0)*h.weight).sum())
    rush_share={pos:float((h.loc[h.position_model.eq(pos),'rushing_attempts'].fillna(0)*h.loc[h.position_model.eq(pos),'weight']).sum())/max(all_carries,1) for pos in ['QB','RB']}
    acc=collections.defaultdict(lambda:collections.defaultdict(float));rush_acc=collections.defaultdict(lambda:collections.defaultdict(float));past=current.iloc[:0]
    for week in range(1,through+1):
        estimates,_=individual(hist,past,entities);g=c[c.week.eq(week)]
        for row in g.itertuples():
            pos=row.position_model;club=team(row.opponent);cid=row.canonical_player_id
            if pos in {'RB','TE','WR'}:
                rs=[pos,row.receiving_role] if pos=='WR' else [pos]
                p=estimates.get(cid,value['players'].get(cid,{}));cp=p.get('catch_probability',{}).get('rate',prior[pos]['catch_probability']);yp=p.get('receiving_yards_per_reception',{}).get('rate',prior[pos]['ypr'])
                for role in rs:
                    a=acc[(club,role)];p0=prior[role]
                    for field in ['targets','receptions','receiving_yards','receiving_touchdowns']:a[field]+=float(getattr(row,field)) if pd.notna(getattr(row,field)) else 0.
                    a['expected_receptions']+=float(row.targets)*cp;a['expected_yards']+=float(row.receptions)*yp;a['expected_td']+=float(row.receptions)*p0['td_rate']
                    own=past[past.team.map(team).eq(team(row.team))]
                    if role in {'WR1','WR2','WR3+'}:share=p0['share'];team_total=float(g[g.team.eq(row.team)&g.position_model.eq('WR')].targets.sum())
                    else:
                        total_p=float(own[own.position_model.isin(['RB','TE','WR'])].targets.sum());part=float(own[own.position_model.eq(pos)].targets.sum());share=(part+100*p0['share'])/(total_p+100);team_total=float(g[g.team.eq(row.team)&g.position_model.isin(['RB','TE','WR'])].targets.sum())
                    # Allocate team role expectation only once per role/team/week.
                    marker=f'share_{week}_{row.team}'
                    if marker not in a:a['expected_targets']+=team_total*share;a[marker]=1.
            if pos in {'QB','RB'}:
                a=rush_acc[(club,pos)];a['carries']+=float(row.rushing_attempts);a['yards']+=float(row.rushing_yards);a['touchdowns']+=float(row.rushing_touchdowns)
                rate=estimates.get(cid,{}).get('rushing_yards_per_carry',{}).get('rate',value['position_priors'][pos]['rushing_yards_per_carry']['rate']);a['expected_yards']+=float(row.rushing_attempts)*rate;a['expected_td']+=float(row.rushing_attempts)*value['td_priors'][pos]['rushing']
                marker=f'share_{week}_{row.team}'
                if marker not in a:
                    own=past[past.team.map(team).eq(team(row.team))];total_p=float(own.rushing_attempts.sum());part=float(own[own.position_model.eq(pos)].rushing_attempts.sum());share=(part+100*rush_share[pos])/(total_p+100);a['expected_carries']+=float(g[g.team.eq(row.team)].rushing_attempts.sum())*share;a[marker]=1.
        past=current[current.week.le(week)]
    receive={};wr={};rush={};off_wr={}
    for club in sorted(value['receiving_defense']):
        receive[club]={};wr[club]={};rush[club]={}
        for role in roles:
            a=acc[(club,role)];p=prior[role]
            effect=(a['targets']+100*p['share'])/(a['expected_targets']+100*p['share'])
            d={'observed':{k:a[k] for k in ['targets','receptions','receiving_yards','receiving_touchdowns']},'weight_multiplier':math.sqrt(max(effect,0)),'catch_probability':float(np.clip(p['catch_probability']*(a['receptions']+40*p['catch_probability'])/(a['expected_receptions']+40*p['catch_probability']),.01,.99)),'ypr':p['ypr']*(a['receiving_yards']+40*p['ypr'])/(a['expected_yards']+40*p['ypr']),'td_rate':float(np.clip(p['td_rate']*(a['receiving_touchdowns']+120*p['td_rate'])/(a['expected_td']+120*p['td_rate']),1e-6,.99))}
            (wr if role in {'WR1','WR2','WR3+'} else receive)[club][role]=d
        for pos in ['QB','RB']:
            a=rush_acc[(club,pos)];p=value['position_priors'][pos]['rushing_yards_per_carry']['rate'];td=value['td_priors'][pos]['rushing']
            effect=(a['carries']+100*rush_share[pos])/(a['expected_carries']+100*rush_share[pos])
            rush[club][pos]={'carry_weight_multiplier':math.sqrt(max(effect,0)),'allowed_ypc':p*(a['yards']+40*p)/(a['expected_yards']+40*p),'allowed_td_rate':float(np.clip(td*(a['touchdowns']+120*td)/(a['expected_td']+120*td),1e-6,.99)),'observed':dict(a)}
        own=c[c.team.eq(club)];off_wr[club]={}
        for role in ['WR1','WR2','WR3+']:
            g=own[own.receiving_role.eq(role)];off_wr[club][role]=(float(g.receiving_touchdowns.sum())+120*prior[role]['td_rate'])/(float(g.receptions.sum())+120)
    value.update({'version':'SOURCE_PREWEEK_ROLE_REFIT_V2','rushing_defense':rush,'receiving_defense':receive,'wr_defense':wr,'wr_offensive_role_td':off_wr,'source_role_priors':prior,'population_ids':len(entities),'training_revision_path':training_dir.as_posix(),'training_revision_sha256':sha(root/training_dir/'training-view.json'),'coefficient_sources':[],'owner_sha256':sha(Path(__file__)),'limitations':['ORIGINAL_WR_TRAINING_CODE_UNAVAILABLE','RECONSTRUCTED_PREWEEK_USAGE_RANKS_WITH_CANONICAL_ID_TIEBREAKS','NO_PREDICTIVE_SUPERIORIORITY_OR_CALIBRATION']})
    write(out,value);print('SOURCE_REFIT_READY',len(entities),flush=True);return value
if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--output',type=Path,required=True);p.add_argument('--bundle',type=Path,required=True);p.add_argument('--training-dir',type=Path,required=True);p.add_argument('--through-week',type=int,required=True);a=p.parse_args();refit(a.output,a.bundle,a.training_dir,a.through_week)
