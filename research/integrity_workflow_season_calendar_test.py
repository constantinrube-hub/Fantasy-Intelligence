#!/usr/bin/env python3
"""No-network calendar boundaries and reversible Actions transition scenarios."""
from copy import deepcopy
import json
from pathlib import Path
import unittest
import tempfile
from types import SimpleNamespace
from unittest.mock import patch
import workflow_calendar_control as control

from workflow_season_calendar import CONFIG, ROOT, decide
from workflow_calendar_control import CONTROLLER, REPOSITORY, apply, make_receipt, operation_for, validate_receipt

CALENDAR = json.loads(CONFIG.read_text())
WRAPPERS = {
    'build-fie-current': 'current_refresh',
    'build-fie-window1c-weekly-actions': 'weekly_actions',
    'build-fie-window1d-optimal-waiver': 'optimal_waiver',
    'build-fie-window2a-trench-evidence': 'trench',
    'capture-fie-pr2-weekly-lineups': 'weekly_lineups',
    'evaluate-fie-pr2-weekly-lineups': 'weekly_lineup_outcomes',
    'capture-fie-availability': 'availability',
    'capture-fie-m10-prospective': 'm10',
    'capture-fie-market': 'weekly_benchmark',
    'capture-fie-season-market': 'season_market',
    'capture-fie-waiver-evidence': 'waivers',
    'capture-fie-weather-evidence': 'weather',
}

class FakeGitHub:
    repository = REPOSITORY
    def __init__(self):
        self.rows = [
            {'id': 1, 'path': '.github/workflows/capture.yml', 'state': 'active'},
            {'id': 2, 'path': '.github/workflows/old.yml', 'state': 'disabled_manually'},
            {'id': 3, 'path': '.github/workflows/manual.yml', 'state': 'active'},
            {'id': 4, 'path': CONTROLLER, 'state': 'active'},
        ]
        self.runs = [
            {'id': 10, 'workflow_id': 1, 'event': 'schedule'},
            {'id': 11, 'workflow_id': 3, 'event': 'workflow_dispatch'},
            {'id': 12, 'workflow_id': 1, 'event': 'push'},
            {'id': 13, 'workflow_id': 4, 'event': 'schedule'},
        ]
        self.calls = []
        self.racing = False
    def workflows(self):
        return deepcopy(self.rows)
    def pages(self, endpoint, key):
        return deepcopy(self.runs)  # repeated statuses exercise deduplication
    def request(self, method, path):
        self.calls.append((method, path))
        if method == 'GET':
            if self.racing:
                self.runs = [row for row in self.runs if str(row['id']) != path.split('/')[-1]]
            return {'status': 'completed' if self.racing else 'in_progress'}
        if method == 'POST':
            if self.racing:
                raise RuntimeError('Completed while cancellation was requested')
            self.runs = [row for row in self.runs if str(row['id']) != path.split('/')[-2]]
            return None
        identity = int(path.split('/')[-2])
        next(row for row in self.rows if row['id'] == identity)['state'] = 'active' if path.endswith('/enable') else 'disabled_manually'

class CalendarTests(unittest.TestCase):
    def result(self, purpose, stamp, **kwargs):
        return decide(CALENDAR, purpose, stamp, **kwargs)
    def test_blackout_all_purposes_inclusive_local_dates(self):
        for purpose in CALENDAR['purposes']:
            for stamp in ('2027-01-11T23:00:00Z', '2027-03-01T08:00:00Z', '2027-04-25T21:59:59Z'):
                self.assertEqual(self.result(purpose, stamp)['reason'], 'GLOBAL_AUTOMATIC_BLACKOUT')
            self.assertNotEqual(self.result(purpose, '2027-04-25T22:00:00Z')['reason'], 'GLOBAL_AUTOMATIC_BLACKOUT')
    def test_availability_january_season_and_september(self):
        self.assertTrue(self.result('availability', '2027-01-10T22:59:59Z')['allowed'])
        self.assertEqual(self.result('availability', '2027-01-10T22:59:59Z')['season'], 2026)
        self.assertFalse(self.result('availability', '2027-01-10T23:00:00Z')['allowed'])
        self.assertFalse(self.result('availability', '2026-08-31T21:59:59Z')['allowed'])
        self.assertTrue(self.result('availability', '2026-08-31T22:00:00Z')['allowed'])
    def test_post_draft_uses_actual_final_day_in_eastern(self):
        self.assertFalse(self.result('season_market', '2027-04-26T12:00:00Z')['allowed'])
        self.assertFalse(self.result('season_market', '2027-05-02T03:59:59Z')['allowed'])
        self.assertTrue(self.result('season_market', '2027-05-02T04:00:00Z')['allowed'])
        self.assertFalse(self.result('season_market', '2027-01-05T12:00:00Z')['allowed'])
        self.assertFalse(self.result('season_market', '2027-10-01T12:00:00Z')['allowed'])
        self.assertEqual(self.result('season_market', '2028-05-02T12:00:00Z')['reason'], 'DRAFT_DATE_UNKNOWN')
    def test_warmup_exactly_seven_days_and_future_fail_closed(self):
        for purpose in ('current_refresh', 'm10', 'weekly_benchmark', 'weather'):
            self.assertFalse(self.result(purpose, '2026-09-03T00:19:59Z')['allowed'])
            self.assertEqual(self.result(purpose, '2026-09-03T00:20:00Z')['mode'], 'WARMUP')
            self.assertEqual(self.result(purpose, '2026-09-10T00:20:00Z')['mode'], 'SEASON')
            self.assertEqual(self.result(purpose, '2027-09-03T00:20:00Z')['reason'], 'FIRST_KICKOFF_UNKNOWN')
        for purpose in ('trench', 'weekly_actions', 'weekly_lineups', 'weekly_lineup_outcomes', 'optimal_waiver'):
            self.assertFalse(self.result(purpose, '2026-09-03T00:20:00Z')['allowed'])
    def test_january_closeout_and_preseason_waiver_scope(self):
        self.assertTrue(self.result('weather', '2027-01-11T18:00:00Z')['allowed'])
        self.assertEqual(self.result('weather', '2027-01-11T18:00:00Z')['season'], 2026)
        self.assertEqual(self.result('weather', '2028-01-11T18:00:00Z')['reason'], 'FIRST_KICKOFF_UNKNOWN')
        self.assertEqual(self.result('waivers', '2027-06-01T12:00:00Z')['reason'], 'PRESEASON_DYNASTY_SCOPE_PENDING')
    def test_explicit_manual_and_invalid_context(self):
        self.assertTrue(self.result('weather', '2027-03-01T00:00:00Z', event='workflow_dispatch')['allowed'])
        self.assertFalse(self.result('weather', '2026-10-03T00:00:00Z', ref='refs/heads/other')['allowed'])
        with self.assertRaises(ValueError):
            self.result('unknown', '2026-10-03T00:00:00Z')
        with self.assertRaises(ValueError):
            self.result('weather', '2026-10-03T00:00:00')
    def test_operational_wrapper_gates_and_controller_dates(self):
        self.assertEqual(set(WRAPPERS.values()), set(CALENDAR['purposes']))
        for wrapper, purpose in WRAPPERS.items():
            text = (ROOT / '.github/workflows' / (wrapper + '.yml')).read_text()
            self.assertIn('uses: ./.github/workflows/_fie-calendar-policy.yml', text)
            self.assertIn('purpose: ' + purpose, text)
            self.assertIn('needs: calendar', text)
            self.assertIn("if: needs.calendar.outputs.allowed == 'true' && github.ref == 'refs/heads/main'", text)
        text = (ROOT / CONTROLLER).read_text()
        self.assertIn("cron: '17 20 11 1 *'", text)
        self.assertIn("cron: '17 8 26 4 *'", text)
        self.assertEqual(text.count('cron:'), 2)
        self.assertEqual(text.count('timezone: Europe/Berlin'), 2)
        self.assertIn('actions: write', text)
        self.assertLess(text.index('git push origin HEAD:main'), text.index('--stage apply'))
        self.assertIn('subprocess.run', (ROOT / 'research/workflow_calendar_control.py').read_text())

class ControllerTests(unittest.TestCase):
    def setUp(self):
        self.client = FakeGitHub()
        self.receipt = make_receipt(self.client.workflows(), REPOSITORY, '2027-01-11T19:17:00Z', dry_run=False)
    def test_pause_resume_preserves_disabled_and_manual_runs(self):
        result = apply(self.client, self.receipt, 'pause', '2027-01-11T19:17:00Z')
        self.assertEqual(result['workflow_changes'], 2)
        self.assertEqual(result['automatic_runs_cancelled'], 2)
        self.assertNotIn(('POST', '/actions/runs/11/cancel'), self.client.calls)
        self.assertNotIn(('POST', '/actions/runs/13/cancel'), self.client.calls)
        self.assertEqual(apply(self.client, self.receipt, 'pause', '2027-01-11T19:20:00Z')['workflow_changes'], 0)
        self.assertEqual(apply(self.client, self.receipt, 'resume', '2027-04-26T06:17:00Z')['workflow_changes'], 2)
        self.assertEqual(self.client.rows[1]['state'], 'disabled_manually')
        self.assertEqual(apply(self.client, self.receipt, 'resume', '2027-04-26T06:20:00Z')['workflow_changes'], 0)
    def test_time_restrictions_and_read_only_plans(self):
        with self.assertRaises(ValueError):
            apply(self.client, self.receipt, 'pause', '2026-10-03T00:00:00Z')
        with self.assertRaises(ValueError):
            apply(self.client, self.receipt, 'resume', '2027-04-25T12:00:00Z')
        dry = deepcopy(self.receipt); dry['dry_run'] = True
        with self.assertRaises(ValueError):
            apply(self.client, dry, 'pause', '2027-01-11T19:17:00Z')
        self.assertEqual(self.client.calls, [])
        self.assertEqual(operation_for('2027-01-11T19:17:00Z', 'auto'), 'pause')
        self.assertEqual(operation_for('2027-04-26T06:17:00Z', 'auto'), 'resume')
    def test_workflow_identity_and_unplanned_work_fail_before_mutation(self):
        self.client.rows[0]['path'] = '.github/workflows/replaced.yml'
        with self.assertRaises(ValueError):
            apply(self.client, self.receipt, 'pause', '2027-01-11T19:17:00Z')
        self.assertEqual(self.client.calls, [])
        self.client = FakeGitHub()
        self.client.rows.append({'id': 5, 'path': '.github/workflows/new.yml', 'state': 'active'})
        with self.assertRaises(ValueError):
            apply(self.client, self.receipt, 'pause', '2027-01-11T19:17:00Z')
        self.assertEqual(self.client.calls, [])
    def test_receipt_identity_duplicate_and_controller_errors(self):
        for field, value in (('repository', 'wrong/repo'), ('cycle_year', 2026)):
            receipt = deepcopy(self.receipt); receipt[field] = value
            with self.assertRaises(ValueError):
                validate_receipt(receipt, REPOSITORY, 2027)
        receipt = deepcopy(self.receipt); receipt['workflows'].append(receipt['workflows'][0])
        with self.assertRaises(ValueError):
            validate_receipt(receipt, REPOSITORY, 2027)
        self.client.rows[-1]['state'] = 'disabled_manually'
        with self.assertRaises(ValueError):
            make_receipt(self.client.workflows(), REPOSITORY, '2027-01-11T19:17:00Z', dry_run=False)
    def test_receipt_must_already_match_published_main(self):
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder)
            state = root / 'data/pause.json'
            state.parent.mkdir(); state.write_bytes(b'published receipt')
            with patch.object(control, 'ROOT', root), patch.object(control.subprocess, 'run', return_value=SimpleNamespace(stdout=b'published receipt')) as git:
                control.verify_published_receipt(state)
                self.assertEqual(git.call_args.args[0], ['git', 'show', 'origin/main:data/pause.json'])
            with patch.object(control, 'ROOT', root), patch.object(control.subprocess, 'run', return_value=SimpleNamespace(stdout=b'other receipt')):
                with self.assertRaises(ValueError):
                    control.verify_published_receipt(state)
        self.assertEqual(self.client.calls, [])
    def test_pause_is_not_verified_while_automatic_work_remains(self):
        original = self.client.request
        def delayed(method, path):
            if method == 'POST':
                self.client.calls.append((method, path))
                return None
            return original(method, path)
        with patch.object(self.client, 'request', side_effect=delayed), patch.object(control.time, 'sleep'):
            with self.assertRaisesRegex(ValueError, 'not finished cancelling'):
                apply(self.client, self.receipt, 'pause', '2027-01-11T19:17:00Z')
    def test_cancellation_race_is_accepted_only_when_completed(self):
        self.client.racing = True
        result = apply(self.client, self.receipt, 'pause', '2027-01-11T19:17:00Z')
        self.assertEqual(result['automatic_runs_cancelled'], 0)
        self.assertIn(('GET', '/actions/runs/10'), self.client.calls)

if __name__ == '__main__':
    unittest.main()
