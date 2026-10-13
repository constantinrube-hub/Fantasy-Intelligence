"""Replay newly observed source bytes through existing exact ledger owners."""
from __future__ import annotations
import argparse
import io
import json
from pathlib import Path
import tempfile
import pandas as pd
from prospective_research_io import binding, now, replay_response, sha, write
from capture_week6_research_sources import validate_manifest
from run_waiver_v2_historical_ledger import run
from waiver_v2_population import certify, extend, close_identity_calendar
from waiver_v2_prospective import POP
from waiver_v2_validation import policy


def prepare(root, envelope, output, completed_week=None):
    source=validate_manifest(root,envelope)
    by_name={r['name']:r for r in source['responses']}
    required={'players','ff_playerids','player_week','weekly_rosters','schedule','pbp','sleeper_players'}
    if not required<=set(by_name):
        raise ValueError('WAIVER_LIVE_RAW_SOURCE_MISSING')
    if output.exists():
        raise ValueError('WAIVER_LIVE_HISTORY_NEW_REVISION_REQUIRED')
    # Restore exact downloaded response bytes only. SourceManager must never
    # silently obtain a different, later optional identity response.
    from fie_research import SourceManager
    season=source['season'];through=source['week']-1 if completed_week is None else completed_week
    if not 1<=through<=18 or through>source['week']:
        raise ValueError('WAIVER_LIVE_HISTORY_NOT_AVAILABLE')
    profiles=[]
    with tempfile.TemporaryDirectory(prefix='fie-waiver-live-') as folder:
        cache=Path(folder)/'cache';manager=SourceManager(cache)
        for name in required-{'sleeper_players'}:
            year=season if name in {'player_week','weekly_rosters','pbp'} else None
            manager.path_for(name if name!='schedule' else 'schedules',year).write_bytes(
                replay_response(root,by_name[name],source['captured_at']))
        for signature in policy()['signatures']:
            scoring=root/POP/f'{signature}-scoring-profile.json'
            if not scoring.exists():
                matches=list((root/POP).glob(f'*{signature}*scoring*json'))
                if len(matches)!=1:raise ValueError('WAIVER_LIVE_FROZEN_PROFILE_MISSING')
                scoring=matches[0]
            target=Path(folder)/signature
            report=run(seasons=[season],cache_dir=cache,scoring_path=scoring,
                       output_dir=target,player_stats_complete=False)
            raw=report['source_snapshot'];adapted=report['adapter_receipt']['outputs'];event=report['event_ledger_receipt']
            stats=pd.read_csv(adapted['player_stats']['path'],low_memory=False)
            roster=pd.read_csv(adapted['weekly_roster']['path'],low_memory=False)
            pbp=pd.read_csv(raw['pbp']['path'],low_memory=False)
            games=pd.read_csv(raw['games']['path'],low_memory=False)
            identity=pd.read_csv(raw['identity']['path'],low_memory=False)
            outcomes=pd.read_csv(report['ledger_receipt']['ledger']['path'],low_memory=False)
            event_weekly=pd.read_csv(event['event_weekly_stats']['path'],low_memory=False)
            scoped_games=games[(games.season==season)&(games.week<=through)].copy()
            destination=output/signature;destination.mkdir(parents=True)
            limitations=[]
            ready_weeks=[]
            try:
                certificates,audit,actors,_=certify(pbp,scoped_games,roster,stats,identity,event['rule_support'],[season])
                cert_path=destination/'zero-certificates.csv.gz'
                certificates.to_csv(cert_path,index=False,compression={'method':'gzip','mtime':0})
                outcomes,_=extend(outcomes,certificates,sha(cert_path))
                outcomes,_=close_identity_calendar(outcomes,stats,event_weekly,audit,actors,scoped_games,
                            json.loads(scoring.read_text()).get('scoring_settings',json.loads(scoring.read_text())),event['rule_support'])
                audit.to_csv(destination/'game-proof-audit.csv.gz',index=False,compression={'method':'gzip','mtime':0})
                ready=audit.groupby(['season','week']).proof_ready.all()
                ready_weeks=[int(w) for (s,w),ok in ready.items() if s==season and ok]
            except ValueError as error:
                # Existing exact observed outcomes may remain usable. The absence
                # proof fails closed; missing rows do not become blanket zeros.
                limitations.append(str(error))
            outcomes=outcomes[(outcomes.season==season)&(outcomes.week<=through)].copy()
            stats=stats[(stats.season==season)&(stats.week<=through)].copy()
            for name,frame in [('outcomes',outcomes),('stats',stats),('identity',identity),('games',scoped_games)]:
                path=destination/(name+'.csv.gz');frame.to_csv(path,index=False,compression={'method':'gzip','mtime':0})
            at=now()
            profiles.append({'scoring_signature':signature,'source_observed_at':source['captured_at'],
                'outcomes':binding(root,destination/'outcomes.csv.gz',at),'stats':binding(root,destination/'stats.csv.gz',at),
                'identity':binding(root,destination/'identity.csv.gz',at),'games':binding(root,destination/'games.csv.gz',at),
                'event_rule_support':event['rule_support'],'zero_proof_blockers':limitations,
                'whole_nfl_ready_weeks':ready_weeks,
                'exact_outcome_rows':int(outcomes.outcome_complete.astype(str).str.lower().eq('true').sum())})
    value={'schema':'fie-waiver-v2-live-history-v1','season':season,'completed_week':through,'prepared_at':now(),
           'source_envelope':binding(root,envelope,source['captured_at']),'profiles':profiles,
           'builder_sha256':sha(Path(__file__)),'research_only':True,'activation_eligible':False,
           'player_stats_complete_asserted':False}
    write(output/'live-history.json',value)
    return output/'live-history.json'


def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--root',type=Path,default=Path(__file__).resolve().parents[1])
    p.add_argument('--source-envelope',type=Path,required=True);p.add_argument('--output-dir',type=Path,required=True)
    p.add_argument('--completed-week',type=int)
    a=p.parse_args();print(prepare(a.root,a.source_envelope,a.output_dir,a.completed_week))


if __name__=='__main__':main()
