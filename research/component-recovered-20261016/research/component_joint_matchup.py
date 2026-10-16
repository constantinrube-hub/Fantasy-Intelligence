"""Research-only shared matchup event forecasts; original C4 owners stay immutable."""
from __future__ import annotations
import argparse,collections,gzip,hashlib,html,io,json,math,re
from html.parser import HTMLParser
from pathlib import Path
import numpy as np
import pandas as pd
from component_baselines import parameters,scenarios,MODELS,FG_BANDS,DISTANCE_MID,POINT_BANDS
from component_scoring import rules_for,score_scenarios,validate_scenarios
from component_training_view import BASE as TRAINING
from component_source_contract import team
from issue_component_forecasts import snapshot,universe,pool_eligibility,game_context,JsonLines
from prospective_research_io import now,sha,write,response,clock

ROOT=Path(__file__).resolve().parents[1]
BASE=Path('data/research/components/2026-10-15/joint-v5')
OLD=Path('data/research/components/2026-10-14/c2-c4-v1/captures/20261014T174651230972Z/issuance')
METHOD=Path('config/component-joint-matchup-methodology-v1.json')
MODEL='J1_JOINT_OPPONENT_AVAILABILITY_V1'
N=1024

class InjuryTable(HTMLParser):
 def __init__(self):super().__init__();self.rows=[];self.row=None;self.cell=None
 def handle_starttag(self,t,a):
  if t=='tr':self.row=[]
  if t in {'td','th'} and self.row is not None:self.cell=[]
 def handle_data(self,d):
  if self.cell is not None:self.cell.append(d)
 def handle_endtag(self,t):
  if t in {'td','th'} and self.cell is not None:self.row.append(' '.join(' '.join(self.cell).split()));self.cell=None
  if t=='tr' and self.row is not None:
   if len(self.row)==7:self.rows.append(self.row)
   self.row=None

def num(x):
 try:v=float(x);return v if np.isfinite(v) else 0.
 except (ValueError,TypeError):return 0.

def norm(x):return re.sub('[^a-z0-9]','',str(x).lower()).replace('patrick','pat').removesuffix('ii').removesuffix('jr')

def prepare(root,folder):
 b=json.loads((folder/'observations/observation-bundle.json').read_text());refs={r['name']:r for r in b['responses']}
 old=json.loads((root/OLD/'capture-manifest.json').read_text())
 for rel,h in {**old['artifacts'],**old['owners']}.items():
  if sha(root/rel)!=h:raise ValueError('ORIGINAL_C4_DRIFT:'+rel)
 lock=json.loads((root/old['model_lock']['path']).read_text())
 data={name:snapshot(root,refs[name],b['observation_cutoff']) for name in ['players','weekly_rosters','sleeper_players','schedule','snaps','pbp']}
 profiles=[];ownership={};owned=set()
 for lid in b['league_ids']:
  profile=snapshot(root,refs[lid+'-profile'],b['observation_cutoff']);profiles.append(profile)
  roster=snapshot(root,refs[lid+'-rosters'],b['observation_cutoff']);ownership[lid]={}
  for r in roster:
   for sid in (r.get('players') or [])+(r.get('reserve') or [])+(r.get('taxi') or []):ownership[lid][str(sid)]={'roster_id':r['roster_id'],'owner_id':r.get('owner_id')};owned.add(str(sid))
 bridge=pd.read_csv(root/'data/research/components/2026-10-14/c0-c1-v1/identity-bridge.csv.gz',dtype={'sleeper_id':'string'})
 # New kickers can precede the roster feed; retain their exact provider IDs separately.
 critical={sid for sid,meta in data['sleeper_players'].items() if meta.get('position')=='K' and meta.get('team') and meta.get('status')=='Active'}
 entities,identity_audit=universe(data['sleeper_players'],data['weekly_rosters'],data['players'],bridge,owned|critical)
 previous={r['canonical_player_id']:r for r in map(json.loads,gzip.open(root/OLD/'model-parameters.jsonl.gz','rt')) if r['model_id']==MODELS[1]}
 training=pd.read_csv(root/TRAINING/'training-2026.csv.gz',low_memory=False);histories={cid:g for cid,g in training.groupby('canonical_player_id')}
 ps={e['canonical_player_id']:previous.get(e['canonical_player_id']) or parameters(lock,histories.get(e['canonical_player_id'],training.iloc[:0]),e['model_position'],MODELS[1]) for e in entities}
 snaps=data['snaps'];snaps=snaps[snaps.week.between(2,5)&snaps.game_type.eq('REG')].copy()
 pf=data['players'].dropna(subset=['pfr_id']).copy();amb=pf.pfr_id.duplicated(keep=False);mapping=dict(zip(pf.loc[~amb,'pfr_id'],pf.loc[~amb,'gsis_id']))
 snaps['cid']=snaps.pfr_player_id.map(mapping);snapmeans=snaps.groupby('cid')[['offense_pct','defense_pct','st_pct']].mean().to_dict('index')
 official=[];status={}
 for label in ['broncos','seahawks']:
  path=Path('/workspace/scratch/3774d34394d4')/(label+'-injury.html');raw=path.read_bytes();observed=__import__('datetime').datetime.fromtimestamp(path.stat().st_mtime,__import__('datetime').timezone.utc).isoformat()
  ref=response(root,folder/'official',label+'-injury','https://www.'+('denverbroncos.com' if label=='broncos' else 'seahawks.com')+'/team/injury-report/',raw,observed,'html');official.append(ref)
  parser=InjuryTable();parser.feed(raw.decode())
  for row in parser.rows:
   if row[-1].upper() in {'OUT','QUESTIONABLE','DOUBTFUL','(-)','UNSPECIFIED'}:status[norm(row[0])]=row[-1].upper()
 for e in entities:
  meta=data['sleeper_players'].get(e['sleeper_id'],{});e['depth_order']=num(meta.get('depth_chart_order'));e['snaps']=snapmeans.get(e['canonical_player_id'],{});e['official_status']=status.get(norm(e['name'])) if e['team'] in {'SEA','DEN'} else None
  e['provider_injury']=str(meta.get('injury_status') or '').upper()
 # Historical consumed-field projections retain missing fields; no weather inputs.
 paths=[]
 for year in range(2021,2026):
  p=root/f'data/research/components/2026-10-14/c2-c4-v1/priors/sources/pbp-{year}.csv.gz';receipt=json.loads(p.with_name(f'pbp-{year}.receipt.json').read_text())
  if sha(p)!=receipt['sha256']:raise ValueError('HISTORICAL_PBP_DRIFT')
  paths.append(p)
 needed={'season_type','game_id','posteam','defteam','week','play_type','game_seconds_remaining','two_point_attempt','pass_attempt','rush_attempt','sack','complete_pass','interception','pass_touchdown','rush_touchdown','first_down_pass','first_down_rush','fumble','fumble_lost','field_goal_attempt','solo_tackle','assist_tackle','qb_hit','safety','passing_yards','rushing_yards','receiver_player_id','desc'}
 historical=[pd.read_csv(p,usecols=lambda k:k in needed,low_memory=False) for p in paths]
 league,_,pools=profiles_from_pbp(pd.concat(historical,ignore_index=True))
 current=data['pbp'];current=current[current.week.le(5)&current.season_type.eq('REG')];_,teamgames,_=profiles_from_pbp(current)
 offense={};defense={}
 for club in sorted({e['team'] for e in entities if e['team']}):
  own=[r for r in teamgames if r['team']==club];allowed=[r for r in teamgames if r['opponent']==club]
  offense[club]=shrink(own,league);defense[club]=shrink(allowed,league)
 source={'observed_at':now(),'observation_bundle_sha256':sha(folder/'observations/observation-bundle.json'),'original_manifest_sha256':sha(root/OLD/'capture-manifest.json'),'methodology_sha256':sha(root/METHOD),'official':official,'historical':[{'path':p.relative_to(root).as_posix(),'sha256':sha(p)} for p in paths],'weather':False,'missing_original_historical_publication_clocks':True}
 if (folder/'input-lock.json').exists():source['observed_at']=json.loads((folder/'input-lock.json').read_text())['observed_at']
 write(folder/'input-lock.json',source);write(folder/'entities.json',{'entities':entities,'identity_audit':identity_audit});write(folder/'team-parameters.json',{'league':league,'offense':offense,'defense':defense})
 return entities,ps,lock,profiles,ownership,data,offense,defense,pools

def profiles_from_pbp(frame):
 f=frame[frame.season_type.eq('REG')].copy();f=f[f.posteam.notna()&f.defteam.notna()&f.play_type.ne('no_play')&f.two_point_attempt.fillna(0).eq(0)]
 # Only completed source games with end-clock evidence enter these descriptive priors.
 finals=frame.loc[frame.game_seconds_remaining.eq(0),'game_id'].unique();f=f[f.game_id.isin(finals)]
 for c in ['pass_attempt','rush_attempt','sack','complete_pass','interception','pass_touchdown','rush_touchdown','first_down_pass','first_down_rush','fumble','fumble_lost','field_goal_attempt','solo_tackle','assist_tackle','qb_hit','safety']:
  if c not in f:raise ValueError('MISSING_PBP_FIELD:'+c)
  f[c]=pd.to_numeric(f[c],errors='coerce')
 f['throws']=f.pass_attempt.eq(1)&f.sack.ne(1);f['rushes']=f.rush_attempt.eq(1);f['passplays']=f['throws']|f.sack.eq(1)
 explicit_non=f.play_type.eq('qb_spike')|f.desc.fillna('').str.contains('spiked|spikes|thrown away|throwaway',case=False,regex=True)
 f['nontarget']=f['throws']&explicit_non;f['targeted']=f['throws']&~explicit_non;f['plays']=f['passplays']|f['rushes']
 f['py']=pd.to_numeric(f.passing_yards,errors='coerce');f['ry']=pd.to_numeric(f.rushing_yards,errors='coerce')
 rows=[]
 for (_,club),g in f.groupby(['game_id','posteam']):
  row={'team':team(club),'opponent':team(g.defteam.iloc[0])}
  for c in ['plays','passplays','throws','rushes','targeted','nontarget','sack','complete_pass','interception','pass_touchdown','rush_touchdown','first_down_pass','first_down_rush','fumble','fumble_lost','field_goal_attempt','solo_tackle','assist_tackle','qb_hit','safety']:row[c]=float(g[c].sum())
  row['py']=float(g.py.sum());row['ry']=float(g.ry.sum());rows.append(row)
 if not rows:raise ValueError('NO_COMPLETE_PBP_GAMES')
 league={k:float(np.mean([r[k] for r in rows])) for k in rows[0] if k not in {'team','opponent'}}
 py=f.loc[f.complete_pass.eq(1)&f.py.notna(),'py'].to_numpy();ry=f.loc[f.rushes&f.ry.notna(),'ry'].to_numpy()
 pools={'pass_yards':py,'rush_yards':ry}
 return league,rows,pools

def shrink(rows,league):return {k:(sum(r[k] for r in rows)+8*v)/(len(rows)+8) for k,v in league.items()}|{'observed_games':len(rows)}

def available(e,week):
 if e['position_model']=='DEF':return True
 if not e['team']:return False
 if e['provider_injury'] in {'IR','PUP','SUSPENDED'} or e['source_roster_status'] in {'RES','PUP'}:return False
 if week==6 and (e['provider_injury']=='OUT' or e['official_status']=='OUT'):return False
 return True

def weights(es,ps,field,positions,week,starter=None):
 values=[]
 for e in es:
  p=ps[e['canonical_player_id']];spec=p['components'].get(field,{});v=max(0.,spec.get('raw_unconditional_mean',0))
  if not available(e,week) or e['position_model'] not in positions:v=0.
  if field in {'passing_attempts','rushing_attempts','targets'}:
   snap=e['snaps'].get('offense_pct');has_role=(snap is not None and snap>0) or (snap is None and 0<e['depth_order']<=2 and spec.get('provenance')!='POOLED_PRIOR_ONLY')
   if not has_role or v<.1:v=0.
   if e['position_model']=='QB' and e['canonical_player_id']!=starter:v=0.
  if field.startswith('idp_') and e['snaps'].get('defense_pct',0)==0:v=0.
  values.append(v)
 a=np.array(values,dtype=float)
 if a.sum()<=0:
  candidates=[i for i,e in enumerate(es) if available(e,week) and e['position_model'] in positions and (not field.startswith('idp_') or e['snaps'].get('defense_pct',0)>0)]
  if not candidates:raise ValueError('NO_SUPPORTED_ALLOCATION:'+field+':'+str(es[0]['team']))
  a[candidates]=1.
 return a/a.sum()

def blended(a,b,key,den):
 x=np.clip(a[key]/max(a[den],1e-9),1e-6,1-1e-6);y=np.clip(b[key]/max(b[den],1e-9),1e-6,1-1e-6)
 z=.5*(math.log(x/(1-x))+math.log(y/(1-y)));return 1/(1+math.exp(-z))

def add_event(arr,field,actor,draw,value=1):np.add.at(arr[field],(actor,draw),value)

def allocate_counts(rng,counts,w):
 draw=np.repeat(np.arange(N),counts.astype(int));actor=rng.choice(len(w),len(draw),p=w);return actor,draw

def team_events(rng,es,ps,lock,week,off,opp,pools,pace):
 ids=[e['canonical_player_id'] for e in es];a={k:np.zeros((len(es),N),dtype=float) for k in lock['components']}
 qb=[e for e in es if e['position_model']=='QB' and available(e,week)]
 if not qb:raise ValueError('NO_AVAILABLE_QB')
 qb.sort(key=lambda e:(e['depth_order'] or 99,-e['snaps'].get('offense_pct',0),e['canonical_player_id']));starter=qb[0]['canonical_player_id'];qi=ids.index(starter)
 dw=weights(es,ps,'idp_tackles_total',{'DL','LB','DB'},week)
 for i,e in enumerate(es):
  if e['position_model']=='DEF' or not available(e,week):continue
  samples,_=scenarios(lock,ps[e['canonical_player_id']],e['canonical_player_id'],week)
  for k in ['idp_tackles_solo','idp_tackles_assisted','idp_tackles_for_loss','idp_quarterback_hits','idp_passes_defended','idp_safeties','idp_blocked_kicks','idp_forced_fumbles','idp_fumble_recoveries','idp_interception_return_yards','idp_fumble_return_yards','idp_sack_yards','idp_defensive_touchdowns','kick_returns','punt_returns','kick_return_yards','punt_return_yards','individual_special_teams_touchdowns','individual_special_teams_forced_fumbles','individual_special_teams_fumble_recoveries','offensive_fumble_recovery_touchdowns']:
   if k in a:a[k][i]=samples[k]
  if e['position_model'] not in {'DL','LB','DB'}:
   for k in a:
    if k.startswith('idp_'):a[k][i]=0.
 # Team volume is independent of how many players are in the roster universe.
 plays=rng.poisson(max(1.,.5*(off['plays']+opp['plays']))*pace)
 passplays=rng.binomial(plays,blended(off,opp,'passplays','plays'));sacks=rng.binomial(passplays,blended(off,opp,'sack','passplays'));throws=passplays-sacks;rushes=plays-passplays
 nontarget=rng.binomial(throws,blended(off,opp,'nontarget','throws'));targeted=throws-nontarget
 a['passing_attempts'][qi]=throws;a['passing_sacks_charged'][qi]=sacks
 recv_w=weights(es,ps,'targets',{'RB','WR','TE'},week,starter);ra,rd=allocate_counts(rng,targeted,recv_w);add_event(a,'targets',ra,rd)
 int_p=blended(off,opp,'interception','throws')/max(1-blended(off,opp,'nontarget','throws'),1e-6)
 intercepted=rng.random(len(rd))<min(.5,int_p)
 completed=(rng.random(len(rd))<min(.98,blended(off,opp,'complete_pass','targeted')))&~intercepted
 ia,idr=ra[intercepted],rd[intercepted];np.add.at(a['passing_interceptions'][qi],idr,1)
 ca,cd=ra[completed],rd[completed];add_event(a,'receptions',ca,cd);np.add.at(a['passing_completions'][qi],cd,1)
 pymean=.5*(off['py']/max(off['complete_pass'],1)+opp['py']/max(opp['complete_pass'],1));yard=np.rint(rng.choice(pools['pass_yards'],len(cd))*pymean/max(float(pools['pass_yards'].mean()),1e-9));yard=np.clip(yard,-99,99)
 add_event(a,'receiving_yards',ca,cd,yard);np.add.at(a['passing_yards'][qi],cd,yard)
 long=yard>=40;add_event(a,'receptions_40_plus',ca[long],cd[long]);np.add.at(a['passing_completions_40_plus'][qi],cd[long],1)
 air=np.rint(yard*.65);add_event(a,'receiving_yards_after_catch',ca,cd,yard-air)
 # Air yards for all targeted throws; completed air+YAC equals credited yards.
 airall=rng.normal(8,8,len(rd));airall[completed]=air;airall=np.rint(airall);add_event(a,'receiving_air_yards',ra,rd,airall);np.add.at(a['passing_air_yards'][qi],rd,airall)
 positive_pass=max(float(np.mean(pools['pass_yards']>0)),.01)
 ptd=(rng.random(len(cd))<min(1.,blended(off,opp,'pass_touchdown','complete_pass')/positive_pass))&(yard>0)
 pfd=(rng.random(len(cd))<min(1.,blended(off,opp,'first_down_pass','complete_pass')/positive_pass))&~ptd&(yard>0)
 # Drives constrain terminal scoring opportunities; this is not a sequential simulator.
 drives=np.maximum(1,np.rint(plays/6)).astype(int);used=np.zeros(N,dtype=int)
 for j in np.flatnonzero(ptd):
  if used[cd[j]]>=drives[cd[j]]:ptd[j]=False
  else:used[cd[j]]+=1
 for field,mask in [('receiving_touchdowns',ptd),('receiving_first_downs',pfd),('receiving_touchdowns_40_plus',ptd&(yard>=40)),('receiving_touchdowns_50_plus',ptd&(yard>=50))]:add_event(a,field,ca[mask],cd[mask])
 for field,mask in [('passing_touchdowns',ptd),('passing_first_downs',pfd),('passing_touchdowns_40_plus',ptd&(yard>=40)),('passing_touchdowns_50_plus',ptd&(yard>=50))]:np.add.at(a[field][qi],cd[mask],1)
 rw=weights(es,ps,'rushing_attempts',{'QB','RB','WR','TE'},week,starter);ua,ud=allocate_counts(rng,rushes,rw)
 rymean=.5*(off['ry']/max(off['rushes'],1)+opp['ry']/max(opp['rushes'],1));uy=np.rint(rng.choice(pools['rush_yards'],len(ud))*rymean/max(float(pools['rush_yards'].mean()),1e-9));uy=np.clip(uy,-99,99)
 add_event(a,'rushing_attempts',ua,ud);add_event(a,'rushing_yards',ua,ud,uy)
 positive_rush=max(float(np.mean(pools['rush_yards']>0)),.01)
 utd=(rng.random(len(ud))<min(1.,blended(off,opp,'rush_touchdown','rushes')/positive_rush))&(uy>0)
 for j in np.flatnonzero(utd):
  if used[ud[j]]>=drives[ud[j]]:utd[j]=False
  else:used[ud[j]]+=1
 ufd=(rng.random(len(ud))<min(1.,blended(off,opp,'first_down_rush','rushes')/positive_rush))&~utd&(uy>0)
 for field,mask in [('rushing_touchdowns',utd),('rushing_first_downs',ufd),('rushes_40_plus',uy>=40),('rushing_touchdowns_40_plus',utd&(uy>=40)),('rushing_touchdowns_50_plus',utd&(uy>=50))]:add_event(a,field,ua[mask],ud[mask])
 # Fumbles and their possession changes have one offensive and defensive ledger.
 fumbles=rng.binomial(plays,blended(off,opp,'fumble','plays'));fa,fd=allocate_counts(rng,fumbles,(rw+recv_w)/2);add_event(a,'fumbles',fa,fd)
 lost=rng.random(len(fd))<blended(off,opp,'fumble_lost','fumble');add_event(a,'fumbles_lost',fa[lost],fd[lost])
 lostcounts=np.bincount(fd[lost],minlength=N);ints=a['passing_interceptions'][qi]
 remaining=np.maximum(drives-used-ints-lostcounts,0).astype(int)
 kicker=[i for i,e in enumerate(es) if e['position_model']=='K' and available(e,week)]
 if not kicker:raise ValueError('NO_AVAILABLE_KICKER')
 ki=max(kicker,key=lambda i:ps[ids[i]]['components']['kicker_field_goal_attempts']['raw_unconditional_mean'])
 fg=rng.poisson(max(.1,.5*(off['field_goal_attempt']+opp['field_goal_attempt'])),N);fg=np.minimum(fg,remaining)
 kp=ps[ids[ki]]['components'];bandw=np.array([max(0,kp['kicker_fgm_'+b]['conditional_mean']+kp['kicker_fgmiss_'+b]['conditional_mean']) for b in FG_BANDS]);bandw/=bandw.sum()
 _,gd=allocate_counts(rng,fg,np.ones(1));bands=rng.choice(len(FG_BANDS),len(gd),p=bandw)
 for j,b in enumerate(FG_BANDS):
  take=bands==j;den=kp['kicker_fgm_'+b]['conditional_mean']+kp['kicker_fgmiss_'+b]['conditional_mean'];pr=kp['kicker_fgm_'+b]['conditional_mean']/den if den else .8
  made=(rng.random(take.sum())<pr);np.add.at(a['kicker_fgm_'+b][ki],gd[take][made],1);np.add.at(a['kicker_fgmiss_'+b][ki],gd[take][~made],1)
 offensive_td=a['passing_touchdowns'].sum(axis=0)+a['rushing_touchdowns'].sum(axis=0)+a['offensive_fumble_recovery_touchdowns'].sum(axis=0)
 return a,{'plays':plays,'throws':throws,'nontarget':nontarget,'targeted':targeted,'rushes':rushes,'sacks':sacks,'interceptions':ints,'fumbles_lost':lostcounts,'drives':drives,'starter':starter,'kicker_index':ki,'offensive_td':offensive_td,'event_pass_actor':ca,'event_pass_draw':cd,'event_pass_yards':yard,'event_pass_td':ptd,'event_pass_fd':pfd,'event_rush_actor':ua,'event_rush_draw':ud,'event_rush_yards':uy,'event_rush_td':utd,'event_rush_fd':ufd,'matchup':{'own':off,'opponent_allowed':opp,'pass_share':blended(off,opp,'passplays','plays'),'completion_rate':blended(off,opp,'complete_pass','targeted'),'yard_per_completion':pymean,'rush_yards_per_carry':rymean}},dw

def finalize_game(rng,clubs,groups,arrays,ledgers,defweights,ps,week):
 # Rare own-fumble recovery scores cannot exceed retained offensive fumbles.
 for club in clubs:
  a=arrays[club];keep=np.maximum(a['fumbles'].sum(axis=0)-a['fumbles_lost'].sum(axis=0),0);old=a['offensive_fumble_recovery_touchdowns'];budget=np.minimum(old.sum(axis=0),keep).astype(int);w=old.sum(axis=1)
  if w.sum()==0:w=np.array([1. if available(e,week) and e['position_model'] in {'RB','WR','TE'} else 0. for e in groups[club]])
  a['offensive_fumble_recovery_touchdowns'][:]=0;aa,dd=allocate_counts(rng,budget,w/w.sum());add_event(a,'offensive_fumble_recovery_touchdowns',aa,dd);ledgers[club]['offensive_td']=a['passing_touchdowns'].sum(axis=0)+a['rushing_touchdowns'].sum(axis=0)+budget
 # Return counts cannot exceed the opposing team's available kicks/punts.
 for club,opp in [(clubs[0],clubs[1]),(clubs[1],clubs[0])]:
  a=arrays[club];enemy=arrays[opp];es=groups[club]
  fg_attempts=sum(enemy['kicker_fgm_'+b] for b in FG_BANDS).sum(axis=0)+sum(enemy['kicker_fgmiss_'+b] for b in FG_BANDS).sum(axis=0)
  fg_makes=sum(enemy['kicker_fgm_'+b] for b in FG_BANDS).sum(axis=0)
  capacities={'kick_returns':ledgers[opp]['offensive_td']+fg_makes+1,'punt_returns':np.maximum(ledgers[opp]['drives']-ledgers[opp]['offensive_td']-fg_attempts-ledgers[opp]['interceptions']-ledgers[opp]['fumbles_lost'],0)}
  for field,yards,cap in [('kick_returns','kick_return_yards',capacities['kick_returns']),('punt_returns','punt_return_yards',capacities['punt_returns'])]:
   counts=np.minimum(a[field].sum(axis=0),cap).astype(int);w=np.array([max(0,ps[e['canonical_player_id']]['components'][field]['raw_unconditional_mean']) if available(e,week) and e['snaps'].get('st_pct',0)>0 else 0. for e in es]);a[field][:]=0;a[yards][:]=0
   if w.sum()>0:
    aa,dd=allocate_counts(rng,counts,w/w.sum());add_event(a,field,aa,dd)
    rates=np.array([num(ps[e['canonical_player_id']]['components'].get(yards,{}).get('rate')) for e in es]);fallback=22. if field=='kick_returns' else 8.;loc=np.where(rates[aa]!=0,rates[aa],fallback);distance=np.clip(np.rint(rng.normal(loc,10)), -20,109);add_event(a,yards,aa,dd,distance)
  a['individual_special_teams_touchdowns']=np.minimum(a['individual_special_teams_touchdowns'],a['kick_returns']+a['punt_returns']+a['idp_blocked_kicks'])
  # No fabricated unit attribution for special-team fumbles; explicit zero forecast policy.
  a['individual_special_teams_forced_fumbles'][:]=0;a['individual_special_teams_fumble_recoveries'][:]=0
  ledgers[club]['kick_return_capacity']=capacities['kick_returns'];ledgers[club]['punt_return_capacity']=capacities['punt_returns']
 for club,opp in [(clubs[0],clubs[1]),(clubs[1],clubs[0])]:
  a=arrays[club];es=groups[club];dw=defweights[club];enemy=ledgers[opp];didx=next(i for i,e in enumerate(es) if e['position_model']=='DEF')
  # Replace marginal defensive credits with the very same opposing offense events.
  for k in ['idp_sacks','idp_interceptions','idp_fumble_recoveries','idp_forced_fumbles','idp_sack_yards','idp_interception_return_yards','idp_fumble_return_yards','idp_defensive_touchdowns']:a[k][:]=0
  for field,counts in [('idp_sacks',enemy['sacks']),('idp_interceptions',enemy['interceptions']),('idp_fumble_recoveries',enemy['fumbles_lost'])]:
   w=weights(es,ps,field,{'DL','LB','DB'},week);actor,draw=allocate_counts(rng,counts,w);add_event(a,field,actor,draw)
   if field=='idp_sacks':add_event(a,'idp_sack_yards',actor,draw,np.maximum(0,np.rint(rng.normal(6.5,3,len(draw)))))
   if field=='idp_interceptions':
    y=np.maximum(0,np.rint(rng.normal(10,12,len(draw))));add_event(a,'idp_interception_return_yards',actor,draw,y)
    td=rng.random(len(draw))<.025;add_event(a,'idp_defensive_touchdowns',actor[td],draw[td]);ledgers[opp]['pick_sixes']=np.bincount(draw[td],minlength=N)
   if field=='idp_fumble_recoveries':add_event(a,'idp_fumble_return_yards',actor,draw,np.maximum(0,np.rint(rng.normal(5,9,len(draw)))))
  # Force/recovery are different scopes: not every lost fumble was forced.
  forced=rng.binomial(enemy['fumbles_lost'].astype(int),.7);actor,draw=allocate_counts(rng,forced,dw);add_event(a,'idp_forced_fumbles',actor,draw)
  # Historical tackle rates rescale with the opponent's current projected plays.
  for k,source,multiple in [('idp_tackles_solo','solo_tackle',1),('idp_tackles_assisted','assist_tackle',2)]:
   prob=blended(enemy['matchup']['own'],enemy['matchup']['opponent_allowed'],source,'plays');budget=multiple*rng.binomial(enemy['plays'].astype(int),prob)
   aa,dd=allocate_counts(rng,budget,dw);a[k][:]=0;add_event(a,k,aa,dd)
  a['idp_tackles_total']=a['idp_tackles_solo']+a['idp_tackles_assisted'];short=np.maximum(np.ceil(a['idp_sacks'])-a['idp_tackles_total'],0);a['idp_tackles_assisted']+=short;a['idp_tackles_total']+=short
  a['idp_tackles_for_loss']=np.minimum(a['idp_tackles_for_loss'],a['idp_tackles_total']);a['idp_quarterback_hits']=np.maximum(a['idp_quarterback_hits'],np.ceil(a['idp_sacks']))
  for player,defense in [('idp_sacks','dst_sacks'),('idp_interceptions','dst_interceptions'),('idp_interception_return_yards','dst_interception_return_yards'),('idp_fumble_recoveries','dst_fumble_recoveries'),('idp_fumble_return_yards','dst_fumble_return_yards'),('idp_forced_fumbles','dst_forced_fumbles'),('idp_passes_defended','dst_passes_defended'),('idp_safeties','dst_safeties'),('idp_blocked_kicks','dst_blocked_kicks'),('idp_defensive_touchdowns','dst_defensive_touchdowns'),('kick_return_yards','dst_kick_return_yards'),('punt_return_yards','dst_punt_return_yards'),('individual_special_teams_touchdowns','dst_special_teams_touchdowns'),('individual_special_teams_forced_fumbles','dst_special_teams_forced_fumbles'),('individual_special_teams_fumble_recoveries','dst_special_teams_fumble_recoveries')]:a[defense][didx]=a[player].sum(axis=0)
  prior=ps[es[didx]['canonical_player_id']]['components']['dst_fourth_down_stops']['raw_unconditional_mean'];a['dst_fourth_down_stops'][didx]=rng.poisson(max(0,prior)*enemy['plays']/max(enemy['matchup']['own']['plays'],1),N);a['dst_field_goal_return_yards'][didx]=0.;a['dst_blocked_kick_return_yards'][didx]=0.
  a['dst_net_yards_allowed'][didx]=arrays[opp]['passing_yards'].sum(axis=0)+arrays[opp]['rushing_yards'].sum(axis=0)-a['idp_sack_yards'].sum(axis=0)
 # All scoring units now exist; kicking opportunities depend on these TDs.
 for club,opp in [(clubs[0],clubs[1]),(clubs[1],clubs[0])]:
  a=arrays[club];es=groups[club];l=ledgers[club];qi=next(i for i,e in enumerate(es) if e['canonical_player_id']==l['starter']);a['passing_pick_sixes'][qi]=l.get('pick_sixes',np.zeros(N))
  td=l['offensive_td']+a['idp_defensive_touchdowns'].sum(axis=0)+a['individual_special_teams_touchdowns'].sum(axis=0)
  ki=l['kicker_index'];two=rng.binomial(td.astype(int),.06);success=rng.binomial(two,.48);rush_two=rng.binomial(success,.25);pass_two=success-rush_two
  # Two-point credits are separate from regular targets/completions.
  rw=weights(es,ps,'rushing_attempts',{'QB','RB','WR','TE'},week,l['starter']);tw=weights(es,ps,'targets',{'RB','WR','TE'},week,l['starter'])
  aa,dd=allocate_counts(rng,rush_two,rw);add_event(a,'rushing_two_point_conversions',aa,dd);a['passing_two_point_conversions'][qi]=pass_two;aa,dd=allocate_counts(rng,pass_two,tw);add_event(a,'receiving_two_point_conversions',aa,dd)
  xp=td-two;kp=ps[es[ki]['canonical_player_id']]['components'];rate=kp['kicker_xpm']['conditional_mean']/max(kp['kicker_xpm']['conditional_mean']+kp['kicker_xpmiss']['conditional_mean'],1e-9);rate=np.clip(rate,.8,1)
  a['kicker_xpm'][ki]=rng.binomial(xp.astype(int),rate);a['kicker_xpmiss'][ki]=xp-a['kicker_xpm'][ki]
  a['kicker_fgm']=sum(a['kicker_fgm_'+b] for b in FG_BANDS);a['kicker_fgmiss']=sum(a['kicker_fgmiss_'+b] for b in FG_BANDS);a['kicker_field_goal_attempts']=a['kicker_fgm']+a['kicker_fgmiss'];a['kicker_fgm_50p']=a['kicker_fgm_50_59']+a['kicker_fgm_60p'];a['kicker_fgm_yds']=np.rint(sum(a['kicker_fgm_'+b]*DISTANCE_MID[b] for b in FG_BANDS));a['kicker_extra_point_attempts']=a['kicker_xpm']+a['kicker_xpmiss']
  for prefix in ['passing','rushing','receiving']:a['source_'+prefix+'_first_downs_including_td']=a[prefix+'_first_downs']+a[prefix+'_touchdowns']
  for k,field,lo,hi in [('prob_pass_yd_300','passing_yards',300,399),('prob_pass_yd_400','passing_yards',400,None),('prob_rush_yd_100','rushing_yards',100,199),('prob_rec_yd_100','receiving_yards',100,199)]:a[k]=((a[field]>=lo)&((a[field]<=hi) if hi else True)).astype(float)
  l['score']=6*td+3*a['kicker_fgm'].sum(axis=0)+a['kicker_xpm'].sum(axis=0)+2*success+2*a['idp_safeties'].sum(axis=0);l['two_point_attempts']=two;l['two_point_successes']=success;l['touchdowns']=td
 for club,opp in [(clubs[0],clubs[1]),(clubs[1],clubs[0])]:
  a=arrays[club];di=next(i for i,e in enumerate(groups[club]) if e['position_model']=='DEF');enemy=ledgers[opp]
  # Sleeper counts all PATs but excludes the six points of opposing defensive TDs.
  pa=enemy['score']-6*arrays[opp]['idp_defensive_touchdowns'].sum(axis=0)-2*arrays[opp]['idp_safeties'].sum(axis=0);a['dst_points_allowed'][di]=pa
  for b,(lo,hi) in POINT_BANDS.items():a['dst_prob_pts_allow_'+b][di]=((pa>=lo)&((pa<=hi) if hi is not None else True)).astype(float)

def audit_game(clubs,groups,arrays,ledgers):
 tests=0
 def same(a,b,label):
  nonlocal tests
  if not np.allclose(a,b,atol=1e-9,rtol=0):raise ValueError('JOINT_CONSERVATION:'+label)
  tests+=1
 for club,opp in [(clubs[0],clubs[1]),(clubs[1],clubs[0])]:
  a=arrays[club];d=arrays[opp];l=ledgers[club];sumstat=lambda k:a[k].sum(axis=0);di=next(i for i,e in enumerate(groups[opp]) if e['position_model']=='DEF')
  for p,r in [('passing_completions','receptions'),('passing_yards','receiving_yards'),('passing_touchdowns','receiving_touchdowns'),('passing_two_point_conversions','receiving_two_point_conversions')]:same(sumstat(p),sumstat(r),p)
  same(sumstat('passing_attempts'),sumstat('targets')+l['nontarget'],'attempt-target');same(sumstat('passing_attempts')+sumstat('passing_sacks_charged')+sumstat('rushing_attempts'),l['plays'],'play budget')
  for offense,defense in [('passing_interceptions','dst_interceptions'),('passing_sacks_charged','dst_sacks'),('fumbles_lost','dst_fumble_recoveries')]:same(sumstat(offense),d[defense][di],offense)
  for i,e in enumerate(groups[club]):
   samples={k:v[i] for k,v in a.items()};validate_scenarios(samples,e['model_position'])
   if not available(e,l['week']) and any(np.any(v) for v in samples.values()):raise ValueError('UNAVAILABLE_PLAYER_CREDIT')
  same(sumstat('kicker_extra_point_attempts')+l['two_point_attempts'],l['touchdowns'],'TD conversions')
 return tests

def issue(root=ROOT,base=BASE):
 folder=root/base;out=folder/'issuance';out.mkdir(parents=True,exist_ok=True)
 if (out/'capture-manifest.json').exists():raise ValueError('NEW_REVISION_REQUIRED')
 es,ps,lock,profiles,owned,data,off,defense,pools=prepare(root,folder)
 contracts=json.loads((root/'config/contracts/runtime-contracts.json').read_text());oldprofiles={p.stem:json.loads(p.read_text()) for p in (root/OLD/'profiles').glob('*.json')}
 contexts,first,games=game_context(data['schedule']);groups={club:[e for e in es if e['team']==club] for club in off};writers={n:JsonLines(out/(n+'.jsonl.gz')) for n in ['weekly-components','weekly-league-scores','team-ledgers','allocation']};horizon=collections.defaultdict(lambda:np.zeros(N));count=0;audit_count=0;all_rows=[]
 (out/'draws').mkdir(exist_ok=True)
 def emit(e,week,samples,context=None):
  nonlocal count
  relevant={k:v for k,v in samples.items() if k.startswith('dst_')==(e['position_model']=='DEF')};means={k:float(v.mean()) for k,v in relevant.items() if not k.startswith(('prob_','dst_prob_'))};probs={k:float(v.mean()) for k,v in relevant.items() if k.startswith(('prob_','dst_prob_'))}
  row={**{k:e[k] for k in ['canonical_player_id','sleeper_id','name','position_model','model_position','team','fantasy_positions']},'week':week,'season':2026,'model_id':MODEL,'means':means,'event_probabilities':probs,'opponent':context['opponent'] if context else None,'game_id':context['game_id'] if context else None,'available':available(e,week),'official_status':e['official_status'],'injury_status':e['provider_injury'],'bye':context is None,'weather_used':False,'intervals_calibrated':False}
  writers['weekly-components'].append(row);all_rows.append(row);count+=1
  for p in profiles:
   lid=str(p['league_id']);old=oldprofiles[lid];elig=pool_eligibility(e,old['research_constraints'],e['sleeper_id'] in owned[lid])
   if not set(e['fantasy_positions']).intersection(old['positions']) or (elig['status']!='ELIGIBLE' and e['sleeper_id'] not in owned[lid]):continue
   rules=rules_for(p['scoring_settings'],e['position_model'],e['fantasy_positions'],contracts);draws,score=score_scenarios(samples,rules);horizon[(lid,e['canonical_player_id'])]+=draws
   writers['weekly-league-scores'].append({'league_id':lid,'canonical_player_id':e['canonical_player_id'],'name':e['name'],'week':week,'model_id':MODEL,**score})
 for game in games:
  clubs=[game['away_team'],game['home_team']];week=game['week'];rng=np.random.default_rng(int.from_bytes(hashlib.sha256((game['game_id']+'|20261015').encode()).digest()[:8],'big'));pace=rng.lognormal(-.5*.08**2,.08,N)
  arrays={};ledgers={};dw={}
  for club,opp in [(clubs[0],clubs[1]),(clubs[1],clubs[0])]:
   arrays[club],ledgers[club],dw[club]=team_events(rng,groups[club],ps,lock,week,off[club],defense[opp],pools,pace);ledgers[club]['week']=week
  finalize_game(rng,clubs,groups,arrays,ledgers,dw,ps,week);audit_count+=audit_game(clubs,groups,arrays,ledgers)
  np.savez_compressed(out/'draws'/(game['game_id']+'.npz'),**{club+'__'+k:v.astype(np.float32) for club,a in arrays.items() for k,v in a.items()},**{club+'__ledger_'+k:v for club,l in ledgers.items() for k,v in l.items() if isinstance(v,np.ndarray)})
  writers['allocation'].append({'game_id':game['game_id'],'week':week,'team_entities':{club:[e['canonical_player_id'] for e in groups[club]] for club in clubs}})
  for club in clubs:
   l=ledgers[club];writers['team-ledgers'].append({'game_id':game['game_id'],'week':week,'team':club,'opponent':contexts[(week,club)]['opponent'],'matchup':l['matchup'],'starter':l['starter'],**{k:float(v.mean()) for k,v in l.items() if isinstance(v,np.ndarray) and not k.startswith('event_')}})
   for i,e in enumerate(groups[club]):emit(e,week,{k:v[i] for k,v in arrays[club].items()},contexts[(week,club)])
   print('JOINT_GAME',game['game_id'],club,'score',float(l['score'].mean()),flush=True)
  del arrays
 for e in es:
  for week in [6,7,8]:
   if (week,e['team']) not in contexts:emit(e,week,{k:np.zeros(N) for k in lock['components']})
 for w in writers.values():w.close()
 h=JsonLines(out/'three-week-summaries.jsonl.gz')
 for (lid,cid),v in sorted(horizon.items()):h.append({'league_id':lid,'canonical_player_id':cid,'model_id':MODEL,'sum':float(v.mean()),'mean':float(v.mean())/3,'p10_sum':float(np.quantile(v,.1)),'p90_sum':float(np.quantile(v,.9))})
 h.close();issued=now()
 if clock(issued)>=clock(first[6]):raise ValueError('ISSUANCE_AFTER_KICKOFF')
 artifacts={p.relative_to(root).as_posix():sha(p) for p in out.rglob('*') if p.is_file()};write(out/'capture-manifest.json',{'model_id':MODEL,'issued_at':issued,'first_kickoff':first[6],'target_weeks':[6,7,8],'enabled_leagues':23,'entities':len(es),'weekly_component_rows':count,'league_rows':writers['weekly-league-scores'].rows,'horizon_rows':h.rows,'games':len(games),'draw_checks':audit_count,'draws':N,'owner_sha256':sha(Path(__file__)),'methodology_sha256':sha(root/METHOD),'input_lock_sha256':sha(folder/'input-lock.json'),'artifacts':artifacts,'weather_used':False,'research_only':True,'provider_exact_certified':False,'calibrated':False,'limitations':['FIXED_OPPONENT_BLEND_NOT_FITTED_OR_CALIBRATED','STATIC_WEEK7_8_AVAILABILITY_ASSUMPTIONS','SPECIALIST_MARGINAL_HEURISTICS','NOT_A_SEQUENTIAL_DRIVE_SIMULATOR','HISTORICAL_CAPTURE_TIMING_EXPLORATORY']})
 print('ISSUED',count,'shared rows',writers['weekly-league-scores'].rows,'league rows',flush=True)

if __name__=='__main__':issue()
