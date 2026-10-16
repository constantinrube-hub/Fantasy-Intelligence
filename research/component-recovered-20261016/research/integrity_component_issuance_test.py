"""C4 ownership, bye-roster retention, scoring scope and first-write protections."""
import json
import tempfile
from pathlib import Path
import unittest
import pandas as pd
from issue_component_forecasts import universe,pool_eligibility,projection_map,entry_season,verify_first_write
from prospective_research_io import sha,write

CLUBS='ARI ATL BAL BUF CAR CHI CIN CLE DAL DEN DET GB HOU IND JAX KC LAC LAR LV MIA MIN NE NO NYG NYJ PHI PIT SEA SF TB TEN WAS'.split()

class IssuanceTests(unittest.TestCase):
    def test_roster_missing_for_bye_club_retains_last_observation(self):
        roster=pd.DataFrame([{'season':2026,'week':5 if i==0 else 6,'team':c,'status':'ACT',
          'gsis_id':f'00-{i+1:07d}','sleeper_id':str(i+1),'position':'WR','full_name':c,'rookie_year':2025} for i,c in enumerate(CLUBS)])
        cat={str(i+1):{'position':'WR','fantasy_positions':['WR'],'team':c,'gsis_id':f'00-{i+1:07d}'} for i,c in enumerate(CLUBS)}
        cat.update({c:{'position':'DEF'} for c in CLUBS})
        cat['999']={'position':'RB','fantasy_positions':['RB'],'team':None}
        bridge=pd.DataFrame([{'identity_status':'EXACT_ONE_TO_ONE','canonical_player_id':f'00-{i+1:07d}','sleeper_id':str(i+1)} for i in range(32)])
        players=pd.DataFrame([{'gsis_id':f'00-{i+1:07d}','rookie_season':2025} for i in range(32)])
        rows,audit=universe(cat,roster,players,bridge,{'999'})
        self.assertEqual(sum(r['position_model']=='DEF' for r in rows),32)
        self.assertEqual(next(r for r in rows if r['sleeper_id']=='1')['current_roster_week'],5)
        self.assertEqual(next(r for r in rows if r['sleeper_id']=='999')['canonical_player_id'],'SLEEPER:999')
        self.assertFalse(audit)

    def test_cohort_unknown_not_guessed_from_name_or_experience(self):
        c=[{'type':'nfl_entry_cohort_floor','minimum_entry_season':2025}]
        self.assertEqual(pool_eligibility({'entry_season':None},c)['status'],'UNKNOWN_ENTRY_SEASON')
        self.assertTrue(pool_eligibility({'entry_season':2024},c,True)['retained_owned_exception'])
        self.assertEqual(pool_eligibility({'entry_season':2025},c)['status'],'ELIGIBLE')
        self.assertIsNone(entry_season(None,'not a season',float('nan')))

    def test_future_endpoint_empty_and_wrong_week_typed(self):
        self.assertEqual(projection_map([],7)[1]['status'],'UNPUBLISHED_OR_NO_USABLE_ROWS')
        values,status=projection_map([{'player_id':'1','season':2026,'week':6,'stats':{'rec':3}}],7)
        self.assertFalse(values);self.assertEqual(status['invalid_rows'],1)

    def test_first_write_rejects_divergence_and_backdated_capture(self):
        with tempfile.TemporaryDirectory() as d:
            root=Path(d);artifact=root/'row.json';write(artifact,{'x':1})
            with self.assertRaisesRegex(ValueError,'DIVERGENT'):write(artifact,{'x':2})
            manifest=root/'manifest.json';value={'artifacts':{'row.json':sha(artifact)},'owners':{},
                'issued_at':'2026-10-14T18:00:00Z','first_target_kickoff':'2026-10-16T00:15:00Z'}
            write(manifest,value);self.assertEqual(verify_first_write(root,manifest),value)
            artifact.write_text('changed')
            with self.assertRaisesRegex(ValueError,'DIVERGENT'):verify_first_write(root,manifest)
            value['artifacts']={};value['issued_at']='2026-10-16T00:15:00Z';manifest.write_text(json.dumps(value))
            with self.assertRaisesRegex(ValueError,'RETROSPECTIVE'):verify_first_write(root,manifest)

if __name__=='__main__':unittest.main()
