"""Synthetic cases prove mechanics, never football calibration."""
from copy import deepcopy
import json
from pathlib import Path
import tempfile

from joint_scenario_engine import ROOT,calibration_diagnostics,run,simulate,survival,validate_bank
from research_bid_curve import curve
from draft_scenario_review import review
from point_in_time_capture import first_write_json
from weekly_evidence_audit import digest


def reject(call):
    try:call()
    except (ValueError,RuntimeError):return
    raise AssertionError('invalid scenario input accepted')


def fixture():
    players={f'canonical:{p}':{'canonical_player_id':p,'position_model':'QB'} for p in ('a','b','c')}
    bank={'schema':'fie-joint-weekly-scenarios-v1','weighting':'UNIFORM','season':2026,'week':6,
          'model_id':'TEST_ONLY','model_version':'1','scoring_signature':'test',
          'generated_at':'2026-10-10T00:00:00Z','cutoff':'2026-10-10T01:00:00Z','first_kickoff':'2026-10-11T12:00:00Z',
          'players':players,'scenarios':[{'scenario_id':str(i),'points':dict(zip(players,values))} for i,values in
                                       enumerate([(0,0,10),(20,20,10),(-2,-2,-4)])]}
    lineups={p:{'player_ids':['canonical:'+p],'roster_positions':['QB'],'mode':'MANAGED_FIXED',
                'scoring_signature':'test','origin':'DECLARED_RESEARCH_ALTERNATIVE'} for p in ('a','b','c')}
    return bank,lineups


def main():
    bank,lineups=fixture()
    result=simulate(bank,lineups,h2h=['a','b'],comparison=['a','c'],chopped={
        'active_field':['a','b','c'],'complete_active_field_bound':True,'eliminations':1,'tie_policy':'EQUAL_RANDOM_ELIMINATION'})
    assert result['h2h']['tie']==1 and result['h2h']['win']==0
    assert result['portfolio_same_scoring_signature'] is None
    scoped=deepcopy(lineups)
    for index, key in enumerate(scoped):scoped[key].update(owner_scope='USER_ROSTER',league_id=str(index+1))
    assert simulate(bank,scoped,portfolio=['a'])['portfolio_same_scoring_signature']['mean']==6
    reject(lambda:simulate(bank,lineups,portfolio=['a','b']))
    assert result['lineup_comparison']['a_beats_b']==2/3
    assert abs(sum(result['chopped']['survival'].values())-2)<1e-12
    sampled=simulate(bank,lineups,mode='SAMPLED',draws=1000,seed=7,h2h=['a','b'])
    assert sampled==simulate(bank,lineups,mode='SAMPLED',draws=1000,seed=7,h2h=['a','b'])
    assert sampled['h2h']['tie']==1
    changed=deepcopy(bank);del changed['scenarios'][0]['points']['canonical:a']
    reject(lambda:validate_bank(changed))
    changed=deepcopy(bank);changed['scenarios'][0]['points']['canonical:a']=float('nan')
    reject(lambda:validate_bank(changed))
    illegal=deepcopy(lineups);illegal['a']['roster_positions']=['RB']
    reject(lambda:simulate(bank,illegal))
    reject(lambda:survival({'a':1,'b':2},True,'EQUAL_RANDOM_ELIMINATION'))
    reject(lambda:survival({'a':1,'b':2},1,'UNKNOWN'))
    automatic=deepcopy(lineups['a']);automatic.update(mode='BESTBALL_AUTOMATIC',origin='AUTOMATIC_ROSTER',player_ids=['canonical:a','canonical:c'])
    result=simulate(bank,{'auto':automatic})
    assert result['lineups']['auto']['minimum']==-2
    holdout={'schema':'fie-distribution-holdout-v1','model_id':'TEST_ONLY','model_version':'1',
        'scoring_signature':'test','training_cutoff':'2026-09-01T00:00:00Z','rows':[
        {'season':2026,'week':1,'canonical_player_id':'canonical:a','position':'QB','exact_scoring':True,
         'forecast_at':'2026-09-02T00:00:00Z','kickoff':'2026-09-03T00:00:00Z','outcome_observed_at':'2026-09-04T00:00:00Z',
         'point_samples':[0,10,20],'realized_points':10}]}
    diagnostics=calibration_diagnostics(holdout,model_id='TEST_ONLY',model_version='1',scoring_signature='test',cutoff=bank['cutoff'])
    assert diagnostics['positions'][0]['central_80_percent_coverage']==1
    assert diagnostics['governed_calibration_approved'] is False
    altered=deepcopy(holdout);altered['rows'][0]['forecast_at']=altered['rows'][0]['kickoff']
    reject(lambda:calibration_diagnostics(altered,model_id='TEST_ONLY',model_version='1',scoring_signature='test',cutoff=bank['cutoff']))
    with tempfile.TemporaryDirectory() as td:
        root=Path(td);(root/'data/research').mkdir(parents=True)
        # Use actual runtime contract only for mechanical legal-assignment tests.
        (root/'config/contracts').mkdir(parents=True)
        (root/'config/contracts/runtime-contracts.json').write_bytes((ROOT/'config/contracts/runtime-contracts.json').read_bytes())
        p=root/'data/research/bank.json';first_write_json(p,bank)
        ref={'path':'data/research/bank.json','sha256':digest(p),'observed_at':bank['generated_at']}
        request={'bank':ref,'season':2026,'week':6,'scoring_signature':'test','lineups':lineups}
        assert run(root,request)['status']=='BLOCKED_CALIBRATION_EVIDENCE_MISSING'
        cp=root/'data/research/calibration.json';first_write_json(cp,holdout)
        request['calibration']={'path':'data/research/calibration.json','sha256':digest(cp),'observed_at':bank['generated_at']}
        assert run(root,request)['production_authorized'] is False
        p.write_text('{}')
        reject(lambda:run(root,request))
    samples=[{'auction_id':str(i),'league_id':'l','currency':'FAAB','observed_at':'2026-10-01T00:00:00Z',
              'complete_competing_bids':True,'maximum_competing_bid':bid} for i,bid in enumerate([0,5,10])]
    bids=curve(samples,league_id='l',currency='FAAB',budget=10,bids=[0,6,11],cutoff='2026-10-02T00:00:00Z',tie_policy='USER_LOSES_TIE')
    assert bids['rows'][1]['empirical_acquisition_probability']==2/3 and bids['rows'][2]['empirical_acquisition_probability'] is None
    for s in samples:s['complete_competing_bids']=False
    assert curve(samples,league_id='l',currency='FAAB',budget=10,bids=[1],cutoff='2026-10-02T00:00:00Z',tie_policy='USER_LOSES_TIE')['status'].startswith('BLOCKED')
    draft=review(bank,{'scoring_signature':'test','constraints_known':True,'picked_player_ids':['canonical:a'],
                      'user_roster_player_ids':['canonical:a'],'roster_positions':['QB']})
    assert draft['remaining_player_pool']==['canonical:b','canonical:c'] and draft['pick_recommendation'] is None
    print('PASS joint scenarios: shared correlation, legal negative scores, fixed/automatic distinction, ties, seeds, calibration/hash gates, bids and draft research')


if __name__=='__main__':main()
