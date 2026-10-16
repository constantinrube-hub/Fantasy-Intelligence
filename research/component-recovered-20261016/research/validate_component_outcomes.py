"""Deterministic C0/C1 closure gate; never certifies a fitted forecast."""
from __future__ import annotations
import argparse
import json
from pathlib import Path
import subprocess
import sys

import numpy as np
import pandas as pd
from build_component_outcomes import BASE, KEYS, CALENDAR_EXCEPTIONS, verified
from component_registry import ROOT, digest, build

def validate(root,base,tests=True):
    root=root.resolve(); folder=root/base
    closure=json.loads((folder/'closure.json').read_text())
    if tests:
        for name in ['integrity_component_registry_test.py','integrity_component_outcomes_test.py']:
            subprocess.run([sys.executable,str(root/'research'/name)],check=True,cwd=root)
    for kind in ['artifacts','owners']:
        for path,expected in closure[kind].items():
            if digest(root/path)!=expected:
                raise ValueError('COMPONENT_CLOSURE_HASH_DRIFT:'+path)
    refs=json.loads((folder/'source-receipts.json').read_text())
    for ref in refs['sources']:
        verified(root,ref)
    if digest(root/refs['current_envelope_path'])!=refs['current_envelope_sha256']:
        raise ValueError('COMPONENT_ENVELOPE_DRIFT')
    if digest(root/refs['provider_capture_manifest_path'])!=refs['provider_capture_manifest_sha256']:
        raise ValueError('COMPONENT_CAPTURE_MANIFEST_DRIFT')
    demand=json.loads((folder/'demand.json').read_text()); current=build(root)
    if demand['leagues']!=current['leagues'] or demand['rules']!=current['rules']:
        raise ValueError('COMPONENT_PROFILE_OR_APPLICABILITY_DRIFT')
    if not closure['c0_complete'] or not closure['c1_outcome_pipeline_complete']:
        raise ValueError('COMPONENT_PIPELINE_NOT_COMPLETE')
    if any(closure[k] for k in ['c1_all_score_targets_certified','model_fitted','forecast_issued',
                               'promotion_eligible','transaction_eligible']):
        raise ValueError('COMPONENT_C0_C1_UNAUTHORIZED_CERTIFICATION')
    coverage=pd.read_csv(folder/'coverage.csv.gz',low_memory=False)
    required={r['component']:r for r in demand['required_components']}
    total=0; usable=0; unknown=0; mismatches=0; known_components=set()
    for scope in closure['seasons']:
        year=scope['season']; frame=pd.read_csv(folder/f'component-week-{year}.csv.gz',low_memory=False)
        if frame.duplicated(KEYS).any() or frame[KEYS].isna().any().any():
            raise ValueError('COMPONENT_INVALID_CANONICAL_ROW_KEY')
        if not frame.season.eq(year).all() or not frame.week.between(1,scope['through_week']).all():
            raise ValueError('COMPONENT_TARGET_OR_POSTSEASON_LEAKAGE')
        if len(frame)!=scope['entity_week_rows']:
            raise ValueError('COMPONENT_POPULATION_DRIFT')
        if frame[frame.position_model.eq('DEF')].groupby('week').size().ne(32).any():
            raise ValueError('COMPONENT_INCOMPLETE_DST_CALENDAR')
        for component,spec in required.items():
            values=pd.to_numeric(frame[component],errors='coerce')
            statuses=frame[component+'__status']
            eligible=frame[component+'__score_target_eligible']
            invalid=statuses.eq('NOT_APPLICABLE')|statuses.str.startswith('UNKNOWN')
            if values[invalid].notna().any() or eligible[invalid].any():
                raise ValueError('COMPONENT_UNKNOWN_OR_INAPPLICABLE_HAS_VALUE:'+component)
            if (~np.isfinite(values[values.notna()])).any():
                raise ValueError('COMPONENT_NONFINITE_OUTCOME:'+component)
            if spec['unit']=='count' and values.dropna().lt(0).any():
                raise ValueError('COMPONENT_NEGATIVE_COUNT:'+component)
            if spec['mode']=='probability' and not values.dropna().isin([0,1]).all():
                raise ValueError('COMPONENT_NON_BINARY_OUTCOME_EVENT:'+component)
            byes=statuses.eq('PROVEN_ZERO_BYE')
            if values[byes].ne(0).any() or frame.loc[byes,'week_state'].ne('PROVEN_BYE').any():
                raise ValueError('COMPONENT_UNPROVEN_ZERO:'+component)
            conflicts=statuses.eq('OBSERVED_SOURCE_PROVIDER_MISMATCH')
            if eligible[conflicts].any():
                raise ValueError('COMPONENT_MISMATCH_ADMITTED_TO_SCORE_FIT:'+component)
            for season,week,club in CALENDAR_EXCEPTIONS:
                bad=frame.season.eq(season)&frame.week.eq(week)&frame.team.eq(club)
                if values[bad].notna().any():
                    raise ValueError('COMPONENT_CANCELLED_GAME_HAS_ORDINARY_ACTUALS')
            if values.notna().any():
                known_components.add(component)
            usable+=int(eligible.sum()); unknown+=int((statuses.ne('NOT_APPLICABLE')&values.isna()).sum())
            mismatches+=int(conflicts.sum())
            aggregate=coverage[coverage.season.eq(year)&coverage.component.eq(component)]
            if aggregate.known_rows.sum()!=values.notna().sum():
                raise ValueError('COMPONENT_COVERAGE_COUNT_DRIFT:'+component)
        # Exclusive labels cannot simultaneously occur; unlike long TD counters.
        cols=['prob_pass_yd_300','prob_pass_yd_400']
        if frame[cols].sum(axis=1,min_count=2).dropna().gt(1).any():
            raise ValueError('COMPONENT_GAME_BONUS_STACKED')
        pts=[c for c in frame if c.startswith('dst_prob_pts_allow_') and '__' not in c]
        summed=frame[pts].sum(axis=1,min_count=len(pts))
        completed=frame.position_model.eq('DEF')&frame.week_state.eq('COMPLETED_GAME')
        if summed[completed].dropna().ne(1).any():
            raise ValueError('COMPONENT_DST_POINTS_BUCKETS_NOT_EXCLUSIVE_EXHAUSTIVE')
        total+=len(frame)
    if known_components!=set(required):
        raise ValueError('COMPONENT_NO_KNOWN_OBSERVATIONS:'+','.join(sorted(set(required)-known_components)))
    return {'status':'C0_C1_SOURCE_MASK_GATE_PASSED','enabled_leagues':current['enabled_leagues'],
            'required_components':len(required),'known_required_components':len(known_components),
            'entity_week_rows':total,'score_target_eligible_cells':usable,
            'unknown_applicable_cells':unknown,'source_provider_mismatch_cells':mismatches,
            'all_score_targets_certified':False,'model_fitted':False,'forecast_issued':False}

def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--root',type=Path,default=ROOT)
    p.add_argument('--dataset',type=Path,default=BASE)
    p.add_argument('--report',type=Path)
    a=p.parse_args(); result=validate(a.root,a.dataset)
    if a.report:
        a.report.parent.mkdir(parents=True,exist_ok=True)
        a.report.write_text(json.dumps(result,indent=2,sort_keys=True)+'\n')
    print(json.dumps(result,sort_keys=True))

if __name__=='__main__':
    main()
