#!/usr/bin/env python3
"""Reversible repository-wide Actions pause, with a persisted original-state receipt.

The workflow publishes a plan before this module may mutate Actions state. No
workflow YAML is deleted. Previously disabled workflows are never re-enabled.
"""
from __future__ import annotations
import argparse
from datetime import datetime, timezone
import json
import os
import subprocess
import time
from pathlib import Path
from urllib.error import HTTPError
from urllib.request import Request, urlopen

from workflow_season_calendar import ROOT, parse_time
from zoneinfo import ZoneInfo

SCHEMA = 'fie-workflow-calendar-pause-v1'
CONTROLLER = '.github/workflows/control-fie-workflow-calendar.yml'
REPOSITORY = 'constantinrube-hub/Fantasy-Intelligence'

class GitHub:
    def __init__(self, repository: str, token: str | None):
        if repository != REPOSITORY:
            raise ValueError('Unexpected calendar-control repository')
        self.repository, self.token = repository, token

    def request(self, method: str, suffix: str):
        if not suffix.startswith('/actions/'):
            raise ValueError('Calendar API path outside Actions')
        headers = {'Accept': 'application/vnd.github+json', 'X-GitHub-Api-Version': '2022-11-28', 'User-Agent': 'FIE-Workflow-Calendar'}
        if self.token:
            headers['Authorization'] = 'Bearer ' + self.token
        if method != 'GET' and not self.token:
            raise ValueError('Actions write token required')
        request = Request('https://api.github.com/repos/' + self.repository + suffix, headers=headers, method=method)
        try:
            with urlopen(request, timeout=30) as response:
                body = response.read()
                return json.loads(body) if body else None
        except HTTPError as error:
            raise RuntimeError(f'GitHub Actions {method} {suffix}: HTTP {error.code}') from None

    def pages(self, endpoint: str, key: str):
        rows = []
        for page in range(1, 101):
            separator = '&' if '?' in endpoint else '?'
            payload = self.request('GET', endpoint + separator + f'per_page=100&page={page}')
            batch = payload[key]
            rows.extend(batch)
            if len(batch) < 100:
                return rows
        raise ValueError('Actions pagination limit exceeded')

    def workflows(self):
        return self.pages('/actions/workflows', 'workflows')


def operation_for(as_of: str, requested: str) -> str:
    local = parse_time(as_of).astimezone(ZoneInfo('Europe/Berlin'))
    md = local.strftime('%m-%d')
    if requested == 'auto':
        if md == '01-11':
            return 'pause'
        if md == '04-26':
            return 'resume'
        raise ValueError('Automatic transition is due only January 11 or April 26')
    if requested == 'pause' and not ('01-11' <= md <= '04-25'):
        raise ValueError('Pause is restricted to the January transition/blackout interval')
    if requested == 'resume' and md < '04-26':
        raise ValueError('Cannot resume workflows inside or before the blackout')
    return requested


def validate_receipt(receipt: dict, repository: str, cycle: int):
    if receipt.get('schema') != SCHEMA or receipt.get('repository') != repository or receipt.get('cycle_year') != cycle or receipt.get('controller_path') != CONTROLLER:
        raise ValueError('Pause receipt identity mismatch')
    rows = receipt['workflows']
    ids = [row['id'] for row in rows]
    if len(ids) != len(set(ids)) or any(not isinstance(value, int) or isinstance(value, bool) for value in ids):
        raise ValueError('Invalid or duplicate workflow IDs in pause receipt')
    if any(row['path'] == CONTROLLER or row['was_active'] != (row['original_state'] == 'active') for row in rows):
        raise ValueError('Invalid workflow restoration state')


def make_receipt(workflows: list[dict], repository: str, as_of: str, *, dry_run: bool):
    cycle = parse_time(as_of).astimezone(ZoneInfo('Europe/Berlin')).year
    controllers = [row for row in workflows if row['path'] == CONTROLLER and row['state'] == 'active']
    if not dry_run and len(controllers) != 1:
        raise ValueError('Calendar controller must be registered and active before pausing')
    receipt = {
        'schema': SCHEMA, 'repository': repository, 'cycle_year': cycle,
        'controller_path': CONTROLLER, 'planned_at': as_of, 'dry_run': dry_run,
        'workflows': [
            {'id': row['id'], 'path': row['path'], 'original_state': row['state'], 'was_active': row['state'] == 'active'}
            for row in sorted(workflows, key=lambda row: row['id']) if row['path'] != CONTROLLER
        ],
    }
    validate_receipt(receipt, repository, cycle)
    return receipt


def apply(client, receipt: dict, operation: str, as_of: str):
    if operation not in {'pause', 'resume'}:
        raise ValueError('Only pause/resume may mutate Actions state')
    operation_for(as_of, operation)
    cycle = parse_time(as_of).astimezone(ZoneInfo('Europe/Berlin')).year
    validate_receipt(receipt, client.repository, cycle)
    if receipt.get('dry_run') is not False:
        raise ValueError('A dry-run plan can never authorize mutation')
    current = {row['id']: row for row in client.workflows()}
    known = {row['id']: row for row in receipt['workflows']}
    controllers = [row for row in current.values() if row['path'] == CONTROLLER and row['state'] == 'active']
    if len(controllers) != 1:
        raise ValueError('Controller is missing or disabled')
    for key, row in known.items():
        if key not in current or current[key]['path'] != row['path']:
            raise ValueError('Workflow ID/path drift; review the saved pause receipt')
    unknown_active = [row for key, row in current.items() if key not in known and row['path'] != CONTROLLER and row['state'] == 'active']
    if unknown_active:
        raise ValueError('Unplanned active workflows appeared; update the pause plan before mutation')
    changes = 0
    for key, row in known.items():
        if operation == 'pause' and current[key]['state'] == 'active':
            client.request('PUT', f'/actions/workflows/{key}/disable'); changes += 1
        elif operation == 'resume' and row['was_active'] and current[key]['state'] != 'active':
            client.request('PUT', f'/actions/workflows/{key}/enable'); changes += 1
    cancelled = 0
    seen = set()
    if operation == 'pause':
        # Stop already queued/running automatic work; explicit manual work may
        # finish. The retained controller is excluded even when scheduled.
        for status in ('queued', 'in_progress', 'waiting', 'pending', 'requested'):
            for run in client.pages('/actions/runs?status=' + status, 'workflow_runs'):
                if run['workflow_id'] == controllers[0]['id'] or run.get('event') == 'workflow_dispatch':
                    continue
                if run['id'] in seen:
                    continue
                seen.add(run['id'])
                try:
                    client.request('POST', f"/actions/runs/{run['id']}/cancel")
                    cancelled += 1
                except RuntimeError:
                    latest = client.request('GET', f"/actions/runs/{run['id']}")
                    if latest.get('status') != 'completed':
                        raise
    if operation == 'pause':
        for attempt in range(10):
            remaining = []
            for status in ('queued', 'in_progress', 'waiting', 'pending', 'requested'):
                remaining.extend(run for run in client.pages('/actions/runs?status=' + status, 'workflow_runs')
                                 if run['workflow_id'] != controllers[0]['id'] and run.get('event') != 'workflow_dispatch')
            if not remaining:
                break
            if attempt == 9:
                raise ValueError('Automatic runs have not finished cancelling; repeat pause verification')
            time.sleep(2)
    verified = {row['id']: row for row in client.workflows()}
    if operation == 'pause' and any(row['state'] == 'active' and row['path'] != CONTROLLER for row in verified.values()):
        raise ValueError('Pause verification found an active repository workflow')
    for key, row in known.items():
        if key not in verified or verified[key]['path'] != row['path']:
            raise ValueError('Workflow identity changed during transition')
        if operation == 'pause' and verified[key]['state'] == 'active':
            raise ValueError('Pause verification failed')
        if operation == 'resume' and row['was_active'] and verified[key]['state'] != 'active':
            raise ValueError('Resume verification failed')
    return {'operation': operation, 'workflow_changes': changes, 'automatic_runs_cancelled': cancelled, 'verified': True}


def verify_published_receipt(state: Path):
    published = subprocess.run(['git', 'show', 'origin/main:' + state.relative_to(ROOT).as_posix()], cwd=ROOT, check=True, capture_output=True).stdout
    if published != state.read_bytes():
        raise ValueError('Pause receipt must match the published main receipt before mutation')


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--operation', choices=('auto', 'pause', 'resume', 'status'), default='status')
    parser.add_argument('--stage', choices=('plan', 'apply'), default='plan')
    parser.add_argument('--state-root', default='data/operations/workflow-calendar')
    parser.add_argument('--dry-run', action='store_true')
    parser.add_argument('--as-of')
    args = parser.parse_args()
    if args.as_of and not args.dry_run:
        raise ValueError('--as-of is permitted only for read-only dry runs')
    as_of = args.as_of or datetime.now(timezone.utc).isoformat()
    operation = operation_for(as_of, args.operation)
    client = GitHub(os.environ.get('GITHUB_REPOSITORY', REPOSITORY), os.environ.get('GH_TOKEN'))
    cycle = parse_time(as_of).astimezone(ZoneInfo('Europe/Berlin')).year
    state = ROOT / args.state_root / f'pause_{cycle}.json'
    if operation == 'status':
        rows = client.workflows()
        print(json.dumps({'operation': 'status', 'active': sum(row['state'] == 'active' for row in rows), 'total': len(rows), 'saved_receipt': state.exists()}, indent=2))
        return
    if state.exists():
        receipt = json.loads(state.read_text())
        validate_receipt(receipt, client.repository, cycle)
    elif args.stage == 'apply':
        raise ValueError('Apply requires a previously published pause receipt')
    elif operation == 'resume':
        raise ValueError('No saved pause receipt; refusing to enable workflows by guesswork')
    else:
        receipt = make_receipt(client.workflows(), client.repository, as_of, dry_run=args.dry_run)
        if not args.dry_run:
            state.parent.mkdir(parents=True, exist_ok=True)
            with state.open('x', encoding='utf-8', newline='\n') as handle:
                handle.write(json.dumps(receipt, indent=2) + '\n')
    if args.dry_run or args.stage == 'plan':
        print(json.dumps({'operation': operation, 'dry_run': args.dry_run, 'receipt': str(state.relative_to(ROOT)), 'workflow_count': len(receipt['workflows']), 'previously_active': sum(row['was_active'] for row in receipt['workflows'])}, indent=2))
        return
    if os.environ.get('GITHUB_REF') != 'refs/heads/main':
        raise ValueError('Actions mutation requires refs/heads/main')
    verify_published_receipt(state)
    print(json.dumps(apply(client, receipt, operation, as_of), indent=2))

if __name__ == '__main__':
    main()
