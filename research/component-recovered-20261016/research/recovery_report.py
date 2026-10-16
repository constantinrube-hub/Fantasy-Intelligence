"""Offline, filterable reconstructed forecast report and plain CSV exports."""
import argparse,csv,gzip,json,html,io
from pathlib import Path
from recovery_common import *
def build(base,output,root=ROOT):
    folder=root/base;m=read(folder/'issuance/capture-manifest.json');raw=list(rows(folder/'issuance/weekly-components.jsonl.gz'));scored=list(rows(folder/'issuance/weekly-league-scores.jsonl.gz'));keys=sorted({k for r in raw for k in {**r['means'],**r['event_probabilities']}})
    out=root/output;out.mkdir(parents=True,exist_ok=True)
    f=io.StringIO(newline='');names=['canonical_player_id','name','position_model','team','week','opponent']+keys;w=csv.DictWriter(f,fieldnames=names);w.writeheader()
    for r in raw:w.writerow({**{k:r.get(k) for k in names[:6]},**r['means'],**r['event_probabilities']})
    atomic_bytes(out/'weekly-components.csv.gz',gzip.compress(f.getvalue().encode(),mtime=0))
    f=io.StringIO(newline='');names=['league_id','canonical_player_id','name','position_model','week','mean','p10','p50','p90'];w=csv.DictWriter(f,fieldnames=names);w.writeheader()
    for r in scored:w.writerow({k:r.get(k) for k in names})
    atomic_bytes(out/'weekly-league-scores.csv.gz',gzip.compress(f.getvalue().encode(),mtime=0))
    payload={'rows':[[r['canonical_player_id'],r['name'],r['position_model'],r['team'],r['week'],r['opponent'],[({**r['means'],**r['event_probabilities']}).get(k) for k in keys]] for r in raw],'keys':keys,'scores':[[r['canonical_player_id'],r['week'],r['league_id'],r['mean'],r['p10'],r['p50'],r['p90']] for r in scored]}
    text='''<!doctype html><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>Recovered component forecast</title><style>body{font:15px/1.5 system-ui;margin:24px;background:#f4f6fa;color:#182534}main{max-width:1200px;margin:auto}table{border-collapse:collapse;width:100%;background:white}td,th{text-align:left;padding:8px;border-bottom:1px solid #dde3ed}select,input,button{padding:8px;margin:6px}.scroll{overflow:auto}.note{padding:16px;background:#fff0d6}</style><main><h1>Reconstructed component forecast</h1><p class="note">Retrospective W6–8 replay from frozen W1–5 sources. This reconstruction preserves the merged forecast separately. Original WR training code remains unavailable; the archived WR offensive TD prior uses a coarse-position source fallback. Read the comparison results before interpreting changes. Intervals are uncalibrated. Weather is not used.</p><label>Week <select id="week"><option>6</option><option>7</option><option>8</option></select></label><label>Team <select id="team"></select></label><label>Position <select id="pos"></select></label><label>Component <select id="component"></select></label><label>League <select id="league"></select></label><input id="search" placeholder="Player name"><button id="prev">Previous</button><button id="next">Next</button><p id="count"></p><div class="scroll" id="table"></div><p>Raw fractional expectations retain their exact values. Player quantiles must not be added to form a team percentile. Blank values indicate a component outside the entity's scope or no league score.</p></main>'''
    lock=read(folder/'pipeline-lock.json');bundle=read(root/lock['bundle_path']);payload['profiles']=[]
    for ref in bundle['responses']:
        if ref.get('role')=='profile':
            p=json.loads(gzip.decompress((root/ref['path']).read_bytes()));payload['profiles'].append([str(p['league_id']),p['name']])
    if lock['source_version'].startswith('SOURCE_'):text=text.replace('the archived WR offensive TD prior uses a coarse-position source fallback.','this model uses a separately versioned preweek source reconstruction for WR tiers and their TD rates.')
    text+='<script id="data" type="application/json">'+json.dumps(payload,separators=(',',':')).replace('</','<\\/')+'</script>'
    text+='''<script>
const D=JSON.parse(document.getElementById('data').textContent),el=x=>document.getElementById(x),esc=x=>String(x??'').replace(/[&<>"']/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c])),S=new Map(D.scores.map(r=>[r[0]+'|'+r[1]+'|'+r[2],r]));let page=0;
function options(id,vs){el(id).innerHTML=vs.map(x=>'<option>'+esc(x)+'</option>').join('')}
options('team',['ALL',...new Set(D.rows.map(r=>r[3]).filter(Boolean))].sort());options('pos',['ALL',...new Set(D.rows.map(r=>r[2]))]);options('component',D.keys);el('component').value='receiving_yards';el('league').innerHTML=D.profiles.map(p=>'<option value="'+esc(p[0])+'">'+esc(p[1])+'</option>').join('');
function render(){const rs=D.rows.filter(r=>r[4]===Number(el('week').value)&&(el('team').value==='ALL'||r[3]===el('team').value)&&(el('pos').value==='ALL'||r[2]===el('pos').value)&&r[1].toLowerCase().includes(el('search').value.toLowerCase()));page=Math.max(0,Math.min(page,Math.ceil(rs.length/50)-1));const col=D.keys.indexOf(el('component').value);el('count').textContent=rs.length+' entities; page '+(page+1)+'; component sum '+rs.reduce((v,r)=>v+(r[6][col]??0),0);const head=['Player','Position','Team','Opponent',el('component').value,'Fantasy mean','P10','P50','P90'];el('table').innerHTML='<table><tr>'+head.map(x=>'<th>'+esc(x)+'</th>').join('')+'</tr>'+rs.slice(page*50,page*50+50).map(r=>{const s=S.get(r[0]+'|'+r[4]+'|'+el('league').value);return '<tr>'+[r[1],r[2],r[3],r[5],r[6][col],...(s?s.slice(3):['','','',''])].map(x=>'<td>'+esc(x)+'</td>').join('')+'</tr>'}).join('')+'</table>'}
for(const id of ['week','team','pos','component','league'])el(id).addEventListener('change',()=>{page=0;render()});el('search').addEventListener('input',()=>{page=0;render()});el('next').onclick=()=>{page++;render()};el('prev').onclick=()=>{page--;render()};render();
</script>'''
    p=out/'FIE-Reconstructed-Forecast.html';atomic_bytes(p,text.encode());print('REPORT',p,len(text));return p
if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--base',type=Path,required=True);p.add_argument('--output',type=Path,required=True);a=p.parse_args();build(a.base,a.output)
