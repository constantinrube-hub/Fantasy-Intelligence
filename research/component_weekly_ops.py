"""Operational adapter for the sealed component recovery; no model changes.

All engine paths remain relative to the standalone project. New evidence is
append-only; scheduled selection uses the fresh NFL calendar, never week math.
"""
from __future__ import annotations
import argparse
import csv
import hashlib
import io
import json
import os
from pathlib import Path
import re
import subprocess
import sys
from datetime import datetime, time as dtime, timedelta, timezone
from urllib.request import Request, urlopen
from zoneinfo import ZoneInfo

REPO = Path(__file__).resolve().parents[1]
PROJECT_REL = Path('research/component-recovered-20261016')
PROJECT = REPO / PROJECT_REL
HISTORY = Path('data/research/components/operational-v1/2026')
REFERENCE = Path('data/research/components/recovery-20261016')
SCHEDULE_URL = 'https://raw.githubusercontent.com/nflverse/nfldata/master/data/games.csv'

def timestamp():
    return datetime.now(timezone.utc).isoformat()

def digest(path):
    h = hashlib.sha256()
    with Path(path).open('rb') as stream:
        for block in iter(lambda: stream.read(1048576), b''):
            h.update(block)
    return h.hexdigest()

def read(path):
    return json.loads(Path(path).read_text(encoding='utf-8'))

def write_new(path, value):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open('x', encoding='utf-8', newline='\n') as stream:
        json.dump(value, stream, indent=2, sort_keys=True, allow_nan=False)
        stream.write('\n')

def schedule_plan(records, as_of):
    """Only a contiguous completed season prefix can authorize a new issue."""
    groups = {}
    for row in records:
        if str(row.get('season')) != '2026' or row.get('game_type') != 'REG':
            continue
        week = int(row['week'])
        kick = datetime.fromisoformat(row['gameday'] + 'T' + row['gametime'])
        if kick.tzinfo is None:
            kick = kick.replace(tzinfo=ZoneInfo('America/New_York'))
        kick = kick.astimezone(timezone.utc)
        completed = all(str(row.get(k, '')).strip().lower() not in {'', 'nan', 'none'} for k in ['home_score', 'away_score']) and kick < as_of
        groups.setdefault(week, []).append((kick, completed))
    if not groups:
        raise ValueError('NO_2026_REGULAR_SEASON_CALENDAR')
    completed = 0
    for week in range(1, 19):
        if week not in groups or not all(final for _, final in groups[week]):
            break
        completed = week
    upcoming = next((w for w in sorted(groups) if min(k for k, _ in groups[w]) > as_of), None)
    start = upcoming if upcoming is not None and upcoming <= 16 and completed == upcoming - 1 and completed >= 5 else None
    return {'completed_through': completed, 'upcoming_week': upcoming, 'forecast_start': start,
            'reason': 'READY' if start else 'WAITING_FOR_COMPLETED_PRIOR_WEEK_OR_OUTSIDE_SUPPORTED_WINDOW'}

BERLIN = ZoneInfo('Europe/Berlin')
# Gate window (Berlin local time). Opens Tue 19:00: Monday-night snap counts were still missing
# from nflverse at 10:01 UTC on Tue 20 Oct and complete by 17:59 UTC, and a week is issued only
# once. Closes Thu 18:00, six hours after the last cron slot (11:35), because GitHub cron on
# this repo starts 1.5-4.5 h late; a late run that still issues before the Thursday session is
# better than a gate rejection.
WINDOW_OPEN = (1, 19)   # (weekday, hour): Tuesday 19:00
WINDOW_CLOSE = (3, 18)  # Thursday 18:00 (exclusive)
RECAPTURE_FROM = (2, 6)  # Wednesday 06:00: one stat-correction recapture after this


def in_window(local):
    """True from Tue 19:00 to Thu 18:00 Berlin (local is a Berlin-aware datetime)."""
    key = (local.weekday(), local.hour)
    return WINDOW_OPEN <= key < WINDOW_CLOSE


def calendar_due(as_of, event, ref, config):
    if event == 'schedule':
        if ref != 'refs/heads/main':
            return False
        local = as_of.astimezone(BERLIN)
        if local.year != 2026 and not (local.year == 2027 and local.month == 1):
            return False
        if not in_window(local):
            return False
        md = local.strftime('%m-%d')
        if config['blackout']['start'] <= md <= config['blackout']['end']:
            return False
        return local.month >= 9 or (local.month == 1 and md <= config['closeout_end'])
    return True


def _utc(value):
    return datetime.fromisoformat(str(value).replace('Z', '+00:00')).astimezone(timezone.utc)


def _week_anchor(as_of, weekday, hour):
    """The Berlin datetime of (weekday, hour) in the Tuesday-anchored week containing as_of."""
    local = as_of.astimezone(BERLIN)
    tuesday = local.date() - timedelta(days=(local.weekday() - 1) % 7)
    day = tuesday + timedelta(days=(weekday - 1) % 7)
    return datetime.combine(day, dtime(hour, 0), BERLIN)


def check_work(as_of, plan, previous):
    """Early exit for scheduled runs inside the window. Returns (due, reason).

    previous: [(folder, receipt)] of sealed PASS runs, folder holding actual-week*/actual-receipt.json.
    Work this week is, in order: (1) issue the upcoming window once; (2) capture the completed
    week's outcomes at least once this week; (3) recapture them once from Wed 06:00 for stat
    corrections. Everything else is ALREADY_DONE and skips the heavy run.
    """
    start = plan.get('forecast_start')
    completed = plan.get('completed_through')
    if start is not None and not any(start in r.get('issued_start_weeks', []) for _, r in previous):
        return True, 'ISSUE_DUE'
    latest = None
    for folder, _ in previous:
        for path in Path(folder).glob('actual-week*/actual-receipt.json'):
            r = read(path)
            if r.get('week') == completed and r.get('built_at'):
                built = _utc(r['built_at'])
                latest = built if latest is None or built > latest else latest
    week_start = _week_anchor(as_of, 1, 0)
    recapture_from = _week_anchor(as_of, *RECAPTURE_FROM)
    if latest is None or latest < week_start:
        return True, 'OUTCOME_CAPTURE_DUE'
    if as_of < recapture_from:
        return False, 'ALREADY_DONE_UNTIL_RECAPTURE'
    if latest >= recapture_from:
        return False, 'ALREADY_DONE'
    return True, 'RECAPTURE_DUE'

def verify_run(folder):
    receipt = read(folder / 'run-receipt.json')
    for rel, expected in receipt['files'].items():
        path = folder / rel
        if Path(rel).is_absolute() or '..' in Path(rel).parts or path.is_symlink() or not path.is_file() or digest(path) != expected:
            raise ValueError('OPERATIONAL_HISTORY_DRIFT:' + str(path))
    actual = {p.relative_to(folder).as_posix() for p in folder.rglob('*') if p.is_file() and p.name != 'run-receipt.json'}
    if actual != set(receipt['files']):
        raise ValueError('OPERATIONAL_HISTORY_FILE_SET_DRIFT')
    return receipt

def prior_pass_runs(project):
    """Sealed, hash-verified PASS runs of the restored operational history."""
    base = Path(project) / HISTORY / 'runs'
    result = []
    for p in sorted(base.glob('*/run-receipt.json')):
        receipt = verify_run(p.parent)
        if receipt['status'] == 'PASS':
            result.append((p.parent, receipt))
    return result


def fetch_schedule():
    with urlopen(Request(SCHEDULE_URL, headers={'User-Agent': 'FIE-Component-Weekly/1'}), timeout=90) as response:
        return response.read()


class Runner:
    def __init__(self, project, run_id, mode, executor=None):
        if not re.fullmatch(r'[A-Za-z0-9_-]{1,90}', run_id):
            raise ValueError('UNSAFE_RUN_ID')
        self.project = Path(project)
        self.relative = HISTORY / 'runs' / run_id
        self.folder = self.project / self.relative
        self.mode = mode
        self.executor = executor
        self.commands = []
        self.receipt = {'schema': 'fie-component-weekly-run-v1', 'run_id': run_id, 'mode': mode,
                        'started_at': timestamp(), 'source_commit': os.getenv('GITHUB_SHA'),
                        'adapter_sha256': digest(Path(__file__)),
                        'research_only': True, 'forecast_accuracy_claimed': False, 'commands': self.commands}

    def command(self, script, *args):
        if script in {'component_diagnostics.py', 'component_challenger.py', 'component_refit_v3.py'}:
            command = [sys.executable, str(REPO / 'research' / script), '--project', str(self.project), *map(str, args)]
        else:
            command = [sys.executable, 'research/' + script, *map(str, args)]
        self.commands.append(command[1:])
        log = self.folder / 'logs' / ('%03d-%s.log' % (len(self.commands), script))
        log.parent.mkdir(parents=True, exist_ok=True)
        if self.executor:
            return self.executor(command, self.project)
        print('RUN', ' '.join(command[1:]), flush=True)
        with log.open('x', encoding='utf-8') as output:
            process = subprocess.Popen(command, cwd=self.project, stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
                                       text=True, encoding='utf-8', errors='replace')
            for line in process.stdout:
                print(line, end='', flush=True)
                output.write(line)
            code = process.wait()
        if code:
            raise RuntimeError('COMMAND_FAILED:%s:%s' % (script, code))

    def capture(self, label, start, actual=None):
        out = self.relative / label
        args = ['--output', out, '--start-week', start]
        if actual is not None:
            args += ['--actual-week', actual]
        self.command('recovery_capture.py', *args)
        bundle = out / 'observation-bundle.json'
        data = read(self.project / bundle)
        critical = {'schedule', 'players', 'ff_playerids', 'player_week', 'weekly_rosters', 'pbp', 'snaps', 'sleeper_players'}
        critical.update(str(lid) + '-' + role for lid in data['league_ids'] for role in ['profile', 'rosters'])
        if actual is not None:
            critical.add('sleeper_actual')
        if len(set(data['league_ids'])) != 23 or not critical <= {r['name'] for r in data['responses']}:
            raise ValueError('INCOMPLETE_CRITICAL_CAPTURE:' + label)
        return bundle

    def validate(self, out):
        self.command('recovery_validate.py', '--base', out)
        self.command('recovery_coverage.py', '--base', out)

    def diagnostics_seed(self):
        out = self.relative / 'diagnostics/parameters-baseline'
        self.command('component_diagnostics.py', 'snapshot', '--fit', REFERENCE / 'fit/source-refit-final.json',
                     '--entities', REFERENCE / 'verified/source-refit/entities.json', '--history', HISTORY, '--output', out)
        self.command('component_challenger.py', '--fit', REFERENCE / 'fit/source-refit-final.json',
                     '--training', REFERENCE / 'training/week05', '--output', self.relative / 'diagnostics/challenger-interface-baseline')
        self.receipt['diagnostics_version'] = 'DIAGNOSTICS_V1'
        self.receipt['challenger_training'] = 'DISABLED_INTERFACE_ONLY'

    def diagnostics_review(self, frozen, selected, label):
        self.command('component_diagnostics.py', 'review', '--freeze', frozen, '--actual', *selected,
                     '--output', self.relative / 'diagnostics/reviews' / label)

    def replay(self):
        out = self.relative / 'replay'
        self.command('recovery_pipeline.py', '--output', out, '--fitted', REFERENCE / 'fit/source-refit-final.json',
                     '--training-dir', REFERENCE / 'training/week05', '--start-week', 6, '--stage', 4, '--replay')
        self.validate(out)
        self.command('recovery_compare_replays.py', '--expected', REFERENCE / 'verified/source-refit', '--actual', out)
        self.receipt['replay_comparison'] = 'EXACT_REPLAY'
        self.diagnostics_seed()

    def fixture(self):
        actual = self.relative / 'actual-week05'
        training = self.relative / 'training-week05'
        self.command('recovery_outcomes.py', '--output', actual, '--week', 5, '--training-output', training)
        self.command('recovery_evaluate.py', 'review', '--freeze', REFERENCE / 'freeze', '--actual', actual,
                     '--output', self.relative / 'fixture-review')
        review = read(self.folder / 'fixture-review/review.json')
        actual_receipt = read(self.project / actual / 'actual-receipt.json')
        if actual_receipt['rows'] != 2411 or review['matched_component_values'] != 0 or review['status'] != 'WAITING_FOR_OUTCOMES':
            raise ValueError('WEEK5_MUST_NOT_MATCH_WEEK6_FORECAST')
        self.receipt['fixture'] = {'actual_rows': actual_receipt['rows'], 'future_review_status': review['status'],
                                   'training_revision': str(training)}
        self.diagnostics_seed()
        self.diagnostics_review(REFERENCE / 'freeze', [actual], 'week05-must-not-match-week06')

    def prior_runs(self):
        return prior_pass_runs(self.project)

    def weekly(self, mode, ablations=False, revise=False):
        self.diagnostics_seed()
        raw = fetch_schedule()
        (self.folder / 'planning-schedule.csv').write_bytes(raw)
        plan = schedule_plan(csv.DictReader(io.StringIO(raw.decode('utf-8-sig'))), datetime.now(timezone.utc))
        self.receipt['plan'] = plan
        previous = self.prior_runs()
        actuals = {}
        for folder, _ in previous:
            for path in folder.glob('actual-week*/actual-receipt.json'):
                r = read(path)
                if r['week'] not in actuals or r['built_at'] > actuals[r['week']][0]:
                    actuals[r['week']] = (r['built_at'], path.parent.relative_to(self.project))
        completed = plan['completed_through']
        # Initial target weeks are W6-8; retain subsequent completed revisions.
        needed = set(range(6, completed + 1)) - set(actuals)
        if completed >= 6:
            needed.add(completed)  # Wednesday retry also captures stat corrections.
        for week in sorted(needed):
            bundle = self.capture('outcome-observations-week%02d' % week, min(week + 1, 16), week)
            out = self.relative / ('actual-week%02d' % week)
            training = self.relative / ('training-week%02d' % week)
            self.command('recovery_outcomes.py', '--output', out, '--week', week, '--bundle', bundle, '--training-output', training)
            r = read(self.project / out / 'actual-receipt.json')
            actuals[week] = (r['built_at'], out)
        freezes = [REFERENCE / 'freeze', REFERENCE / 'ablation-freeze']
        for folder, _ in previous:
            p = folder / 'forecast-freeze/freeze-receipt.json'
            if p.is_file():
                freezes.append(p.parent.relative_to(self.project))
        for i, frozen in enumerate(freezes):
            weeks = read(self.project / frozen / 'freeze-receipt.json')['target_weeks']
            selected = [actuals[w][1] for w in weeks if w in actuals]
            self.command('recovery_evaluate.py', 'review', '--freeze', frozen, '--actual', *selected,
                         '--output', self.relative / 'reviews' / ('freeze-%03d' % i))
            self.diagnostics_review(frozen, selected, 'freeze-%03d' % i)
        self.receipt['reviewed_freezes'] = list(map(str, freezes))
        self.receipt['actual_revisions'] = {str(w): str(ref[1]) for w, ref in sorted(actuals.items())}
        if mode == 'review':
            return
        start = plan['forecast_start']
        issued = any(start in r.get('issued_start_weeks', []) for _, r in previous)
        if start is None or (issued and not revise):
            self.receipt['forecast_status'] = 'ALREADY_FROZEN' if issued else plan['reason']
            return
        training = REFERENCE / 'training/week05' if start == 6 else actuals[start - 1][1].parent / ('training-week%02d' % (start - 1))
        bundle = self.capture('forecast-observations', start)
        fitted = self.relative / 'fit/source-refit.json'
        self.command('component_refit_v3.py', '--output', fitted, '--bundle', bundle, '--training', training, '--through-week', start - 1)
        self.receipt['fresh_fit_version'] = 'SOURCE_PREWEEK_ROLE_REFIT_V3_OPPONENT_COLUMN'
        issuances = []
        for stage in range(5) if ablations else [4]:
            out = self.relative / ('stage%d' % stage)
            self.command('recovery_pipeline.py', '--output', out, '--bundle', bundle, '--fitted', fitted,
                         '--training-dir', training, '--start-week', start, '--stage', stage)
            self.validate(out)
            issuances.append(out)
        self.command('component_diagnostics.py', 'snapshot', '--fit', fitted,
                     '--entities', issuances[-1] / 'entities.json', '--history', HISTORY,
                     '--output', self.relative / 'diagnostics/parameters-fresh')
        self.command('component_challenger.py', '--fit', fitted, '--training', training,
                     '--output', self.relative / 'diagnostics/challenger-interface-fresh')
        basic = self.relative / 'baselines'
        self.command('recovery_comparators.py', '--output', basic, '--reference', issuances[-1])
        self.command('recovery_evaluate.py', 'freeze', '--issuance', *issuances, basic, '--output', self.relative / 'forecast-freeze')
        self.command('recovery_report.py', '--base', issuances[-1], '--output', self.relative / 'reports')
        # The sealed recovery report is a W6-8 explorer. Correct only this new
        # operational report's labels; never edit the frozen report or owner.
        report = self.folder / 'reports/FIE-Reconstructed-Forecast.html'
        html = report.read_text(encoding='utf-8')
        html = html.replace('<option>6</option><option>7</option><option>8</option>',
                            ''.join('<option>%d</option>' % w for w in range(start, start + 3)))
        html = html.replace('Retrospective W6–8 replay from frozen W1–5 sources.',
                            'Prospective weeks %d–%d from sources through week %d.' % (start, start + 2, start - 1))
        report.write_text(html, encoding='utf-8')
        self.receipt.update({'issued_start_weeks': [start], 'forecast_status': 'FROZEN', 'ablations': ablations})

    def run(self, ablations=False, revise=False):
        self.folder.mkdir(parents=True, exist_ok=False)
        code = 0
        try:
            if self.mode == 'replay':
                self.replay()
            elif self.mode == 'fixture':
                self.fixture()
            elif self.mode == 'diagnostics':
                self.diagnostics_seed()
                for i, frozen in enumerate([REFERENCE / 'freeze', REFERENCE / 'ablation-freeze']):
                    self.diagnostics_review(frozen, [], 'initial-freeze-%d' % i)
            else:
                self.weekly(self.mode, ablations, revise)
            self.receipt['status'] = 'PASS'
        except Exception as exc:
            self.receipt.update({'status': 'FAIL', 'error': str(exc)})
            code = 1
        self.receipt['completed_at'] = timestamp()
        self.receipt['files'] = {p.relative_to(self.folder).as_posix(): digest(p) for p in sorted(self.folder.rglob('*')) if p.is_file()}
        write_new(self.folder / 'run-receipt.json', self.receipt)
        print(json.dumps({k: v for k, v in self.receipt.items() if k not in {'files', 'commands'}}), flush=True)
        return code

def main():
    p = argparse.ArgumentParser()
    p.add_argument('--mode', choices=['replay', 'fixture', 'weekly', 'forecast', 'review', 'diagnostics'], default='replay')
    p.add_argument('--run-id', default=datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%SZ'))
    p.add_argument('--ablations', action='store_true')
    p.add_argument('--revise', action='store_true')
    p.add_argument('--check-due', action='store_true')
    p.add_argument('--check-work', action='store_true',
                   help='After a due calendar check and a history restore: skip scheduled runs with no work left')
    a = p.parse_args()
    if a.check_due:
        due = calendar_due(datetime.now(timezone.utc), os.getenv('GITHUB_EVENT_NAME', 'workflow_dispatch'),
                           os.getenv('GITHUB_REF', 'refs/heads/main'), read(REPO / 'config/workflow-season-calendar.json'))
        print('due=' + str(due).lower())
        print('reason=' + ('IN_WINDOW' if due else 'OUTSIDE_WINDOW_OR_CALENDAR'))
        return 0
    if a.check_work:
        if os.getenv('GITHUB_EVENT_NAME', 'workflow_dispatch') != 'schedule':
            due, reason = True, 'MANUAL_DISPATCH_ALWAYS_RUNS'
        else:
            as_of = datetime.now(timezone.utc)
            plan = schedule_plan(csv.DictReader(io.StringIO(fetch_schedule().decode('utf-8-sig'))), as_of)
            due, reason = check_work(as_of, plan, prior_pass_runs(PROJECT))
        print('due=' + str(due).lower())
        print('reason=' + reason)
        return 0
    if a.mode in {'weekly', 'forecast', 'review', 'diagnostics'} and os.getenv('GITHUB_ACTIONS') == 'true' and os.getenv('GITHUB_REF') != 'refs/heads/main':
        raise ValueError('LIVE_OPERATION_REQUIRES_MAIN')
    return Runner(PROJECT, a.run_id, a.mode).run(a.ablations, a.revise)

if __name__ == '__main__':
    raise SystemExit(main())

