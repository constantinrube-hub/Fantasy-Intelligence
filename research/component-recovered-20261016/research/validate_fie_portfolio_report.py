#!/usr/bin/env python3
from __future__ import annotations
import argparse,json
from pathlib import Path
import pandas as pd
from fie_research_pipeline_contract import ROOT,enabled_league_rows,load_json,PORTFOLIO_SCHEMA
def main(argv=None):
    ap=argparse.ArgumentParser();ap.add_argument('--season',type=int,required=True);ap.add_argument('--output-dir',default='');a=ap.parse_args(argv);out=Path(a.output_dir) if a.output_dir else ROOT/'data/research/portfolio'/str(a.season);x=load_json(out/'research-overview.json',{});assert x.get('schema')==PORTFOLIO_SCHEMA
    n=len(enabled_league_rows());c=x.get('coverage') or {};assert int(c.get('enabled') or -1)==n;assert int(c.get('completed') or 0)+int(c.get('blocked') or 0)+int(c.get('failed') or 0)==n;assert len(x.get('leagues') or [])==n;assert len({str(r.get('league_id')) for r in x.get('leagues') or []})==n
    g=x.get('governance') or {};assert g.get('cross_league_validation_pooling') is False;assert g.get('automatic_promotion') is False;assert g.get('league_specific_decisions_preserved') is True
    df=pd.read_csv(out/'model-readiness.csv');assert len(df)==n
    print(json.dumps({'status':'PASS','enabled':n,'coverage':c},indent=2));return 0
if __name__=='__main__':raise SystemExit(main())
