"""Deterministic registry, public privacy and immutable input preservation."""
import sys,tempfile,hashlib
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'tools'))
from build_waiver_ui_evidence import build as waivers,read
from build_report_ui_evidence import build,DOCS
root=Path(__file__).resolve().parents[1]
paths=[root/p for p,_ in DOCS]+list((root/'data/research/portfolio').glob('*/research-completeness-inventory.json'))
before={str(p):hashlib.sha256(p.read_bytes()).hexdigest() for p in paths}
with tempfile.TemporaryDirectory() as tmp:
 d=Path(tmp);waivers(root,d,'personal');a=build(root,d,'personal');b=(d/'data/ui/reports/index.json').read_bytes();build(root,d,'personal');assert b==(d/'data/ui/reports/index.json').read_bytes()
 assert a['reporting_only'] and len(a['documents'])>=10 and a['inventories']
 for doc in a['documents']:
  x=read(d/doc['url']);assert x['source']==doc['source'];assert hashlib.sha256((root/x['source']['path']).read_bytes().replace(b'\r\n',b'\n')).hexdigest()==x['source']['sha256']
 waivers(root,d,'public');x=build(root,d,'public');assert not x['inventories'];assert not (d/'data/ui/reports/inventories').exists()
assert before=={str(p):hashlib.sha256(p.read_bytes()).hexdigest() for p in paths}
print('PASS report registry: deterministic source bindings, shared waiver URLs, public privacy, immutable inputs')
