"""Restore/publish immutable weekly evidence on one dedicated research branch."""
from __future__ import annotations
import argparse
import os
from pathlib import Path
import shutil
import subprocess
import tempfile
from component_weekly_ops import REPO, PROJECT_REL, HISTORY, digest, verify_run

BRANCH = 'research/component-weekly-evidence-2026'
PREFIX = PROJECT_REL / HISTORY

def git(repo, *args, check=True):
    result = subprocess.run(['git', '-C', str(repo), *map(str, args)], text=True,
                            stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    if check and result.returncode:
        raise RuntimeError('GIT_FAILED:' + ' '.join(map(str, args)) + '\n' + result.stderr)
    return result

def validate_history(base):
    if not base.exists():
        return
    if any(p.is_symlink() for p in base.rglob('*')):
        raise ValueError('SYMLINK_IN_HISTORY')
    runs = base / 'runs'
    if any(p.name != 'runs' for p in base.iterdir()):
        raise ValueError('UNEXPECTED_HISTORY_PATH')
    for folder in runs.iterdir() if runs.exists() else []:
        if not folder.is_dir() or not (folder / 'run-receipt.json').is_file():
            raise ValueError('UNSEALED_OPERATIONAL_RUN:' + str(folder))
        verify_run(folder)

def merge_immutable(source, destination):
    validate_history(source)
    validate_history(destination)
    for path in sorted(source.rglob('*')) if source.exists() else []:
        if not path.is_file():
            continue
        target = destination / path.relative_to(source)
        if target.exists():
            if target.is_symlink() or digest(path) != digest(target):
                raise ValueError('IMMUTABLE_HISTORY_COLLISION:' + str(target))
        else:
            target.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(path, target)

def remote_head(repo):
    result = git(repo, 'ls-remote', '--exit-code', '--heads', 'origin', 'refs/heads/' + BRANCH, check=False)
    if result.returncode == 2:
        return None
    if result.returncode:
        raise RuntimeError('CANNOT_READ_EVIDENCE_REMOTE:' + result.stderr)
    git(repo, 'fetch', '--no-tags', 'origin', 'refs/heads/' + BRANCH)
    return git(repo, 'rev-parse', 'FETCH_HEAD').stdout.strip()

def operation(mode, repo=REPO):
    repo = Path(repo).resolve()
    if mode == 'publish' and os.getenv('GITHUB_ACTIONS') == 'true' and os.getenv('GITHUB_REF') != 'refs/heads/main':
        raise ValueError('LIVE_PUBLICATION_REQUIRES_MAIN')
    if mode == 'publish':
        validate_history(repo / PREFIX)
    for attempt in range(2):
        head = remote_head(repo)
        if mode == 'restore' and head is None:
            print('NO_PREVIOUS_OPERATIONAL_HISTORY')
            return
        base = head or git(repo, 'rev-parse', 'HEAD').stdout.strip()
        with tempfile.TemporaryDirectory(prefix='fie-evidence-') as temp:
            work = Path(temp) / 'worktree'
            git(repo, 'worktree', 'add', '--detach', '--no-checkout', work, base)
            try:
                # Do not duplicate the entire app/historical dataset on runners.
                git(work, 'sparse-checkout', 'init', '--no-cone')
                git(work, 'sparse-checkout', 'set', '--no-cone', '/' + PREFIX.as_posix() + '/',
                    '/.gitattributes', '/' + PROJECT_REL.as_posix() + '/.gitattributes')
                git(work, 'checkout', '--detach', base)
                if mode == 'restore':
                    merge_immutable(work / PREFIX, repo / PREFIX)
                    print('RESTORED_HISTORY', head)
                    return
                merge_immutable(repo / PREFIX, work / PREFIX)
                git(work, 'add', '--', PREFIX)
                changed = git(work, 'diff', '--cached', '--name-only').stdout.splitlines()
                if any(not path.startswith(PREFIX.as_posix() + '/') for path in changed):
                    raise ValueError('WRITE_OUTSIDE_EVIDENCE_ALLOWLIST')
                if not changed:
                    print('NO_NEW_HISTORY')
                    return
                git(work, '-c', 'user.name=FIE Component Evidence Bot', '-c', 'user.email=actions@users.noreply.github.com',
                    'commit', '-m', 'Archive immutable component forecast and evaluation evidence')
                new = git(work, 'rev-parse', 'HEAD').stdout.strip()
                result = git(work, 'push', 'origin', 'HEAD:refs/heads/' + BRANCH, check=False)
                if not result.returncode:
                    remote = git(work, 'ls-remote', '--heads', 'origin', 'refs/heads/' + BRANCH).stdout.split()[0]
                    if remote != new:
                        raise ValueError('PUBLISHED_HISTORY_HEAD_MISMATCH')
                    print('HISTORY_PUBLISHED', new)
                    return
                if attempt:
                    raise RuntimeError('HISTORY_PUSH_FAILED:' + result.stderr)
            finally:
                git(repo, 'worktree', 'remove', '--force', work)
    raise RuntimeError('HISTORY_PUBLICATION_NOT_COMPLETED')

if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('mode', choices=['restore', 'publish'])
    args = parser.parse_args()
    operation(args.mode)
