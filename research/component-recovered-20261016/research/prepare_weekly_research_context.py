"""Replay captured PBP/snaps/schedule into existing descriptive feature owners."""
from __future__ import annotations
import argparse
import csv
import io
import json
from pathlib import Path
from prospective_research_io import binding, clock, gates, now, replay_response, write
from capture_week6_research_sources import validate_manifest
from research_feature_tables import pbp_tables, snap_table, role_changes
from research_snap_identity import bind
from research_rest_context import rest_features
from window2d_context_foundation import parse_schedule_csv


def build(root,envelope):
    source=validate_manifest(root,envelope);at=source['captured_at']
    responses={r['name']:r for r in source['responses']}
    def rows(name):
        return list(csv.DictReader(io.StringIO(replay_response(root,responses[name],at).decode('utf-8-sig'))))
    season,week=source['season'],source['week']
    table=pbp_tables(rows('pbp'),season,week)
    snaps=snap_table(rows('snaps'),season,week)
    identity=rows('players');canonical=bind(snaps['rows'],identity)
    teams={(r['week'],r['game_id'],r['team']):r for r in table['team_games']}
    opportunities=[]
    for player in table['red_zone_players']:
        team=teams[(player['week'],player['game_id'],player['team'])]
        for metric,denominator in [('carries','rush_attempts'),('targets','pass_attempts')]:
            opportunities.append({**{k:player[k] for k in ['season','week','game_id','team','source_gsis_player_id']},
                                  'metric':metric,'numerator':player['metrics'][metric],
                                  'denominator':team[denominator],'observed_at':at})
    try:
        rest=rest_features(parse_schedule_csv(replay_response(root,responses['schedule'],at),season),
                           season=season,target_week=week,observed_at=responses['schedule']['observed_at'],cutoff=at)
    except ValueError as error:
        if str(error)!='REST_PRIOR_GAME_TIME_INVALID':raise
        rest={'status':'BLOCKED_REST_PRIOR_GAME_TIME_INVALID','rows':[], 'blockers':[str(error)]}
    return {'schema':'fie-weekly-research-context-v1','season':season,'target_week':week,'cutoff':at,'generated_at':now(),
            'source_envelope':binding(root,envelope,at),'tables':table,'canonical_snaps':canonical,
            'snap_exclusions':snaps['excluded_rows'],'role_change':role_changes(opportunities,target_week=week,cutoff=at),
            'rest_context':rest,'history_weeks_expected':list(range(1,week)),
            'observed_pbp_weeks':sorted({r['week'] for r in table['team_games']}),
            'missing_fields':['routes','charted_end_zone_targets','tracking_alignment','realized_weather_counterpart'],
            'interpretation':'Prior-week descriptive evidence; raw observed now is not historical publication timing or incremental model validation.',
            **gates(['BLOCKED_FEATURE_ABLATION_REQUIRED','BLOCKED_PROSPECTIVE_VALIDATION_REQUIRED'])}


def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--root',type=Path,default=Path(__file__).resolve().parents[1])
    p.add_argument('--source-envelope',type=Path,required=True);a=p.parse_args();value=build(a.root,a.source_envelope)
    at=now();path=a.root/f"data/research/prospective/football-context/{value['season']}/week_{value['target_week']:02d}/{clock(at).strftime('%Y%m%dT%H%M%S%fZ')}/context.json"
    write(path,value);print(json.dumps({'status':'DESCRIPTIVE_CONTEXT_PREPARED','path':str(path)}))


if __name__=='__main__':main()
