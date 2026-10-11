"""Conditional draft roster review over a supplied joint weekly bank."""
from statistics import mean
from joint_scenario_engine import distribution,validate_bank,lineup_score,ROOT
from weekly_lineup_decision_support import exact_lineup


def review(bank,state,*,root=ROOT):
    validate_bank(bank)
    if state.get('scoring_signature')!=bank['scoring_signature'] or state.get('constraints_known') is not True:
        return {'status':'BLOCKED_DRAFT_SCORING_OR_CONSTRAINTS','production_authorized':False}
    picked=state.get('picked_player_ids') or [];roster=state.get('user_roster_player_ids') or []
    if len(set(picked))!=len(picked) or len(set(roster))!=len(roster) or not set(roster)<=set(picked) or not set(picked)<=set(bank['players']):
        raise ValueError('DRAFT_PICK_OR_ROSTER_IDENTITY_INVALID')
    pool=sorted(set(bank['players'])-set(picked))
    slots=state.get('roster_positions') or []
    if not slots:raise ValueError('DRAFT_ROSTER_SLOTS_MISSING')
    def scores(ids):
        if not ids:return None
        legal=exact_lineup([{**bank['players'][p],'value':1} for p in ids],slots,value_key='value',root=root)
        if not legal['complete_assignment']:return None
        lineup={'mode':'BESTBALL_AUTOMATIC','player_ids':ids,'roster_positions':slots}
        return [lineup_score(lineup,bank,s,root) for s in bank['scenarios']]
    baseline=scores(roster);candidates=[]
    boards=state.get('future_board_scenarios') or []
    for board in boards:
        taken=board.get('taken_before_next_turn') or []
        if len(set(taken))!=len(taken) or not set(taken)<=set(pool):raise ValueError('DRAFT_FUTURE_BOARD_IDENTITY_INVALID')
    for pid in pool:
        values=scores([*roster,pid])
        candidates.append({'player_id':pid,'conditional_best_legal_roster_distribution':distribution(values) if values else None,
            'marginal_best_legal_roster_mean':mean(a-b for a,b in zip(values,baseline)) if baseline and values else None,
            'available_at_next_turn_given_supplied_boards':mean(pid not in b.get('taken_before_next_turn',[]) for b in boards) if boards else None,
            'missing_legal_roster_coverage':values is None})
    return {'schema':'fie-draft-scenario-review-v1','status':'RESEARCH_CONDITIONAL_ROSTER_REVIEW',
            'remaining_player_pool':pool,'candidates':candidates,
            'current_best_legal_roster_distribution':distribution(baseline) if baseline else None,
            'board_scenarios':len(boards),'pick_recommendation':None,'adp_owner_changed':False,'production_authorized':False,
            'note':'Best-legal roster outcomes assume automatic selection within each vector. This is not a fixed managed-lineup forecast or a validated draft-value policy.'}
