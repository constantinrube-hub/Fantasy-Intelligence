"""Read-only replay of the established PR2 postgame outcome/evaluation chain."""
import json
from pathlib import Path
from weekly_evidence_audit import stamp, digest


def paired_projection_readiness(capture: dict, evaluation: dict, baseline_archive: dict | None = None) -> dict:
    """Audit comparison inputs without treating league-scored rows as a validated forecast test."""
    reports = {str(row.get('league_id')): row for row in capture.get('leagues', []) if isinstance(row, dict)}
    pairs = 0
    governed_pairs = 0
    declared_models = 0
    bound_fie_leagues = 0
    scoring_signatures = set()
    ready = [row for row in evaluation.get('leagues', []) if row.get('status') == 'READY']
    for row in ready:
        source = reports.get(str(row.get('league_id')), {})
        evaluation_input = source.get('evaluation_input') or {}
        candidates = {str(candidate.get('captured_player_id')): candidate for candidate in evaluation_input.get('active_candidates', []) if isinstance(candidate, dict)}
        artifacts = evaluation_input.get('fie_forecast_artifacts') or {}
        if all(isinstance(artifacts.get(label), dict) and artifacts[label].get('status') == 'BOUND' and
               isinstance(artifacts[label].get('sha256'), str) and len(artifacts[label]['sha256']) == 64 and
               all(char in '0123456789abcdef' for char in artifacts[label]['sha256'])
               for label in ('M4', 'M5', 'M6')):
            bound_fie_leagues += 1
        signature = (row.get('capture_evidence') or {}).get('scoring_signature')
        if signature:
            scoring_signatures.add(str(signature))
        for pair in row.get('paired_projection_rows', []):
            pairs += 1
            governed_pairs += pair.get('fie_weekly_activation_eligible') is True
            evidence = (candidates.get(str(pair.get('captured_player_id'))) or {}).get('projection_evidence') or {}
            declared_models += bool(evidence.get('model_id') and evidence.get('model_version'))
    blockers = []
    if not ready:
        blockers.append('NO_EXACT_SCORED_PR2_LEAGUES')
    if not pairs:
        blockers.append('NO_PAIRED_FORECAST_ROWS')
    if bound_fie_leagues < len(ready):
        blockers.append('FIE_FORECAST_ARTIFACTS_UNBOUND')
    if declared_models < pairs:
        blockers.append('FIE_MODEL_IDENTITY_INCOMPLETE')
    if baseline_archive is None:
        blockers.append('SLEEPER_BASELINE_SOURCE_AND_SCORING_UNVERIFIED')
    else:
        if baseline_archive.get('refresh_source_bound_leagues', 0) < len(ready):
            blockers.append('SLEEPER_BASELINE_SOURCE_UNVERIFIED')
        blockers.append('SLEEPER_BASELINE_SCORING_UNVERIFIED')
    return {'status': 'BLOCKED_PAIRED_FORECAST_VALIDATION', 'ready_leagues': len(ready),
            'paired_league_player_rows': pairs, 'governed_fie_paired_rows': governed_pairs,
            'fie_model_identity_rows': declared_models, 'fie_artifact_bound_leagues': bound_fie_leagues,
            'scoring_signatures': sorted(scoring_signatures), 'blockers': blockers,
            'note': 'Counts are league-player observations, not independent players; no error metric or promotion claim.'}


def review(root: Path, season: int, week: int, as_of, eligible_at) -> dict:
    from weekly_report_bundle import bind_pr2_capture
    from point_in_time_capture import validate_envelope
    from adapt_in_season_pr2_lineup_outcome_stats import adapt_source
    from build_in_season_pr2_lineup_outcome import build_outcome
    from evaluate_in_season_pr2_lineups import evaluate_capture
    from weekly_pr2_baseline_archive import audit as audit_baseline_archive
    base = root / f"data/research/evaluation/{season}/weeks/week-{week}/lineups"
    records, errors = [], []
    for path in sorted((base / 'outcomes').glob('*/evaluation.json')):
        try:
            evaluation = json.loads(path.read_text())
            if (evaluation.get('season'),evaluation.get('week')) != (season,week):
                raise ValueError('REVIEW_TARGET_MISMATCH')
            capture_id = evaluation.get('capture_id')
            if not isinstance(capture_id,str) or len(capture_id)!=16 or any(c not in '0123456789abcdef' for c in capture_id):
                raise ValueError('REVIEW_CAPTURE_ID_INVALID')
            capture_path = base / 'captures' / f'portfolio-{capture_id}.json'
            capture = json.loads(capture_path.read_text())
            binding = bind_pr2_capture(root,base/'portfolio-latest.json',capture)
            if any((league.get('season'),league.get('week')) != (season,week) for league in capture['leagues']):
                raise ValueError('REVIEW_CAPTURE_TARGET_MISMATCH')
            revision = evaluation['outcome_revision_id']
            if revision != path.parent.name or not revision or any(c not in 'abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789._-' for c in revision):
                raise ValueError('REVIEW_REVISION_ID_INVALID')
            source_path = base / 'outcomes/source-inputs' / f'{revision}.json'
            raw_path, envelope_path, outcome_path = [path.parent/name for name in ('raw-stats.json','source-envelope.json','outcome.json')]
            source, raw, envelope, outcome = [json.loads(p.read_text()) for p in (source_path,raw_path,envelope_path,outcome_path)]
            observed = stamp(source['observed_at'])
            if observed < eligible_at or observed > as_of or stamp(capture['generated_at']) > observed:
                raise ValueError('REVIEW_OUTCOME_TIME_INVALID')
            validate_envelope(envelope)
            if envelope['payload'] != raw or stamp(envelope['observed_at']) != observed:
                raise ValueError('REVIEW_RAW_ENVELOPE_MISMATCH')
            if adapt_source(capture,source) != raw:
                raise ValueError('REVIEW_SOURCE_ADAPTER_REPLAY_MISMATCH')
            if build_outcome(capture,raw,outcome_revision_id=revision) != outcome:
                raise ValueError('REVIEW_SCORING_REPLAY_MISMATCH')
            if evaluate_capture(capture,outcome,root=root) != evaluation:
                raise ValueError('REVIEW_EVALUATION_REPLAY_MISMATCH')
            files = (source_path,raw_path,envelope_path,outcome_path,path)
            baseline_archive = audit_baseline_archive(root,capture,evaluation)
            records.append({'observed_at':observed.isoformat(),'capture_binding':binding,
                            'source_bindings':[{'path':p.relative_to(root).as_posix(),'sha256':digest(p)} for p in files],
                            'evaluation':evaluation,'paired_projection_readiness':paired_projection_readiness(capture,evaluation,baseline_archive),
                            'sleeper_baseline_archive':baseline_archive,
                            'validation_scope':'Stored provider payload through exact scoring and existing evaluation; provider raw response hash is declared, not independently replayed.'})
        except Exception as exc:
            errors.append({'path':path.relative_to(root).as_posix(),'status':'BLOCKED_INVALID_REVIEW','reason':f'{type(exc).__name__}:{exc}'})
    return {'status':'PARTIAL_REPLAYED_OWNER_EVALUATION' if records else 'BLOCKED_MISSING_OR_INVALID_EVALUATION',
            'season':season,'week':week,'revisions':records,'blocked_revisions':errors,
            'paired_fie_sleeper_comparison':'NOT_PROVIDED_BY_THIS_OWNER','user_adoption':'NOT_INFERRED',
            'complete':False,'production_model_changed':False}
