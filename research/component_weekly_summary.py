"""Truthful Actions summary; a green job alone is not a forecast receipt."""
import argparse
import json
from component_weekly_ops import PROJECT, HISTORY

def summary(run_id, due):
    if due != 'true':
        return 'Component workflow: **NO_OP — outside the scheduled Berlin/season window**.'
    path = PROJECT / HISTORY / 'runs' / run_id / 'run-receipt.json'
    if not path.is_file():
        return 'Component workflow: **BLOCKED — no sealed run receipt**.'
    r = json.loads(path.read_text())
    lines = ['Component workflow: **%s**' % r['status'], '',
             '- Run: `%s`' % run_id, '- Mode: `%s`' % r['mode'],
             '- Forecast: `%s`' % r.get('forecast_status', 'NOT_REQUESTED'),
             '- Evidence history: `research/component-weekly-evidence-2026`',
             '- Research only; no accuracy or promotion claim.']
    if 'error' in r:
        lines.append('- Error: `%s`' % r['error'].replace('`', ''))
    return '\n'.join(lines)

if __name__ == '__main__':
    p = argparse.ArgumentParser()
    p.add_argument('--run-id', required=True)
    p.add_argument('--due', default='false')
    a = p.parse_args()
    print(summary(a.run_id, a.due))
