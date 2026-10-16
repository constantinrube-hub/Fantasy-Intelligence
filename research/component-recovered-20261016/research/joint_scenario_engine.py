"""Research-only legal lineup simulation over supplied complete joint vectors."""
from __future__ import annotations

import argparse
from collections import defaultdict
import json
import math
from pathlib import Path
import random
from statistics import mean

from point_in_time_capture import first_write_json
from strict_sleeper_baseline import finite
from weekly_evidence_audit import digest, stamp
from weekly_lineup_decision_support import canonical_player_id, exact_lineup, load_runtime_contract, starter_slot_instances

ROOT=Path(__file__).resolve().parents[1]


def quantile(values,p):
    if not values or not 0<=p<=1:
        raise ValueError('SCENARIO_QUANTILE_INPUT_INVALID')
    ordered=sorted(values);index=(len(ordered)-1)*p
    low=math.floor(index);high=math.ceil(index)
    return ordered[low]+(ordered[high]-ordered[low])*(index-low)


def distribution(values):
    return {'mean':mean(values),'p10':quantile(values,.1),'median':quantile(values,.5),'p90':quantile(values,.9),
            'minimum':min(values),'maximum':max(values)}


def binding(root,ref):
    path=(root/ref['path']).resolve()
    if not path.is_relative_to(root.resolve()/'data/research') or not path.is_file() or digest(path)!=ref['sha256']:
        raise ValueError('SCENARIO_SOURCE_PATH_OR_HASH_INVALID')
    stamp(ref['observed_at'])
    return json.loads(path.read_text())


def calibration_diagnostics(payload,*,model_id,model_version,scoring_signature,cutoff):
    if payload.get('schema')!='fie-distribution-holdout-v1' or (payload.get('model_id'),payload.get('model_version'))!=(model_id,model_version):
        raise ValueError('CALIBRATION_MODEL_OR_SCHEMA_MISMATCH')
    if payload.get('scoring_signature')!=scoring_signature:
        raise ValueError('CALIBRATION_SCORING_MISMATCH')
    training=stamp(payload['training_cutoff']);limit=stamp(cutoff)
    groups=defaultdict(list);seen=set()
    for row in payload.get('rows') or []:
        key=(row['season'],row['week'],row['canonical_player_id'])
        if key in seen:
            raise ValueError('CALIBRATION_DUPLICATE_HOLDOUT_PLAYER_WEEK')
        seen.add(key)
        forecast,kickoff,outcome=[stamp(row[k]) for k in ('forecast_at','kickoff','outcome_observed_at')]
        if not training<forecast<kickoff<outcome<=limit or row.get('exact_scoring') is not True:
            raise ValueError('CALIBRATION_TIME_OR_SCORING_INVALID')
        points=[finite(v) for v in row.get('point_samples') or []]
        actual=finite(row.get('realized_points'))
        if not points or any(v is None for v in points) or actual is None or not row.get('position'):
            raise ValueError('CALIBRATION_POINTS_OR_POSITION_INVALID')
        lower,upper=quantile(points,.1),quantile(points,.9)
        groups[row['position']].append({'covered':lower<=actual<=upper,'error':mean(points)-actual,
                                      'width':upper-lower,'week':(row['season'],row['week'])})
    return {'status':'CALIBRATION_DIAGNOSTICS_ONLY' if groups else 'BLOCKED_NO_HOLDOUT_ROWS',
            'positions':[{'position':position,'rows':len(rows),'weeks':len({r['week'] for r in rows}),
                          'central_80_percent_coverage':mean(r['covered'] for r in rows),
                          'mean_prediction_error':mean(r['error'] for r in rows),
                          'mean_interval_width':mean(r['width'] for r in rows)} for position,rows in sorted(groups.items())],
            'governed_calibration_approved':False,
            'note':'Holdout metrics are descriptive; declared source times and exact-scoring flags require their owning evidence audit.'}


def validate_bank(bank):
    if bank.get('schema')!='fie-joint-weekly-scenarios-v1' or bank.get('weighting')!='UNIFORM':
        raise ValueError('SCENARIO_BANK_SCHEMA_OR_WEIGHTING_INVALID')
    if not bank.get('model_id') or not bank.get('model_version') or not bank.get('scoring_signature'):
        raise ValueError('SCENARIO_MODEL_OR_SCORING_IDENTITY_MISSING')
    if not stamp(bank['generated_at'])<=stamp(bank['cutoff'])<stamp(bank['first_kickoff']):
        raise ValueError('SCENARIO_BANK_NOT_PREGAME')
    if not isinstance(bank.get('season'),int) or isinstance(bank['season'],bool) or not isinstance(bank.get('week'),int) or isinstance(bank['week'],bool) or not 1<=bank['week']<=18:
        raise ValueError('SCENARIO_TARGET_INVALID')
    players=bank.get('players') or {}
    if not players or any(canonical_player_id(row)!=key or not row.get('position_model') for key,row in players.items()):
        raise ValueError('SCENARIO_PLAYER_IDENTITY_INVALID')
    scenarios=bank.get('scenarios') or [];seen=set()
    if not scenarios:
        raise ValueError('SCENARIO_BANK_EMPTY')
    for row in scenarios:
        sid=row.get('scenario_id')
        if not sid or sid in seen or 'weight' in row:
            raise ValueError('SCENARIO_ID_OR_WEIGHT_INVALID')
        seen.add(sid)
        points=row.get('points') or {}
        if set(points)!=set(players) or any(finite(v) is None for v in points.values()):
            raise ValueError('SCENARIO_INCOMPLETE_OR_NONFINITE_VECTOR')
    return bank


def validate_lineup(lineup,bank,root):
    ids=lineup.get('player_ids') or [];mode=lineup.get('mode')
    if not ids or len(set(ids))!=len(ids) or not set(ids)<=set(bank['players']):
        raise ValueError('SCENARIO_LINEUP_IDENTITY_INVALID')
    if mode not in {'MANAGED_FIXED','BESTBALL_AUTOMATIC'} or lineup.get('scoring_signature')!=bank['scoring_signature']:
        raise ValueError('SCENARIO_LINEUP_MODE_OR_SCORING_MISMATCH')
    if lineup.get('origin') not in {'CAPTURED_SUBMITTED','DECLARED_RESEARCH_ALTERNATIVE','AUTOMATIC_ROSTER'}:
        raise ValueError('SCENARIO_LINEUP_ORIGIN_UNDECLARED')
    contract,_=load_runtime_contract(root)
    slots=starter_slot_instances(lineup.get('roster_positions'),contract)
    players=[{**bank['players'][pid],'scenario_value':1} for pid in ids]
    result=exact_lineup(players,lineup['roster_positions'],value_key='scenario_value',root=root)
    if not result['complete_assignment'] or (mode=='MANAGED_FIXED' and len(ids)!=len(slots)):
        raise ValueError('SCENARIO_LINEUP_ILLEGAL_OR_INCOMPLETE')
    return lineup


def lineup_score(lineup,bank,scenario,root):
    ids=lineup['player_ids'];points=scenario['points']
    if lineup['mode']=='MANAGED_FIXED':
        return sum(float(points[pid]) for pid in ids)
    # The existing owner permits dummies. Shift uniformly so full automatic
    # assignments remain legal even when all outcomes at a position are negative.
    shift=max(0,-min(float(points[pid]) for pid in ids))+1
    players=[{**bank['players'][pid],'scenario_value':float(points[pid])+shift} for pid in ids]
    result=exact_lineup(players,lineup['roster_positions'],value_key='scenario_value',root=root)
    if not result['complete_assignment']:
        raise ValueError('SCENARIO_AUTOMATIC_ASSIGNMENT_INCOMPLETE')
    return sum(float(points[pid]) for pid in result['selected_player_ids'])


def survival(scores,eliminations,tie_policy):
    if isinstance(eliminations,bool) or not isinstance(eliminations,int) or not 1<=eliminations<len(scores):
        raise ValueError('CHOPPED_ELIMINATION_COUNT_INVALID')
    if tie_policy!='EQUAL_RANDOM_ELIMINATION':
        raise ValueError('CHOPPED_TIE_POLICY_UNSUPPORTED')
    cutoff=sorted(scores.values())[eliminations-1]
    below=sum(v<cutoff for v in scores.values());tied=sum(v==cutoff for v in scores.values())
    tie_survival=1-(eliminations-below)/tied
    return cutoff,{key:1.0 if value>cutoff else 0.0 if value<cutoff else tie_survival for key,value in scores.items()}


def simulate(bank,lineups,*,root=ROOT,mode='EXHAUSTIVE',draws=10000,seed=0,h2h=None,chopped=None,comparison=None,portfolio=None):
    validate_bank(bank)
    if not lineups or any(not key for key in lineups):
        raise ValueError('SCENARIO_LINEUPS_MISSING')
    for lineup in lineups.values():validate_lineup(lineup,bank,root)
    if mode=='EXHAUSTIVE':
        indices=list(range(len(bank['scenarios'])))
    elif mode=='SAMPLED':
        if isinstance(draws,bool) or not isinstance(draws,int) or not 1<=draws<=100000 or isinstance(seed,bool) or not isinstance(seed,int):
            raise ValueError('SCENARIO_SAMPLE_PARAMETERS_INVALID')
        rng=random.Random(seed);indices=[rng.randrange(len(bank['scenarios'])) for _ in range(draws)]
    else:
        raise ValueError('SCENARIO_SIMULATION_MODE_INVALID')
    totals={key:[] for key in lineups}
    # Solve automatic rosters once per unique vector, then reuse for sampling.
    cache={}
    for index in set(indices):
        scenario=bank['scenarios'][index]
        cache[index]={key:lineup_score(lineup,bank,scenario,root) for key,lineup in lineups.items()}
    for index in indices:
        for key in totals:totals[key].append(cache[index][key])
    report={'schema':'fie-joint-scenario-result-v1','status':'RESEARCH_CONDITIONAL_SCENARIOS',
            'season':bank['season'],'week':bank['week'],'scoring_signature':bank['scoring_signature'],
            'mode':mode,'seed':seed if mode=='SAMPLED' else None,'draws':len(indices),'bank_scenarios':len(bank['scenarios']),
            'lineups':{key:{**distribution(values),'selection_mode':lineups[key]['mode'],'origin':lineups[key]['origin']} for key,values in totals.items()},
            'portfolio_same_scoring_signature':None,
            'correlation':'Shared complete joint vectors; supplied dependence preserved, empirical football validity unverified.',
            'calibrated_production_probability':False,'production_authorized':False}
    if portfolio is not None:
        if not portfolio or len(set(portfolio))!=len(portfolio) or not set(portfolio)<=set(totals):
            raise ValueError('SCENARIO_PORTFOLIO_KEYS_INVALID')
        leagues=[lineups[k].get('league_id') for k in portfolio]
        if any(lineups[k].get('owner_scope')!='USER_ROSTER' for k in portfolio) or not all(leagues) or len(set(leagues))!=len(leagues):
            raise ValueError('SCENARIO_PORTFOLIO_OWNER_OR_LEAGUE_SCOPE_INVALID')
        report['portfolio_same_scoring_signature']={'lineup_keys':portfolio,
            **distribution([sum(totals[k][i] for k in portfolio) for i in range(len(indices))])}
    if h2h:
        if len(h2h)!=2 or h2h[0]==h2h[1] or not set(h2h)<=set(totals):raise ValueError('H2H_LINEUP_KEYS_INVALID')
        margins=[a-b for a,b in zip(totals[h2h[0]],totals[h2h[1]])]
        win=mean(v>0 for v in margins)
        report['h2h']={'user':h2h[0],'opponent':h2h[1],'win':win,'tie':mean(v==0 for v in margins),
                        'loss':mean(v<0 for v in margins),'margin':distribution(margins),
                        'conditional_sampling_standard_error':math.sqrt(win*(1-win)/len(indices)) if mode=='SAMPLED' else 0,
                        'model_uncertainty_included':False}
    if comparison:
        if len(comparison)!=2 or not set(comparison)<=set(totals):raise ValueError('COMPARISON_LINEUP_KEYS_INVALID')
        delta=[a-b for a,b in zip(totals[comparison[0]],totals[comparison[1]])]
        report['lineup_comparison']={'a':comparison[0],'b':comparison[1],'a_beats_b':mean(v>0 for v in delta),
                                    'tie':mean(v==0 for v in delta),'delta':distribution(delta)}
    if chopped:
        field=chopped.get('active_field') or []
        if chopped.get('complete_active_field_bound') is not True or not field or len(set(field))!=len(field) or not set(field)<=set(totals):
            raise ValueError('CHOPPED_ACTIVE_FIELD_INCOMPLETE')
        owned=set()
        for key in field:
            ids=set(lineups[key]['player_ids'])
            if ids & owned:raise ValueError('CHOPPED_DUPLICATE_FIELD_PLAYER_OWNERSHIP')
            owned.update(ids)
        values={key:[] for key in field};cutoffs=[]
        for i in range(len(indices)):
            cutoff,probabilities=survival({key:totals[key][i] for key in field},chopped['eliminations'],chopped['tie_policy'])
            cutoffs.append(cutoff)
            for key in field:values[key].append(probabilities[key])
        report['chopped']={'active_field':field,'tie_policy':chopped['tie_policy'],'eliminations':chopped['eliminations'],
                           'cutoff_distribution':distribution(cutoffs),'survival':{key:mean(v) for key,v in values.items()}}
    return report


def run(root:Path,request:dict):
    bank=binding(root,request['bank']);validate_bank(bank)
    if (request.get('season'),request.get('week'),request.get('scoring_signature'))!=(bank['season'],bank['week'],bank['scoring_signature']):
        raise ValueError('SCENARIO_REQUEST_TARGET_MISMATCH')
    if stamp(request['bank']['observed_at'])>stamp(bank['cutoff']):
        raise ValueError('SCENARIO_BANK_OBSERVED_AFTER_CUTOFF')
    calibration_ref=request.get('calibration')
    if not calibration_ref:
        return {'status':'BLOCKED_CALIBRATION_EVIDENCE_MISSING','production_authorized':False}
    calibration=binding(root,calibration_ref)
    if stamp(calibration_ref['observed_at'])>stamp(bank['cutoff']):raise ValueError('CALIBRATION_RECEIPT_AFTER_CUTOFF')
    diagnostics=calibration_diagnostics(calibration,model_id=bank['model_id'],model_version=bank['model_version'],
                                        scoring_signature=bank['scoring_signature'],cutoff=bank['cutoff'])
    if diagnostics['status']=='BLOCKED_NO_HOLDOUT_ROWS':
        return {'status':diagnostics['status'],'calibration':diagnostics,'production_authorized':False}
    result=simulate(bank,request['lineups'],root=root,mode=request.get('mode','EXHAUSTIVE'),
                    draws=request.get('draws',10000),seed=request.get('seed',0),h2h=request.get('h2h'),
                    chopped=request.get('chopped'),comparison=request.get('comparison'),portfolio=request.get('portfolio'))
    result['source_bindings']={'bank':request['bank'],'calibration':calibration_ref}
    result['calibration_diagnostics']=diagnostics
    return result


def main():
    ap=argparse.ArgumentParser();ap.add_argument('--root',type=Path,default=ROOT)
    ap.add_argument('--input',type=Path,required=True);ap.add_argument('--output',type=Path,required=True)
    args=ap.parse_args();request=json.loads(args.input.read_text())
    result=run(args.root.resolve(),request);result['request_sha256']=digest(args.input)
    print(first_write_json(args.output,result))


if __name__=='__main__':main()
