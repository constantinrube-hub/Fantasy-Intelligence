"""Additional signatures reuse inference but cannot override legacy authority."""
from pathlib import Path
import copy,json
import pandas as pd
from prospective_research_io import gates
from waiver_v2_prospective import forecast

def main():
    root=Path(__file__).resolve().parents[1];c=json.loads((root/'config/waiver-v2-expanded-methodology.json').read_text());sig=c['signatures'][0]
    history=pd.DataFrame([{'canonical_player_id':'00-0000001','season':2026,'week':w,'team':'KC','position_model':'QB','scoring_signature':sig,'fantasy_points_exact':float(w),'outcome_complete':True,'exact_scoring':True} for w in [3,4,5]])
    stats=history[['canonical_player_id','season','week']].copy();stats['attempts']=10.;stats['passing_yards']=100.
    universe=[{'canonical_player_id':'00-0000001','position_model':'QB','team':'KC'}]
    lock={'schema':'fie-waiver-v2-expanded-lock-v1','season':2026,'frozen_at':'2026-10-13T00:00:00+00:00','parameters_selected_from_2026':False,
        'units':[{'scoring_signature':sig,'position':p,'model':None} for p in c['positions']],**gates([])}
    args=dict(season=2026,completed_week=5,captured_at='2026-10-14T00:00:00+00:00',first_kickoff='2026-10-16T00:15:00+00:00')
    try:forecast(lock,sig,history,stats,universe,**args)
    except ValueError as e:assert str(e)=='WAIVER_CAPTURE_UNSUPPORTED_SIGNATURE'
    else:raise AssertionError('Legacy signature boundary changed')
    rows=forecast(lock,sig,history,stats,universe,additional_methodology=c,**args)
    assert len(rows)==1 and rows[0]['forecast_mean'] is None and rows[0]['baseline_mean']==4.
    assert all(rows[0][k] is False for k in gates([]) if k.endswith('_eligible'))
    bad=copy.deepcopy(c);bad['minimum_history']=1
    try:forecast(lock,sig,history,stats,universe,additional_methodology=bad,**args)
    except ValueError as e:assert str(e)=='WAIVER_ADDITIONAL_NUMERICAL_METHOD_DRIFT'
    else:raise AssertionError('Additional method override admitted')
    print('PASS expanded inference: declared signatures, same source baseline/nulls, legacy boundary and numerical-method rejection')
if __name__=='__main__':main()
