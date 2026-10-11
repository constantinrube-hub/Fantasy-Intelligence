"""Explain missing simulation evidence without manufacturing distributions."""
import argparse
from collections import Counter
from datetime import datetime,timezone
import json
from pathlib import Path

from current_snapshot_storage import load_current_snapshot
from point_in_time_capture import first_write_json
from strict_sleeper_baseline import finite
from weekly_evidence_audit import digest,stamp


def build(root,*,season,week,as_of):
    root=root.resolve();limit=stamp(as_of)
    if isinstance(week,bool) or not 1<=week<=18:raise ValueError('SCENARIO_READINESS_TARGET_INVALID')
    config=root/'config/league-portfolio.json';registry=json.loads(config.read_text())
    rows=[];seen=set()
    for league in registry['leagues']:
        lid=str(league['league_id'])
        if not lid.isdigit() or lid in seen:raise ValueError('SCENARIO_READINESS_LEAGUE_ID_INVALID')
        seen.add(lid)
        path=root/f'data/research/leagues/{lid}/current/milestone5_current.json'
        base=root/f'data/research/simulation/{season}/week_{week:02d}/{lid}'
        blockers=[];snapshot=None;coverage=None
        if path.is_file():
            try:
                current=load_current_snapshot(path,root=root)
                if (current.get('season'),current.get('week'))!=(season,week) or stamp(current['generated_at'])>limit:
                    blockers.append('CURRENT_TARGET_OR_TIME_MISMATCH')
                else:
                    players=current.get('players') or []
                    coverage={'player_rows':len(players),'finite_mean_rows':sum(finite(r.get('fie_weekly_projection')) is not None for r in players),
                        'complete_marginal_quantile_rows':sum(all(finite(r.get(k)) is not None for k in ('p10','p50','p90')) for r in players)}
                    snapshot={'path':path.relative_to(root).as_posix(),'sha256':digest(path),
                              'scoring_signature':current.get('scoring_signature'),'generated_at':current['generated_at']}
            except (ValueError,KeyError,TypeError,OSError) as exc:
                blockers.append('CURRENT_SOURCE_INVALID:'+type(exc).__name__)
        else:blockers.append('CURRENT_SNAPSHOT_MISSING')
        files={}
        for label in ('bank','calibration','request'):
            p=base/(label+'.json')
            if p.is_file():files[label]={'path':p.relative_to(root).as_posix(),'sha256':digest(p)}
            else:blockers.append(label.upper()+'_EVIDENCE_MISSING')
        blockers.append('GOVERNED_CALIBRATION_AND_DECISION_PROMOTION_PENDING')
        rows.append({'league_id':lid,'format':league.get('format'),'status':'BLOCKED_PRODUCTION_SIMULATION',
                     'current_snapshot':snapshot,'marginal_coverage':coverage,'available_simulation_files':files,
                     'blockers':blockers,'production_ready':False})
    return {'schema':'fie-scenario-readiness-v1','season':season,'week':week,'as_of':limit.isoformat(),
            'registry':{'path':'config/league-portfolio.json','sha256':digest(config)},'leagues':rows,
            'blocker_counts':dict(sorted(Counter(b for r in rows for b in r['blockers']).items())),
            'note':'Marginal means/quantiles do not establish a joint distribution or calibrated win/survival probabilities.',
            'production_authorized':False}


def main():
    ap=argparse.ArgumentParser();ap.add_argument('--root',type=Path,default=Path(__file__).resolve().parents[1])
    ap.add_argument('--season',type=int,required=True);ap.add_argument('--week',type=int,required=True)
    ap.add_argument('--as-of',default=None);ap.add_argument('--output',type=Path,required=True)
    args=ap.parse_args();report=build(args.root,season=args.season,week=args.week,as_of=args.as_of or datetime.now(timezone.utc).isoformat())
    print(first_write_json(args.output,report))


if __name__=='__main__':main()
