"""Operational regressions: timing, immutable history, failure, Git recovery."""
import csv
from datetime import datetime, timezone
import json
from pathlib import Path
import subprocess
import tempfile
import unittest
from unittest.mock import patch
from component_weekly_ops import Runner, HISTORY, calendar_due, check_work, digest, schedule_plan, verify_run, write_new
from component_weekly_history import PREFIX, BRANCH, merge_immutable, operation

CONFIG = {'blackout': {'start': '01-12', 'end': '04-25'}, 'closeout_end': '01-11'}
def at(value):
    return datetime.fromisoformat(value).astimezone(timezone.utc)

def game(week, day, final=True):
    return {'season': '2026', 'game_type': 'REG', 'week': str(week), 'gameday': day,
            'gametime': '20:15', 'home_score': '20' if final else '', 'away_score': '17' if final else ''}

def seal(base, run_id='test', content='hello'):
    folder = base / 'runs' / run_id
    folder.mkdir(parents=True)
    (folder / 'evidence.txt').write_text(content)
    write_new(folder / 'run-receipt.json', {'status': 'PASS', 'files': {'evidence.txt': digest(folder / 'evidence.txt')}})
    return folder

class TimingTests(unittest.TestCase):
    def test_game_started_does_not_become_new_pregame_issue(self):
        rows = [game(w, '2026-09-%02d' % (w + 1)) for w in range(1, 6)]
        rows += [game(6, '2026-10-15', False), game(7, '2026-10-22', False), game(8, '2026-10-29', False)]
        p = schedule_plan(rows, at('2026-10-16T10:00:00+00:00'))
        self.assertEqual(p['completed_through'], 5)
        self.assertIsNone(p['forecast_start'])

    def test_completed_prior_week_opens_next_window(self):
        rows = [game(w, '2026-09-%02d' % (w + 1)) for w in range(1, 7)]
        rows += [game(7, '2026-10-22', False), game(8, '2026-10-29', False)]
        self.assertEqual(schedule_plan(rows, at('2026-10-20T07:00:00+00:00'))['forecast_start'], 7)

    def test_completed_weeks_cannot_skip_a_gap(self):
        rows = [game(1, '2026-09-01'), game(2, '2026-09-02', False), game(3, '2026-09-03')]
        self.assertEqual(schedule_plan(rows, at('2026-10-20T07:00:00+00:00'))['completed_through'], 1)

    def test_flexible_start_time_uses_eastern_not_utc(self):
        rows = [game(w, '2026-09-%02d' % (w + 1)) for w in range(1, 6)] + [game(6, '2026-10-15', False)]
        self.assertEqual(schedule_plan(rows, at('2026-10-16T00:00:00+00:00'))['forecast_start'], 6)
        self.assertIsNone(schedule_plan(rows, at('2026-10-16T00:16:00+00:00'))['forecast_start'])

    def test_short_late_season_window_never_issued(self):
        rows = [game(w, '2026-09-%02d' % (w + 1)) for w in range(1, 17)] + [game(17, '2026-12-30', False)]
        self.assertIsNone(schedule_plan(rows, at('2026-12-28T10:00:00+00:00'))['forecast_start'])

    def test_summer_and_winter_berlin_window(self):
        # Window: Tue 19:00 - Thu 18:00 Berlin. 20 Oct is CEST (UTC+2), 3 Nov is CET (UTC+1).
        inside = ['2026-10-20T17:00:00+00:00',  # Tue 19:00 CEST, first admitted minute
                  '2026-11-03T18:00:00+00:00',  # Tue 19:00 CET
                  '2026-11-04T09:35:00+00:00',  # Wed
                  '2026-11-05T16:59:00+00:00',  # Thu 17:59 CET, a 5 h late 11:35 slot
                  '2027-01-05T18:35:00+00:00']  # January closeout, Tue 19:35 CET
        outside = ['2026-10-20T16:59:00+00:00',  # Tue 18:59 CEST
                   '2026-10-20T05:35:00+00:00',  # the old Tue 07:35 slot
                   '2026-11-03T17:59:00+00:00',  # Tue 18:59 CET
                   '2026-11-05T17:00:00+00:00',  # Thu 18:00 CET, closed
                   '2026-11-06T09:35:00+00:00',  # Fri
                   '2026-11-02T20:00:00+00:00']  # Mon
        for value in inside:
            self.assertTrue(calendar_due(at(value), 'schedule', 'refs/heads/main', CONFIG), value)
        for value in outside:
            self.assertFalse(calendar_due(at(value), 'schedule', 'refs/heads/main', CONFIG), value)

    def test_blackout_research_branch_and_other_season_blocked(self):
        for value, ref in [('2026-02-03T18:35:00+00:00', 'refs/heads/main'),
                           ('2026-10-20T17:35:00+00:00', 'refs/heads/research/x'),
                           ('2027-10-19T17:35:00+00:00', 'refs/heads/main'),
                           ('2027-01-12T18:35:00+00:00', 'refs/heads/main')]:
            self.assertFalse(calendar_due(at(value), 'schedule', ref, CONFIG))

    def test_manual_dispatch_is_never_gated(self):
        self.assertTrue(calendar_due(at('2026-11-06T09:35:00+00:00'), 'workflow_dispatch', 'refs/heads/main', CONFIG))


class WorkCheckTests(unittest.TestCase):
    """--check-work: issue once, capture outcomes once, recapture once from Wed 06:00 Berlin."""
    PLAN = {'completed_through': 8, 'forecast_start': 9, 'upcoming_week': 9}

    def runs(self, base, specs):
        out = []
        for i, (issued, built) in enumerate(specs):
            folder = Path(base) / ('run%d' % i)
            folder.mkdir(parents=True)
            if built:
                write_new(folder / 'actual-week08/actual-receipt.json', {'week': 8, 'built_at': built})
            out.append((folder, {'status': 'PASS', 'issued_start_weeks': issued}))
        return out

    def check(self, now, specs, plan=None):
        with tempfile.TemporaryDirectory() as d:
            return check_work(at(now), plan or self.PLAN, self.runs(d, specs))

    def test_issue_due_until_upcoming_week_frozen(self):
        self.assertEqual(self.check('2026-11-03T18:35:00+00:00', []), (True, 'ISSUE_DUE'))
        self.assertEqual(self.check('2026-11-03T18:35:00+00:00', [([8], '2026-10-27T18:40:00+00:00')]), (True, 'ISSUE_DUE'))

    def test_issued_tuesday_skips_until_wednesday_recapture(self):
        done = [([9], '2026-11-03T18:40:00+00:00')]  # manual run Tue 19:40 CET
        self.assertEqual(self.check('2026-11-03T20:35:00+00:00', done), (False, 'ALREADY_DONE_UNTIL_RECAPTURE'))
        self.assertEqual(self.check('2026-11-04T04:59:00+00:00', done), (False, 'ALREADY_DONE_UNTIL_RECAPTURE'))
        self.assertEqual(self.check('2026-11-04T05:00:00+00:00', done), (True, 'RECAPTURE_DUE'))  # Wed 06:00 CET

    def test_recaptured_wednesday_is_done(self):
        done = [([9], '2026-11-03T18:40:00+00:00'), ([], '2026-11-04T07:50:00+00:00')]
        self.assertEqual(self.check('2026-11-04T09:35:00+00:00', done), (False, 'ALREADY_DONE'))
        self.assertEqual(self.check('2026-11-05T10:35:00+00:00', done), (False, 'ALREADY_DONE'))

    def test_last_weeks_outcomes_do_not_count(self):
        # Issued for week 9 but outcomes of week 8 not captured this week (e.g. a manual run on
        # Monday): the Tuesday window must still capture them.
        stale = [([9], '2026-11-02T20:00:00+00:00')]
        self.assertEqual(self.check('2026-11-03T18:35:00+00:00', stale), (True, 'OUTCOME_CAPTURE_DUE'))

    def test_nothing_to_issue_still_captures_and_recaptures_outcomes(self):
        late = {'completed_through': 16, 'forecast_start': None, 'upcoming_week': 17}
        with tempfile.TemporaryDirectory() as d:
            base = Path(d)
            def mk(name, built):
                f = base / name; f.mkdir()
                write_new(f / 'actual-week16/actual-receipt.json', {'week': 16, 'built_at': built})
                return (f, {'status': 'PASS'})
            self.assertEqual(check_work(at('2026-12-29T18:35:00+00:00'), late, []), (True, 'OUTCOME_CAPTURE_DUE'))
            first = [mk('a', '2026-12-29T18:50:00+00:00')]
            self.assertEqual(check_work(at('2026-12-29T20:35:00+00:00'), late, first), (False, 'ALREADY_DONE_UNTIL_RECAPTURE'))
            self.assertEqual(check_work(at('2026-12-30T06:35:00+00:00'), late, first), (True, 'RECAPTURE_DUE'))
            both = first + [mk('b', '2026-12-30T07:00:00+00:00')]
            self.assertEqual(check_work(at('2026-12-30T10:35:00+00:00'), late, both), (False, 'ALREADY_DONE'))

    def test_summer_time_recapture_boundary(self):
        done = [([7], '2026-10-20T17:40:00+00:00')]  # Tue 19:40 CEST, plan for week 7
        plan = {'completed_through': 6, 'forecast_start': 7, 'upcoming_week': 7}
        def mk(base):
            f = Path(base) / 'r'; f.mkdir()
            write_new(f / 'actual-week06/actual-receipt.json', {'week': 6, 'built_at': '2026-10-20T17:40:00+00:00'})
            return [(f, {'status': 'PASS', 'issued_start_weeks': [7]})]
        with tempfile.TemporaryDirectory() as d:
            prev = mk(d)
            self.assertEqual(check_work(at('2026-10-21T03:59:00+00:00'), plan, prev)[0], False)  # Wed 05:59 CEST
            self.assertEqual(check_work(at('2026-10-21T04:00:00+00:00'), plan, prev), (True, 'RECAPTURE_DUE'))

class EvidenceTests(unittest.TestCase):
    def test_failure_seals_receipt_without_success_claim(self):
        def fail(*args):
            raise RuntimeError('fixture failure')
        with tempfile.TemporaryDirectory() as temp:
            runner = Runner(Path(temp), 'failed', 'replay', fail)
            self.assertEqual(runner.run(), 1)
            self.assertEqual(verify_run(runner.folder)['status'], 'FAIL')
            self.assertNotIn('replay_comparison', runner.receipt)

    def test_existing_run_cannot_be_overwritten(self):
        with tempfile.TemporaryDirectory() as temp:
            runner = Runner(Path(temp), 'same', 'replay', lambda *a: None)
            runner.folder.mkdir(parents=True)
            with self.assertRaises(FileExistsError):
                runner.run()

    def test_unsafe_run_identifier_rejected(self):
        with self.assertRaises(ValueError):
            Runner(Path('.'), '../escape', 'replay')

    def test_replay_calls_generation_both_validators_and_comparison(self):
        commands = []
        with tempfile.TemporaryDirectory() as temp:
            runner = Runner(Path(temp), 'replay', 'replay', lambda c, cwd: commands.append(c))
            self.assertEqual(runner.run(), 0)
            self.assertEqual([Path(c[1]).name for c in commands], ['recovery_pipeline.py', 'recovery_validate.py', 'recovery_coverage.py', 'recovery_compare_replays.py', 'component_diagnostics.py', 'component_challenger.py'])
            self.assertIn('--replay', commands[0])

    def test_history_modification_and_extra_files_detected(self):
        with tempfile.TemporaryDirectory() as temp:
            folder = seal(Path(temp))
            verify_run(folder)
            (folder / 'evidence.txt').write_text('changed')
            with self.assertRaisesRegex(ValueError, 'DRIFT'):
                verify_run(folder)

    def test_extra_unmanifested_file_detected(self):
        with tempfile.TemporaryDirectory() as temp:
            folder = seal(Path(temp))
            (folder / 'extra').write_text('extra')
            with self.assertRaisesRegex(ValueError, 'FILE_SET'):
                verify_run(folder)

    def test_merge_is_idempotent_and_conflicting_bytes_rejected(self):
        with tempfile.TemporaryDirectory() as temp:
            a, b = Path(temp) / 'a', Path(temp) / 'b'
            seal(a)
            merge_immutable(a, b)
            merge_immutable(a, b)
            (b / 'runs/test/evidence.txt').write_text('conflict')
            with self.assertRaisesRegex(ValueError, 'COLLISION|DRIFT'):
                merge_immutable(a, b)

    def test_source_symlink_rejected(self):
        with tempfile.TemporaryDirectory() as temp:
            a, b = Path(temp) / 'a', Path(temp) / 'b'
            seal(a)
            with patch.object(Path, 'is_symlink', autospec=True,
                              side_effect=lambda path: path.name == 'evidence.txt'):
                with self.assertRaisesRegex(ValueError, 'SYMLINK'):
                    merge_immutable(a, b)

    def test_real_source_symlink_rejected_when_supported(self):
        with tempfile.TemporaryDirectory() as temp:
            a, b = Path(temp) / 'a', Path(temp) / 'b'
            folder = seal(a)
            try:
                (folder / 'link').symlink_to(folder / 'evidence.txt')
            except OSError as exc:
                if getattr(exc, 'winerror', None) == 1314:
                    self.skipTest('Windows account cannot create symlinks; rejection logic tested separately')
                raise
            with self.assertRaisesRegex(ValueError, 'SYMLINK'):
                merge_immutable(a, b)

    def test_forecast_runs_all_stages_before_freeze_and_updates_report_labels(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            runner = Runner(root, 'fresh', 'weekly')
            runner.folder.mkdir(parents=True)
            def fake_command(script, *args):
                runner.commands.append([script, *map(str, args)])
                if script == 'recovery_report.py':
                    path = root / Path(args[args.index('--output') + 1]) / 'FIE-Reconstructed-Forecast.html'
                    path.parent.mkdir(parents=True)
                    path.write_text('<option>6</option><option>7</option><option>8</option> Retrospective W6–8 replay from frozen W1–5 sources.', encoding="utf-8")
            runner.command = fake_command
            runner.capture = lambda *args: Path('observations/bundle.json')
            runner.prior_runs = lambda: []
            schedule = b'season,game_type,week,gameday,gametime,home_score,away_score\n2026,REG,1,2026-09-01,20:15,20,17\n'
            # Seed the original freeze contracts expected by the orchestrator.
            from component_weekly_ops import REFERENCE
            for name in ['freeze', 'ablation-freeze']:
                write_new(root / REFERENCE / name / 'freeze-receipt.json', {'target_weeks': [6, 7, 8]})
            class Response:
                def __enter__(self): return self
                def __exit__(self, *args): pass
                def read(self): return schedule
            # An existing completed W6 training revision supports a W7 issue.
            prior = root / HISTORY / 'runs/old'
            write_new(prior / 'actual-week06/actual-receipt.json', {'week': 6, 'built_at': '2026-10-20'})
            runner.prior_runs = lambda: [(prior, {'status': 'PASS'})]
            # The latest completed week is refreshed; fake its new actual receipt.
            base_command = runner.command
            def actual_command(script, *args):
                base_command(script, *args)
                if script == 'recovery_outcomes.py':
                    path = root / Path(args[args.index('--output') + 1]) / 'actual-receipt.json'
                    write_new(path, {'week': 6, 'built_at': '2026-10-21'})
            runner.command = actual_command
            with patch('component_weekly_ops.urlopen', return_value=Response()), patch('component_weekly_ops.schedule_plan', return_value={'completed_through': 6, 'forecast_start': 7, 'upcoming_week': 7}):
                runner.weekly('weekly', ablations=True)
            generation = [c for c in runner.commands if c[0] == 'recovery_pipeline.py']
            self.assertEqual([c[c.index('--stage') + 1] for c in generation], ['0', '1', '2', '3', '4'])
            self.assertEqual(len([c for c in runner.commands if c[0] == 'recovery_validate.py']), 5)
            self.assertEqual(len([c for c in runner.commands if c[0] == 'recovery_coverage.py']), 5)
            refits = [c for c in runner.commands if c[0] == 'component_refit_v3.py']
            self.assertEqual(len(refits), 1)
            self.assertIn('--training', refits[0])
            self.assertEqual(runner.receipt['fresh_fit_version'], 'SOURCE_PREWEEK_ROLE_REFIT_V3_OPPONENT_COLUMN')
            self.assertEqual(runner.receipt['issued_start_weeks'], [7])
            html = (runner.folder / 'reports/FIE-Reconstructed-Forecast.html').read_text(encoding="utf-8")
            self.assertIn('<option>9</option>', html)
            self.assertNotIn('Retrospective W6', html)

    def test_missing_critical_capture_never_reaches_fitting(self):
        with tempfile.TemporaryDirectory() as temp:
            runner = Runner(Path(temp), 'partial', 'weekly')
            def fake(script, *args):
                path = runner.project / Path(args[args.index('--output') + 1]) / 'observation-bundle.json'
                write_new(path, {'league_ids': list(range(23)), 'responses': []})
            runner.command = fake
            with self.assertRaisesRegex(ValueError, 'CRITICAL_CAPTURE'):
                runner.capture('observations', 7)

    def test_real_git_publication_restore_and_append(self):
        def command(*args):
            return subprocess.run(['git', *map(str, args)], check=True, capture_output=True, text=True).stdout
        with tempfile.TemporaryDirectory() as temp, patch.dict('os.environ', {'GITHUB_ACTIONS': 'false'}):
            d = Path(temp); remote = d / 'remote.git'; repo = d / 'repo'
            command('init', '--bare', remote)
            command('init', repo)
            command('-C', repo, 'config', 'user.email', 'test@example.test')
            command('-C', repo, 'config', 'user.name', 'Test')
            (repo / 'production.txt').write_text('preserve')
            command('-C', repo, 'add', '.')
            command('-C', repo, 'commit', '-m', 'base')
            command('-C', repo, 'remote', 'add', 'origin', remote)
            command('-C', repo, 'push', 'origin', 'HEAD:main')
            seal(repo / PREFIX, 'one')
            operation('publish', repo)
            command('-C', repo, 'clone', remote, d / 'restored')
            command('-C', d / 'restored', 'checkout', 'main')
            operation('restore', d / 'restored')
            verify_run(d / 'restored' / PREFIX / 'runs/one')
            seal(d / 'restored' / PREFIX, 'two')
            operation('publish', d / 'restored')
            files = command('--git-dir', remote, 'ls-tree', '-r', '--name-only', 'refs/heads/' + BRANCH)
            self.assertIn('runs/one/run-receipt.json', files)
            self.assertIn('runs/two/run-receipt.json', files)
            self.assertEqual(command('--git-dir', remote, 'show', 'refs/heads/main:production.txt').strip(), 'preserve')

if __name__ == '__main__':
    unittest.main()

