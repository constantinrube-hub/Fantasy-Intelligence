#!/usr/bin/env python3
"""Official unified FIE pipeline wrapper with M9.1c research challenger integration.

Production contract:
- run the existing unified pipeline first, unchanged;
- build/validate M9.1c only after canonical outputs exist;
- attach M9.1c as research evidence;
- rerun existing unified/report validators after attachment;
- never promote M9.1c or modify canonical M9 production/value fields.
"""
from __future__ import annotations

import argparse
import subprocess
import sys
from pathlib import Path

from fie_research_pipeline_contract import derived_dir, load_json, load_profile, pipeline_dir, resolve_adp_key


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

    # Canonical unified pipeline remains the source of all production outputs.
    cp=subprocess.run([sys.executable,"research/run_fie_league_research_pipeline.py",*args])
    if cp.returncode!=0:
        return cp.returncode

    profile=load_profile(ident.league_id)
    resolved,_=resolve_adp_key(profile,ident.adp_key)
    dd=derived_dir(ident.league_id)

    m91c_dir=(
        Path("data/research/leagues")/
        ident.league_id/"performance"/str(ident.season)/"m91c_challenger"
    )

    # report_only may reuse a previously validated challenger. All other modes
    # recompute against the current immutable season market + current availability.
    if str(ident.mode).lower()!="report_only" or not (
        (m91c_dir/"m91c_season_board.csv").is_file()
        and (m91c_dir/"m91c_meta.json").is_file()
        and (m91c_dir/"m91c_evaluation.json").is_file()
    ):
        run([
            sys.executable,"research/build_m91c_season_challenger.py",
            "--league-id",ident.league_id,
            "--season",str(ident.season),
            "--adp-key",resolved,
            "--player-week",str(dd/"player_week.csv.gz"),
        ])

    # Always validate even when report_only reuses an existing challenger.
    run([
        sys.executable,"research/validate_m91c_season_challenger.py",
        "--league-id",ident.league_id,
        "--season",str(ident.season),
    ])

    out=Path(ident.output_root) if ident.output_root else pipeline_dir(ident.league_id,ident.season)
    run([
        sys.executable,"research/integrate_m91c_research_challenger.py",
        "--league-id",ident.league_id,
        "--season",str(ident.season),
        "--output-dir",str(out),
    ])

    # Existing validators must remain green after the additive challenger fields.
    run([
        sys.executable,"research/validate_fie_research_pipeline.py",
        "--league-id",ident.league_id,
        "--season",str(ident.season),
        "--output-dir",str(out),
    ])
    run([
        sys.executable,"research/validate_fie_league_report.py",
        "--league-id",ident.league_id,
        "--season",str(ident.season),
        "--output-dir",str(out),
    ])

    audit=load_json(out/"m91c-integration.json",{})
    if (
        audit.get("status")!="complete_research_only"
        or audit.get("official_preseason_projection_challenger")!="M9.1c"
        or audit.get("production_model_unchanged")!="M9"
        or audit.get("production_activation") is not False
        or audit.get("canonical_production_columns_unchanged") is not True
    ):
        raise RuntimeError("M9.1c unified integration audit failed")

    print(
        f"Unified M9.1c integration complete for {ident.league_id}: "
        "M9 production unchanged; M9.1c official preseason projection challenger."
    )
    return 0


if __name__=="__main__":
    raise SystemExit(main())
