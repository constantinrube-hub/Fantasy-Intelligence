"""Independent C2/C3 leakage, missingness, constraints and scoring tests."""
import json
from pathlib import Path
import unittest
import numpy as np
import pandas as pd
from component_registry import ROOT,build
from component_baselines import summary,lagged_roles,parameters,scenarios,MODELS,RATE_PARENT,YARD_PARENT
from component_scoring import rules_for,score_scenarios,sleeper_comparison,validate_scenarios
from component_training_view import negative_events


class BaselineTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.contracts=json.loads((ROOT/'config/contracts/runtime-contracts.json').read_text())
        cls.required=[x['component'] for x in build()['required_components']]

    def synthetic(self,pos='QB'):
        comps=sorted(set(self.required)|{'targets','kick_returns','punt_returns','kicker_fgm','kicker_fgmiss_50_59','kicker_fgmiss_60p',
            'kicker_field_goal_attempts','kicker_extra_point_attempts','dst_points_allowed','dst_net_yards_allowed','dst_prob_pts_allow_21_27',
            'kicker_blocked_field_goals','kicker_blocked_extra_points',
            'source_passing_first_downs_including_td','source_rushing_first_downs_including_td','source_receiving_first_downs_including_td'})
        specs={c:{'conditional_mean':1.,'std':2.,'rate':.2 if c in RATE_PARENT else 5. if c in YARD_PARENT else None,
                   'per_opportunity_scale':3.,'hurdle_probability':.2,'nonzero_std':2.} for c in comps}
        specs['passing_attempts']['conditional_mean']=25.;specs['targets']['conditional_mean']=8.
        specs['dst_points_allowed']['conditional_mean']=24.
        return {'components':comps,'draws':1024,'random_seed':4}, {'model_id':MODELS[1],'position':pos,'components':specs,'stat_activity_probability':.8}

    def test_rate_uses_joint_valid_exposure_not_zero_fill(self):
        x=summary(pd.Series([2.,0.,np.nan,4.]),pd.Series([4.,0.,20.,0.]))
        self.assertEqual(x['exposure_sum'],4)
        self.assertEqual(x['rate'],.5)
        self.assertEqual(x['paired_exposure_rows'],2)

    def test_lagged_role_cannot_see_target_or_later_season(self):
        f=pd.DataFrame({'canonical_player_id':['X']*5,'season':[2025]*4+[2026],'week':[1,2,3,4,1],
                        'position_model':['WR']*5,'targets':[2.,3.,5.,20.,100.]})
        a=lagged_roles(f);f.loc[3,'targets']=999.;b=lagged_roles(f)
        self.assertEqual(a.loc[3,'lagged_workload'],b.loc[3,'lagged_workload'])
        self.assertTrue(pd.isna(a.loc[4,'lagged_workload']))

    def test_joint_constraints_and_deterministic_sampling(self):
        lock,par=self.synthetic();a,_=scenarios(lock,par,'NFL:X',6);b,_=scenarios(lock,par,'NFL:X',6)
        validate_scenarios(a,'QB')
        for key in a:np.testing.assert_array_equal(a[key],b[key])

    def test_byes_and_unavailability_zero_forecast_not_actual_labels(self):
        lock,par=self.synthetic();a,_=scenarios(lock,par,'X',6,bye=True);validate_scenarios(a,'QB',True)
        b,_=scenarios(lock,par,'X',6,availability=0)
        self.assertTrue(all(np.all(v==0) for v in b.values()))

    def test_dst_bucket_labels_exhaustive_and_bonus_disjoint(self):
        lock,par=self.synthetic('DEF');a,_=scenarios(lock,par,'TEAM:BUF',6)
        validate_scenarios(a,'DEF')

    def test_negative_score_and_premium_independent_arithmetic(self):
        samples={'receptions':np.array([2.,4.]),'receiving_yards':np.array([-1.,20.])}
        rules=rules_for({'rec':-.5,'rec_yd':.1,'bonus_rec_te':.25},'TE',['TE'],self.contracts)
        totals,out=score_scenarios(samples,rules)
        np.testing.assert_allclose(totals,[-.6,1.])
        self.assertAlmostEqual(out['mean'],.2)

    def test_bonus_uses_event_probability_not_mean_yard_cutoff(self):
        samples={'passing_yards':np.array([299.,400.]),'prob_pass_yd_300':np.array([0.,0.]),'prob_pass_yd_400':np.array([0.,1.])}
        rules=rules_for({'pass_yd':.04,'bonus_pass_yd_300':2.,'bonus_pass_yd_400':3.},'QB',['QB'],self.contracts)
        _,out=score_scenarios(samples,rules)
        self.assertAlmostEqual(out['mean'],349.5*.04+1.5)

    def test_dual_position_idp_and_premium_primary_position(self):
        rules=rules_for({'rec':1.,'idp_tkl_solo':2.,'bonus_rec_te':.5},'WR',['WR','DB'],self.contracts)
        self.assertEqual({r['scoring_key'] for r in rules},{'rec','idp_tkl_solo'})

    def test_sleeper_missing_and_probability_are_not_invented(self):
        rules=rules_for({'pass_yd':.04,'bonus_pass_yd_300':2.},'QB',['QB'],self.contracts)
        r=sleeper_comparison({'pass_yd':310.},rules)
        self.assertIsNone(r['points']);self.assertEqual(r['supported_subtotal'],12.4)
        self.assertFalse(r['threshold_mean_plug_in_used']);self.assertFalse(r['missing_fields_imputed'])
        self.assertEqual(sleeper_comparison(None,rules)['status'],'NO_PUBLISHED_PLAYER_PROJECTION')

    def test_source_flags_missing_prevent_negative_event_certificate(self):
        game=pd.DataFrame({'play_type':['pass'],'fumble':[0]})
        proof,reason=negative_events(game)
        self.assertFalse(proof);self.assertEqual(reason,'BLOCKED_EVENT_FLAGS')

    def test_same_nfl_samples_different_league_weights(self):
        samples={'receptions':np.array([3.,5.]),'receiving_yards':np.array([20.,80.])}
        r1=rules_for({'rec':1.,'rec_yd':.1},'WR',['WR'],self.contracts)
        r2=rules_for({'rec':.5,'rec_yd':.1},'WR',['WR'],self.contracts)
        _,a=score_scenarios(samples,r1);_,b=score_scenarios(samples,r2)
        self.assertEqual(a['mean']-b['mean'],2.)

if __name__=='__main__':unittest.main()
