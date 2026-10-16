"""Independent readiness units; historical signal never promotes a live model."""
import json
from prospective_research_io import binding,gates,now,verified
from waiver_v2_prospective import validate_lock


def build(root,season,week,capture_path=None):
    lock_path=root/f'data/research/prospective/waiver-v2/locks/{season}/revision-1/model-lock.json'
    lock=validate_lock(root,lock_path);at=now();capture=None
    if capture_path and capture_path.is_file():
        capture=json.loads(capture_path.read_text())
        if capture.get('schema')!='fie-waiver-v2-prospective-capture-v1' or (capture['season'],capture['week'])!=(season,week):raise ValueError('READINESS_CAPTURE_CONTEXT')
        if any(capture.get(k) is not False for k in gates([]) if k.endswith('_eligible')):raise ValueError('READINESS_AUTHORITY')
        for ref in capture['bindings'].values():verified(root,ref,capture['captured_at'])
    units=[]
    for unit in lock['units']:
        rows=[r for r in (capture or {}).get('forecasts',[]) if (r['scoring_signature'],r['position'])==(unit['scoring_signature'],unit['position'])]
        units.append({'scoring_signature':unit['scoring_signature'],'position':unit['position'],
                      'historical_research_signal':unit['historical_research_signal'],'historical_only_model_frozen':unit['model'] is not None,
                      'cutoff_rows':len(rows),'forecast_rows':sum(r['forecast_mean'] is not None for r in rows),
                      'abstained_rows':sum(r['forecast_mean'] is None for r in rows),'live_parity':'BOUND_SHARED_OWNER' if rows else 'PENDING_SOURCE_VALID_CAPTURE',
                      'temporal_confirmation':'PENDING_UNSEEN_2026_FULL_HORIZONS','free_agent_decision_domain':'UNVERIFIED',
                      'actual_adoption':'UNKNOWN','calibration':'UNAVAILABLE',
                      **gates(['BLOCKED_PROSPECTIVE_CONFIRMATION','BLOCKED_DECISION_DOMAIN','BLOCKED_PROMOTION_REVIEW'])})
    return {'schema':'fie-research-readiness-ledger-v1','season':season,'week':week,'generated_at':at,'units':units,
            'model_lock':binding(root,lock_path,lock['frozen_at']),
            'capture':binding(root,capture_path,capture['captured_at']) if capture else None,
            'review_protocol':{'nonoverlapping_start_weeks':[6,9,12,15],'weekly_starts_overlap':True,
                              'unit':'same-season calendar three-week horizon','same_season_replaces_historical_holdouts':False,
                              'baseline':'SAME_CUTOFF_FP_PRIOR_4','sleeper_comparison':False},
            **gates(['BLOCKED_UNIT_SPECIFIC_EVIDENCE_AND_GOVERNED_REVIEW'])}
