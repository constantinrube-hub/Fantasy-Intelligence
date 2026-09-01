#!/usr/bin/env python3
"""Permanent Tranche 2B primary-action responsive contract."""
from pathlib import Path
import re, subprocess, sys
ROOT=Path(__file__).resolve().parents[1]
css=(ROOT/'app/decision-ui.css').read_text(encoding='utf-8')
dist=(ROOT/'dist/app/decision-ui.css').read_text(encoding='utf-8')
assert css==dist, 'source/dist decision-ui.css mismatch'
assert '.fie93-table-card{overflow:auto}' in css, 'wide decision tables must remain horizontally accessible'
for bad in ('th:nth-child(n+9)','td:nth-child(n+9)','th:nth-child(n+7)','td:nth-child(n+7)'):
    assert bad not in css, f'generic ordinal hide rule remains: {bad}'
required=(
    ':has(th[data-fie93-sort="decision"])',
    ':has(th[data-fie93-sort="action"])',
    ':has(th[data-fie93-sort="faab"])',
    '#dstSummary .fie93-table th:last-child',
    '#kickerSummary .fie93-table th:last-child',
    '#dstDrawerWeeks .fie93-table th:nth-child(7)',
    '#kDrawerWeeks .fie93-table th:nth-child(7)',
    'display:table-cell!important;position:sticky;right:0',
)
missing=[x for x in required if x not in css]
assert not missing, f'missing primary-action visibility guards: {missing}'

ui=(ROOT/'app/decision-ui.js').read_text(encoding='utf-8')
def between(src,start,end):
    i=src.index(start); j=src.index(end,i); return src[i:j]
def keys(chunk): return re.findall(r"\{key:'([^']+)'",chunk)
ss=keys(between(ui,'function renderStartSit()','renderTable(\'startsit\''))
assert ss[-2:] == ['decision','posrank'], f'Start/Sit schema changed unexpectedly: {ss}'
wc=between(ui,'function renderWaivers()','function renderTargets()')
ws=[keys(x) for x in re.findall(r'schema=\[(.*?)\];',wc,re.S)]
assert len(ws)==3 and all(x[-2:]==['faab','action'] for x in ws), f'Waiver schema changed unexpectedly: {ws}'

for rel,entity,drawer in [
    ('app/dst-intelligence.js','D/ST','dstDrawerWeeks'),
    ('app/kicker-intelligence.js','Kicker','kDrawerWeeks'),
]:
    src=(ROOT/rel).read_text(encoding='utf-8')
    assert drawer in src, f'{entity} drawer identity missing'
    tables=re.findall(r'<thead><tr>(.*?)</tr></thead>',src,re.S)
    labels=[re.findall(r'<th>(.*?)</th>',t) for t in tables]
    action_positions=[x.index('Action')+1 for x in labels if 'Action' in x]
    assert sorted(action_positions)==[7,9], f'{entity} Action positions changed unexpectedly: {action_positions}'

subprocess.run([sys.executable,str(ROOT/'research/integrity_tranche1_responsive_decision_visibility.py'),'--mode','target'],check=True)
print('PASS Tranche 2B responsive primary-action contract')
