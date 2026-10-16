#!/usr/bin/env python3
from resolve_fie_position_models import _offense_decision
fail={'per_position':{'WR':{'status':'diagnostic_only','reason':'one_or_more_unchanged_head_to_head_or_standalone_safety_gates_not_cleared','football_model_promotion_review_ready':False,'all_v972_folds_exact_scoring_replay':True,'all_m9_folds_exact_scoring_replay':True}}}
x=_offense_decision('WR',fail,{},{});assert x['selected_production_model']=='M9';assert x['decision']!='PROMOTION_REVIEW_READY';assert x['current_challenger_projection_activated'] is False
ready={'per_position':{'WR':{'status':'promotion_review_ready','football_model_promotion_review_ready':True,'all_v972_folds_exact_scoring_replay':True,'all_m9_folds_exact_scoring_replay':True}}}
y=_offense_decision('WR',ready,{},{});assert y['decision']=='PROMOTION_REVIEW_READY';assert y['selected_production_model']=='M9';assert y['research_final_model']=='M9';assert y['current_challenger_projection_activated'] is False
qb={'per_position':{'QB':{'status':'promotion_review_ready','football_model_promotion_review_ready':True,'all_v972_folds_exact_scoring_replay':True,'all_m9_folds_exact_scoring_replay':True}}}
z=_offense_decision('QB',ready,qb,{});assert z['best_research_challenger']=='V9.7.5';assert z['selected_production_model']=='M9'
print('PASS model gate: promotion review never auto-activates challenger')
