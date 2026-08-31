#!/usr/bin/env python3
"""Validate report completeness, market boundaries and canonical display semantics."""
from __future__ import annotations
import argparse, json, math
from pathlib import Path
import pandas as pd
from fie_research_pipeline_contract import load_json, pipeline_dir

TOP={'QB':10,'RB':20,'WR':20,'TE':10,'DST':10,'K':10}
OFFENSE={'QB','RB','WR','TE'}


def _finite(v):
    try:
        x=float(v)
        return x if math.isfinite(x) else None
    except Exception:
        return None


def _canonical_replacement(board: pd.DataFrame, pos: str):
    q=pd.to_numeric(board.loc[board.position.astype(str).eq(pos),'replacement_points'],errors='coerce').dropna()
    if q.empty:
        return None
    base=float(q.iloc[0])
    assert bool((q-base).abs().le(1e-8).all()), f'conflicting board replacement values for {pos}'
    return base


def _validate_intervals(rows):
    for r in rows:
        vals=[_finite(r.get(k)) for k in ('p10','p25','p50','p75','p90')]
        present=[x for x in vals if x is not None]
        if len(present)>=2:
            assert present==sorted(present), (r.get('name'),'non_monotonic_interval',present)
        basis=str(r.get('projection_basis') or '')
        interval=str(r.get('interval_source') or '')
        if basis and interval:
            assert basis==interval, (r.get('name'),'projection_interval_source_mismatch',basis,interval)


def main(argv=None):
    ap=argparse.ArgumentParser(); ap.add_argument('--league-id',required=True); ap.add_argument('--season',type=int,required=True); ap.add_argument('--output-dir',default=''); a=ap.parse_args(argv)
    out=Path(a.output_dir) if a.output_dir else pipeline_dir(a.league_id,a.season); report=load_json(out/'league-report.json',{}); summary=load_json(out/'report-summary.json',{})
    assert str(report.get('league_id'))==str(a.league_id); assert str(summary.get('league_id'))==str(a.league_id)
    board=pd.read_csv(out/'final_player_board.csv',low_memory=False)
    for pos,n in TOP.items():
        meta=((report.get('position_evaluation') or {}).get(pos) or {})
        selected=meta.get('validation_status')
        rows=(report.get('top') or {}).get(pos) or []
        if selected=='NOT_APPLICABLE': assert rows==[]; continue
        eligible=board[(board.position.astype(str)==pos)&board.projection_points.notna()]
        expected=min(n,len(eligible)); assert len(rows)==expected, (pos,len(rows),expected)
        ids=[str(x.get('player_id') or x.get('sleeper_id') or '') for x in rows]; assert all(ids); assert len(ids)==len(set(ids))
        _validate_intervals(rows)
        if pos in OFFENSE:
            expected_repl=_canonical_replacement(board,pos)
            shown=_finite(meta.get('replacement_points'))
            if expected_repl is None:
                assert shown is None
            else:
                assert shown is not None and abs(shown-expected_repl)<=1e-8, (pos,shown,expected_repl)
    for x in (report.get('outliers_top100') or {}).get('positive',[]): assert float(x['adp'])<=100
    for x in (report.get('outliers_top100') or {}).get('negative',[]): assert float(x['adp'])<=100
    for pos,rows in ((report.get('sleepers_gt100') or {})).items():
        for x in rows:
            assert float(x['adp'])>100; assert float(x['rank_edge_position'])>=8; assert float(x['vorp'])>=0
            assert isinstance(x.get('why'),list)
    gov=report.get('governance') or {}; assert gov.get('adp_in_football_model') is False; assert gov.get('automatic_promotion') is False; assert gov.get('report_calculates_new_rank') is False
    assert (out/'league-report.md').is_file() and (out/'league-report.md').stat().st_size>200
    md=(out/'league-report.md').read_text(encoding='utf-8')
    # Known regression signature: formatting 10/20/30 with .rstrip('0') used to
    # collapse them to 1/2/3 in Markdown.
    assert '| Market Pos Rank |' in md
    print(json.dumps({'status':'PASS','league_id':a.league_id,'top_counts':{p:len((report.get('top') or {}).get(p) or []) for p in TOP}},indent=2)); return 0
if __name__=='__main__': raise SystemExit(main())
