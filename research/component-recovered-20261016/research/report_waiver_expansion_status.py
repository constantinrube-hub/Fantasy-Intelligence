"""Read frozen artifacts into a league-by-league research blocker report."""
from pathlib import Path
import json
from prospective_research_io import now, sha, gates
from archive_waiver_expansion_sources import BASE

ROOT=Path(__file__).resolve().parents[1]
def build(root=ROOT):
    lock_path=root/BASE/'model-lock.json';lock=json.loads(lock_path.read_text())
    registry=json.loads((root/'data/research/leagues/registry.json').read_text())['leagues']
    capture_path=root/'data/research/prospective/waiver-expanded/forecasts/2026/week_06/capture.json'
    capture=json.loads(capture_path.read_text()) if capture_path.is_file() else None
    rows=[]
    for p in lock['profiles']:
        units=[u for u in lock['units'] if u['scoring_signature']==p['scoring_signature']]
        forecasts=[r for r in (capture or {}).get('forecasts',[]) if r['scoring_signature']==p['scoring_signature']]
        for lid in p['league_ids']:
            rows.append({'league_id':lid,'league_name':registry[lid]['league_name'],'scoring_signature':p['scoring_signature'],
                'lifecycle':'ELIMINATED_RESEARCH_ONLY' if lid=='1400561646463672320' else 'ACTIVE_RESEARCH_ONLY',
                'complete_next3_targets_all_outcome_rows':p['complete_next3_targets'],'excluded_historical_outcomes':p['excluded_outcomes'],
                'position_results':[{ 'position':u['position'],'historical_research_signal':u['historical_research_signal'],
                    'research_signal_blockers':u['metrics']['research_signal_blockers'],
                    'equal_season_relative_mae_lift':u['metrics']['equal_season_relative_mae_lift']} for u in units],
                'captured_at':(capture or {}).get('captured_at'),'forecast_rows':sum(r['forecast_mean'] is not None for r in forecasts),
                'abstained_rows':sum(r['forecast_mean'] is None for r in forecasts),**gates(['BLOCKED_PROSPECTIVE_CONFIRMATION','BLOCKED_DECISION_DOMAIN','BLOCKED_PROMOTION_REVIEW'])})
    lid='1400388486179123200'
    rows.append({'league_id':lid,'league_name':registry[lid]['league_name'],'scoring_signature':registry[lid]['scoring_signature'],
        'lifecycle':'ELIMINATED_COLLECTION_ONLY','position_results':[],'captured_at':None,'forecast_rows':0,'abstained_rows':0,
        **gates(['ELIMINATED_RESEARCH_ONLY','NO_ADDITIONAL_MODEL_DECLARED'])})
    rows.sort(key=lambda r:r['league_name'])
    audit=json.loads((root/BASE/'sources/field-goal-return-audit.json').read_text())
    import pandas as pd
    scope=json.loads((root/BASE/'shared/scope.json').read_text())
    events=pd.read_csv(root/BASE/'shared/events.csv.gz',low_memory=False)
    counts=events.event_type.value_counts().to_dict()
    raw_counts=pd.Series([x['event_type'] for x in scope['raw_blockers']]).value_counts().to_dict()
    families=['kick_return_yards','punt_return_yards','fumble_recovery_td','reception_40','reception_td_40','reception_td_50']
    event_counts=[{'event_type':k,'attributed_ledger_rows':int(counts.get(k,0)),
        'unresolved_pbp_events':int(raw_counts.get(k,0)),
        'attributed_share_of_detected_events':counts.get(k,0)/(counts.get(k,0)+raw_counts.get(k,0))} for k in families]
    value={'schema':'fie-waiver-expanded-league-status-v1','generated_at':now(),'model_lock_sha256':sha(lock_path),
        'league_count':len(rows),'profile_count':len(lock['profiles']),'units':len(lock['units']),
        'historical_signal_units':sum(u['historical_research_signal'] for u in lock['units']),
        'capture_sha256':sha(capture_path) if capture else None,'field_goal_return_audit':audit,'scoped_event_counts':event_counts,
        'scoped_exclusion_records':len(scope['exclusions']),'leagues':rows,**gates(['BLOCKED_RESEARCH_ONLY'])}
    if len(rows)!=20:raise ValueError('EXPANSION_LEAGUE_UNIVERSE')
    return value

def markdown(v):
    lines=['# Remaining 20 leagues: evidence and blockers','',
        'These are the 20 leagues outside the original three-signature capture. Nineteen receive additional offensive research models; Ultimate ITN remains collection-only after elimination. Final Cut remains research-only after elimination. All production and decision eligibility remains false.','',
        'Historical signal means the unchanged nested historical method passes its declared checks. It does not mean approval for projections, rankings, recommendations or transactions. Reused historical holdouts are exploratory. A positive average improvement can coexist with a material regression in a history-coverage group.','',
        '| League | ID | QB | RB | WR | TE | Historical exclusions | Week 6 rows forecast / abstain | Lifecycle |',
        '|---|---|---|---|---|---|---:|---:|---|']
    for r in v['leagues']:
        positions={u['position']:('Signal' if u['historical_research_signal'] else 'Coverage regression') for u in r['position_results']}
        lines.append('| '+ ' | '.join([r['league_name'].replace('|','/'),r['league_id'],*[positions.get(p,'Not modeled') for p in ['QB','RB','WR','TE']],str(r.get('excluded_historical_outcomes','—')),f"{r['forecast_rows']} / {r['abstained_rows']}",r['lifecycle']])+' |')
    lines += ['', 'The exclusions count concerns historical player-week outcomes, not unique football events. Some exclusions cover both offensive game teams and unknown-team zero proofs. Scoring weights for return yards and long-play bonuses remain intact; only unverifiable observations retain null values.', '',
        'For each active league, the next steps are: (1) verify its exact cutoff profile and capture rows; (2) observe the complete Weeks 6–8 outcome horizon; (3) compare model and baseline on the same admissible cohort; (4) verify uncertainty calibration and cutoff free-agent/legal-roster evidence; (5) complete a separate promotion review. Positions marked Coverage regression additionally need a separately preregistered correction and fresh confirmation, rather than another tuning pass over these holdouts.', '',
        'Among Us additionally requires the explicit Week 2 roster base anchor and planned Week 6 bench-stage checks. Final Cut requires no active bid/lineup decision; retained data supports research. Ultimate ITN receives source collection for future-season research, without a 2026 active-decision model.', '',
        f"Field-goal returns: {v['field_goal_return_audit']['event_count']} unblocked missed-field-goal return candidates across the six archived training seasons, totaling {v['field_goal_return_audit']['description_yards']} yards in descriptions. This is a description audit, not a certified DST yardage ledger. Archived Sleeper nonzero fg_ret_yd observations occur on team IDs, not offensive player IDs. Offensive attribution is repaired; exact DST reconciliation remains open.", '',
        'Shared limits remain: 2019/2020 source conflicts; historical source publication times; unseen 2026 confirmation; calibrated uncertainty; decision-domain legality and availability; private Chopped bids and actual adoption; and per-product report certification. Seven report adapters cannot become certified advice merely because a workflow passes.', '']
    lines += ['## Return and bonus attribution counts','',
        '| Event family | Attributed ledger rows | Unresolved detected PBP events | Attributed share |',
        '|---|---:|---:|---:|']
    for r in v['scoped_event_counts']:
        lines.append(f"| {r['event_type']} | {r['attributed_ledger_rows']} | {r['unresolved_pbp_events']} | {100*r['attributed_share_of_detected_events']:.3f}% |")
    lines += ['',f"These are source-event attribution rates, not a forecastability estimate, a yardage-completeness guarantee, or a model accuracy rate. Additional return-total reconciliation failures are included in {v['scoped_exclusion_records']} scoped exclusion records, and the affected observations stay null. The full source replay checks those exclusions before model verification.",'']
    return '\n'.join(lines)

if __name__=='__main__':
    value=build();dest=ROOT/'docs/audits/WAIVER_EXPANSION_LEAGUE_STATUS_2026-10-14'
    dest.with_suffix('.json').write_text(json.dumps(value,indent=2,ensure_ascii=False,allow_nan=False)+'\n')
    dest.with_suffix('.md').write_text(markdown(value))
    print('LEAGUE_STATUS_WRITTEN',value['league_count'],value['historical_signal_units'])
