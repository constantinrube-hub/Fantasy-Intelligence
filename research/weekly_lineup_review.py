"""Read-only replay of the established PR2 postgame outcome/evaluation chain."""
import json
from pathlib import Path
from weekly_evidence_audit import stamp, digest


def review(root: Path, season: int, week: int, as_of, eligible_at) -> dict:
    from weekly_report_bundle import bind_pr2_capture
    from point_in_time_capture import validate_envelope
    from adapt_in_season_pr2_lineup_outcome_stats import adapt_source
    from build_in_season_pr2_lineup_outcome import build_outcome
    from evaluate_in_season_pr2_lineups import evaluate_capture
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
            records.append({'observed_at':observed.isoformat(),'capture_binding':binding,
                            'source_bindings':[{'path':p.relative_to(root).as_posix(),'sha256':digest(p)} for p in files],
                            'evaluation':evaluation,'validation_scope':'Stored provider payload through exact scoring and existing evaluation; provider raw response hash is declared, not independently replayed.'})
        except Exception as exc:
            errors.append({'path':path.relative_to(root).as_posix(),'status':'BLOCKED_INVALID_REVIEW','reason':f'{type(exc).__name__}:{exc}'})
    return {'status':'PARTIAL_REPLAYED_OWNER_EVALUATION' if records else 'BLOCKED_MISSING_OR_INVALID_EVALUATION',
            'season':season,'week':week,'revisions':records,'blocked_revisions':errors,
            'paired_fie_sleeper_comparison':'NOT_PROVIDED_BY_THIS_OWNER','user_adoption':'NOT_INFERRED',
            'complete':False,'production_model_changed':False}
