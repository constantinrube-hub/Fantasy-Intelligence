"""Source-proven event-absence zeros and frozen-forecast population audit."""
from __future__ import annotations

import argparse
import json
import shutil
from pathlib import Path

import numpy as np
import pandas as pd

from build_waiver_v2_label_batch import digest, label_frame
from build_waiver_v2_outcome_ledger import scoring_signature
from waiver_v2_contract import _true
from waiver_v2_event_ledger import _canonical_resolver
from waiver_v2_validation import KEYS, TARGET, FULL, keyed, metrics, verified
from week1_game_projections import canonical_team
from waiver_v2_outcomes import build_offensive_scoring_inventory, _score_exact_row

ROOT = Path(__file__).resolve().parents[1]
CONTRACT = ROOT/'config/waiver-v2-zero-outcome-contract.json'
GLOBAL_CONTRACT = ROOT/'config/waiver-v2-global-identity-outcome-extension.json'
SCHEMA = 'fie-waiver-v2-population-revision-v1'
META = ['game_id','season','week','season_type','home_team','away_team','play_id','play_type',
        'play_deleted','game_seconds_remaining','total_home_score','total_away_score','pass_attempt',
        'complete_pass','interception','rush_attempt','pass_touchdown','rush_touchdown','two_point_attempt',
        'two_point_conv_result','lateral_receiving_yards','lateral_rushing_yards','fumble',
        'posteam','posteam_score_post','defteam_score_post']
ACTORS = ['td_player_id','passer_player_id','receiver_player_id','rusher_player_id','lateral_receiver_player_id',
          'lateral_rusher_player_id','fumbled_1_player_id','fumbled_2_player_id']
EVENT_RULES = ['fum','fum_lost','pass_int_td']
POSITIVE_STATS = ['passing_yards','passing_tds','passing_interceptions','completions','receptions','receiving_yards',
                  'receiving_tds','carries','rushing_yards','rushing_tds','passing_2pt_conversions',
                  'rushing_2pt_conversions','receiving_2pt_conversions']


def scope(scoring, signature, contract):
    active = {key for key,value in scoring.items() if float(value) != 0.0}
    if scoring_signature(scoring)!=signature or signature not in contract['scoring_signatures'] or not active <= set(contract['allowed_rules']):
        raise ValueError('WAIVER_ZERO_UNSUPPORTED_SCORING_SCOPE')


def certify(pbp, games, roster, stats, identity, event_support, seasons):
    """Closed-source absence; a score match or missing CSV row alone is insufficient."""
    if any((event_support.get(key) or {}).get('support_status') != 'EXACT_EVENT_READY' for key in EVENT_RULES):
        raise ValueError('WAIVER_ZERO_EVENT_RECEIPT_BLOCKED')
    missing = set(META+ACTORS)-set(pbp)
    if missing:
        raise ValueError('WAIVER_ZERO_PBP_SCHEMA_INCOMPLETE: '+','.join(sorted(missing)))
    if not set(POSITIVE_STATS) <= set(stats):
        raise ValueError('WAIVER_ZERO_PUBLISHED_STATS_SCHEMA_INCOMPLETE')
    p = pbp[pbp.season_type.eq('REG') & pbp.season.isin(seasons)].copy()
    g = games[games.game_type.eq('REG') & games.season.isin(seasons)].copy()
    if g.duplicated('game_id').any() or g[['game_id','season','week','home_team','away_team']].isna().any().any():
        raise ValueError('WAIVER_ZERO_AMBIGUOUS_SCHEDULE')
    keyed(roster); keyed(stats)
    if p[['game_id','season','week','play_id']].isna().any().any():
        raise ValueError('WAIVER_ZERO_MISSING_PLAY_IDENTITY')
    resolver = _canonical_resolver(identity)
    id_columns = sorted(column for column in p if 'player_id' in column)
    # Include deleted/administrative occurrences in the exclusion index. They
    # cannot score, but discarding them could only make absence less conservative.
    actors = p[['game_id','season','week']+id_columns].melt(id_vars=['game_id','season','week'],
                    value_vars=id_columns, value_name='source_id').dropna(subset=['source_id'])
    actors['source_id'] = actors.source_id.astype(str).str.strip()
    actors = actors[actors.source_id.ne('')]
    bindings = {value:resolver(value)[0] for value in actors.source_id.unique()}
    actors['canonical_player_id'] = actors.source_id.map(bindings)
    actors.loc[actors.source_id.eq('00-0000000'),'canonical_player_id'] = None
    bad_actor_games = set(actors.loc[actors.canonical_player_id.isna(),'game_id'])
    actor_index = actors.dropna(subset=['canonical_player_id'])[['canonical_player_id','season','week','game_id']].drop_duplicates()
    valid = p[~p.play_deleted.map(_true)].copy()
    def absent(column):
        values = valid[column].fillna('').astype(str).str.strip()
        return ~values.str.fullmatch(r'00-\d{7}') | values.eq('00-0000000')
    core_flags = ['pass_attempt','complete_pass','interception','rush_attempt','pass_touchdown','rush_touchdown','two_point_attempt','fumble']
    football = valid.play_type.isin(['pass','run','qb_spike','qb_kneel'])
    unknown_flags = pd.Series(False,index=valid.index)
    for column in core_flags:
        value = pd.to_numeric(valid[column],errors='coerce')
        unknown_flags |= football & ~value.isin([0,1])
    conditions = {
        'BLOCKED_CORE_FLAGS':unknown_flags,
        'BLOCKED_PASSER':(valid.pass_attempt.eq(1)|valid.interception.eq(1)|valid.complete_pass.eq(1)|valid.pass_touchdown.eq(1)|valid.play_type.isin(['pass','qb_spike'])) & absent('passer_player_id'),
        'BLOCKED_RECEIVER':(valid.complete_pass.eq(1)|valid.pass_touchdown.eq(1)) & absent('receiver_player_id'),
        'BLOCKED_RUSHER':(valid.rush_attempt.eq(1)|valid.rush_touchdown.eq(1)|valid.play_type.isin(['run','qb_kneel'])) & absent('rusher_player_id'),
        'BLOCKED_LATERAL_RECEIVER':valid.lateral_receiving_yards.fillna(0).ne(0)&absent('lateral_receiver_player_id'),
        'BLOCKED_LATERAL_RUSHER':valid.lateral_rushing_yards.fillna(0).ne(0)&absent('lateral_rusher_player_id'),
        'BLOCKED_TWO_POINT_ACTOR':valid.two_point_conv_result.eq('success')&absent('passer_player_id')&absent('rusher_player_id')&absent('receiver_player_id'),
        'BLOCKED_FUMBLER':valid.fumble.eq(1)&absent('fumbled_1_player_id')&absent('fumbled_2_player_id'),
    }
    invalid_by_game = {}
    for code,mask in conditions.items():
        for game in valid.loc[mask,'game_id'].unique():invalid_by_game.setdefault(game,set()).add(code)
    duplicate_games = set(p.loc[p.duplicated(['game_id','play_id'],keep=False),'game_id'])
    # Positive published statistics are an independent backstop for actor loss.
    positive = stats[stats[POSITIVE_STATS].apply(pd.to_numeric,errors='coerce').fillna(0).ne(0).any(axis=1)]
    represented = actor_index[KEYS].drop_duplicates().assign(in_pbp=True)
    absent_published = positive.merge(represented,on=KEYS,how='left',validate='one_to_one')
    absent_published = absent_published[absent_published.in_pbp.isna()]
    bad_published_weeks = set(zip(absent_published.season.astype(int),absent_published.week.astype(int)))
    game_rows = []
    grouped = {name:frame for name,frame in valid.groupby('game_id')}
    for row in g.itertuples(index=False):
        reasons = set(invalid_by_game.get(row.game_id,set()))
        frame = grouped.get(row.game_id)
        if pd.isna(row.home_score) or pd.isna(row.away_score):reasons.add('BLOCKED_GAME_INCOMPLETE')
        if row.game_id in bad_actor_games:reasons.add('BLOCKED_UNRESOLVED_ACTOR')
        if row.game_id in duplicate_games:reasons.add('BLOCKED_DUPLICATE_PLAY')
        if (int(row.season),int(row.week)) in bad_published_weeks:reasons.add('BLOCKED_PUBLISHED_SCORER_MISSING_IN_PBP')
        if frame is None or frame.empty:
            reasons.add('BLOCKED_MISSING_GAME_PBP')
        else:
            if (set(frame.season)!={row.season} or set(frame.week)!={row.week} or
                set(frame.home_team.map(canonical_team))!={canonical_team(row.home_team)} or
                set(frame.away_team.map(canonical_team))!={canonical_team(row.away_team)}):reasons.add('BLOCKED_GAME_BINDING')
            if pd.to_numeric(frame.game_seconds_remaining,errors='coerce').min()!=0:reasons.add('BLOCKED_END_CLOCK')
            # Play IDs do not define chronology: corrected/admin rows may have
            # larger IDs than the final football play. Include post-play scores
            # (e.g. the winning OT touchdown) and require each scoreboard's
            # nondeleted maximum to reconcile to the completed official score.
            home = frame.posteam.map(canonical_team).eq(canonical_team(row.home_team))
            away = frame.posteam.map(canonical_team).eq(canonical_team(row.away_team))
            home_values = pd.concat([frame.total_home_score,frame.loc[home,'posteam_score_post'],frame.loc[away,'defteam_score_post']])
            away_values = pd.concat([frame.total_away_score,frame.loc[away,'posteam_score_post'],frame.loc[home,'defteam_score_post']])
            if pd.to_numeric(home_values,errors='coerce').max()!=row.home_score or pd.to_numeric(away_values,errors='coerce').max()!=row.away_score:
                reasons.add('BLOCKED_FINAL_SCORE')
        game_rows.append({'game_id':row.game_id,'season':int(row.season),'week':int(row.week),
                          'home_team':row.home_team,'away_team':row.away_team,
                          'pbp_rows':0 if frame is None else len(frame),'proof_ready':not reasons,
                          'blockers':';'.join(sorted(reasons))})
    unexpected = set(valid.game_id)-set(g.game_id)
    if unexpected:raise ValueError('WAIVER_ZERO_UNSCHEDULED_GAME_PBP')
    game_audit = pd.DataFrame(game_rows)
    ready = game_audit.groupby(['season','week']).proof_ready.all()
    ready_weeks = set(ready[ready].index.tolist())
    team_games = pd.concat([g[['season','week','home_team','game_id']].rename(columns={'home_team':'team'}),
                            g[['season','week','away_team','game_id']].rename(columns={'away_team':'team'})],ignore_index=True)
    if team_games.duplicated(['season','week','team']).any():raise ValueError('WAIVER_ZERO_MULTIPLE_TEAM_GAMES')
    candidates = roster.merge(team_games,on=['season','week','team'],how='left',validate='many_to_one')
    candidates = candidates.merge(stats[KEYS].assign(published_stat=True),on=KEYS,how='left',validate='one_to_one')
    candidates = candidates.merge(represented,on=KEYS,how='left',validate='one_to_one')
    candidates = candidates[candidates.game_id.notna() & candidates.roster_complete.map(_true) &
                    candidates.published_stat.isna() & candidates.in_pbp.isna()].copy()
    candidates = candidates.loc[np.array([tuple(pair) in ready_weeks for pair in candidates[['season','week']].to_numpy()],dtype=bool)]
    certificates = candidates[KEYS+['team','position_model','game_id']].copy()
    certificates['proof_status'] = 'CONFIRMED_SOURCE_NO_EVENT_ZERO'
    certificates['fantasy_points_proven'] = 0.0
    return certificates,game_audit,actor_index,absent_published[KEYS+['team']]


def extend(outcomes, certificates, certificate_sha256):
    """Never overwrite an observed value, even a diagnostic incomplete one."""
    ledger = keyed(outcomes).reset_index(drop=True)
    proof = keyed(certificates).reset_index(drop=True)
    if (not proof.proof_status.eq('CONFIRMED_SOURCE_NO_EVENT_ZERO').all() or
        not pd.to_numeric(proof.fantasy_points_proven,errors='coerce').eq(0).all() or
        proof.game_id.isna().any() or proof.game_id.astype(str).str.strip().eq('').any()):
        raise ValueError('WAIVER_ZERO_INVALID_CERTIFICATE')
    proof = proof[KEYS+['team','position_model','proof_status','game_id']].rename(columns={
        'team':'proof_team','position_model':'proof_position','game_id':'zero_proof_game_id'})
    result = ledger.merge(proof,on=KEYS,how='left',validate='one_to_one')
    eligible = (result.proof_status.eq('CONFIRMED_SOURCE_NO_EVENT_ZERO') & result.exact_scoring.map(_true) &
                ~result.outcome_complete.map(_true) & result.fantasy_points_exact.isna() &
                result.outcome_status.eq('BLOCKED_PLAYER_STATS_INCOMPLETE') &
                result.team.eq(result.proof_team) & result.position_model.eq(result.proof_position))
    result['zero_certificate_sha256'] = np.where(eligible,certificate_sha256,None)
    result.loc[eligible,'fantasy_points_exact'] = 0.0
    result.loc[eligible,'outcome_complete'] = True
    result.loc[eligible,'outcome_status'] = 'CONFIRMED_SOURCE_NO_EVENT_ZERO'
    result.loc[eligible,'outcome_blocker_codes'] = ''
    result.loc[~eligible,'zero_proof_game_id'] = None
    return result.drop(columns=['proof_team','proof_position','proof_status']),int(eligible.sum())


def stress(predictions, updated_labels):
    """Keep forecasts/baseline/features fixed; only join new outcome evidence."""
    labels = keyed(updated_labels)[KEYS+[TARGET,FULL]].reset_index(drop=True)
    new = labels.rename(columns={TARGET:'new_target',FULL:'new_full'})
    paired = predictions.merge(new,on=KEYS,how='left',validate='one_to_one')
    paired['new_label_complete'] = paired.new_full.map(_true) & np.isfinite(pd.to_numeric(paired.new_target,errors='coerce'))
    previous = paired.label_complete.map(_true)
    if (~paired.loc[previous,'new_label_complete']).any() or not np.allclose(paired.loc[previous,TARGET],paired.loc[previous,'new_target'],rtol=0,atol=1e-12):
        raise ValueError('WAIVER_POPULATION_CHANGED_PRIOR_COMPLETE_TARGET')
    paired['target_population'] = np.where(previous,'ORIGINAL_OBSERVED_TARGET',np.where(paired.new_label_complete,'NEWLY_OBSERVABLE_TARGET','STILL_INCOMPLETE'))
    paired[TARGET] = paired.new_target
    results = []
    for season,rows in paired.groupby('season'):
        item = {'season':int(season),'decision_rows':len(rows),'feature_admissible_rows':int(rows.feature_admissible.map(_true).sum()),'cohorts':{}}
        for name,mask in [('original',rows.target_population.eq('ORIGINAL_OBSERVED_TARGET')),
                          ('newly_observable',rows.target_population.eq('NEWLY_OBSERVABLE_TARGET')),
                          ('combined',rows.new_label_complete)]:
            base = rows[mask & rows.feature_admissible.map(_true)]
            covered = base[np.isfinite(pd.to_numeric(base.prediction,errors='coerce'))]
            item['cohorts'][name] = {'base_paired_rows':len(base),'covered_paired_rows':len(covered),'metrics':metrics(covered)}
        item['still_missing_feature_rows'] = int((rows.feature_admissible.map(_true)&~rows.new_label_complete).sum())
        results.append(item)
    return results,paired


def close_identity_calendar(outcomes,stats,event_weekly,game_audit,actors,games,scoring,event_support):
    """Add target-only exact outcomes for identities known before that week.

    Unknown future team/position stays null on absence zeros. These rows may
    complete future labels but never create a new cutoff or feature row.
    """
    source=keyed(outcomes).reset_index(drop=True).copy()
    source['target_only_row']=False
    first=source.groupby(['canonical_player_id','season']).week.min()
    exists=set(keyed(source).index)
    actor_keys=set(pd.MultiIndex.from_frame(actors[KEYS].drop_duplicates()))
    ready=game_audit.groupby(['season','week']).proof_ready.all()
    ready_weeks=set(ready[ready].index)
    max_week=game_audit.groupby('season').week.max().to_dict()
    joined=keyed(stats).reset_index(drop=True).merge(event_weekly,on=KEYS,how='left',validate='one_to_one')
    lookup=keyed(joined)
    additions=[];proofs=[]
    regular=games[games.game_type.eq('REG')]
    for (player,season),anchor in first.items():
        for week in range(int(anchor)+1,int(max_week[season])+1):
            key=(player,int(season),week)
            if key in exists:continue
            value=None;team=None;position=None;game=None;basis=None
            if key in lookup.index and key in actor_keys:
                row=lookup.loc[key];position=str(row.position_model);team=str(row.team)
                selected=regular[(regular.season==season)&(regular.week==week)&
                                 (regular.home_team.map(canonical_team).eq(canonical_team(team))|
                                  regular.away_team.map(canonical_team).eq(canonical_team(team)))]
                inv=build_offensive_scoring_inventory(scoring,position=position,available_columns=set(joined),event_rule_support=event_support)
                required={c for rule in inv['relevant_nonzero_rules'] for c in rule['required_columns']}
                complete=len(selected)==1 and selected[['home_score','away_score']].notna().all().all()
                complete=complete and inv['exact_replay_eligible'] and all(pd.notna(row.get(c)) and np.isfinite(float(row[c])) for c in required)
                if complete:
                    value=_score_exact_row(row,scoring,position);game=str(selected.game_id.iloc[0]);basis='EXACT_PUBLISHED_PLAYER_WEEK'
            elif key not in lookup.index and key not in actor_keys and (int(season),week) in ready_weeks:
                value=0.0;basis='GLOBAL_NFL_WEEK_NO_EVENT';game=f'GLOBAL:{season}:{week}'
            if value is None:continue
            additions.append({'canonical_player_id':player,'season':int(season),'week':week,
                              'team':team,'position_model':position,'scoring_signature':str(source.scoring_signature.iloc[0]),
                              'outcome_ledger_version':'waiver-v2-global-identity-target-outcome-v1','exact_scoring':True,
                              'fantasy_points_exact':value,'outcome_complete':True,
                              'outcome_status':'COMPLETE_PUBLISHED_SOURCE_WITHOUT_ROSTER' if basis=='EXACT_PUBLISHED_PLAYER_WEEK' else 'CONFIRMED_GLOBAL_NO_EVENT_ZERO',
                              'outcome_blocker_codes':'','target_only_row':True,'identity_anchor_week':int(anchor),
                              'future_membership_verified':False,'population_source_basis':basis})
            proofs.append({'canonical_player_id':player,'season':int(season),'week':week,'identity_anchor_week':int(anchor),
                           'proof_basis':basis,'proof_game_id':game,'fantasy_points_proven':value})
    result=pd.concat([source,pd.DataFrame(additions)],ignore_index=True,sort=False) if additions else source
    return result,pd.DataFrame(proofs,columns=KEYS+['identity_anchor_week','proof_basis','proof_game_id','fantasy_points_proven'])


def run(validation_report,source_batch,output_dir,global_identity_closure=False):
    if output_dir.exists():raise ValueError('WAIVER_POPULATION_OUTPUT_MUST_BE_NEW')
    contract = json.loads(CONTRACT.read_text())
    vr = json.loads(validation_report.read_text())
    # The immutable observation pins the report separately from its own fields.
    summary = json.loads(validation_report.with_name('summary.json').read_text())
    if digest(validation_report)!=summary['validation_report']['sha256']:
        raise ValueError('WAIVER_POPULATION_FROZEN_REPORT_CHANGED')
    if digest(source_batch)!=vr['source_batch']['sha256']:
        raise ValueError('WAIVER_POPULATION_SOURCE_BATCH_CHANGED')
    batch = json.loads(source_batch.read_text());shared=batch['shared_source_run']
    for binding in shared['source_snapshot'].values():verified(binding)
    for binding in shared['adapter_receipt']['outputs'].values():verified(binding)
    event = shared['event_ledger_receipt']
    # Bind the actual shared event receipt and its ledger/blocker bytes as well.
    for name in ['event_ledger','event_weekly_stats','blockers']:verified(event[name])
    raw = shared['source_snapshot']; adapted=shared['adapter_receipt']['outputs']
    header=pd.read_csv(verified(raw['pbp']),nrows=0).columns
    cols=list(dict.fromkeys(META+ACTORS+[c for c in header if 'player_id' in c]))
    pbp=pd.read_csv(verified(raw['pbp']),usecols=cols,low_memory=False)
    stats=pd.read_csv(verified(adapted['player_stats']),low_memory=False)
    roster=pd.read_csv(verified(adapted['weekly_roster']))
    games=pd.read_csv(verified(raw['games']));identity=pd.read_csv(verified(raw['identity']),low_memory=False)
    cert,game_audit,actors,missing=certify(pbp,games,roster,stats,identity,event['rule_support'],vr['requested_seasons'])
    prepared=[]
    for signature in contract['scoring_signatures']:
        entry=next(row for row in batch['profiles'] if row['scoring_signature']==signature)
        receipt=json.loads(Path(entry['outcome_report']['path']).read_text())
        profile=json.loads(verified(receipt['inputs']['scoring']).read_text())
        scope(profile['scoring_settings'],signature,contract)
        unit=next(row for row in vr['units'] if row['scoring_signature']==signature)
        # Copied v1 sources are portable; no current-profile/stat substitution.
        source=validation_report.parent/'sources'/Path(unit['source_labels']['path']).name
        if digest(source)!=unit['source_labels']['sha256']:raise ValueError('WAIVER_POPULATION_FROZEN_LABEL_CHANGED')
        outcomes=pd.read_csv(source)
        prepared.append((signature,outcomes,unit['source_labels'],profile['scoring_settings'],receipt['inputs']['scoring']))
    output_dir.mkdir(parents=True)
    def save(name,frame):
        p=output_dir/name;frame.to_csv(p,index=False,compression={'method':'gzip','mtime':0})
        return {'path':str(p),'sha256':digest(p),'rows':len(frame)}
    certificate=save('zero-certificates.csv.gz',cert)
    audit=save('game-proof-audit.csv.gz',game_audit)
    actor_binding=save('actor-occurrence-index.csv.gz',actors)
    backstop=save('published-scorer-absence-audit.csv.gz',missing)
    event_source=verified(event['event_weekly_stats'])
    event_copy=output_dir/'event-weekly-stats.csv.gz';shutil.copy2(event_source,event_copy)
    event_binding={'path':str(event_copy),'sha256':digest(event_copy)}
    profiles=[]
    for signature,outcomes,source,scoring,scoring_source in prepared:
        scoring_path=output_dir/f'{signature}-scoring-profile.json';shutil.copy2(verified(scoring_source),scoring_path)
        new,filled=extend(outcomes,cert,certificate['sha256'])
        global_binding=None
        if global_identity_closure:
            event_weekly=pd.read_csv(verified(event['event_weekly_stats']))
            new,global_proofs=close_identity_calendar(new,stats,event_weekly,game_audit,actors,games,scoring,event['rule_support'])
            global_binding=save(f'{signature}-global-identity-proofs.csv.gz',global_proofs)
            new['global_identity_proof_sha256']=np.where(new.target_only_row,global_binding['sha256'],None)
        labels=label_frame(new,signature,vr['requested_seasons'])
        label_binding=save(f'{signature}-expanded-targets.csv.gz',labels)
        units=[]
        for unit in vr['units']:
            if unit['scoring_signature']!=signature:continue
            binding=unit['artifacts']['predictions'];pred=validation_report.parent/Path(binding['path']).name
            if digest(pred)!=binding['sha256']:raise ValueError('WAIVER_POPULATION_ISSUED_FORECAST_CHANGED')
            evaluation,joined=stress(pd.read_csv(pred),labels)
            paired=save(f'{signature}-{unit["position"]}-stress.csv.gz',joined)
            units.append({'position':unit['position'],'frozen_forecasts':binding,'stress_artifact':paired,
                          'seasons':evaluation,'forecast_eligible':False,'ranking_eligible':False,
                          'recommendation_eligible':False,'transaction_eligible':False})
        profiles.append({'scoring_signature':signature,'source_labels':source,'expanded_labels':label_binding,
                         'certified_zero_rows_added':filled,'complete_next3_targets':int(labels[FULL].map(_true).sum()),'units':units})
        profiles[-1]['global_identity_proofs']=global_binding
        profiles[-1]['scoring_profile']={'path':str(scoring_path),'sha256':digest(scoring_path)}
        if global_identity_closure:
            profiles[-1]['complete_next3_targets_original_decision_rows']=int((labels[FULL].map(_true)&~labels.target_only_row.map(_true)).sum())
    report={'schema':SCHEMA,'diagnostic_only':True,'activation_eligible':False,'builder_sha256':digest(Path(__file__)),
            'contract':{'path':str(CONTRACT),'sha256':digest(CONTRACT)},
            'frozen_validation_report':{'path':str(validation_report),'sha256':digest(validation_report)},
            'source_batch':{'path':str(source_batch),'sha256':digest(source_batch)},'raw_source_snapshot':raw,
            'game_proof_audit':audit,'actor_index':actor_binding,'published_absence_audit':backstop,'certificates':certificate,
            'event_weekly_stats':event_binding,'event_rule_support':event['rule_support'],
            'game_count':len(game_audit),'ready_games':int(game_audit.proof_ready.sum()),
            'ready_weeks':int(game_audit.groupby(['season','week']).proof_ready.all().sum()),
            'profiles':profiles,'source_player_stats_complete_asserted':False,'model_refitted':False,
            'global_identity_closure':global_identity_closure,
            'global_contract':{'path':str(GLOBAL_CONTRACT),'sha256':digest(GLOBAL_CONTRACT)} if global_identity_closure else None,
            'limitations':['Future roster/bye membership stays unknown; only a stronger global event proof may resolve its point score.','Source zero certificates are restricted to the declared scoring signatures/rules.',
                           'Reused outer forecasts are a post-selection population stress audit, not independent confirmation.',
                           'Publication timing, live feature parity, free-agent utility and promotion remain blocked.']}
    (output_dir/'population-report.json').write_text(json.dumps(report,indent=2,sort_keys=True,allow_nan=False)+'\n')
    return report


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--validation-report',type=Path,required=True);parser.add_argument('--source-batch-report',type=Path,required=True)
    parser.add_argument('--output-dir',type=Path,required=True);args=parser.parse_args()
    r=run(args.validation_report,args.source_batch_report,args.output_dir,global_identity_closure=True)
    print(json.dumps({'certificates':r['certificates']['rows'],'ready_games':r['ready_games'],'ready_weeks':r['ready_weeks'],
                      'targets':{p['scoring_signature']:p['complete_next3_targets'] for p in r['profiles']},'activation_eligible':False},sort_keys=True))


if __name__=='__main__':main()
