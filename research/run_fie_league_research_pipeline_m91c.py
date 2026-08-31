#!/usr/bin/env python3
"""Pilot wrapper: existing unified FIE pipeline + official M9.1c evidence integration.

The existing unified pipeline remains the source of all canonical production outputs.
Only after it succeeds do we build/validate M9.1c and attach it as research evidence.
"""
from __future__ import annotations

import argparse
import subprocess
import sys

from fie_research_pipeline_contract import derived_dir, load_profile, resolve_adp_key


def run(cmd:list[str])->None:
    print("+"," ".join(str(x) for x in cmd),flush=True)
    subprocess.run(cmd,check=True)


def parse_identity(argv:list[str]):
    p=argparse.ArgumentParser(add_help=False)
    p.add_argument("--league-id",required=True)
    p.add_argument("--season",type=int,required=True)
    p.add_argument("--adp-key",default="AUTO")
    p.add_argument("--mode",default="full")
    p.add_argument("--output-root",default="")
    a,_=p.parse_known_args(argv)
    return a


def main(argv=None)->int:
    args=list(argv if argv is not None else sys.argv[1:])
    ident=parse_identity(args)

    # First run the exact existing unified pipeline unchanged.
    cp=subprocess.run([sys.executable,"research/run_fie_league_research_pipeline.py",*args])
    if cp.returncode!=0:
        return cp.returncode

    profile=load_profile(ident.league_id)
    resolved,_=resolve_adp_key(profile,ident.adp_key)
    dd=derived_dir(ident.league_id)

    # report_only may reuse an already-built official challenger.
    m91c_dir=(
        __import__("pathlib").Path("data/research/leagues")/
        ident.league_id/"performance"/str(ident.season)/"m91c_challenger"
    )
    if str(ident.mode).lower()!="report_only" or not (m91c_dir/"m91c_season_board.csv").is_file():
        run([
            sys.executable,"research/build_m91c_season_challenger.py",
            "--league-id",ident.league_id,
            "--season",str(ident.season),
            "--adp-key",resolved,
            "--player-week",str(dd/"player_week.csv.gz"),
        ])
        run([
            sys.executable,"research/validate_m91c_season_challenger.py",
            "--league-id",ident.league_id,
            "--season",str(ident.season),
        ])

    bridge=[
        sys.executable,"research/integrate_m91c_research_challenger.py",
        "--league-id",ident.league_id,
        "--season",str(ident.season),
    ]
    if ident.output_root:
        bridge += ["--output-dir",ident.output_root]
    run(bridge)

    print(
        f"Unified M9.1c integration complete for {ident.league_id}: "
        "M9 production unchanged; M9.1c attached as official preseason projection challenger."
    )
    return 0


if __name__=="__main__":
    raise SystemExit(main())
