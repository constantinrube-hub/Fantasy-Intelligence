"""Empirical rival-bid curves; no hidden manager model or bid recommendation."""
from statistics import mean
from strict_sleeper_baseline import finite
from weekly_evidence_audit import stamp


def curve(samples,*,league_id,currency,budget,bids,cutoff,tie_policy):
    if not league_id or currency!='FAAB' or isinstance(budget,bool) or not isinstance(budget,int) or budget<0:
        raise ValueError('BID_BUDGET_OR_SCOPE_INVALID')
    if tie_policy not in {'USER_WINS_TIE','USER_LOSES_TIE'}:
        raise ValueError('BID_TIE_POLICY_UNSUPPORTED')
    if not bids or len(set(bids))!=len(bids) or any(isinstance(b,bool) or not isinstance(b,int) or b<0 for b in bids):
        raise ValueError('BID_GRID_INVALID')
    eligible,excluded,seen=[],0,set()
    for sample in samples:
        identity=sample.get('auction_id')
        if not identity or identity in seen:
            raise ValueError('BID_AUCTION_ID_MISSING_OR_DUPLICATE')
        seen.add(identity)
        if sample.get('league_id')!=league_id or sample.get('currency')!=currency or stamp(sample['observed_at'])>stamp(cutoff):
            excluded+=1;continue
        if sample.get('complete_competing_bids') is not True:
            excluded+=1;continue
        rival=finite(sample.get('maximum_competing_bid'))
        if rival is None or rival!=int(rival) or rival<0:
            raise ValueError('BID_RIVAL_MAXIMUM_INVALID')
        eligible.append(rival)
    rows=[]
    for bid in sorted(bids):
        wins=[bid>r or (bid==r and tie_policy=='USER_WINS_TIE') for r in eligible]
        rows.append({'bid':bid,'within_budget':bid<=budget,
                     'empirical_acquisition_probability':mean(wins) if wins and bid<=budget else None,
                     'remaining_budget_if_acquired':budget-bid if bid<=budget else None})
    return {'schema':'fie-research-bid-curve-v1','status':'DESCRIPTIVE_CAPTURED_RIVAL_BIDS' if eligible else 'BLOCKED_COMPLETE_RIVAL_BIDS_MISSING',
            'league_id':league_id,'currency':currency,'budget':budget,'cutoff':cutoff,'tie_policy':tie_policy,
            'eligible_auctions':len(eligible),'excluded_auctions':excluded,'rows':rows,
            'survival_gain':None,'joint_market_field_model':False,'optimal_bid':None,'production_authorized':False,
            'note':'Historical sampled auction frequency is not a calibrated next-auction win probability. Winner-only bids are excluded.'}
