#!/usr/bin/env python3
"""Canonical per-league M7-M9 builder on top of the existing M1-M6 architecture."""
from __future__ import annotations
import argparse,json,subprocess
from datetime import datetime,timezone
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]

def run(*parts,check=True):
    cmd=[str(x) for x in parts];print('+',' '.join(cmd),flush=True);return subprocess.run(cmd,cwd=ROOT,check=check)

def season_window():
    d=datetime.now(timezone.utc);last=d.year-(2 if d.month==1 else 1);return f'2019-{last}'

def extended_season_window():
    d=datetime.now(timezone.utc);last=d.year-(2 if d.month==1 else 1);return f'2016-{last}'

def adp_key(profile):
    fmt=str(profile.get('format') or '').upper();sc=profile.get('scoring_settings') or profile.get('scoring') or {}
    roster=profile.get('roster_positions') or []
    sf=('SUPER_FLEX' in roster) or sum(1 for x in roster if x=='QB')>=2
    try:rec=float(sc.get('rec',0))
    except Exception:rec=0
    dynasty='DYNASTY' in fmt
    if dynasty and sf:return 'adp_dynasty_2qb'
    if dynasty and rec>=.75:return 'adp_dynasty_ppr'
    if dynasty and rec>=.25:return 'adp_dynasty_half_ppr'
    if dynasty:return 'adp_dynasty_std'
    if sf:return 'adp_2qb'
    if rec>=.75:return 'adp_ppr'
    if rec>=.25:return 'adp_half_ppr'
    return 'adp_std'

def main():
    ap=argparse.ArgumentParser();ap.add_argument('--league-id',required=True);ap.add_argument('--format',required=True)
    ap.add_argument('--rebuild-base',action='store_true');ap.add_argument('--full-raw-cache',action='store_true')
    ap.add_argument('--league-root');ap.add_argument('--derived-dir');ap.add_argument('--cache-dir')
    ap.add_argument('--trench-source',default='');ap.add_argument('--trench-player-source',default='');ap.add_argument('--coverage-source',default='')
    ap.add_argument('--route-source',default='');ap.add_argument('--qb-coverage-source',default='')
    ap.add_argument('--season',type=int,default=None);ap.add_argument('--capture-market',action='store_true');ap.add_argument('--build-report',action='store_true')
    ap.add_argument('--stop-after-m8',action='store_true',help='Build/validate through M8, then exit so CI can checkpoint expensive state')
    ap.add_argument('--resume-from-m9',action='store_true',help='Require an existing M1-M8 checkpoint and run M9/report only')
    a=ap.parse_args();lid=str(a.league_id)
    if a.stop_after_m8 and a.resume_from_m9: raise SystemExit('--stop-after-m8 and --resume-from-m9 are mutually exclusive')
    if a.resume_from_m9 and a.rebuild_base: raise SystemExit('--resume-from-m9 cannot be combined with --rebuild-base')
    if not lid.isdigit() or not (6<=len(lid)<=32):raise SystemExit('invalid Sleeper League ID')
    league=Path(a.league_root or f'data/research/leagues/{lid}');derived=Path(a.derived_dir or f'.cache/fie-research/leagues/{lid}/derived');cache=Path(a.cache_dir or f'.cache/fie-research/leagues/{lid}')
    if a.rebuild_base and not a.resume_from_m9:
        cmd=['python','research/build_league_research.py','--league-id',lid,'--format',a.format,'--league-root',str(league),'--derived-dir',str(derived),'--cache-dir',str(cache),
             '--registry','data/research/leagues/registry.json','--portfolio-config','config/league-portfolio.json']
        if a.full_raw_cache:cmd.append('--full-raw-cache')
        run(*cmd)
        # The canonical bulk M1-M6 builder intentionally excludes the first-class
        # D/ST and kicker augmentations.  Reapply them when those current-architecture
        # modules are present, then restamp/govern so M7-M9 is built on the same M1-M6
        # state as the normal historical research workflow.
        dst=ROOT/'research/fie_dst.py'; kicker=ROOT/'research/fie_kicker.py'
        if dst.exists():
            run('python','research/fie_dst.py','augment','--profile',str(league/'profile.json'),
                '--m1',str(league/'milestone1.json'),'--m2',str(league/'milestone2.json'),'--m3',str(league/'milestone3.json'),
                '--m4',str(league/'milestone4.json'),'--m5',str(league/'milestone5.json'),'--m6',str(league/'milestone6.json'),
                '--derived-dir',str(derived),'--cache-dir',str(cache),'--seasons',extended_season_window())
        if kicker.exists():
            run('python','research/fie_kicker.py','augment','--profile',str(league/'profile.json'),
                '--m1',str(league/'milestone1.json'),'--m2',str(league/'milestone2.json'),'--m3',str(league/'milestone3.json'),
                '--m4',str(league/'milestone4.json'),'--m5',str(league/'milestone5.json'),'--m6',str(league/'milestone6.json'),
                '--derived-dir',str(derived),'--cache-dir',str(cache),'--seasons',extended_season_window())
        if dst.exists() or kicker.exists():
            for i,v in [(4,'validate_m4_bundle.py'),(5,'validate_m5_bundle.py'),(6,'validate_m6_bundle.py')]:
                run('python',f'research/{v}',str(league/f'milestone{i}.json'))
            run('python','research/stamp_league_artifacts.py','--profile',str(league/'profile.json'),
                *[str(league/f'milestone{i}.json') for i in range(1,7)])
            run('python','research/fie_governance.py','--league-id',lid,'--league-profile',str(league/'profile.json'),
                '--m4-bundle',str(league/'milestone4.json'),'--m5-bundle',str(league/'milestone5.json'),'--m6-bundle',str(league/'milestone6.json'),
                '--current-snapshot',str(league/'current/milestone5_current.json'),
                '--operator-override',str(league/'governance/operator_override.json'),
                '--global-operator-override','data/research/governance/operator_override.json',
                '--output',str(league/'governance/active_release.json'))
    required_through = 8 if a.resume_from_m9 else 6
    for i in range(1, required_through + 1):
        if not (league/f'milestone{i}.json').exists():
            hint='restore the M1-M8 checkpoint' if a.resume_from_m9 else 'use --rebuild-base on a fresh runner'
            raise SystemExit(f'missing {league}/milestone{i}.json; {hint}')
    profile=json.loads((league/'profile.json').read_text());seasons=season_window();league.mkdir(parents=True,exist_ok=True);derived.mkdir(parents=True,exist_ok=True);cache.mkdir(parents=True,exist_ok=True)
    if not a.resume_from_m9:
        common=[]
        for i in range(1,7):common += [f'--m{i}-bundle',str(league/f'milestone{i}.json')]
        m7=['python','research/fie_m7.py','--derived-dir',str(derived),'--cache-dir',str(cache),'--seasons',seasons,*common,
            '--route-source',a.route_source,'--qb-coverage-source',a.qb_coverage_source,'--output',str(league/'milestone7.json')]
        run(*m7);run('python','research/validate_m7_bundle.py',str(league/'milestone7.json'))
        m8=['python','research/fie_m8.py','--derived-dir',str(derived),'--cache-dir',str(cache),'--seasons',seasons]
        for i in range(1,8):m8 += [f'--m{i}-bundle',str(league/f'milestone{i}.json')]
        m8 += ['--trench-source',a.trench_source,'--trench-player-source',a.trench_player_source,'--coverage-source',a.coverage_source,'--output',str(league/'milestone8.json')]
        run(*m8);run('python','research/validate_m8_bundle.py',str(league/'milestone8.json'))
        if a.stop_after_m8:
            print(f'Performance checkpoint complete through M8 for {lid}: {league}')
            return
    else:
        run('python','research/validate_m7_bundle.py',str(league/'milestone7.json'))
        run('python','research/validate_m8_bundle.py',str(league/'milestone8.json'))
    m9=['python','research/fie_m9.py','--derived-dir',str(derived),'--cache-dir',str(cache),'--seasons',seasons]
    for i in range(1,9):m9 += [f'--m{i}-bundle',str(league/f'milestone{i}.json')]
    m9 += ['--output',str(league/'milestone9.json')];run(*m9);run('python','research/validate_m9_bundle.py',str(league/'milestone9.json'))
    run('python','research/stamp_league_artifacts.py','--profile',str(league/'profile.json'),str(league/'milestone7.json'),str(league/'milestone8.json'),str(league/'milestone9.json'))
    run('python','research/validate_m7_bundle.py',str(league/'milestone7.json'));run('python','research/validate_m8_bundle.py',str(league/'milestone8.json'));run('python','research/validate_m9_bundle.py',str(league/'milestone9.json'))
    season=a.season or datetime.now(timezone.utc).year;day=datetime.now(timezone.utc).date().isoformat();market=Path(f'data/research/market/sleeper/{season}/season_market_{day}.jsonl.gz')
    if a.capture_market or a.build_report:
        run('python','research/capture_sleeper_season_market.py','--season',str(season),'--derived-dir',str(derived),check=True)
    if a.build_report:
        perf=league/'performance'/str(season);perf.mkdir(parents=True,exist_ok=True);board=perf/'season_board.csv'
        run('python','research/build_m9_season_board.py','--m1-bundle',str(league/'milestone1.json'),'--m9-bundle',str(league/'milestone9.json'),'--market-snapshot',str(market),'--adp-key',adp_key(profile),'--output',str(board))
        run('python','research/build_fantasy_success_report.py','--board',str(board),'--m7-bundle',str(league/'milestone7.json'),'--m8-bundle',str(league/'milestone8.json'),'--m9-bundle',str(league/'milestone9.json'),'--output-dir',str(perf/'report'))
    print(f'Performance build complete for {lid}: {league}')
if __name__=='__main__':main()
