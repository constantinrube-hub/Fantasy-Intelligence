"""Replay local research source graph without downloads or evidence mutation."""
import argparse,json
from pathlib import Path
from prospective_research_io import clock,sha,verified,replay_response
from capture_week6_research_sources import validate_manifest
from capture_retrospective_auction_history import validate_receipt
from publish_weekly_research_view import validate as validate_view


def validate(root):
    base=root/'data/research/prospective';count=0;raw=0
    for path in sorted(base.rglob('*.json')):
        if not any(part in path.parts for part in ['weekly-sources','waiver-v2','waiver-expanded','auction-history','weekly-preparation','weekly-research-view','specialist-strategies']):continue
        value=json.loads(path.read_text())
        if not isinstance(value,dict):continue
        at=value.get('captured_at') or value.get('generated_at') or value.get('prepared_at') or value.get('completed_at') or value.get('observed_at')
        if at:clock(at)
        for k in ['activation_eligible','forecast_eligible','ranking_eligible','recommendation_eligible','transaction_eligible']:
            if k in value and value[k] is not False:raise ValueError('RESEARCH_GRAPH_AUTHORITY:'+str(path))
        if value.get('schema')=='fie-weekly-research-source-envelope-v1':validate_manifest(root,path);raw+=len(value['responses'])
        elif value.get('schema')=='fie-weekly-research-view-v1':validate_view(value,root)
        elif value.get('schema')=='fie-retrospective-auction-history-v1':
            for item in value['responses']:
                validate_receipt(root,item,value['season'],item['league_id'],item['round'],value['captured_at']);raw+=1
        def walk(x):
            if isinstance(x,dict):
                if all(k in x for k in ['path','sha256','observed_at']):
                    verified(root,x,at or x['observed_at'])
                    if 'raw_sha256' in x:replay_response(root,x,at or x['observed_at'])
                for child in x.values():walk(child)
            elif isinstance(x,list):
                for child in x:walk(child)
        walk(value);count+=1
    return {'status':'REPLAYED','json_artifacts':count,'raw_response_references':raw,'network_requests':0}


if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('--root',type=Path,default=Path(__file__).resolve().parents[1]);args=parser.parse_args()
    print(json.dumps(validate(args.root)))
