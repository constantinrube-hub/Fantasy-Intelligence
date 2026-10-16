#!/usr/bin/env python3
from __future__ import annotations
import argparse, hashlib, json
from pathlib import Path

EXPECTED_BUILD = "V9.6-CONTROLLED-RUNTIME-1"


def sha256(path: Path) -> str:
    h=hashlib.sha256()
    with path.open('rb') as f:
        for b in iter(lambda:f.read(1024*1024), b''): h.update(b)
    return h.hexdigest()


def validate(path: Path) -> None:
    b=json.loads(path.read_text())
    assert b.get('status')=='approved_controlled_runtime'
    assert b.get('runtime_build')==EXPECTED_BUILD
    assert b.get('league_id') and b.get('profile_fingerprint') and b.get('scoring_signature')
    gov=b.get('governance') or {}
    assert gov.get('runtime_activation_allowed') is True
    assert gov.get('controlled_runtime_only') is True
    assert gov.get('require_current_season_completed_features') is True
    assert gov.get('require_existing_weekly_activation_for_main_projection') is True
    assert gov.get('wr_te_histgb_enabled') is False
    assert gov.get('rb_alternate_is_diagnostic_only') is True
    assert gov.get('component_consumers_replace_canonical_projection') is False
    assert gov.get('horizon_consumers_replace_canonical_weekly_projection') is False
    assert gov.get('next_season_enabled') is False
    assert gov.get('prior_season_live_fallback') is False
    approved=set(b.get('approved_consumers') or [])
    assert 'QB:weekly_projection_residual:histgb' in approved
    assert 'RB:weekly_projection_residual:histgb' in approved
    assert 'WR:weekly_projection_residual:histgb' not in approved
    assert 'TE:weekly_projection_residual:histgb' not in approved
    for r in b.get('consumer_validation') or []:
        assert r.get('robust') is True
        assert int(r.get('folds') or 0) >= 4
        assert float(r.get('mean_improvement') or 0) >= .01
        assert float(r.get('ci95_low') or 0) > 0
    model=path.parent / str(b.get('model_file') or '')
    assert model.exists() and model.stat().st_size > 100
    assert sha256(model)==b.get('model_sha256')
    print(f"PASS V9.6 runtime bundle consumers={len(approved)} model_bytes={model.stat().st_size}")


def main():
    p=argparse.ArgumentParser(); p.add_argument('manifest'); a=p.parse_args(); validate(Path(a.manifest))
if __name__=='__main__': main()
