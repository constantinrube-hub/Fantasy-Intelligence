import unittest
import numpy as np
from component_joint_matchup import available,weights,blended,InjuryTable,team

class JointBoundaryTests(unittest.TestCase):
 def entity(self,cid,pos='WR',**kw):return {'canonical_player_id':cid,'position_model':pos,'team':'SEA','provider_injury':'','official_status':None,'source_roster_status':'ACT','depth_order':1,'snaps':{'offense_pct':.6,'defense_pct':.6},**kw}
 def test_availability_clock_scope(self):
  e=self.entity('out',official_status='OUT');self.assertFalse(available(e,6));self.assertTrue(available(e,7))
  for week in [6,7,8]:self.assertFalse(available(self.entity('ir',provider_injury='IR'),week))
  self.assertTrue(available(self.entity('q',provider_injury='QUESTIONABLE'),6));self.assertFalse(available(self.entity('none',team=None),6))
 def test_unsupported_and_tiny_roles_do_not_receive_share(self):
  es=[self.entity('main'),self.entity('tiny'),self.entity('unsupported',snaps={'offense_pct':0})]
  ps={e['canonical_player_id']:{'components':{'targets':{'raw_unconditional_mean':v,'provenance':'SHRUNK_CONDITIONAL_MEAN'}}} for e,v in zip(es,[8,.05,3])}
  np.testing.assert_array_equal(weights(es,ps,'targets',{'WR'},6),[1,0,0])
 def test_backup_does_not_add_attempts(self):
  es=[self.entity('first','QB'),self.entity('second','QB')];ps={e['canonical_player_id']:{'components':{'passing_attempts':{'raw_unconditional_mean':v,'provenance':'SHRUNK_CONDITIONAL_MEAN'}}} for e,v in zip(es,[32,16])}
  np.testing.assert_array_equal(weights(es,ps,'passing_attempts',{'QB'},6,'first'),[1,0])
 def test_opponent_effect_direction(self):
  own={'complete_pass':20,'targeted':32};strong={'complete_pass':15,'targeted':32};weak={'complete_pass':25,'targeted':32}
  self.assertLess(blended(own,strong,'complete_pass','targeted'),blended(own,weak,'complete_pass','targeted'))
 def test_official_status_parser_and_alias(self):
  p=InjuryTable();p.feed('<table><tr><td>Drake Thomas</td><td>LB</td><td>Ankle</td><td>DNP</td><td>DNP</td><td>DNP</td><td>OUT</td></tr></table>');self.assertEqual(p.rows[0][-1],'OUT');self.assertEqual(team('LA'),'LAR')

if __name__=='__main__':unittest.main()
