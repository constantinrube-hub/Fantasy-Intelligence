"""All-profile scoring coverage and exact eligible-entity row population checks."""
import argparse,collections
from pathlib import Path
from recovery_common import *
from component_scoring import rules_for
from issue_component_forecasts import snapshot,pool_eligibility
def run(base,root=ROOT):
    folder=root/base;m=read(folder/'issuance/capture-manifest.json');lock=read(folder/'pipeline-lock.json');b=read(root/lock['bundle_path']);refs={r['name']:r for r in b['responses']};contracts=read(root/'config/contracts/runtime-contracts.json');entities=read(folder/'entities.json')['entities'];em={e['canonical_player_id']:e for e in entities};expected=set();profiles=[];errors=[]
    for lid in b['league_ids']:
        lid=str(lid);p=snapshot(root,refs[lid+'-profile'],b['observation_cutoff']);old=read(root/OLD/'profiles'/(lid+'.json'));rosters=snapshot(root,refs[lid+'-rosters'],b['observation_cutoff']);owned={str(x) for r in rosters for x in (r.get('players') or [])+(r.get('reserve') or [])+(r.get('taxi') or [])};active=[]
        for e in entities:
            eligible=pool_eligibility(e,old['research_constraints'],e['sleeper_id'] in owned)
            if not set(e['fantasy_positions']).intersection(old['positions']) or (eligible['status']!='ELIGIBLE' and e['sleeper_id'] not in owned):continue
            active.append(e['canonical_player_id'])
            for w in m['target_weeks']:expected.add((lid,e['canonical_player_id'],w))
        profiles.append({'league_id':lid,'name':p['name'],'nonzero_scoring_keys':sorted(k for k,v in p['scoring_settings'].items() if v),'positions':old['positions'],'eligible_entities':len(active),'expected_weekly_rows':len(active)*3})
    actual=set();lookup={(r['canonical_player_id'],r['week']):r for r in rows(folder/'issuance/weekly-components.jsonl.gz')};rule_count=0
    for r in rows(folder/'issuance/weekly-league-scores.jsonl.gz'):
        lid=str(r['league_id']);cid=r['canonical_player_id'];e=em[cid];key=(lid,cid,r['week'])
        if key in actual:errors.append('DUPLICATE_LEAGUE_ROW')
        actual.add(key)
        # Cache the complete frozen profile rather than trusting emitted keys.
    frozen={str(lid):snapshot(root,refs[str(lid)+'-profile'],b['observation_cutoff']) for lid in b['league_ids']}
    for r in rows(folder/'issuance/weekly-league-scores.jsonl.gz'):
        lid=str(r['league_id']);cid=r['canonical_player_id'];e=em[cid];rules=rules_for(frozen[lid]['scoring_settings'],e['position_model'],e['fantasy_positions'],contracts);rule_count+=len(rules)
        if set(r['contributions'])!={x['scoring_key'] for x in rules}:errors.append('OMITTED_OR_EXTRA_SCORING_KEYS')
        values={**lookup[(cid,r['week'])]['means'],**lookup[(cid,r['week'])]['event_probabilities']}
        for rule in rules:
            if rule['component'] not in values:errors.append('MISSING_COMPONENT:'+rule['component'])
    if expected!=actual:errors.append('LEAGUE_ENTITY_POPULATION_MISMATCH')
    result={'status':'PASS' if not errors else 'FAIL','leagues':len(profiles),'component_keys':len({k for r in lookup.values() for k in {**r['means'],**r['event_probabilities']}}),'positions':sorted({e['position_model'] for e in entities}),'weekly_component_rows':len(lookup),'weekly_league_rows':len(actual),'expected_weekly_league_rows':len(expected),'scoring_contributions_checked':rule_count,'profiles':profiles,'errors':errors[:30],'error_count':len(errors),'provider_semantic_certification':False,'arithmetic_coverage_only':True}
    write(folder/'coverage.json',result);print('COVERAGE',result['status'],result['leagues'],result['component_keys']);return result
if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--base',type=Path,required=True);a=p.parse_args();raise SystemExit(run(a.base)['status']!='PASS')
