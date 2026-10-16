import json,shutil,tempfile,unittest
from pathlib import Path
import numpy as np
from recovery_common import ROOT,BASE,JOINT,read,write,lines,sha,closure,rows,atomic_npz
from recovery_engine import available,configure,base_weights,weights
from recovery_evaluate import review,metrics
from component_scoring import rules_for,score_scenarios

class RecoveryTests(unittest.TestCase):
 def entity(self,cid,pos='WR',**kw):return {'canonical_player_id':cid,'position_model':pos,'team':'SEA','provider_injury':'','official_status':None,'source_roster_status':'ACT','depth_order':1,'snaps':{'offense_pct':.6,'defense_pct':.6},**kw}
 def test_availability_moves_with_window(self):
  configure({},0,{},7);e=self.entity('x',official_status='OUT');self.assertFalse(available(e,7));self.assertTrue(available(e,8));self.assertFalse(available(self.entity('ir',provider_injury='IR'),8))
 def test_role_support_and_tiny_threshold(self):
  es=[self.entity('main'),self.entity('tiny'),self.entity('unsupported',snaps={'offense_pct':0})];ps={e['canonical_player_id']:{'components':{'targets':{'raw_unconditional_mean':v,'provenance':'SHRUNK_CONDITIONAL_MEAN'}}} for e,v in zip(es,[8,.05,3])};np.testing.assert_array_equal(base_weights(es,ps,'targets',{'WR'},7),[1,0,0])
 def test_backup_attempts_are_not_added(self):
  es=[self.entity('q','QB'),self.entity('b','QB')];ps={e['canonical_player_id']:{'components':{'passing_attempts':{'raw_unconditional_mean':32,'provenance':'SHRUNK_CONDITIONAL_MEAN'}}} for e in es};np.testing.assert_array_equal(base_weights(es,ps,'passing_attempts',{'QB'},7,'q'),[1,0])
 def test_real_zero_error_metrics(self):
  m=metrics([(2,0),(-2,0)]);self.assertEqual(m['mae'],2);self.assertEqual(m['bias'],0);self.assertEqual(m['nonzero_actuals'],0)
 def test_atomic_archive(self):
  with tempfile.TemporaryDirectory() as d:
   p=Path(d)/'a.npz';atomic_npz(p,a=np.arange(10));np.testing.assert_array_equal(np.load(p)['a'],np.arange(10))
 def fixture(self,root):
  c=root/'config/contracts';c.mkdir(parents=True);shutil.copy2(ROOT/'config/contracts/runtime-contracts.json',c/'runtime-contracts.json');write(root/JOINT/'entities.json',{'entities':[{'canonical_player_id':'p','fantasy_positions':['QB']}]})
  f=root/'freeze';f.mkdir();rs=[]
  for model,pred in [('A',10),('B',8)]:
   for week in [6,7,8]:rs.append({'model_id':model,'canonical_player_id':'p','season':2026,'week':week,'position_model':'QB','components':{'passing_yards':pred,'passing_touchdowns':1},'scores':{'L':{'mean':pred*.04,'p10':0,'p90':20}},'replay_only':True})
  lines(f/'forecasts.jsonl.gz',rs);write(f/'profiles.json',[{'league_id':'L','scoring_settings':{'pass_yd':.04}}]);write(f/'freeze-receipt.json',{'models':['A','B'],'target_weeks':[6,7,8],'artifacts':closure(f,root)})
  a=root/'actual';a.mkdir();lines(a/'actual-components.jsonl.gz',[{'canonical_player_id':'p','season':2026,'week':6,'position_model':'QB','components':{'passing_yards':0},'basis':{'passing_yards':'OBSERVED_ZERO'}},{'canonical_player_id':'p','season':2026,'week':8,'position_model':'QB','components':{'passing_yards':5},'basis':{'passing_yards':'OBSERVED'}}]);write(a/'actual-receipt.json',{'artifacts':closure(a,root)});return f,a
 def test_missing_actuals_do_not_become_zero_and_horizon_requires_three_weeks(self):
  with tempfile.TemporaryDirectory() as d:
   r=Path(d);self.fixture(r);x=review(Path('freeze'),[Path('actual')],Path('review'),r);self.assertEqual(x['matched_component_values'],4);self.assertEqual(x['complete_three_week_rows'],0);self.assertGreater(x['unmatched_or_unknown_component_values'],0)
   e=list(rows(r/'review/component-errors.jsonl.gz'));self.assertTrue(all(x['component']=='passing_yards' for x in e));self.assertEqual(next(x for x in e if x['week']==6)['actual'],0)
 def test_paired_comparisons_use_same_observed_population(self):
  with tempfile.TemporaryDirectory() as d:
   r=Path(d);self.fixture(r);review(Path('freeze'),[Path('actual')],Path('review'),r);p=list(rows(r/'review/paired-comparisons.jsonl.gz'));self.assertTrue(all(x['n']==2 for x in p));self.assertEqual(p[0]['delta_mae_a_minus_b'],2)
 def test_forecast_corruption_fails_closed(self):
  with tempfile.TemporaryDirectory() as d:
   r=Path(d);self.fixture(r);(r/'freeze/forecasts.jsonl.gz').write_bytes(b'broken')
   with self.assertRaisesRegex(ValueError,'FREEZE_DRIFT'):review(Path('freeze'),[],Path('review'),r)
 def test_unknown_scoring_rule_fails(self):
  contracts=read(ROOT/'config/contracts/runtime-contracts.json')
  with self.assertRaises(ValueError):rules_for({'unknown_real_rule':1},'QB',['QB'],contracts)
 def test_position_premiums_do_not_leak(self):
  contracts=read(ROOT/'config/contracts/runtime-contracts.json');scoring={'rec':1,'bonus_rec_te':.5,'bonus_rush_td_qb':2}
  te=rules_for(scoring,'TE',['TE'],contracts);wr=rules_for(scoring,'WR',['WR'],contracts);self.assertEqual(sum(r['weight'] for r in te),1.5);self.assertEqual(sum(r['weight'] for r in wr),1)
 def test_documented_individual_source_rate_reproduced(self):
  f=read(ROOT/BASE/'fit/fitted.json');self.assertAlmostEqual(f['players']['00-0034869']['rushing_yards_per_carry']['rate'],3.203670959267878,places=13)
 def test_three_week_population_source_cutoff_parameterized(self):
  import pandas as pd
  from recovery_population import universe
  clubs=sorted(read(ROOT/JOINT/'team-parameters.json')['offense']);catalog={};roster=[];bridge=[];players=[]
  for i,club in enumerate(clubs,1):
   cid=f'00-{i:07d}';sid=str(i);catalog[sid]={'gsis_id':cid,'position':'WR','fantasy_positions':['WR'],'team':club,'full_name':sid};roster.append({'season':2026,'week':9,'team':club,'status':'ACT','gsis_id':cid,'sleeper_id':sid,'position':'WR','rookie_year':2026});bridge.append({'identity_status':'EXACT_ONE_TO_ONE','canonical_player_id':cid,'sleeper_id':sid});players.append({'gsis_id':cid,'rookie_season':2026})
  entities,_=universe(catalog,pd.DataFrame(roster),pd.DataFrame(players),pd.DataFrame(bridge),set(),target_week=9)
  self.assertEqual(len(entities),64);self.assertTrue(all(e['current_roster_week']==9 for e in entities))
 def test_partial_sleeper_subtotal_uses_matching_actual_keys(self):
  with tempfile.TemporaryDirectory() as d:
   r=Path(d);self.fixture(r);f=r/'freeze';existing=list(rows(f/'forecasts.jsonl.gz'));(f/'forecasts.jsonl.gz').unlink()
   for week in [6,7,8]:existing.append({'model_id':'SLEEPER_EXPLICIT_FIELDS','canonical_player_id':'p','season':2026,'week':week,'position_model':'QB','components':{'passing_yards':9},'scores':{},'replay_only':False})
   lines(f/'forecasts.jsonl.gz',existing);(f/'profiles.json').write_text(json.dumps([{'league_id':'L','scoring_settings':{'pass_yd':.04,'pass_td':4}}]));receipt={'models':['A','B','SLEEPER_EXPLICIT_FIELDS'],'target_weeks':[6,7,8],'artifacts':{}}
   receipt['artifacts']={p.relative_to(r).as_posix():sha(p) for p in f.glob('*') if p.name!='freeze-receipt.json'};(f/'freeze-receipt.json').write_text(json.dumps(receipt))
   result=review(Path('freeze'),[Path('actual')],Path('review'),r);sc=list(rows(r/'review/league-errors.jsonl.gz'));self.assertTrue(sc);self.assertTrue(all(x.get('score_scope')=='SLEEPER_MATCHED_COMPONENT_SUBTOTAL' and x['scoring_keys']==['pass_yd'] for x in sc));self.assertTrue(all(x['covered_rule_count']==1 and x['full_rule_count']==2 for x in sc))
if __name__=='__main__':unittest.main()
