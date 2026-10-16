#!/usr/bin/env python3
"""Observe stored context integrity; never regenerate prospective context."""
from __future__ import annotations
import hashlib
import json
from datetime import datetime, timedelta
from pathlib import Path
from point_in_time_capture import canonical_bytes, validate_envelope
from weekly_pipeline_readiness import stamp, digest
from capture_fie_availability import CONTRACT, validate_capture
from capture_fie_weather import CONTEXT_SCHEMA, hourly_at_kickoff
from window2a_trench_evidence import SCHEMA as TRENCH_SCHEMA


def binding(root: Path, path: Path) -> dict:
    return {"path": path.relative_to(root).as_posix(), "sha256": digest(path)}


def latest(root: Path, pattern: str, time_of, as_of: datetime) -> tuple[Path | None, dict | None]:
    rows = []
    for path in root.glob(pattern):
        value = json.loads(path.read_text(encoding='utf-8'))
        observed = stamp(time_of(value))
        if observed <= as_of:
            rows.append((observed, path, value))
    if not rows:
        return None, None
    _, path, value = max(rows, key=lambda row: (row[0], str(row[1])))
    return path, value


def availability(root: Path, season: int, as_of: datetime) -> dict:
    path, meta = latest(root, f'data/research/availability/sleeper/{season}/availability_*.jsonl.gz.meta.json',
                        lambda value: value['captured_at'], as_of)
    if path is None:
        return {'status': 'MISSING', 'next_action': 'Run the original availability capture owner.'}
    snapshot = Path(str(path).removesuffix('.meta.json'))
    checked = validate_capture(snapshot)
    if checked.get('capture_contract') != CONTRACT:
        return {'status': 'LEGACY_NOT_SOURCE_VALIDATED', **binding(root, path)}
    observed = stamp(checked['captured_at'])
    if checked['season'] != season:
        raise ValueError('AVAILABILITY_SEASON_MISMATCH')
    source = snapshot.parent / checked['source_archive']
    return {'status': 'STALE' if as_of - observed > timedelta(hours=36) else 'SOURCE_VALIDATED',
            'observed_at': observed.isoformat(), 'snapshot': binding(root, snapshot),
            'metadata': binding(root, path), 'source': binding(root, source),
            'coverage': checked.get('coverage'), 'freshness_limit_hours': 36,
            'validation_scope': 'Captured provider response and normalized archive integrity; not injury forecast accuracy.'}


def weather(root: Path, season: int, week: int, as_of: datetime) -> dict:
    path, value = latest(root, f'data/research/context/weather/{season}/week_{week:02d}/*/context-evidence.json',
                         lambda row: row['provenance']['generated_at'], as_of)
    if path is None:
        return {'status': 'MISSING', 'next_action': 'Run the original weather capture owner.'}
    if value.get('schema_version') != CONTEXT_SCHEMA or (value.get('season'), value.get('week')) != (season, week):
        raise ValueError('WEATHER_SCHEMA_OR_TARGET_MISMATCH')
    observed = stamp(value['provenance']['generated_at'])
    schedule_path = path.with_name('schedule-source-envelope.json')
    schedule = json.loads(schedule_path.read_text(encoding='utf-8'))
    validate_envelope(schedule)
    if stamp(schedule['observed_at']) != observed or (schedule['payload']['season'], schedule['payload']['week']) != (season, week):
        raise ValueError('WEATHER_SCHEDULE_BINDING_MISMATCH')
    expected = {row['game_id']: row for row in schedule['payload']['games'] if stamp(row['kickoff']) > observed}
    actual = value['games']
    if len(actual) != len(expected) or {row['game_id'] for row in actual} != set(expected):
        raise ValueError('WEATHER_GAME_SCOPE_MISMATCH')
    sources, missing = [], []
    refs = value['provenance']['sources']
    for row in actual:
        game = expected[row['game_id']]
        if any(row.get(key) != game.get(key) for key in ('home_team','away_team','kickoff')):
            raise ValueError('WEATHER_GAME_IDENTITY_MISMATCH')
        environment = row['environment']
        source_path = path.with_name(f"{row['game_id']}.source-envelope.json")
        if not source_path.exists():
            if environment.get('forecast_observed_at') is not None or any(environment.get(key) is not None for key in ('wind_mph','gust_mph','temperature_f','precipitation_probability')):
                raise ValueError('WEATHER_UNSOURCED_NUMERIC_VALUES')
            if not str(environment.get('forecast_run_metadata_status','')).startswith('UNAVAILABLE_'):
                raise ValueError('WEATHER_MISSING_SOURCE_NOT_EXPLICIT')
            missing.append(row['game_id'])
            continue
        source = json.loads(source_path.read_text(encoding='utf-8'))
        validate_envelope(source)
        if stamp(source['observed_at']) != observed or stamp(source['effective_at']) != stamp(game['kickoff']):
            raise ValueError('WEATHER_FORECAST_TIME_BINDING_MISMATCH')
        reference = [ref for ref in refs if ref.get('payload_sha256') == source['payload_sha256'] and ref.get('endpoint') == source['endpoint'] and stamp(ref['effective_at']) == stamp(game['kickoff'])]
        if len(reference) != 1:
            raise ValueError('WEATHER_PROVENANCE_REFERENCE_MISMATCH')
        selected = hourly_at_kickoff(source['payload'], game['kickoff'])
        if any(environment.get(key) != number for key, number in selected.items()) or stamp(environment['forecast_observed_at']) != observed:
            raise ValueError('WEATHER_NORMALIZATION_MISMATCH')
        sources.append(binding(root, source_path))
    return {'status': 'PARTIAL_SOURCE_VALIDATED' if missing else 'SOURCE_VALIDATED',
            'observed_at': observed.isoformat(), 'age_hours': round((as_of-observed).total_seconds()/3600, 3),
            'context': binding(root,path), 'schedule': binding(root,schedule_path), 'forecast_sources': sources,
            'future_game_count': len(actual), 'missing_weather_game_ids': sorted(missing),
            'validation_scope': 'Source bindings and normalization; no forecast-accuracy or venue-coordinate certification.'}


def trench(root: Path, season: int, week: int, as_of: datetime) -> dict:
    path = root / f'data/research/trench/{season}/prospective/week_{week:02d}/trench-evidence-v1.json'
    if not path.exists():
        return {'status': 'MISSING', 'next_action': 'Run the existing Window 2A trench evidence owner.'}
    value = json.loads(path.read_text(encoding='utf-8'))
    if stamp(value['generated_at']) > as_of or stamp(value['source']['captured_at']) > as_of:
        return {'status': 'NOT_OBSERVED_AS_OF'}
    if value.get('schema') != TRENCH_SCHEMA or (value['season'],value['target_week']) != (season,week):
        raise ValueError('TRENCH_SCHEMA_OR_TARGET_MISMATCH')
    if value.get('target_week_realised_stats_excluded') is not True or value.get('max_input_week',week) >= week or value.get('through_week',week) >= week:
        raise ValueError('TRENCH_TARGET_WEEK_LEAKAGE')
    if value.get('research_only') is not True or value['feature_owner'].get('production_validated') is not False:
        raise ValueError('TRENCH_AUTHORITY_MISMATCH')
    if len(value.get('teams',{})) != value['team_count']:
        raise ValueError('TRENCH_TEAM_COUNT_MISMATCH')
    return {'status': 'BOUND_RESEARCH_ONLY', **binding(root,path), 'owner_status': value['status'],
            'observed_at': value['generated_at'], 'source_observed_at': value['source']['captured_at'],
            'source_sha256': value['source']['sha256'], 'team_count': value['team_count'],
            'max_input_week': value['max_input_week'],
            'validation_scope': 'Stored target, leakage guard and ownership; raw PBP hash is declared, not replayed by this audit.'}


def audit(root: Path, season: int, week: int, as_of: datetime) -> dict:
    if as_of.tzinfo is None or not 1 <= week <= 18:
        raise ValueError('CONTEXT_AUDIT_TARGET_OR_TIME_INVALID')
    result = {'producer':{'module':'research/weekly_context_audit.py','version':'1.0.0','sha256':digest(Path(__file__))},'schema':'fie-weekly-context-audit-v1', 'season':season, 'week':week,
              'as_of_utc':as_of.isoformat(), 'read_only':True, 'network_access':False, 'datasets':{}}
    for name, run in [('AVAILABILITY',lambda: availability(root,season,as_of)),
                      ('WEATHER',lambda: weather(root,season,week,as_of)),
                      ('TRENCH',lambda: trench(root,season,week,as_of))]:
        try:
            result['datasets'][name] = run()
        except Exception as exc:
            result['datasets'][name] = {'status':'BLOCKED_INVALID_EVIDENCE','reason':f'{type(exc).__name__}:{exc}'}
    states = [row['status'] for row in result['datasets'].values()]
    result['status'] = 'BLOCKED' if any(state.startswith('BLOCKED') for state in states) else 'ATTENTION' if any(state not in {'SOURCE_VALIDATED','BOUND_RESEARCH_ONLY'} for state in states) else 'BOUND'
    return result
