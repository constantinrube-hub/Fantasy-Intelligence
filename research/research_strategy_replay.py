"""D/ST and kicker hold/stream counterfactuals on frozen research universes."""
from strict_sleeper_baseline import finite


def replay(weeks,*,held_player_id,position,selected_hold_bottom_n=10):
    if position not in {'DST','K'} or not held_player_id or not 1<=selected_hold_bottom_n<=32:
        raise ValueError('STRATEGY_DESIGN_INVALID')
    results=[];seen=set()
    for week in weeks:
        key=(week['season'],week['week'],week['league_id'])
        if key in seen:
            raise ValueError('STRATEGY_DUPLICATE_WEEK')
        seen.add(key)
        if week.get('prospective_universe_bound') is not True or week.get('exact_scoring') is not True:
            results.append({'target':key,'status':'BLOCKED_UNIVERSE_OR_SCORING'})
            continue
        candidates=week.get('candidates') or []
        ids=[r.get('canonical_player_id') for r in candidates]
        if not all(ids) or len(set(ids))!=len(ids):
            raise ValueError('STRATEGY_IDENTITY_MISSING_OR_DUPLICATE')
        if any(finite(r.get('mean')) is None or finite(r.get('realized_points')) is None or
               r.get('position')!=position or not isinstance(r.get('available'),bool) or not isinstance(r.get('bye'),bool)
               for r in candidates):
            results.append({'target':key,'status':'BLOCKED_FORECAST_OR_OUTCOME'})
            continue
        by_id={r['canonical_player_id']:r for r in candidates}
        held=by_id.get(held_player_id)
        if held is None:
            results.append({'target':key,'status':'BLOCKED_HELD_PLAYER_NOT_CAPTURED'})
            continue
        pool=[r for r in candidates if not r['bye'] and (r['available'] or r['canonical_player_id']==held_player_id)]
        if not pool:
            results.append({'target':key,'status':'BLOCKED_NO_AVAILABLE_STREAMER'})
            continue
        best=min(pool,key=lambda r:(-float(r['mean']),r['canonical_player_id']))
        selections={'FULL_HOLD':best if held['bye'] else held,'FULL_STREAM':best}
        # Rank threshold requires a full frozen rank universe, including rostered
        # alternatives. Available-player rank is a different, biased question.
        ranks=week.get('league_position_rank') or {}
        complete=week.get('rank_universe_size')==32 and len(ranks)==32 and set(ranks.values())==set(range(1,33))
        if complete and held_player_id in ranks:
            selections['SELECTED_HOLD']=best if held['bye'] or ranks[held_player_id]>32-selected_hold_bottom_n else held
        results.append({'target':key,'status':'DESCRIPTIVE_STRATEGY_REPLAY',
            'selected_hold_status':'AVAILABLE' if 'SELECTED_HOLD' in selections else 'BLOCKED_FULL_RANK_UNIVERSE_MISSING',
            'strategies':{name:{'player_id':r['canonical_player_id'],'mean':float(r['mean']),
                         'realized_points':float(r['realized_points']),
                         'acquisition_required':r['canonical_player_id']!=held_player_id} for name,r in selections.items()},
            'waiver_opportunity_cost':None,'production_authorized':False})
    return results
