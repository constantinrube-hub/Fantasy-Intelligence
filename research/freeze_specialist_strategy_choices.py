"""Freeze source-bound midseason specialist counterfactuals before kickoff."""
from __future__ import annotations
import argparse
import json
from pathlib import Path
from prospective_research_io import binding, clock, gates, now, verified, write
from strict_sleeper_baseline import finite


def choose(board):
    candidates=board['candidates']
    held=[r for r in candidates if r['sleeper_id']==board.get('initial_hold_sleeper_id')]
    if len(held)!=1 or not held[0]['canonical_player_id']:
        return {'status':'BLOCKED_INITIAL_HOLD_IDENTITY','choices':{}}
    current=held[0]
    pool=[r for r in candidates if r['canonical_player_id'] and finite(r['mean']) is not None
          and r.get('bye') is False and (r.get('available') is True or r.get('held') is True)]
    if not pool:
        return {'status':'BLOCKED_AVAILABLE_FORECAST_UNIVERSE','choices':{}}
    best=min(pool,key=lambda r:(-float(r['mean']),r['canonical_player_id']))
    potential=[r for r in candidates if r.get('held') is True or r.get('available') is True]
    coverage={'catalog_candidates':len(candidates),'known_held_or_available':len(potential),'supported_nonbye_pool':len(pool),
              'unknown_availability':sum(r.get('available') is None and r.get('held') is not True for r in candidates),
              'unsupported_known_nonbye_alternatives':sum(r.get('bye') is not True and (not r.get('canonical_player_id') or finite(r.get('mean')) is None) for r in potential)}
    coverage['complete_available_pool']=coverage['unknown_availability']==0 and coverage['unsupported_known_nonbye_alternatives']==0
    choices={'FULL_STREAM':best}
    if current.get('bye') is True:
        choices['FULL_HOLD']=best
    elif current.get('bye') is False and finite(current['mean']) is not None:
        choices['FULL_HOLD']=current
    # Complete finite ranks are required; absent bye projections are not
    # imputed into the rank universe to force Selected Hold readiness.
    ranks=[r for r in candidates if r['canonical_player_id'] and finite(r['mean']) is not None]
    if board['position']=='DST' and len(ranks)==32 and len({r['team'] for r in ranks})==32:
        ordered=sorted(ranks,key=lambda r:(-float(r['mean']),r['canonical_player_id']))
        rank=next((i+1 for i,r in enumerate(ordered) if r['sleeper_id']==current['sleeper_id']),None)
        if rank is not None and 'FULL_HOLD' in choices:
            choices['SELECTED_HOLD']=best if current['bye'] or rank>22 else current
    return {'status':'FROZEN_RESEARCH_CHOICES','held_sleeper_id':current['sleeper_id'],
            'hold_basis':board['hold_basis'],'position':board['position'],
            'choices':{name:{'canonical_player_id':r['canonical_player_id'],'sleeper_id':r['sleeper_id'],
                            'mean':r['mean'],'acquisition_required':not r['held']} for name,r in choices.items()},
            'selected_hold_status':'AVAILABLE' if 'SELECTED_HOLD' in choices else 'BLOCKED_COMPLETE_RANK_OR_BYE_UNIVERSE',
            'candidate_coverage':coverage,'choice_scope':'BEST_WITHIN_SUPPORTED_OBSERVED_POOL',
            'globally_optimal_claim':False,'acquisition_cost':None,'roster_changes_executed':False,
            **gates(['BLOCKED_EXACT_OUTCOME_REQUIRED','BLOCKED_STRATEGY_VALIDATION_REQUIRED'])}


def freeze(root,evidence_path,first_kickoff):
    evidence=json.loads(evidence_path.read_text());at=now()
    if evidence.get('schema')!='fie-weekly-league-research-evidence-v1' or clock(at)>=clock(first_kickoff):
        raise ValueError('SPECIALIST_SOURCE_OR_PREGAME_WINDOW')
    verified(root,evidence['source_envelope'],at)
    created=0
    for league in evidence['leagues']:
        if 'specialists' not in league:continue
        for board in league['specialists']:
            path=root/f"data/research/prospective/specialist-strategies/{evidence['season']}/week_{evidence['week']:02d}/{league['league_id']}/{board['position']}/decision.json"
            if path.exists():continue
            decision=choose(board)
            if decision['status']!='FROZEN_RESEARCH_CHOICES':continue
            value={'schema':'fie-specialist-strategy-decision-v1','season':evidence['season'],'week':evidence['week'],
                   'league_id':league['league_id'],'captured_at':at,'first_kickoff':first_kickoff,
                   'evidence':binding(root,evidence_path,evidence.get('prepared_at',evidence['captured_at'])),**decision,
                   'note':'Same observed available universe, structural counterfactual only; not acquisition or season-long causal policy evaluation.'}
            write(path,value)
            created+=1
    return {'status':'RESEARCH_CHOICES_RECORDED' if created else 'NO_NEW_SUPPORTED_CHOICES','created':created}


def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--root',type=Path,default=Path(__file__).resolve().parents[1])
    p.add_argument('--evidence',type=Path,required=True);p.add_argument('--first-kickoff',required=True)
    a=p.parse_args();freeze(a.root,a.evidence,a.first_kickoff)


if __name__=='__main__':main()
