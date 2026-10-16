"""C0/C1 source-bound outcome ledgers. No fitting, issuance or promotion."""
from __future__ import annotations
import argparse
from collections import defaultdict
from datetime import datetime, timezone
import gzip
import hashlib
import io
import json
from pathlib import Path
import re

import numpy as np
import pandas as pd

from component_registry import ROOT, build, digest
from component_source_contract import (PLAYER_FIELDS, EVENT_FIELDS, PROVIDER_OVERRIDES,
                                       DST_PLAYER_FIELDS, SEMANTIC_SOURCES, position, team, source_definition)

BASE = Path('data/research/components/2026-10-14/c0-c1-v1')
HISTORY = Path('data/research/waiver-expanded/2026/recovery-1')
ENVELOPE = Path('data/research/prospective/weekly-sources/2026/week_06/20261014T140737440892Z/source-envelope.json')
KEYS = ['canonical_player_id','season','week']
GSIS = re.compile(r'^00-\d{7}$')
MEMBERS = {'ACT','DEV','E14','EXE','INA','PUP','RES','RSN','SUS'}
# The schedule omits this cancelled game. It is not an ordinary bye and has
# no comparable completed NFL outcome; league-specific substitutions differ.
CALENDAR_EXCEPTIONS = {(2022,17,'BUF'),(2022,17,'CIN')}

def write_json(path, value):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, indent=2, sort_keys=True, allow_nan=False)+'\n')

def csv(frame, path):
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open('wb') as out:
        with gzip.GzipFile(filename='', mode='wb', fileobj=out, mtime=0) as gz:
            with io.TextIOWrapper(gz,encoding='utf-8',newline='') as stream:
                frame.to_csv(stream,index=False,float_format='%.10g')

def verified(root, ref):
    path = (root/ref['path']).resolve()
    if not path.is_relative_to(root.resolve()):
        raise ValueError('COMPONENT_SOURCE_OUTSIDE_ROOT')
    if digest(path) != ref['sha256']:
        raise ValueError('COMPONENT_SOURCE_HASH_MISMATCH:' + ref['path'])
    clock = datetime.fromisoformat(ref['observed_at'])
    if clock.tzinfo is None:
        raise ValueError('COMPONENT_SOURCE_CLOCK_NOT_AWARE')
    if clock > datetime.now(timezone.utc):
        raise ValueError('COMPONENT_SOURCE_CLOCK_IN_FUTURE')
    return path

def regular(frame, through_week):
    column = 'season_type' if 'season_type' in frame else 'game_type'
    if column not in frame:
        raise ValueError('COMPONENT_MISSING_SEASON_TYPE')
    out = frame[frame[column].astype(str).str.upper().isin({'REG','REGULAR'})].copy()
    out['week'] = pd.to_numeric(out.week,errors='raise').astype(int)
    out['season'] = pd.to_numeric(out.season,errors='raise').astype(int)
    return out[out.week.between(1,through_week)].copy()

def additive(frame, fields):
    if not set(fields) <= set(frame):
        return pd.Series(np.nan,index=frame.index,dtype=float)
    numbers = frame[list(fields)].apply(pd.to_numeric,errors='coerce')
    if (numbers.notna() & ~np.isfinite(numbers)).any().any():
        raise ValueError('COMPONENT_NONFINITE_SOURCE_VALUE')
    # min_count prevents either partial sums or all-null sums becoming zero.
    return numbers.sum(axis=1,min_count=len(fields))

def band_indicator(values, lower, upper):
    values = pd.to_numeric(values,errors='coerce')
    mask = values.ge(lower)
    if upper is not None:
        mask &= values.le(upper)
    return mask.astype(float).where(values.notna())

def missed_distance_counts(frame, lower, upper):
    results = []
    for row in frame[['fg_missed','fg_blocked','fg_missed_list','fg_blocked_list']].itertuples(index=False):
        values = []; valid = True
        for count, distances in [(row.fg_missed,row.fg_missed_list),(row.fg_blocked,row.fg_blocked_list)]:
            if pd.isna(count):
                valid = False; break
            text = '' if pd.isna(distances) else str(distances).strip()
            if text and not re.fullmatch(r'\d+(?:\.0)?(?:[,; ]+\d+(?:\.0)?)*',text):
                valid = False; break
            parsed = [float(x) for x in re.split(r'[,; ]+',text) if x]
            if count != len(parsed):
                valid = False; break
            values.extend(parsed)
        results.append(float(sum(v >= lower and (upper is None or v <= upper) for v in values)) if valid else np.nan)
    return pd.Series(results,index=frame.index,dtype=float)

def identity_bridge(players, ff, sleeper, rosters):
    pairs = defaultdict(set); evidence = defaultdict(set)
    def add(gsis, provider, origin):
        gsis = str(gsis).strip(); provider = str(provider).strip().removesuffix('.0')
        if GSIS.fullmatch(gsis) and provider.isdigit():
            pairs[gsis].add(provider); evidence[(gsis,provider)].add(origin)
    for pid,row in sleeper.items():
        add(row.get('gsis_id'),pid,'SLEEPER_PLAYERS_EXACT_GSIS')
    for row in ff[['gsis_id','sleeper_id']].itertuples(index=False):
        add(row.gsis_id,row.sleeper_id,'FF_PLAYERIDS_EXACT_CROSSWALK')
    for raw in rosters:
        if {'gsis_id','sleeper_id'} <= set(raw):
            for row in raw[['gsis_id','sleeper_id']].drop_duplicates().itertuples(index=False):
                add(row.gsis_id,row.sleeper_id,'NFLVERSE_ROSTER_EXACT_CROSSWALK')
    # Exact secondary ID joins close missing GSIS entries without name matching.
    catalogs = [players, *rosters]
    secondary = {key:defaultdict(set) for key in ['espn_id','pfr_id','sportradar_id']}
    for catalog in catalogs:
        for key,lookup in secondary.items():
            if not {'gsis_id',key} <= set(catalog):
                continue
            for gsis,other in catalog[['gsis_id',key]].dropna().drop_duplicates().itertuples(index=False,name=None):
                gsis=str(gsis).strip(); other=str(other).strip().removesuffix('.0')
                if GSIS.fullmatch(gsis) and other:
                    lookup[other].add(gsis)
    for pid,row in sleeper.items():
        for key,lookup in secondary.items():
            matches = lookup.get(str(row.get(key)).strip().removesuffix('.0'),set())
            if len(matches)==1:
                add(next(iter(matches)),pid,'EXACT_SLEEPER_NFLVERSE_'+key.upper())
    for key,lookup in secondary.items():
        if key in ff:
            for pid,other in ff[['sleeper_id',key]].dropna().drop_duplicates().itertuples(index=False,name=None):
                matches = lookup.get(str(other).strip().removesuffix('.0'),set())
                if len(matches)==1:
                    add(next(iter(matches)),pid,'EXACT_FF_NFLVERSE_'+key.upper())
    reverse = defaultdict(set)
    for gsis,pids in pairs.items():
        for pid in pids:
            reverse[pid].add(gsis)
    rows = []
    pfr_map = {}
    for catalog in catalogs:
        if {'gsis_id','pfr_id'} <= set(catalog):
            for gsis,other in catalog[['gsis_id','pfr_id']].dropna().drop_duplicates().itertuples(index=False,name=None):
                gsis=str(gsis).strip(); pfr_map.setdefault(gsis,set()).add(str(other))
    ids = set(players.gsis_id.dropna().astype(str).str.strip()) | set(pairs) | set(pfr_map)
    for gsis in sorted(ids):
        if not GSIS.fullmatch(gsis):
            continue
        pids = pairs[gsis]
        valid = len(pids)==1 and len(reverse[next(iter(pids))])==1
        pid = next(iter(pids)) if valid else None
        pfrs = sorted(pfr_map.get(gsis,[]))
        rows.append({'canonical_player_id':gsis,'sleeper_id':pid,
                     'pfr_id':pfrs[0] if len(pfrs)==1 else None,
                     'identity_status':'EXACT_ONE_TO_ONE' if valid else ('UNKNOWN_NO_PROVIDER_BINDING' if not pids else 'UNKNOWN_CONFLICTING_CROSSWALK'),
                     'candidate_sleeper_ids':';'.join(sorted(pids)),
                     'binding_evidence':';'.join(sorted(evidence[(gsis,pid)])) if valid else '',
                     'current_eligibility_only':True})
    return pd.DataFrame(rows)

def normalize_population(raw, roster, games, season, limit):
    raw = regular(raw,limit); roster = regular(roster,limit)
    raw = raw[raw.season.eq(season)].copy(); roster = roster[roster.season.eq(season)].copy()
    invalid = ~raw.player_id.astype(str).str.strip().str.fullmatch(GSIS.pattern)
    aggregate_excluded = int(invalid.sum()); raw = raw[~invalid].copy()
    raw['canonical_player_id'] = raw.player_id.astype(str).str.strip()
    if raw.duplicated(KEYS).any():
        raise ValueError('COMPONENT_DUPLICATE_PLAYER_WEEK')
    raw['team'] = raw.team.map(team); raw['position_model'] = raw.position.map(position)
    membership = roster.status.astype(str).isin(MEMBERS)
    if 'status_description_abbr' in roster:
        membership |= roster.status_description_abbr.eq('A01')
    roster = roster[membership & roster.gsis_id.astype(str).str.strip().str.fullmatch(GSIS.pattern)].copy()
    roster['canonical_player_id'] = roster.gsis_id.astype(str).str.strip()
    roster['team'] = roster.team.map(team); roster['position_model'] = roster.position.map(position)
    # Multiple week/team memberships are retained as uncertainty, never selected by order.
    members = roster.groupby(KEYS,as_index=False).agg(
        roster_team=('team',lambda s:s.iloc[0] if s.nunique()==1 else None),
        roster_position=('position_model',lambda s:s.iloc[0] if s.nunique()==1 else None),
        membership_status=('status',lambda s:';'.join(sorted(set(s.astype(str))))),
        membership_team_count=('team','nunique'))
    members = members.merge(raw,on=KEYS,how='outer',validate='one_to_one',indicator=True)
    members['published_stat_row'] = members['_merge'].ne('left_only')
    members['team'] = members.team.where(members.published_stat_row,members.roster_team)
    members['position_model'] = members.position_model.where(members.published_stat_row,members.roster_position)
    calendar = []
    for g in games.itertuples(index=False):
        if int(g.season)!=season or int(g.week)>limit or g.game_type!='REG':
            continue
        complete = pd.notna(g.home_score) and pd.notna(g.away_score)
        for club,opp in [(g.home_team,g.away_team),(g.away_team,g.home_team)]:
            calendar.append({'season':season,'week':int(g.week),'team':team(club),
                             'calendar_game_id':g.game_id,'opponent':team(opp),'game_complete':complete})
    cal = pd.DataFrame(calendar)
    if cal.duplicated(['season','week','team']).any():
        raise ValueError('COMPONENT_DUPLICATE_TEAM_WEEK')
    members = members.merge(cal,on=['season','week','team'],how='left',validate='many_to_one')
    conflict = members.published_stat_row & members.calendar_game_id.notna() & members.game_id.ne(members.calendar_game_id)
    if conflict.any():
        raise ValueError('COMPONENT_PLAYER_GAME_CALENDAR_MISMATCH')
    members['game_id'] = members.calendar_game_id
    completed_weeks = set(cal.groupby('week').game_complete.all().loc[lambda s:s].index)
    exception = pd.Series([(int(r.season),int(r.week),r.team) in CALENDAR_EXCEPTIONS
                           for r in members.itertuples()],index=members.index)
    bye = (members.team.notna() & members.calendar_game_id.isna() & ~exception &
           members.week.isin(completed_weeks) & members.membership_team_count.eq(1))
    members['week_state'] = np.select([bye,members.game_complete.eq(True)],['PROVEN_BYE','COMPLETED_GAME'],default='UNKNOWN_GAME_OR_TEAM')
    return members.drop(columns=['_merge','calendar_game_id']),cal,{'aggregate_rows_excluded':aggregate_excluded,
              'multiple_membership_rows':int(members.membership_team_count.gt(1).sum())}

def provider_frame(root, refs, bridge):
    binding = dict(zip(bridge.dropna(subset=['sleeper_id']).sleeper_id,
                       bridge.dropna(subset=['sleeper_id']).canonical_player_id))
    rows = []; unresolved = []
    for ref in refs:
        if ref['week'] is None:
            continue
        payload = json.loads(gzip.decompress(verified(root,ref).read_bytes()))
        for pid,stats in sorted(payload.items()):
            # TEAM_* entries are provider team offense aggregates, not D/ST.
            if pid.startswith('TEAM_'):
                continue
            if re.fullmatch(r'[A-Z]{2,3}',pid):
                canonical = 'TEAM:'+team(pid)
            else:
                canonical = binding.get(pid)
            if canonical is None:
                unresolved.append({'sleeper_id':pid,'season':ref['season'],'week':ref['week'],'reason':'UNKNOWN_EXACT_IDENTITY'})
                continue
            numeric = {}
            for key,value in stats.items():
                if isinstance(value,bool) or not isinstance(value,(float,int)) or not np.isfinite(value):
                    continue
                numeric[key] = float(value)
            rows.append({**numeric,'canonical_player_id':canonical,'season':ref['season'],
                         'week':ref['week'],'provider_source_path':ref['path']})
    result = pd.DataFrame(rows)
    if result.duplicated(KEYS).any():
        raise ValueError('COMPONENT_PROVIDER_DUPLICATE_CANONICAL_WEEK')
    return result, pd.DataFrame(unresolved,columns=['sleeper_id','season','week','reason'])

def apply_components(population, demand, events, provider):
    pop = population.copy()
    if events is not None:
        pop = pop.merge(events,on=KEYS,how='left',validate='one_to_one')
    provider = provider.rename(columns={c:'provider_'+c for c in provider if c not in KEYS})
    pop = pop.merge(provider,on=KEYS,how='left',validate='one_to_one')
    rules = defaultdict(list)
    for r in demand['rules']:
        rules[r['component']].append(r)
    definitions = {c['component']:c for c in demand['required_components']}
    for component in PLAYER_FIELDS:
        definitions.setdefault(component,{'component':component,'mode':'mean',
            'unit':'yards' if 'yards' in component else 'count','event_bounds':None})
    for component in ['dst_points_allowed','dst_net_yards_allowed','dst_prob_pts_allow_21_27']:
        definitions.setdefault(component,{'component':component,'mode':'mean','unit':'count','event_bounds':None})
    outputs = {}; coverage = []; mismatches = []
    for component,spec in sorted(definitions.items()):
        relevant = set(p for r in rules[component] for p in r['positions'])
        applicable = (pop.position_model.isin(relevant) if relevant else
                      pop.position_model.eq('DEF') if component.startswith('dst_') else pop.position_model.ne('DEF'))
        value = pd.Series(np.nan,index=pop.index,dtype=float)
        source = pd.Series('UNRESOLVED',index=pop.index,dtype=object)
        if component in PLAYER_FIELDS:
            value = additive(pop,PLAYER_FIELDS[component]); source[:] = 'NFLVERSE_PLAYER_WEEK'
            if component in {'passing_first_downs','rushing_first_downs','receiving_first_downs'}:
                td_field = component.removesuffix('_first_downs')+'_tds'
                value = value - pd.to_numeric(pop.get(td_field,pd.Series(np.nan,index=pop.index)),errors='coerce')
                source[:] = 'NFLVERSE_FIRST_DOWNS_MINUS_TDS'
                # Lateral attribution/corrections can make a simple subtraction
                # invalid. Preserve the native totals and require an explicit
                # provider outcome rather than clamp the result to zero.
                negative = value.lt(0)
                value.loc[negative] = np.nan
                source.loc[negative] = 'UNKNOWN_FIRST_DOWN_TD_ACCOUNTING'
        elif component in DST_PLAYER_FIELDS:
            # Team totals use published player-week fields, not a position
            # subset. A missing addend invalidates that team/component.
            counts = additive(pop,DST_PLAYER_FIELDS[component])
            native = pop[pop.published_stat_row.eq(True) & pop.position_model.ne('DEF')][['season','week','team']].copy()
            native['value'] = counts.loc[native.index]
            totals = native.groupby(['season','week','team']).value.agg(lambda s:s.sum() if s.notna().all() else np.nan)
            value = pd.Series([totals.get((int(row.season),int(row.week),row.team),np.nan)
                               if row.position_model=='DEF' else np.nan for row in pop.itertuples()],index=pop.index)
            source[:] = 'NFLVERSE_PUBLISHED_TEAM_PLAYER_TOTALS'
        elif component in EVENT_FIELDS and EVENT_FIELDS[component] in pop:
            value = pd.to_numeric(pop[EVENT_FIELDS[component]],errors='coerce'); source[:] = 'SCOPED_EVENT_LEDGER'
        elif component.startswith('prob_'):
            kind = component.split('_')[1]
            field = {'pass':'passing_yards','rush':'rushing_yards','rec':'receiving_yards'}[kind]
            b = spec['event_bounds']; value = band_indicator(pop[field],b['lower_inclusive'],b['upper_inclusive'])
            source[:] = 'NFLVERSE_EXCLUSIVE_YARDAGE_BAND'
        elif component.startswith('kicker_fgmiss_') and {'fg_missed','fg_blocked','fg_missed_list','fg_blocked_list'} <= set(pop):
            band = component.removeprefix('kicker_fgmiss_')
            lower,upper = (int(band[:-1]),None) if band.endswith('p') else map(int,band.split('_'))
            value = missed_distance_counts(pop,lower,upper); source[:] = 'NFLVERSE_MISSED_AND_BLOCKED_DISTANCE_LISTS'
        elif component.startswith('dst_prob_pts_allow_') or component=='dst_points_allowed':
            points = pd.to_numeric(pop.get('provider_pts_allow',pd.Series(np.nan,index=pop.index)),errors='coerce')
            shutout = pd.to_numeric(pop.get('provider_pts_allow_0',pd.Series(np.nan,index=pop.index)),errors='coerce').eq(1)
            points = points.where(points.notna(),pd.Series(0.,index=pop.index).where(shutout))
            if component=='dst_points_allowed':
                value = points
            else:
                band = component.removeprefix('dst_prob_pts_allow_')
                lower,upper = ((int(band[:-1]),None) if band.endswith('p') else
                               (0,0) if band=='0' else tuple(map(int,band.split('_'))))
                value = band_indicator(points,lower,upper)
            source[:] = 'EXPLICIT_PROVIDER_POINTS_ALLOWED_TOTAL'
        elif component=='dst_net_yards_allowed':
            value = pd.to_numeric(pop.get('provider_yds_allow',value),errors='coerce')
            source[:] = 'EXPLICIT_PROVIDER_NET_YARDS_ALLOWED'
        keys = sorted(set(r['scoring_key'] for r in rules[component]))
        if component in PROVIDER_OVERRIDES:
            keys = [PROVIDER_OVERRIDES[component]]
        explicit = pd.Series(np.nan,index=pop.index,dtype=float)
        for key in keys:
            if 'provider_'+key in pop:
                found = pd.to_numeric(pop['provider_'+key],errors='coerce')
                disagreement = explicit.notna() & found.notna() & ~np.isclose(explicit,found,atol=1e-9,rtol=0)
                if disagreement.any():
                    raise ValueError('COMPONENT_PROVIDER_ALIAS_DISAGREEMENT:' + component)
                explicit = explicit.where(explicit.notna(),found)
        # Bonus values for QB TD/premiums reuse raw counts but provider keys may
        # be absent. Exact same raw component keys only enter reconciliation.
        if component=='rushing_touchdowns':
            explicit = pd.to_numeric(pop.get('provider_rush_td',explicit),errors='coerce')
        if component=='receptions':
            explicit = pd.to_numeric(pop.get('provider_rec',explicit),errors='coerce')
        conflict = value.notna() & explicit.notna() & ~np.isclose(value,explicit,atol=1e-9,rtol=0) & applicable
        for row in pop.loc[conflict,KEYS].itertuples(index=True):
            mismatches.append({'canonical_player_id':row.canonical_player_id,'season':int(row.season),'week':int(row.week),
                               'component':component,'independent_value':float(value.loc[row.Index]),
                               'provider_value':float(explicit.loc[row.Index])})
        # Independent outcomes remain available with an explicit parity mask.
        # Only provider-defined targets fall back to an explicit provider key.
        fill = value.isna() & explicit.notna()
        value.loc[fill] = explicit.loc[fill]; source.loc[fill] = 'EXPLICIT_SLEEPER_ACTUAL_STAT'
        status = pd.Series('UNKNOWN_ABSENT_SOURCE_VALUE',index=pop.index,dtype=object)
        status.loc[value.notna()] = 'OBSERVED'
        status.loc[value.eq(0)] = 'OBSERVED_ZERO'
        status.loc[conflict] = 'OBSERVED_SOURCE_PROVIDER_MISMATCH'
        invalid_game = ~pop.week_state.isin(['COMPLETED_GAME','PROVEN_BYE'])
        value.loc[invalid_game] = np.nan; status.loc[invalid_game] = 'UNKNOWN_GAME_OR_TEAM'
        bye = pop.week_state.eq('PROVEN_BYE') & applicable
        value.loc[bye] = 0.; status.loc[bye] = 'PROVEN_ZERO_BYE'; source.loc[bye] = 'WEEKLY_MEMBERSHIP_AND_COMPLETED_CALENDAR'
        value.loc[~applicable] = np.nan; status.loc[~applicable] = 'NOT_APPLICABLE'; source.loc[~applicable] = 'POSITION_ENTITY_CONTRACT'
        outputs[component] = value
        outputs[component+'__status'] = status
        outputs[component+'__source'] = source
        outputs[component+'__provider_parity'] = np.select(
            [~applicable,conflict,value.notna() & explicit.notna()],
            ['NOT_APPLICABLE','MISMATCH','MATCHED'],default='UNVERIFIED')
        outputs[component+'__score_target_eligible'] = (value.notna() & applicable & ~conflict &
            ~status.str.startswith('UNKNOWN'))
        for (year,pos),indices in pop.groupby(['season','position_model'],dropna=False).groups.items():
            s = status.loc[indices]; v = value.loc[indices]
            relevant_count = int(s.ne('NOT_APPLICABLE').sum())
            if relevant_count:
                coverage.append({'season':int(year),'position':str(pos),'component':component,
                    'applicable_rows':relevant_count,'known_rows':int(v.notna().sum()),
                    'unknown_rows':int((s.ne('NOT_APPLICABLE') & v.isna()).sum()),
                    'observed_zero_rows':int(s.eq('OBSERVED_ZERO').sum()),
                    'proven_bye_zero_rows':int(s.eq('PROVEN_ZERO_BYE').sum()),
                    'provider_mismatch_rows':int(s.eq('OBSERVED_SOURCE_PROVIDER_MISMATCH').sum()),
                    'value_sum':float(v.sum(min_count=1)) if v.notna().any() else None})
    metadata = ['canonical_player_id','season','week','game_id','team','opponent','position_model',
                'published_stat_row','membership_status','membership_team_count','week_state']
    return pd.concat([pop.reindex(columns=metadata),pd.DataFrame(outputs,index=pop.index)],axis=1),coverage,mismatches

def run(root, base, envelope_path, source_manifest=None):
    root = root.resolve(); base = root/base
    if not base.resolve().is_relative_to(root):
        raise ValueError('COMPONENT_OUTPUT_OUTSIDE_ROOT')
    base.mkdir(parents=True,exist_ok=True)
    if (base/'closure.json').exists():
        from validate_component_outcomes import validate
        validate(root,base.relative_to(root),tests=False)
        print('C0_C1_FROZEN_DATASET_PRESERVED_VERIFIED',flush=True)
        return
    demand = build(root); envelope = json.loads((root/envelope_path).read_text())
    current = {r['name']:r for r in envelope['responses']}
    if envelope['season']!=2026 or envelope['history_weeks_requested']!=[1,2,3,4,5]:
        raise ValueError('COMPONENT_CURRENT_SOURCE_SCOPE_CHANGED')
    archive = json.loads((root/HISTORY/'sources/source-receipts.json').read_text())
    source_manifest = source_manifest or BASE/'sources/manifest.json'
    captured = json.loads((root/source_manifest).read_text())
    if captured['failures']:
        raise ValueError('COMPONENT_CAPTURE_HAS_FAILURES')
    receipts = []; snapshots = {}
    for name in ['players','ff_playerids','weekly_rosters','player_week','schedule','snaps','pbp','sleeper_players']:
        ref = current[name]; verified(root,ref); receipts.append(ref)
        if name=='sleeper_players':
            snapshots[name] = json.loads(gzip.decompress((root/ref['path']).read_bytes()))
        else:
            snapshots[name] = pd.read_csv(root/ref['path'],low_memory=False,dtype={'sleeper_id':'string'})
    refs = captured['sources']; rosters = {2026:snapshots['weekly_rosters']}
    raw_stats = {2026:snapshots['player_week']}
    for year in range(2021,2026):
        ref = next(r for r in refs if r['season']==year and r['week'] is None)
        rosters[year] = pd.read_csv(verified(root,ref),low_memory=False,dtype={'sleeper_id':'string'}); receipts.append(ref)
        ref = next(r for r in archive['raw_player_stats'] if r['season']==year)
        raw_stats[year] = pd.read_csv(verified(root,ref),low_memory=False); receipts.append(ref)
    bridge = identity_bridge(snapshots['players'],snapshots['ff_playerids'],snapshots['sleeper_players'],list(rosters.values()))
    provider,unresolved = provider_frame(root,refs,bridge); receipts += [r for r in refs if r['week'] is not None]
    for name in ['scoped-weekly.csv.gz','scope.json','events-report.json','events.csv.gz','input-hashes.json']:
        path = root/HISTORY/'shared'/name
        receipts.append({'path':path.relative_to(root).as_posix(),'sha256':digest(path),
                         'observed_at':archive['pbp_sources'][-1]['observed_at'],
                         'clock_basis':'INHERITED_SOURCE_OBSERVATION_NOT_ORIGINAL_DERIVATION_TIME'})
    history_events = pd.read_csv(root/HISTORY/'shared/scoped-weekly.csv.gz',low_memory=False)
    # Authenticate reused derived archives against their frozen input hashes.
    frozen = json.loads((root/HISTORY/'shared/input-hashes.json').read_text())
    if digest(root/HISTORY/'sources/offensive-stats.csv.gz')!=frozen['stats']:
        raise ValueError('COMPONENT_HISTORICAL_EVENT_INPUT_DRIFT')
    old_report = json.loads((root/HISTORY/'shared/events-report.json').read_text())
    if digest(root/HISTORY/'shared/events.csv.gz')!=old_report['event_ledger']['sha256']:
        raise ValueError('COMPONENT_HISTORICAL_EVENT_LEDGER_DRIFT')
    # Bind scoped rows to the recorded exclusions/support; raw unscoped events
    # must never erase these nulls. A compact derived receipt freezes the reuse.
    write_json(base/'event-reuse-receipt.json',{'schema':'fie-component-event-reuse-v1',
        'source_namespace':HISTORY.as_posix(),'scoped_weekly_sha256':digest(root/HISTORY/'shared/scoped-weekly.csv.gz'),
        'scope_sha256':digest(root/HISTORY/'shared/scope.json'),'requested_seasons':[2021,2022,2023,2024,2025],
        'excluded_2018_from_this_dataset':True,'2019_2020_exact_fumble_admitted':False})
    # Current events are generated with the established owner in this new namespace.
    from waiver_v2_event_ledger import build_e5_event_ledger
    from waiver_v2_source_adapter import normalize_player_stats
    from waiver_v2_scoped_sources import component_sources
    current_raw = regular(raw_stats[2026],5)
    ids = sorted(set(current_raw.player_id.dropna().astype(str)))
    ident = pd.DataFrame({'gsis_id':[i for i in ids if GSIS.fullmatch(i)]})
    ident['canonical_player_id'] = ident.gsis_id
    allstats,_ = normalize_player_stats(current_raw,ident,offensive_only=False)
    stats = allstats[allstats.position_model.isin(['QB','RB','WR','TE'])].copy()
    scratch = base/'current-events'; scratch.mkdir(exist_ok=True)
    csv(ident,scratch/'identity.csv.gz'); csv(allstats,scratch/'all-stats.csv.gz'); csv(stats,scratch/'offense-stats.csv.gz')
    pbp = regular(snapshots['pbp'],5); csv(pbp,scratch/'pbp.csv.gz')
    pbp_ref = {**current['pbp'],'season':2026,'url':current['pbp']['endpoint']}
    report = build_e5_event_ledger(raw_pbp_path=scratch/'pbp.csv.gz',identity_path=scratch/'identity.csv.gz',
        canonical_player_stats_path=scratch/'offense-stats.csv.gz',canonical_return_stats_path=scratch/'all-stats.csv.gz',
        requested_seasons=[2026],pbp_source_items=[pbp_ref],output_path=scratch/'events.csv.gz',
        weekly_stats_output_path=scratch/'weekly.csv.gz',report_path=scratch/'report.json')
    blockers = [json.loads(line) for line in (scratch/Path(report['blockers']['path']).name).read_text().splitlines() if line]
    weekly,support,excluded = component_sources(pbp,stats,pd.read_csv(scratch/'events.csv.gz',low_memory=False),report,blockers,allstats)
    csv(weekly,scratch/'scoped-weekly.csv.gz'); write_json(scratch/'scope.json',{'support':support,'exclusions':excluded,'raw_blockers':blockers})
    totals = []; coverages = []; mismatches = []; audits = []
    games = snapshots['schedule']
    for year in range(2021,2027):
        limit = 5 if year==2026 else 18
        population,cal,audit = normalize_population(raw_stats[year],rosters[year],games,year,limit)
        clubs = sorted(set(cal.team))
        dense = pd.DataFrame([(year,w,club) for w in range(1,limit+1) for club in clubs],
                             columns=['season','week','team'])
        teams = dense.merge(cal,on=['season','week','team'],how='left',validate='one_to_one')
        teams['canonical_player_id'] = 'TEAM:'+teams.team
        teams['position_model'] = 'DEF'; teams['game_id'] = teams.pop('calendar_game_id')
        completed_weeks = set(cal.groupby('week').game_complete.all().loc[lambda s:s].index)
        team_bye = (teams.game_id.isna() & teams.week.isin(completed_weeks) &
                    ~pd.Series([(int(r.season),int(r.week),r.team) in CALENDAR_EXCEPTIONS for r in teams.itertuples()]))
        teams['week_state'] = np.select([teams.game_complete.eq(True),team_bye],
                                       ['COMPLETED_GAME','PROVEN_BYE'],default='UNKNOWN_GAME_OR_TEAM')
        teams['published_stat_row'] = False
        population = pd.concat([population,teams],ignore_index=True,sort=False)
        events = weekly if year==2026 else history_events[history_events.season.eq(year)]
        output,c,m = apply_components(population,demand,events,provider[provider.season.eq(year)])
        output = output.sort_values(['season','week','canonical_player_id']).reset_index(drop=True)
        csv(output,base/f'component-week-{year}.csv.gz')
        totals.append({'season':year,'through_week':limit,'entity_week_rows':len(output),
                       'player_week_rows':int(output.position_model.ne('DEF').sum()),
                       'dst_week_rows':int(output.position_model.eq('DEF').sum())})
        coverages += c; mismatches += m; audits.append({'season':year,**audit})
        print('C1_OUTCOMES',year,len(output),'rows',flush=True)
    csv(bridge,base/'identity-bridge.csv.gz'); csv(unresolved,base/'unresolved-provider-identities.csv.gz')
    csv(pd.DataFrame(coverages),base/'coverage.csv.gz')
    csv(pd.DataFrame(mismatches,columns=KEYS+['component','independent_value','provider_value']),base/'provider-reconciliation.csv.gz')
    # Current snap exposures use exact PFR -> GSIS, with no name fallback.
    snaps = regular(snapshots['snaps'],5)
    pfr = bridge.dropna(subset=['pfr_id'])[['canonical_player_id','pfr_id']].drop_duplicates()
    pfr = pfr[~pfr.pfr_id.duplicated(keep=False)]
    snaps = snaps.merge(pfr,left_on='pfr_player_id',right_on='pfr_id',how='left',validate='many_to_one')
    snaps['identity_status'] = np.where(snaps.canonical_player_id.notna(),'EXACT_PFR_GSIS','UNKNOWN_EXACT_IDENTITY')
    csv(snaps,base/'snap-exposures-2026.csv.gz')
    definitions = [{**c,'source_definition':source_definition(c['component'])} for c in demand['required_components']]
    demand['component_source_definitions'] = definitions
    demand['semantic_sources'] = SEMANTIC_SOURCES
    demand['semantic_audit_completed'] = True
    demand['source_semantics_verified'] = False
    write_json(base/'demand.json',demand)
    csv(pd.DataFrame(demand['rules']),base/'demand.csv.gz')
    demand_lines = ['# C0 component demand and source audit','',
        f"{demand['enabled_leagues']} enabled leagues; {demand['distinct_nonzero_configured_keys']} configured nonzero keys; "
        f"{demand['distinct_relevant_keys']} relevant keys; {len(definitions)} required component/probability outputs.",
        '', 'Registration and source-bound outcomes do not certify every provider convention or a complete forecast.', '',
        '| League | Relevant keys | Explicitly irrelevant configured keys |', '|---|---:|---:|']
    for league in demand['leagues']:
        demand_lines.append(f"| {league['league_name'].replace('|','/')} ({league['league_id']}) | "
                            f"{len(league['required_scoring_keys'])} | {len(league['irrelevant_configured_rules'])} |")
    demand_lines += ['', '| Component | Mode | Unit | Source method |', '|---|---|---|---|']
    for spec in definitions:
        demand_lines.append(f"| {spec['component']} | {spec['mode']} | {spec['unit']} | {spec['source_definition']['method']} |")
    (base/'demand.md').write_text('\n'.join(demand_lines)+'\n')
    write_json(base/'population-audit.json',audits)
    write_json(base/'calendar-exceptions.json',{'schema':'fie-component-calendar-exceptions-v1',
        'exceptions':[{'season':year,'week':week,'team':club,'status':'UNKNOWN_CANCELLED_GAME_NONSTANDARD_LEAGUE_SCORING'}
                       for year,week,club in sorted(CALENDAR_EXCEPTIONS)],
        'source':'https://www.nfl.com/news/week-17-buffalo-cincinnati-game-will-not-be-resumed-neutral-afc-championship-game-be',
        'policy':'NOT_A_BYE_NO_INFERRED_ZERO'})
    write_json(base/'source-receipts.json',{'schema':'fie-component-source-receipts-v1',
        'sources':receipts,'original_historical_publication_times_verified':False,
        'current_envelope_path':envelope_path.as_posix(),'current_envelope_sha256':digest(root/envelope_path),
        'provider_capture_manifest_path':source_manifest.as_posix(),
        'provider_capture_manifest_sha256':digest(root/source_manifest)})
    files = sorted(p for p in base.iterdir() if p.is_file() and p.name!='closure.json')
    write_json(base/'closure.json',{'schema':'fie-component-c0-c1-closure-v1',
        'status':'IMPLEMENTED_WITH_EXPLICIT_SOURCE_AND_PARITY_MASKS', 'c0_complete':True,
        'c1_outcome_pipeline_complete':True,'c1_all_score_targets_certified':False,
        'enabled_leagues':demand['enabled_leagues'],'distinct_relevant_keys':demand['distinct_relevant_keys'],
        'required_components':len(demand['required_components']),'seasons':totals,
        'provider_reconciliation_mismatch_rows':len(mismatches),
        'unresolved_provider_identity_rows':len(unresolved),
        'snap_identity_unknown_rows':int(snaps.canonical_player_id.isna().sum()),
        'sources_publication_timing':'HISTORICAL_EXPLORATORY_CURRENT_OBSERVED_CLOCKS',
        'model_fitted':False,'forecast_issued':False,'promotion_eligible':False,
        'transaction_eligible':False,
        'specialist_missing_stat_dnp_zeros_certified':False,
        'historical_snap_exposures_normalized':False,
        'artifacts':{p.relative_to(root).as_posix():digest(p) for p in files},
        'owners':{p:digest(root/p) for p in ['research/component_registry.py','research/component_source_contract.py',
            'research/build_component_outcomes.py','research/capture_component_outcome_sources.py',
            'config/component-projection-contract-v1.json','config/contracts/runtime-contracts.json']}})
    print('C0_C1_PIPELINE_COMPLETE_WITH_MASKS',len(definitions),'required components',flush=True)

def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--root',type=Path,default=ROOT)
    p.add_argument('--output',type=Path,default=BASE)
    p.add_argument('--current-envelope',type=Path,default=ENVELOPE)
    p.add_argument('--source-manifest',type=Path)
    a = p.parse_args(); run(a.root,a.output,a.current_envelope,a.source_manifest)

if __name__ == '__main__':
    main()
