"""Adversarial C1 tests: source masks, exact identities, and scoring labels."""
import copy
import gzip
import json
from pathlib import Path
import tempfile
import unittest

import numpy as np
import pandas as pd
from build_component_outcomes import (additive, band_indicator, missed_distance_counts,
    identity_bridge, normalize_population, regular, verified, csv, apply_components)


class ComponentOutcomesTests(unittest.TestCase):
    def test_partial_additive_fields_never_become_zero_or_partial_total(self):
        d = pd.DataFrame({'a':[0,2,np.nan],'b':[0,np.nan,3]})
        out = additive(d,('a','b'))
        self.assertEqual(out.iloc[0],0)
        self.assertTrue(out.iloc[1:].isna().all())
        self.assertTrue(additive(d,('absent',)).isna().all())

    def test_exclusive_bonus_boundaries_and_missing(self):
        yards = pd.Series([299,300,399,400,450,np.nan])
        low = band_indicator(yards,300,399); high = band_indicator(yards,400,None)
        self.assertEqual(low.iloc[:5].tolist(),[0,1,1,0,0])
        self.assertEqual(high.iloc[:5].tolist(),[0,0,0,1,1])
        self.assertTrue(pd.isna(low.iloc[5]))
        self.assertTrue((low+high).dropna().le(1).all())

    def test_blocked_kicks_are_misses_and_distance_lists_reconcile(self):
        d = pd.DataFrame({'fg_missed':[1,0,0,1], 'fg_blocked':[1,1,0,1],
            'fg_missed_list':['27',None,None,'27'], 'fg_blocked_list':['36','46',None,None]})
        self.assertEqual(missed_distance_counts(d,30,39).iloc[:3].tolist(),[1,0,0])
        self.assertEqual(missed_distance_counts(d,40,49).iloc[1],1)
        self.assertTrue(pd.isna(missed_distance_counts(d,0,None).iloc[3]))

    def test_postseason_and_target_weeks_cannot_enter(self):
        d = pd.DataFrame({'season':[2026]*4,'week':[5,6,1,1], 'season_type':['REG','REG','POST',None]})
        self.assertEqual(regular(d,5).week.tolist(),[5])
        with self.assertRaisesRegex(ValueError,'MISSING_SEASON_TYPE'):
            regular(d.drop(columns='season_type'),5)

    def test_crosswalk_conflicts_are_quarantined_without_name_fallback(self):
        players = pd.DataFrame({'gsis_id':['00-0000001','00-0000002'],'pfr_id':['Aaaa00','Bbbb00']})
        ff = pd.DataFrame({'gsis_id':['00-0000001'],'sleeper_id':['10']})
        sleeper = {'11':{'gsis_id':'00-0000001','name':'Same Name'}}
        bridge = identity_bridge(players,ff,sleeper,[]).set_index('canonical_player_id')
        self.assertTrue(pd.isna(bridge.loc['00-0000001','sleeper_id']))
        self.assertEqual(bridge.loc['00-0000001','identity_status'],'UNKNOWN_CONFLICTING_CROSSWALK')
        self.assertTrue(pd.isna(bridge.loc['00-0000002','sleeper_id']))

    def test_hash_and_clock_guards(self):
        from component_registry import digest
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp); p=root/'source'; p.write_text('actual')
            ref={'path':'source','sha256':digest(p),'observed_at':'2026-01-01T00:00:00+00:00'}
            self.assertEqual(verified(root,ref),p)
            p.write_text('changed')
            with self.assertRaisesRegex(ValueError,'HASH_MISMATCH'):
                verified(root,ref)
            ref['sha256']=digest(p); ref['observed_at']='2999-01-01T00:00:00+00:00'
            with self.assertRaisesRegex(ValueError,'CLOCK_IN_FUTURE'):
                verified(root,ref)

    def test_deterministic_gzip_bytes(self):
        with tempfile.TemporaryDirectory() as tmp:
            a=Path(tmp)/'a.gz'; b=Path(tmp)/'b.gz'; d=pd.DataFrame({'value':[0,1,np.nan]})
            csv(d,a); csv(d,b)
            self.assertEqual(a.read_bytes(),b.read_bytes())

    def test_provider_omitted_stat_stays_unknown_even_with_completed_game(self):
        pop = pd.DataFrame({'canonical_player_id':['TEAM:BUF'],'season':[2025],'week':[1],
            'position_model':['DEF'],'week_state':['COMPLETED_GAME']})
        provider=pd.DataFrame({'canonical_player_id':['TEAM:BUF'],'season':[2025],'week':[1],'gp':[1]})
        demand={'rules':[{'component':'dst_field_goal_return_yards','positions':['DEF'],'scoring_key':'fg_ret_yd'}],
            'required_components':[{'component':'dst_field_goal_return_yards','mode':'mean','unit':'yards'}]}
        out,_,_=apply_components(pop,demand,None,provider)
        self.assertTrue(pd.isna(out.dst_field_goal_return_yards.iloc[0]))
        self.assertEqual(out.dst_field_goal_return_yards__status.iloc[0],'UNKNOWN_ABSENT_SOURCE_VALUE')

    def test_duplicate_player_weeks_rejected_and_absence_is_not_dnp_zero(self):
        raw=pd.DataFrame({'player_id':['00-0000001'],'season':[2025],'week':[1],'season_type':['REG'],
                         'team':['BUF'],'position':['WR'],'game_id':['G1']})
        roster=pd.DataFrame({'gsis_id':['00-0000002'],'season':[2025],'week':[1],'game_type':['REG'],
                            'team':['BUF'],'position':['WR'],'status':['INA']})
        games=pd.DataFrame({'game_id':['G1'],'season':[2025],'week':[1],'game_type':['REG'],
                           'home_team':['BUF'],'away_team':['NE'],'home_score':[7],'away_score':[3]})
        pop,_,_=normalize_population(raw,roster,games,2025,18)
        absent=pop[pop.canonical_player_id.eq('00-0000002')].iloc[0]
        self.assertFalse(absent.published_stat_row)
        self.assertEqual(absent.week_state,'COMPLETED_GAME')
        with self.assertRaisesRegex(ValueError,'DUPLICATE_PLAYER_WEEK'):
            normalize_population(pd.concat([raw,raw]),roster,games,2025,18)

    def test_cancelled_bills_bengals_game_is_not_a_bye_zero(self):
        raw=pd.DataFrame({'player_id':['00-0000001'],'season':[2022],'week':[17],'season_type':['REG'],
                         'team':['NE'],'position':['WR'],'game_id':['G1']})
        roster=pd.DataFrame({'gsis_id':['00-0000002'],'season':[2022],'week':[17],'game_type':['REG'],
                            'team':['BUF'],'position':['WR'],'status':['ACT']})
        games=pd.DataFrame({'game_id':['G1'],'season':[2022],'week':[17],'game_type':['REG'],
                           'home_team':['NE'],'away_team':['MIA'],'home_score':[7],'away_score':[3]})
        pop,_,_=normalize_population(raw,roster,games,2022,18)
        state=pop[pop.canonical_player_id.eq('00-0000002')].week_state.iloc[0]
        self.assertEqual(state,'UNKNOWN_GAME_OR_TEAM')


if __name__=='__main__':
    unittest.main()
