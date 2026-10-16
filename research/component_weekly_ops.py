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
from datetime import datetime, timezone
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

def calendar_due(as_of, event, ref, config):
    if event == 'schedule':
        if ref != 'refs/heads/main':
            return False
        local = as_of.astimezone(ZoneInfo('Europe/Berlin'))
        if local.year != 2026 and not (local.year == 2027 and local.month == 1):
            return False
        if local.weekday() not in {1, 2} or local.hour != 7:
            return False
        md = local.strftime('%m-%d')
        if config['blackout']['start'] <= md <= config['blackout']['end']:
            return False
        return local.month >= 9 or (local.month == 1 and md <= config['closeout_end'])
    return True

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

    def replay(self):
        out = self.relative / 'replay'
        self.command('recovery_pipeline.py', '--output', out, '--fitted', REFERENCE / 'fit/source-refit-final.json',
                     '--training-dir', REFERENCE / 'training/week05', '--start-week', 6, '--stage', 4, '--replay')
        self.validate(out)
        self.command('recovery_compare_replays.py', '--expected', REFERENCE / 'verified/source-refit', '--actual', out)
        self.receipt['replay_comparison'] = 'EXACT_REPLAY'

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

    def prior_runs(self):
        base = self.project / HISTORY / 'runs'
        result = []
        for p in sorted(base.glob('*/run-receipt.json')):
            receipt = verify_run(p.parent)
            if receipt['status'] == 'PASS':
                result.append((p.parent, receipt))
        return result

    def weekly(self, mode, ablations=False, revise=False):
        with urlopen(Request(SCHEDULE_URL, headers={'User-Agent': 'FIE-Component-Weekly/1'}), timeout=90) as response:
            raw = response.read()
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
        self.command('recovery_refit.py', '--output', fitted, '--bundle', bundle, '--training-dir', training, '--through-week', start - 1)
        issuances = []
        for stage in range(5) if ablations else [4]:
            out = self.relative / ('stage%d' % stage)
            self.command('recovery_pipeline.py', '--output', out, '--bundle', bundle, '--fitted', fitted,
                         '--training-dir', training, '--start-week', start, '--stage', stage)
            self.validate(out)
            issuances.append(out)
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
    p.add_argument('--mode', choices=['replay', 'fixture', 'weekly', 'forecast', 'review'], default='replay')
    p.add_argument('--run-id', default=datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%SZ'))
    p.add_argument('--ablations', action='store_true')
    p.add_argument('--revise', action='store_true')
    p.add_argument('--check-due', action='store_true')
    a = p.parse_args()
    if a.check_due:
        due = calendar_due(datetime.now(timezone.utc), os.getenv('GITHUB_EVENT_NAME', 'workflow_dispatch'),
                           os.getenv('GITHUB_REF', 'refs/heads/main'), read(REPO / 'config/workflow-season-calendar.json'))
        print('due=' + str(due).lower())
        return 0
    if a.mode in {'weekly', 'forecast', 'review'} and os.getenv('GITHUB_ACTIONS') == 'true' and os.getenv('GITHUB_REF') != 'refs/heads/main':
        raise ValueError('LIVE_OPERATION_REQUIRES_MAIN')
    return Runner(PROJECT, a.run_id, a.mode).run(a.ablations, a.revise)

if __name__ == '__main__':
    raise SystemExit(main())
