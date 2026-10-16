#!/usr/bin/env python3
from scoring_relevance import relevant_scoring_audit,position_support
scoring={'pass_td':4,'kr_yd':.05,'fgm_60p':6,'pts_allow_0':10,'def_kr_yd':.05}
audit={'unsupported':[{'key':'kr_yd','reason':'no mapping'},{'key':'fgm_60p','reason':'no mapping'},{'key':'pts_allow_0','reason':'no mapping'},{'key':'def_kr_yd','reason':'no mapping'}]}
r=relevant_scoring_audit(scoring,audit,['QB','RB','WR','TE','FLEX','BN'])
assert 'fgm_60p' in r['ignored_irrelevant'] and 'pts_allow_0' in r['ignored_irrelevant'] and 'def_kr_yd' in r['ignored_irrelevant']
assert [x['key'] for x in r['unsupported']]==['kr_yd']
assert r['exact_replay_eligible'] is False
assert position_support(scoring,audit,'QB')['exact'] is True
assert position_support(scoring,audit,'WR')['exact'] is False
# Unknown rules remain relevant and therefore cannot disappear from governance.
r2=relevant_scoring_audit({'mystery_rule':1},{'unsupported':[{'key':'mystery_rule'}]},['QB'])
assert r2['exact_replay_eligible'] is False
print('PASS integrity_scoring_relevance_test')
