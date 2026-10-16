"""Prepare seven reports from existing owners without certifying templates."""
from __future__ import annotations
import argparse
import json
from pathlib import Path
from prospective_research_io import binding, clock, gates, now, write
from weekly_report_bundle import PRODUCTS, bundle


def preparation(root,season,week,as_of):
    config_path=root/'config/week6-evidence-preparation.json'
    config=json.loads(config_path.read_text())
    if not 2<=week<=18 or set(config['report_requirements'])!=set(PRODUCTS):
        raise ValueError('REPORT_PREPARATION_TARGET_OR_PRODUCTS')
    previous=bundle(root,season,week-1,clock(as_of))
    current=bundle(root,season,week,clock(as_of))
    products=[]
    for name in PRODUCTS:
        historical=name in {'PLAYER_PERFORMANCE','POST_WEEK_REVIEW'}
        selected=previous if historical else current
        owner=selected['products'][name]
        products.append({'name':name,'season':season,'source_week':week-1 if historical else week,
            'decision_week':week,'as_of_utc':as_of,'phase':'POST_COMPLETED_WEEK' if historical else 'PREGAME_TARGET_WEEK',
            'requirements':config['report_requirements'][name],
            'status':'OWNER_OUTPUT_AVAILABLE' if owner.get('content') else 'PREPARED_TEMPLATE',
            'complete':False,'owner_output':owner,
            'template':{'headline':name.replace('_',' ').title(),'coverage':None,
                        'findings':[],'actions':[],'blockers':owner.get('blockers',[]),
                        'source_details':selected['sources']},
            'note':'Template availability is not product certification. Render stored owner advice without inventing values.'})
    result={'schema':'fie-weekly-report-preparation-v1','season':season,'decision_week':week,
            'completed_week':week-1,'as_of_utc':as_of,'products':products,
            'complete_product_count':0,'requirements_contract':binding(root,config_path,as_of),
            **gates(['BLOCKED_PER_PRODUCT_VALIDATION_REQUIRED'])}
    validate(result)
    return result


def validate(value):
    if value.get('schema')!='fie-weekly-report-preparation-v1' or len(value.get('products',[]))!=7:
        raise ValueError('REPORT_PREPARATION_SCHEMA')
    if {p['name'] for p in value['products']}!=set(PRODUCTS) or value['complete_product_count']!=0:
        raise ValueError('REPORT_PREPARATION_PRODUCT_COUNT')
    for row in value['products']:
        expected=value['completed_week'] if row['name'] in {'PLAYER_PERFORMANCE','POST_WEEK_REVIEW'} else value['decision_week']
        if row['source_week']!=expected or row['complete'] is not False or not row['requirements']:
            raise ValueError('REPORT_TEMPLATE_FALSE_COMPLETENESS_OR_WEEK')
        if row['season']!=value['season'] or row['as_of_utc']!=value['as_of_utc']:
            raise ValueError('REPORT_TEMPLATE_CONTEXT_DRIFT')


def markdown(value):
    lines=[f"# Week {value['decision_week']} report preparation",'',
           f"Season {value['season']}; observed {value['as_of_utc']}. Previous-week outcomes and upcoming decisions retain separate targets.",'']
    for row in value['products']:
        lines.extend([f"## {row['template']['headline']} — source Week {row['source_week']}",'',
                      f"State: {row['status']}. Full product certification: pending.",'',
                      'Required evidence:','',*[f'- {r}' for r in row['requirements']],'',
                      'Existing owner output:','', '```json',json.dumps(row['owner_output'],indent=2,default=str),'```',''])
    return '\n'.join(lines)+'\n'


def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--root',type=Path,default=Path(__file__).resolve().parents[1])
    p.add_argument('--season',type=int,required=True);p.add_argument('--week',type=int,required=True);a=p.parse_args()
    at=now();value=preparation(a.root,a.season,a.week,at)
    destination=a.root/f"data/research/prospective/report-preparation/{a.season}/week_{a.week:02d}/{clock(at).strftime('%Y%m%dT%H%M%S%fZ')}"
    write(destination/'preparation.json',value)
    with (destination/'preparation.md').open('x',encoding='utf-8') as f:f.write(markdown(value))
    print(json.dumps({'status':'SEVEN_PRODUCTS_PREPARED','complete_product_count':0,'path':str(destination)}))


if __name__=='__main__':main()
