#!/usr/bin/env python3
from league_profile import structural_settings,structural_contract,sha256_json
base={'type':3,'best_ball':0,'waiver_budget':100,'daily_waivers_last_ran':100,'leg':2,'last_chopped_leg':1}
a=structural_settings(base);assert 'type'in a and 'waiver_budget'in a;assert 'daily_waivers_last_ran' not in a and 'leg' not in a and 'last_chopped_leg' not in a
c1=structural_contract('123456','CHOPPED',{'rec':1},['QB','RB','BN'],base,18,'2026','regular')
b={**base,'daily_waivers_last_ran':999,'leg':7,'last_chopped_leg':6}
c2=structural_contract('123456','CHOPPED',{'rec':1},['QB','RB','BN'],b,18,'2026','regular')
assert sha256_json(c1)==sha256_json(c2),'volatile Sleeper state changed structural fingerprint'
c3=structural_contract('123456','CHOPPED',{'rec':.5},['QB','RB','BN'],b,18,'2026','regular')
assert sha256_json(c1)!=sha256_json(c3),'scoring change did not change structural fingerprint'
print('PASS integrity_structural_profile_test')
