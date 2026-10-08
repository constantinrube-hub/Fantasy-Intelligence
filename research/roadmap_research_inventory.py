#!/usr/bin/env python3
"""Hash existing P2 owners and preserve declared research/promotion boundaries.

This is source inventory, not statistical assessment or completeness scoring.
"""
import argparse,json
from pathlib import Path
from weekly_pipeline_readiness import digest


def inventory(root: Path) -> dict:
    path=root/'config/roadmap-research-registry.json';registry=json.loads(path.read_text(encoding='utf-8'))
    if registry.get('schema')!='fie-roadmap-research-registry-v1' or registry.get('automatic_promotion') is not False:
        raise ValueError('RESEARCH_REGISTRY_SCHEMA_OR_AUTHORITY_INVALID')
    rows=[];seen=set()
    for item in registry['experiments']:
        identity=item['research_id']
        if identity in seen:raise ValueError('RESEARCH_REGISTRY_DUPLICATE_ID')
        seen.add(identity)
        if item.get('production_authorized') is not False or item['status'] not in {'IDEA','FEASIBLE'}:
            raise ValueError('RESEARCH_REGISTRY_UNAPPROVED_STAGE')
        if not item.get('required_evidence') or not item.get('promotion_requirements'):
            raise ValueError('RESEARCH_REGISTRY_EVIDENCE_OR_GATES_MISSING')
        owner=item.get('owner_module');row={'research_id':identity,'declared_status':item['status'],
            'production_authorized':False,'historical_result':item.get('historical_result'),
            'prospective_result':item.get('prospective_result'),'next_action':'Complete the declared evidence and required design handoff before modeling.'}
        if owner:
            source=(root/owner).resolve()
            if not source.is_relative_to(root) or not source.is_file():raise ValueError('RESEARCH_OWNER_PATH_INVALID')
            row.update(owner_module=owner,owner_sha256=digest(source),owner_status='MODULE_PRESENT')
        else:row.update(owner_module=None,owner_status='DESIGN_AND_IMPLEMENTATION_REQUIRED')
        rows.append(row)
    return {'schema':'fie-roadmap-research-inventory-v1','registry_sha256':digest(path),
            'assessment':'DECLARED_SOURCE_INVENTORY_ONLY','experiments':rows,'automatic_promotion':False}


def main():
    parser=argparse.ArgumentParser();parser.add_argument('--root',default=str(Path(__file__).resolve().parents[1]));parser.add_argument('--output',type=Path,required=True);args=parser.parse_args()
    report=inventory(Path(args.root).resolve());args.output.parent.mkdir(parents=True,exist_ok=True)
    with args.output.open('x',encoding='utf-8') as stream:stream.write(json.dumps(report,indent=2,sort_keys=True)+'\n')
    print(f"Declared P2 source inventory: {len(report['experiments'])} experiments; no promotion authority.")

if __name__=='__main__':main()
