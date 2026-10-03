#!/usr/bin/env python3
"""Shared date policy; never guesses an unknown future kickoff or draft date."""
from __future__ import annotations
import argparse
from datetime import date, datetime, time, timedelta, timezone
import json
from pathlib import Path
from zoneinfo import ZoneInfo

ROOT = Path(__file__).resolve().parents[1]
CONFIG = ROOT / 'config/workflow-season-calendar.json'

def parse_time(value: str) -> datetime:
    result = datetime.fromisoformat(value.replace('Z', '+00:00'))
    if result.tzinfo is None:
        raise ValueError('Calendar time must include a timezone')
    return result.astimezone(timezone.utc)

def decide(config: dict, purpose: str, as_of: str, *, event: str = 'schedule', ref: str = 'refs/heads/main') -> dict:
    if config.get('schema') != 'fie-workflow-season-calendar-v1' or purpose not in config['purposes']:
        raise ValueError('Unknown calendar contract or purpose')
    now = parse_time(as_of)
    local = now.astimezone(ZoneInfo(config['timezone']))
    md = local.strftime('%m-%d')
    season = local.year - 1 if local.month == 1 else local.year
    result = {'allowed': False, 'reason': '', 'mode': 'NO_DUE', 'season': season, 'as_of': now.isoformat(), 'local_date': local.date().isoformat()}
    def finish(allowed, reason, mode):
        return {**result, 'allowed': allowed, 'reason': reason, 'mode': mode}
    if event == 'workflow_dispatch':
        return finish(True, 'EXPLICIT_MANUAL_OPERATION', 'MANUAL')
    if ref != 'refs/heads/main':
        return finish(False, 'AUTOMATIC_OPERATION_REQUIRES_MAIN', 'NO_DUE')
    if config['blackout']['start'] <= md <= config['blackout']['end']:
        return finish(False, 'GLOBAL_AUTOMATIC_BLACKOUT', 'BLACKOUT')
    if purpose == 'availability':
        allowed = md >= config['availability']['start'] or md <= config['availability']['end']
        return finish(allowed, 'IN_AVAILABILITY_WINDOW' if allowed else 'OUTSIDE_AVAILABILITY_WINDOW', 'SEASON' if allowed else 'NO_DUE')
    if purpose == 'waivers':
        allowed = local.month >= 9 or (local.month == 1 and md <= config['closeout_end'])
        return finish(allowed, 'IN_WAIVER_SEASON' if allowed else 'PRESEASON_DYNASTY_SCOPE_PENDING', 'SEASON' if allowed else 'NO_DUE')
    dates = config['seasons'].get(str(season)) or {}
    if local.month == 1 and purpose != 'season_market':
        if not dates.get('first_kickoff_at'):
            return finish(False, 'FIRST_KICKOFF_UNKNOWN', 'NO_DUE')
        return finish(md <= config['closeout_end'], 'REGULAR_SEASON_CLOSEOUT' if md <= config['closeout_end'] else 'AFTER_CLOSEOUT', 'CLOSEOUT')
    if purpose == 'season_market':
        draft = dates.get('draft_last_day_eastern')
        if not draft:
            return finish(False, 'DRAFT_DATE_UNKNOWN', 'NO_DUE')
        # Wait until the entire officially scheduled last draft day has ended
        # in New York; a later announced date can be updated without code edits.
        after_draft = datetime.combine(date.fromisoformat(draft) + timedelta(days=1), time(), ZoneInfo('America/New_York'))
        allowed = now >= after_draft and 4 <= local.month <= 9
        return finish(allowed, 'POST_DRAFT_SEASON_MARKET' if allowed else 'OUTSIDE_SEASON_MARKET_WINDOW', 'POST_DRAFT' if allowed else 'NO_DUE')
    kickoff = dates.get('first_kickoff_at')
    if not kickoff:
        return finish(False, 'FIRST_KICKOFF_UNKNOWN', 'NO_DUE')
    start = parse_time(kickoff) - timedelta(days=config['warmup_days'])
    if now < start:
        return finish(False, 'BEFORE_KICKOFF_WARMUP', 'NO_DUE')
    mode = 'WARMUP' if now < parse_time(kickoff) else 'SEASON'
    if purpose in {'trench', 'weekly_actions', 'optimal_waiver'} and mode == 'WARMUP':
        return finish(False, 'REGULAR_SEASON_OUTPUT_ONLY', 'NO_DUE')
    return finish(True, 'IN_' + mode, mode)

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--purpose', required=True)
    parser.add_argument('--event', default='schedule')
    parser.add_argument('--ref', default='refs/heads/main')
    parser.add_argument('--as-of')
    parser.add_argument('--github-output', action='store_true')
    args = parser.parse_args()
    result = decide(json.loads(CONFIG.read_text()), args.purpose, args.as_of or datetime.now(timezone.utc).isoformat(), event=args.event, ref=args.ref)
    if args.github_output:
        for key in ('allowed', 'reason', 'mode', 'season'):
            value = str(result[key]).lower() if isinstance(result[key], bool) else result[key]
            print(f'{key}={value}')
    else:
        print(json.dumps(result, indent=2))

if __name__ == '__main__':
    main()
