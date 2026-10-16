"""Independent archived-draw and scored-row reconciliation; does not import issuer."""
import argparse,gzip,json,math,hashlib
from pathlib import Path
import numpy as np
ROOT=Path(__file__).resolve().parents[1]
def digest(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def run(base,root=None):
 global ROOT
 ROOT=Path(root or ROOT).resolve()
 folder=ROOT/base;out=folder/'issuance';m=json.loads((out/'capture-manifest.json').read_text());errors=[];checks=0
 def test(ok,label):
  nonlocal checks
  checks+=1
  if not bool(ok):errors.append(label)
 def eq(a,b,label):
  scalar=isinstance(a,(int,float,np.number)) and isinstance(b,(int,float,np.number))
  test(math.isclose(float(a),float(b),abs_tol=1e-8,rel_tol=0) if scalar else np.allclose(a,b,atol=1e-8,rtol=0),label)
 for rel,h in m['artifacts'].items():test(digest(ROOT/rel)==h,'artifact:'+rel)
 for rel,h in m['owners'].items():test(digest(ROOT/rel)==h,'source owner:'+rel)
 test(digest(folder/'pipeline-lock.json')==m['pipeline_lock_sha256'],'pipeline lock')
 pl=json.loads((folder/'pipeline-lock.json').read_text())
 for pathkey,hashkey in [('fitted_path','fitted_sha256'),('bundle_path','bundle_sha256'),('training_path','training_sha256')]:
  test(digest(ROOT/pl[pathkey])==pl[hashkey],pathkey)
 fit=json.loads((ROOT/pl['fitted_path']).read_text())
 for ref in fit.get('training_sources',[])+fit.get('coefficient_sources',[])+pl.get('historical',[]):
  test(digest(ROOT/ref['path'])==ref['sha256'],'fitted source:'+ref['path'])
 if fit.get('training_revision_path'):
  revision=ROOT/fit['training_revision_path']/'training-view.json';test(digest(revision)==fit['training_revision_sha256'],'fitted training revision')
  trained=json.loads(revision.read_text());test(trained['training_sha256']==pl['training_sha256'],'feature-training source equals fitted revision')
 entities={e['canonical_player_id']:e for e in json.loads((folder/'entities.json').read_text())['entities']}
 rows=[json.loads(x) for x in gzip.open(out/'weekly-components.jsonl.gz','rt')];lookup={(r['canonical_player_id'],r['week']):r for r in rows}
 allocations=[json.loads(x) for x in gzip.open(out/'allocation.jsonl.gz','rt')];indices={};archives={}
 for item in allocations:
  game=item['game_id'];z=np.load(out/'draws'/(game+'.npz'));archives[game]=z;clubs=list(item['team_entities'])
  for club in clubs:
   opp=next(c for c in clubs if c!=club);ids=item['team_entities'][club];opids=item['team_entities'][opp];di=next(i for i,cid in enumerate(ids) if entities[cid]['position_model']=='DEF');odi=next(i for i,cid in enumerate(opids) if entities[cid]['position_model']=='DEF')
   a={k.split('__',1)[1]:z[k] for k in z.files if k.startswith(club+'__') and not k.startswith(club+'__ledger_')};d={k.split('__',1)[1]:z[k] for k in z.files if k.startswith(opp+'__') and not k.startswith(opp+'__ledger_')};s=lambda k:a[k].sum(axis=0)
   for p,r in [('passing_completions','receptions'),('passing_yards','receiving_yards'),('passing_touchdowns','receiving_touchdowns'),('passing_two_point_conversions','receiving_two_point_conversions')]:eq(s(p),s(r),game+club+p)
   eq(s('passing_attempts'),s('targets')+z[club+'__ledger_nontarget'],game+club+'targets')
   eq(s('passing_attempts')+s('rushing_attempts')+s('passing_sacks_charged'),z[club+'__ledger_plays'],game+club+'plays')
   for p,k in [('passing_interceptions','dst_interceptions'),('passing_sacks_charged','dst_sacks'),('fumbles_lost','dst_fumble_recoveries')]:eq(s(p),d[k][odi],game+club+p)
   eq(a['idp_sacks'].sum(axis=0),a['dst_sacks'][di],game+club+'IDP sacks');eq(a['idp_interceptions'].sum(axis=0),a['dst_interceptions'][di],game+club+'IDP interceptions')
   eq(s('kicker_extra_point_attempts')+z[club+'__ledger_two_point_attempts'],z[club+'__ledger_touchdowns'],game+club+'TD opportunities')
   if club+'__ledger_kick_return_capacity' in z.files:
    test(np.all(s('kick_returns')<=z[club+'__ledger_kick_return_capacity']),game+club+'kick return capacity')
    test(np.all(s('punt_returns')<=z[club+'__ledger_punt_return_capacity']),game+club+'punt return capacity')
    test(np.all(a['individual_special_teams_touchdowns']<=a['kick_returns']+a['punt_returns']+a['idp_blocked_kicks']),game+club+'ST touchdown parent')
   retained=s('fumbles')-s('fumbles_lost');test(np.all(s('offensive_fumble_recovery_touchdowns')<=retained),game+club+'own fumble score parent')
   test(np.std(s('kicker_field_goal_attempts'))>.01,game+club+'per-scenario FG sampler')
   if club+'__ledger_event_pass_yards' in z.files:
    for kind in ['pass','rush']:
     prefix=club+'__ledger_event_'+kind+'_';actor=z[prefix+'actor'].astype(int);draw=z[prefix+'draw'].astype(int);yards=z[prefix+'yards'];td=z[prefix+'td'].astype(bool);fd=z[prefix+'fd'].astype(bool)
     test(np.all(yards[td]>0),game+club+kind+'positive TD gains');test(np.all(yards[fd]>0),game+club+kind+'positive FD gains')
     expected=np.zeros((len(ids),m['draws']));np.add.at(expected,(actor,draw),yards);eq(expected,a['receiving_yards' if kind=='pass' else 'rushing_yards'],game+club+kind+'event yards')
     expected[:]=0;np.add.at(expected,(actor[td],draw[td]),1);eq(expected,a['receiving_touchdowns' if kind=='pass' else 'rushing_touchdowns'],game+club+kind+'event TDs')
   expected_pa=z[opp+'__ledger_score']-6*d['idp_defensive_touchdowns'].sum(axis=0)-2*d['idp_safeties'].sum(axis=0);eq(a['dst_points_allowed'][di],expected_pa,game+club+'points allowed')
   for total,children in [('idp_tackles_total',['idp_tackles_solo','idp_tackles_assisted']),('kicker_field_goal_attempts',['kicker_fgm','kicker_fgmiss']),('kicker_extra_point_attempts',['kicker_xpm','kicker_xpmiss']),('kicker_fgm_50p',['kicker_fgm_50_59','kicker_fgm_60p'])]:eq(a[total],sum(a[k] for k in children),game+club+total)
   for child,parent in [('passing_completions','passing_attempts'),('receptions','targets'),('passing_interceptions','passing_attempts'),('fumbles_lost','fumbles'),('passing_touchdowns','passing_completions'),('receiving_touchdowns','receptions'),('rushing_touchdowns','rushing_attempts'),('passing_touchdowns_50_plus','passing_touchdowns_40_plus'),('receiving_touchdowns_50_plus','receiving_touchdowns_40_plus'),('rushing_touchdowns_50_plus','rushing_touchdowns_40_plus')]:test(np.all(a[child]<=a[parent]+1e-8),game+club+child+' parent')
   test(np.all(a['passing_completions']+a['passing_interceptions']<=a['passing_attempts']),game+club+'disjoint pass outcomes')
   eq(sum(a[k][di] for k in a if k.startswith('dst_prob_pts_allow_')),np.ones(m['draws']),game+club+'DST bands')
   for i,cid in enumerate(ids):
    indices[(cid,item['week'])]=(game,club,i);r=lookup[(cid,item['week'])]
    for k,v in {**r['means'],**r['event_probabilities']}.items():eq(float(a[k][i].mean()),v,game+cid+k+' replay')
    if not r['available']:test(all(not np.any(a[k][i]) for k in a),game+cid+'unavailable')
   test(35<=float(z[club+'__ledger_plays'].mean())<=95,game+club+'mean plays plausibility')
   test(0<=float(z[club+'__ledger_score'].mean())<=50,game+club+'mean score plausibility')
   test(sum(np.any(a['passing_attempts'][i]>0) for i,cid in enumerate(ids) if entities[cid]['position_model']=='QB')==1,game+club+'one QB role')
 for r in rows:
  if r['bye']:test(all(v==0 for v in {**r['means'],**r['event_probabilities']}.values()),r['canonical_player_id']+' bye')
 league_sums={};score_rows=0;cached_key=None;cached_samples={};cached_game=None;matrix_cache={}
 for r in map(json.loads,gzip.open(out/'weekly-league-scores.jsonl.gz','rt')):
  cid=r['canonical_player_id'];wk=r['week'];dr=np.zeros(m['draws']);row=lookup[(cid,wk)];values={**row['means'],**row['event_probabilities']}
  if (cid,wk)!=cached_key:
   cached_key=(cid,wk);cached_samples={}
   if (cid,wk) in indices:
    game,club,i=indices[(cid,wk)]
    if cached_game!=game:
     cached_game=game;matrix_cache={k:archives[game][k] for k in archives[game].files if '__ledger_' not in k}
    cached_samples={c['component']:matrix_cache[club+'__'+c['component']][i].astype(np.float64) for c in r['contributions'].values()}
  for key,c in r['contributions'].items():
   eq(c['expectation'],values[c['component']],'score expectation');eq(c['points'],c['weight']*c['expectation'],'score weight')
   if (cid,wk) in indices:
    if c['component'] not in cached_samples:
     game,club,i=indices[(cid,wk)];cached_samples[c['component']]=matrix_cache[club+'__'+c['component']][i].astype(np.float64)
    dr+=cached_samples[c['component']]*c['weight']
  eq(r['mean'],sum(c['points'] for c in r['contributions'].values()),'score sum');eq(r['mean'],float(dr.mean()),'score draw mean')
  eq(r['p10'],float(np.quantile(dr,.1)),'p10');eq(r['p50'],float(np.quantile(dr,.5)),'p50');eq(r['p90'],float(np.quantile(dr,.9)),'p90')
  kk=(r['league_id'],cid);league_sums.setdefault(kk,np.zeros(m['draws']));league_sums[kk]+=dr;score_rows+=1
 for r in map(json.loads,gzip.open(out/'three-week-summaries.jsonl.gz','rt')):
  v=league_sums[(r['league_id'],r['canonical_player_id'])];eq(r['sum'],float(v.mean()),'horizon sum');eq(r['mean'],float(v.mean())/3,'horizon mean')
 receipt={'status':'PASS' if not errors else 'FAIL','checks':checks,'errors':errors[:40],'error_count':len(errors),'component_rows':len(rows),'league_rows':score_rows,'games':len(allocations),'draws_per_game':m['draws'],'manifest_sha256':digest(out/'capture-manifest.json'),'independent_of_issuer':True,'predictive_accuracy_validated':False}
 (folder/'independent-validation.json').write_text(json.dumps(receipt,indent=2));print(json.dumps(receipt));return 1 if errors else 0
if __name__=='__main__':
 p=argparse.ArgumentParser();p.add_argument('--base',type=Path,default=Path('data/research/components/recovery-20261016/release/stage4'));a=p.parse_args();raise SystemExit(run(a.base))

