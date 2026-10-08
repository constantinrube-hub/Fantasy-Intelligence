#!/usr/bin/env python3
import json,tempfile
from pathlib import Path
import roadmap_research_inventory as w


def main():
    root=Path(__file__).resolve().parents[1];report=w.inventory(root)
    assert len(report['experiments'])==9 and report['assessment']=='DECLARED_SOURCE_INVENTORY_ONLY'
    assert all(row['production_authorized'] is False for row in report['experiments'])
    with tempfile.TemporaryDirectory() as td:
        target=Path(td);(target/'config').mkdir();path=target/'config/roadmap-research-registry.json'
        original=json.loads((root/'config/roadmap-research-registry.json').read_text())
        for alter in ('promote','duplicate','escape'):
            data=json.loads(json.dumps(original))
            for item in data['experiments']:item['owner_module']=None
            if alter=='promote':data['experiments'][0]['production_authorized']=True
            if alter=='duplicate':data['experiments'].append(data['experiments'][0])
            if alter=='escape':data['experiments'][0]['owner_module']='../outside.py'
            path.write_text(json.dumps(data))
            try:w.inventory(target);raise AssertionError('Invalid registry accepted')
            except ValueError:pass
    print('PASS research source inventory: nine declared experiments, explicit missing owners, no promotion, duplicate/path/authority guards')

if __name__=='__main__':main()
