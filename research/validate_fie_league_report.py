#!/usr/bin/env python3
"""Validate report completeness, market boundaries and no silent league mixing."""
from __future__ import annotations
import argparse, json
from pathlib import Path
import pandas as pd
from fie_research_pipeline_contract import load_json, pipeline_dir
TOP={'QB':10,'RB':20,'WR':20,'TE':10,'DST':10,'K':10}
def main(argv=None):
    ap=argparse.ArgumentParser(); ap.add_argument('--league-id',required=True); ap.add_argument('--season',type=int,required=True); ap.add_argument('--output-dir',default=''); a=ap.parse_args(argv)
    out=Path(a.output_dir) if a.output_dir else pipeline_dir(a.league_id,a.season); report=load_json(out/'league-report.json',{}); summary=load_json(out/'report-summary.json',{})
    assert str(report.get('league_id'))==str(a.league_id); assert str(summary.get('league_id'))==str(a.league_id)
    board=pd.read_csv(out/'final_player_board.csv',low_memory=False)
    for pos,n in TOP.items():
        selected=((report.get('position_evaluation') or {}).get(pos) or {}).get('validation_status')
        rows=(report.get('top') or {}).get(pos) or []
        if selected=='NOT_APPLICABLE': assert rows==[]; continue
        eligible=board[(board.position.astype(str)==pos)&board.projection_points.notna()]
        expected=min(n,len(eligible)); assert len(rows)==expected, (pos,len(rows),expected)
        ids=[str(x.get('player_id') or x.get('sleeper_id') or '') for x in rows]; assert all(ids); assert len(ids)==len(set(ids))
    for x in (report.get('outliers_top100') or {}).get('positive',[]): assert float(x['adp'])<=100
    for x in (report.get('outliers_top100') or {}).get('negative',[]): assert float(x['adp'])<=100
    for pos,rows in ((report.get('sleepers_gt100') or {})).items():
        for x in rows: assert float(x['adp'])>100; assert float(x['rank_edge_position'])>=8; assert float(x['vorp'])>=0
    gov=report.get('governance') or {}; assert gov.get('adp_in_football_model') is False; assert gov.get('automatic_promotion') is False; assert gov.get('report_calculates_new_rank') is False
    assert (out/'league-report.md').is_file() and (out/'league-report.md').stat().st_size>200
    print(json.dumps({'status':'PASS','league_id':a.league_id,'top_counts':{p:len((report.get('top') or {}).get(p) or []) for p in TOP}},indent=2)); return 0
if __name__=='__main__': raise SystemExit(main())
