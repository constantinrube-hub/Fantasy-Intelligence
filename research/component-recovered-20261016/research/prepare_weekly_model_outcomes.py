"""Wire existing frozen M10 outcome/review owners, without fresh recaptures."""
import json
from prospective_research_io import clock,gates,now
from m10_prospective_capture_contract import capture_paths
from append_m10_real_outcomes import publish
from weekly_m10_outcome_review import review


def build(root,season,completed_week):
    at=clock(now());paths=capture_paths(root/'data/research/prospective/m10',season,completed_week)
    append={'status':'NOT_ATTEMPTED_ORIGINAL_CAPTURE_MISSING'}
    if paths['manifest'].is_file() and not (paths['outcome_dir']/'outcome-manifest.json').is_file():
        sources=[]
        for p in (root/f'data/operations/weekly-performance/{season}/week_{completed_week:02d}/sources').glob('*/source-envelope.json'):
            item=json.loads(p.read_text())
            if clock(item['observed_at'])<=at:sources.append((clock(item['observed_at']),p))
        if sources:
            try:
                value=publish(root,season,completed_week,max(sources,key=lambda r:(r[0],str(r[1])))[1],as_of=at)
                append={'status':value['status'],'coverage':value['coverage']}
            except (ValueError,KeyError,TypeError,OSError) as error:
                append={'status':'BLOCKED_EXISTING_OWNER_SOURCE','reason':str(error)}
        else:append={'status':'BLOCKED_ARCHIVED_WEEKLY_PERFORMANCE_SOURCE_MISSING'}
    elif (paths['outcome_dir']/'outcome-manifest.json').is_file():append={'status':'EXISTING_IMMUTABLE_OUTCOME'}
    result=review(root,season,completed_week,at)
    return {'schema':'fie-weekly-model-owner-wiring-v1','season':season,'completed_week':completed_week,'generated_at':at.isoformat(),
            'outcome_append':append,'m10_owner_review':result,
            'weekly_sleeper_comparison_owner':'PR2 paired_forecast_metrics; separate Sunday capture where valid',
            'waiver_baseline':'SAME_CUTOFF_FP_PRIOR_4','providers_fetched':False,
            **gates(['BLOCKED_UNIT_SPECIFIC_PAIRED_COVERAGE_AND_GOVERNED_REVIEW'])}
