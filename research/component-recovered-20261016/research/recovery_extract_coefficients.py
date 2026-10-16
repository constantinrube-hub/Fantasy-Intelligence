from html.parser import HTMLParser
from pathlib import Path
import json,re,html
class Tables(HTMLParser):
    def __init__(self): super().__init__(); self.tables=[]; self.table=None; self.row=None; self.cell=None
    def handle_starttag(self,t,a):
        if t=='table': self.table=[]
        elif t=='tr': self.row=[]
        elif t in ('td','th'): self.cell=[]
    def handle_data(self,d):
        if self.cell is not None:self.cell.append(d)
    def handle_endtag(self,t):
        if t in ('td','th') and self.cell is not None:
            self.row.append(''.join(self.cell));self.cell=None
        elif t=='tr' and self.row is not None:
            self.table.append(self.row);self.row=None
        elif t=='table':self.tables.append(self.table);self.table=None

def extract(reference_dir):
 r=Path(reference_dir)
 for short in ['Step2_Recovered_Completion','Step3_Receiving_Defense','Step4_WR_Hierarchy']:
    text=(r/('FIE_'+short+'_2026-10-15.html')).read_text().split('<script')[0]
    sections=[]
    for summary,body in re.findall(r'<details><summary>(.*?)</summary>(.*?)</details>',text,re.S):
        if 'defensive inputs' in summary or 'QB/RB evidence' in summary:
            p=Tables();p.feed(body);sections.append({'name':html.unescape(summary),'tables':p.tables})
    target=r/(short+'-sections.json')
    raw=json.dumps(sections,indent=2)
    if target.exists() and target.read_text()!=raw:raise ValueError('DEFENSIVE_COEFFICIENT_REFERENCE_DIFFERS')
    if not target.exists():target.write_text(raw)
    print(short,len(sections),'defense profiles')

if __name__=='__main__':
 import argparse
 p=argparse.ArgumentParser();p.add_argument('--reference-dir',type=Path,required=True);a=p.parse_args();extract(a.reference_dir)

