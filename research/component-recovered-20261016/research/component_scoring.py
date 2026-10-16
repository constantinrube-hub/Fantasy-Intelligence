"""C3 exact expectation arithmetic and explicit provider comparison coverage."""
from __future__ import annotations
import math
import numpy as np
from component_registry import mapping, finite, canonical

PREMIUMS={'bonus_rec_te':'TE','bonus_rush_td_qb':'QB'}

def rules_for(scoring,position,eligible_positions,contracts):
    position=canonical(position,contracts)
    eligibility={canonical(p,contracts) for p in eligible_positions}|{position}
    rules=[]
    for key,weight in sorted(scoring.items()):
        weight=finite(weight)
        if not weight:continue
        spec=mapping(key,contracts)
        if key in PREMIUMS and position!=PREMIUMS[key]:continue
        if not eligibility.intersection(spec['positions']):continue
        rules.append({**spec,'weight':weight})
    return rules

def score_scenarios(samples,rules):
    if not samples:raise ValueError('COMPONENT_EMPTY_SCENARIOS')
    n=len(next(iter(samples.values())));total=np.zeros(n,dtype=float);contributions={}
    for rule in rules:
        comp=rule['component']
        if comp not in samples:raise ValueError('COMPONENT_SCORE_MISSING:'+comp)
        values=np.asarray(samples[comp],dtype=float)
        if values.shape!=(n,) or not np.isfinite(values).all():raise ValueError('COMPONENT_SCORE_INVALID_VALUES')
        points=values*rule['weight'];total+=points
        contributions[rule['scoring_key']]={'component':comp,'weight':rule['weight'],
            'expectation':float(values.mean()),'points':float(points.mean()),'mode':rule['mode']}
    expected=math.fsum(v['points'] for v in contributions.values())
    if not math.isclose(expected,float(total.mean()),abs_tol=1e-9):raise ValueError('COMPONENT_CONTRIBUTION_RECONCILIATION')
    return total,{'mean':expected,'p10':float(np.quantile(total,.1)),'p50':float(np.quantile(total,.5)),
                  'p90':float(np.quantile(total,.9)),'contributions':contributions,
                  'scoring_arithmetic_complete':True,'provider_exact_certified':False}

def sleeper_comparison(stats,rules):
    """Only explicit projection fields form matched component comparisons.

    Sparse omissions are not declared forecast zeros. An unobserved threshold
    probability is not derived by plugging expected yards into a cutoff.
    """
    if stats is None:
        return {'status':'NO_PUBLISHED_PLAYER_PROJECTION','points':None,'supported_subtotal':None,
                'missing_keys':[r['scoring_key'] for r in rules],'contributions':{},'raw_components':{}}
    contributions={};missing=[];raw={}
    for r in rules:
        key=r['scoring_key'];value=stats.get(key)
        if key=='bonus_rec_te':value=stats.get('rec')
        elif key=='bonus_rush_td_qb':value=stats.get('rush_td')
        if value is None or isinstance(value,bool):missing.append(key);continue
        try:value=finite(value)
        except (ValueError,TypeError):missing.append(key);continue
        if r['mode']=='probability' and not 0<=value<=1:
            missing.append(key);continue
        contributions[key]=value*r['weight'];raw[r['component']]=value
    subtotal=math.fsum(contributions.values())
    return {'status':'EXPLICIT_FIELDS_COMPLETE' if not missing else 'PARTIAL_RAW_COMPONENT_COVERAGE',
            'points':subtotal if not missing else None,'supported_subtotal':subtotal,
            'missing_keys':missing,'contributions':contributions,'raw_components':raw,
            'provider_native_points':{k:stats[k] for k in ['pts_std','pts_half_ppr','pts_ppr'] if k in stats},
            'threshold_mean_plug_in_used':False,'missing_fields_imputed':False}

def validate_scenarios(samples,position,bye=False):
    def le(a,b):
        if np.any(samples[a]>samples[b]+1e-9):raise ValueError('COMPONENT_CONSTRAINT:'+a+'>'+b)
    for a,b in [('passing_completions','passing_attempts'),('receptions','targets'),('fumbles_lost','fumbles'),
      ('passing_pick_sixes','passing_interceptions'),('passing_touchdowns','passing_completions'),
      ('rushing_touchdowns','rushing_attempts'),('receiving_touchdowns','receptions'),
      ('passing_touchdowns_40_plus','passing_touchdowns'),('passing_touchdowns_50_plus','passing_touchdowns_40_plus'),
      ('rushing_touchdowns_40_plus','rushing_touchdowns'),('rushing_touchdowns_50_plus','rushing_touchdowns_40_plus'),
      ('receiving_touchdowns_40_plus','receiving_touchdowns'),('receiving_touchdowns_50_plus','receiving_touchdowns_40_plus')]:le(a,b)
    for total,children in [('idp_tackles_total',['idp_tackles_solo','idp_tackles_assisted']),
                          ('kicker_fgm_50p',['kicker_fgm_50_59','kicker_fgm_60p']),
                          ('kicker_field_goal_attempts',['kicker_fgm','kicker_fgmiss']),
                          ('kicker_extra_point_attempts',['kicker_xpm','kicker_xpmiss'])]:
        if not np.allclose(samples[total],sum(samples[c] for c in children),atol=1e-9,rtol=0):raise ValueError('COMPONENT_ACCOUNTING:'+total)
    if np.any(samples['prob_pass_yd_300']+samples['prob_pass_yd_400']>1):raise ValueError('COMPONENT_STACKED_GAME_BONUS')
    if position=='DEF' and not bye:
        keys=[k for k in samples if k.startswith('dst_prob_pts_allow_')]
        if not np.allclose(sum(samples[k] for k in keys),1,rtol=0,atol=1e-9):raise ValueError('COMPONENT_DST_BUCKETS_NOT_EXHAUSTIVE')
    if bye and any(np.any(v!=0) for v in samples.values()):raise ValueError('COMPONENT_BYE_NOT_ZERO')
    return True
