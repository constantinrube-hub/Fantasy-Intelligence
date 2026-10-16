"""Resumable bounded additional-profile research: profiles, unit batches, freeze."""
from __future__ import annotations
import argparse,gc,json,tempfile
from pathlib import Path
import pandas as pd
from archive_waiver_expansion_sources import BASE,csv
from prospective_research_io import sha,binding,now,write,verified,gates,encoded
from waiver_v2_scoped_sources import component_sources,profile_outcomes
from waiver_v2_event_ledger import build_e5_event_ledger
from build_waiver_v2_label_batch import label_frame
from waiver_v2_validation import features,evaluate,select,fit,policy,KEYS,TARGET,FULL

ROOT=Path(__file__).resolve().parents[1]
CONTRACT='config/waiver-v2-expanded-methodology.json'
OLD='data/research/waiver-v2/model-validation/2026-10-12/revision-1/sources'

def methodology(root):
    declared=json.loads((root/CONTRACT).read_text());original=policy()
    for key in original:
        if key not in {'schema','status','signatures','uncertainty'} and declared.get(key)!=original[key]:raise ValueError('EXPANDED_NUMERICAL_METHOD_CHANGED')
    expected=dict(original['uncertainty']);expected['comparison_family_size']=len(declared['signatures'])*4
    expected['multiplicity']='Bonferroni tail levels across all declared additional signatures and four positions; no pooling or best-profile selection'
    if expected!=declared['uncertainty']:raise ValueError('EXPANDED_UNCERTAINTY_METHOD_CHANGED')
    return declared

def source_inputs(root):
    base=root/BASE;s=base/'sources';raw=json.loads((s/'source-receipts.json').read_text());shared=base/'shared';shared.mkdir(exist_ok=True)
    refs={k:binding(root,p,now()) for k,p in {'stats':s/'offensive-stats.csv.gz','reconciliation_stats':s/'all-position-stats.csv.gz',
        'roster':root/OLD/'weekly-roster.csv.gz','identity':s/'identity.csv.gz','games':s/'games.csv.gz','source_receipts':s/'source-receipts.json',
        'event_owner':root/'research/waiver_v2_event_ledger.py','scoring_owner':root/'research/waiver_v2_outcomes.py',
        'source_owner':root/'research/waiver_v2_scoped_sources.py','scoring_contract':root/'config/contracts/runtime-contracts.json'}.items()}
    for item in raw['pbp_sources']:refs['pbp_'+str(item['season'])]=item
    signature={k:v['sha256'] for k,v in refs.items()};cache=shared/'input-hashes.json'
    if cache.exists() and json.loads(cache.read_text())!=signature:raise ValueError('EXPANDED_DRAFT_INPUT_DRIFT_REQUIRES_NEW_REVISION')
    write(cache,signature)
    stats=pd.read_csv(s/'offensive-stats.csv.gz',low_memory=False);allstats=pd.read_csv(s/'all-position-stats.csv.gz',low_memory=False)
    pbp=pd.concat([pd.read_csv(verified(root,i,now()),low_memory=False) for i in raw['pbp_sources']],ignore_index=True,sort=False)
    report_path=shared/'events-report.json'
    if not report_path.exists():
        with tempfile.TemporaryDirectory(prefix='fie-expanded-source-') as tmp:
            path=Path(tmp)/'pbp.csv.gz';csv(pbp,path)
            build_e5_event_ledger(raw_pbp_path=path,identity_path=s/'identity.csv.gz',canonical_player_stats_path=s/'offensive-stats.csv.gz',
                canonical_return_stats_path=s/'all-position-stats.csv.gz',requested_seasons=raw['training_seasons'],pbp_source_items=raw['pbp_sources'],
                output_path=shared/'events.csv.gz',weekly_stats_output_path=shared/'weekly.csv.gz',report_path=report_path)
    report=json.loads(report_path.read_text())
    if report['phase']!='E5_LONG_PLAY_COUNTERS' or report['fumble_lost_reconciliation']['status']!='EXACT_EVENT_READY' or sha(shared/'events.csv.gz')!=report['event_ledger']['sha256']:raise ValueError('EXPANDED_CORE_SOURCE_OR_CACHE_BLOCKED')
    events=pd.read_csv(shared/'events.csv.gz',low_memory=False)
    blocker_path=shared/Path(report['blockers']['path']).name
    blockers=[json.loads(line) for line in blocker_path.read_text().splitlines() if line]
    weekly,support,excluded=component_sources(pbp,stats,events,report,blockers,allstats)
    csv(weekly,shared/'scoped-weekly.csv.gz');write(shared/'scope.json',{'effective_support':support,'original_support':report['rule_support'],'exclusions':excluded,'raw_blockers':blockers})
    for name,path in {'events':shared/'events.csv.gz','event_report':report_path,'scoped_weekly':shared/'scoped-weekly.csv.gz','scope':shared/'scope.json'}.items():refs[name]=binding(root,path,now())
    games=pd.read_csv(s/'games.csv.gz',low_memory=False);games=games[games.season.isin(raw['training_seasons'])&games.game_type.eq('REG')]
    args=(pbp,stats,pd.read_csv(root/OLD/'weekly-roster.csv.gz',low_memory=False),games,pd.read_csv(s/'identity.csv.gz',low_memory=False),weekly,support,excluded)
    return args,refs

def prepare_profiles(root):
    contract=methodology(root);base=root/BASE;args,refs=source_inputs(root);stats=args[1];games=args[3]
    registry=json.loads((root/'data/research/leagues/registry.json').read_text())['leagues'];groups={}
    for lid,row in registry.items():
        if not row.get('enabled',True) or not row.get('current_refresh',True) or lid=='1400388486179123200':continue
        profile=json.loads((root/row['profile_path']).read_text());sig=profile['scoring_signature']
        if sig in contract['signatures']:groups.setdefault(sig,{'settings':profile['scoring_settings'],'league_ids':[]})['league_ids'].append(lid)
    if set(groups)!=set(contract['signatures']):raise ValueError('EXPANDED_PROFILE_UNIVERSE_DRIFT')
    profiles=[]
    for sig,group in sorted(groups.items()):
        dest=base/'profiles'/sig;dest.mkdir(parents=True,exist_ok=True);done=dest/'profile.json'
        if done.exists():
            item=json.loads(done.read_text())
            for ref in item['artifacts'].values():verified(root,ref,now())
            profiles.append(item);print('PROFILE_PRESERVED',sig,flush=True);continue
        print('PROFILE_BUILD',sig,flush=True)
        outcomes,audit,proofs=profile_outcomes(*args,group['settings']);labels=label_frame(outcomes,sig,contract['seasons'])
        csv(outcomes,dest/'outcomes.csv.gz');csv(labels,dest/'labels.csv.gz');csv(audit,dest/'game-proof-audit.csv.gz')
        write(dest/'scoring.json',{'scoring_signature':sig,'scoring_settings':group['settings']})
        decision=outcomes[~outcomes.target_only_row.fillna(False).astype(bool)&(outcomes.week+3<=outcomes.season.map(games.groupby('season').week.max()))]
        for pos in contract['positions']:
            f=features(outcomes,stats,pos,contract);f=f[pd.MultiIndex.from_frame(f[KEYS]).isin(pd.MultiIndex.from_frame(decision[KEYS]))]
            csv(f,dest/f'{pos}-features.csv.gz')
        ready=audit.groupby(['season','week']).proof_ready.all()
        paths={'outcomes':dest/'outcomes.csv.gz','labels':dest/'labels.csv.gz','scoring':dest/'scoring.json','game_audit':dest/'game-proof-audit.csv.gz'}
        paths.update({pos+'_features':dest/f'{pos}-features.csv.gz' for pos in contract['positions']})
        item={'scoring_signature':sig,'league_ids':group['league_ids'],'prepared_at':now(),'complete_next3_targets':int(labels[FULL].sum()),
              'excluded_outcomes':int(outcomes.outcome_status.eq('BLOCKED_SCOPED_EVENT_ATTRIBUTION').sum()),
              'whole_nfl_ready_weeks':[[int(s),int(w)] for (s,w),ok in ready.items() if ok],
              'artifacts':{k:binding(root,p,now()) for k,p in paths.items()},**gates(['BLOCKED_RESEARCH_ONLY'])}
        write(done,item);profiles.append(item);print('PROFILE_COMPLETE',sig,'targets',item['complete_next3_targets'],flush=True)
    value={'schema':'fie-expanded-prepared-profiles-v1','prepared_at':now(),'profiles':profiles,'inputs':refs,
           'methodology':binding(root,root/CONTRACT,now()),'feature_owner':binding(root,root/'research/waiver_v2_validation.py',now()),**gates(['BLOCKED_RESEARCH_ONLY'])}
    write(base/'prepared-profiles.json',value);return value

def train_unit(root,sig,pos):
    contract=methodology(root);base=root/BASE;prep=json.loads((base/'prepared-profiles.json').read_text())
    for ref in [prep['methodology'],prep['feature_owner'],*prep['inputs'].values()]:verified(root,ref,now())
    p=next(x for x in prep['profiles'] if x['scoring_signature']==sig);dest=base/'models';dest.mkdir(exist_ok=True);out=dest/f'{sig}-{pos}-unit.json'
    if out.exists():
        unit=json.loads(out.read_text())
        for ref in [unit['features'],unit['labels'],unit['predictions'],unit['folds']]:verified(root,ref,now())
        print('UNIT_PRESERVED',sig,pos,flush=True);return unit
    f=pd.read_csv(verified(root,p['artifacts'][pos+'_features'],now()),low_memory=False);labels=pd.read_csv(verified(root,p['artifacts']['labels'],now()),low_memory=False)
    result,pred,folds=evaluate(f,labels,contract)
    pair=f.merge(labels[KEYS+[TARGET,FULL]],on=KEYS,how='left',validate='one_to_one');pair['label_complete']=pair[FULL].fillna(False).astype(bool)
    choice,audit=select(pair,contract);model=fit(pair,choice,contract) if choice else None
    csv(pred,dest/f'{sig}-{pos}-predictions.csv.gz');write(dest/f'{sig}-{pos}-folds.json',folds)
    at=now();unit={'scoring_signature':sig,'position':pos,'model':model,'selection_audit':audit,'trained_at':at,
        'historical_research_signal':result['research_signal_passed'],'metrics':result,'research_interpretation':'REUSED_HISTORICAL_SEASONS_EXPLORATORY',
        'features':p['artifacts'][pos+'_features'],'labels':p['artifacts']['labels'],
        'predictions':binding(root,dest/f'{sig}-{pos}-predictions.csv.gz',at),'folds':binding(root,dest/f'{sig}-{pos}-folds.json',at),
        **gates(['BLOCKED_PROSPECTIVE_CONFIRMATION','BLOCKED_DECISION_DOMAIN','BLOCKED_PROMOTION_REVIEW'])}
    write(out,unit);print('UNIT_COMPLETE',sig,pos,'model',bool(model),'signal',unit['historical_research_signal'],flush=True);return unit

def freeze(root):
    base=root/BASE;contract=methodology(root);prep=json.loads((base/'prepared-profiles.json').read_text());units=[]
    for sig in contract['signatures']:
        for pos in contract['positions']:
            path=base/'models'/f'{sig}-{pos}-unit.json'
            if not path.exists():raise ValueError('EXPANDED_UNITS_INCOMPLETE:'+sig+' '+pos)
            u=json.loads(path.read_text())
            for ref in [u['features'],u['labels'],u['predictions'],u['folds']]:verified(root,ref,now())
            units.append(u)
    at=now();lock={'schema':'fie-waiver-v2-expanded-lock-v1','season':2026,'frozen_at':at,'horizon_weeks':3,'baseline':'same_cutoff_fp_prior_4',
        'profiles':prep['profiles'],'units':units,'methodology':prep['methodology'],'feature_owner':prep['feature_owner'],
        'source_owner':binding(root,root/'research/waiver_v2_scoped_sources.py',at),'inputs':prep['inputs'],'training_seasons':contract['seasons'],
        'parameters_selected_from_2026':False,'independent_confirmation':False,**gates(['BLOCKED_RESEARCH_ONLY'])}
    write(base/'model-lock.json',lock)
    write(root/'config/waiver-v2-expanded-scope.json',{'schema':'fie-waiver-v2-expanded-scope-v1','base':BASE,'model_lock_sha256':sha(base/'model-lock.json'),'signatures':contract['signatures'],'excluded_active_league':'1400388486179123200',**gates(['BLOCKED_RESEARCH_ONLY'])})
    print('LOCK_FROZEN',len(units),at,flush=True);return lock

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--root',type=Path,default=ROOT);p.add_argument('--phase',choices=['profiles','unit','freeze'],required=True);p.add_argument('--signature');p.add_argument('--position');a=p.parse_args()
    if a.phase=='profiles':prepare_profiles(a.root)
    elif a.phase=='unit':train_unit(a.root,a.signature,a.position)
    else:freeze(a.root)
