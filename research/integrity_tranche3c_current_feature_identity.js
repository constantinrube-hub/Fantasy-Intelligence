/* Permanent Tranche 3C governed current-feature identity integration. */
'use strict';
const fs=require('fs'),vm=require('vm'),assert=require('assert');
const live=[
  {sleeperId:'101',name:'Receiver One',position:'WR',team:'AAA'},
  {internal_id:'int-202',name:'Canonical Only',position:'LB',team:'BBB'},
  {sleeperId:'303',name:'Duplicate Target',position:'RB',team:'CCC'},
  {sleeperId:'404',name:'No Match',position:'TE',team:'DDD'},
];
const current={players:[
  {sleeper_id:'101',activation_eligible:true,current_features:{schema_version:1,leakage_safe:true,source:'fixture',values:{snap_share:.75}}},
  {canonical_player_id:'int-202',activation_eligible:true,current_features:{schema_version:1,leakage_safe:true,source:'fixture',values:{tackle_competition_index:.42}}},
  {sleeper_id:'303',activation_eligible:true,current_features:{schema_version:1,leakage_safe:true,source:'fixture-a',values:{carry_share:.4}}},
  {player_id:'303',activation_eligible:true,current_features:{schema_version:1,leakage_safe:true,source:'fixture-b',values:{carry_share:.5}}},
  {full_name:'No Match',activation_eligible:true,current_features:{schema_version:1,leakage_safe:true,source:'name-only',values:{target_share:.9}}},
]};
const ctx={console,window:null,PLAYERS:live,state:{league:{league_id:'fixture'}},FIE_M6_GOVERNANCE_ALLOW:true,Date,Math,Map,Set,WeakMap,Promise};
ctx.window=ctx;ctx.FIE_M5={getCurrentBundle:()=>current};
vm.createContext(ctx);
vm.runInContext(fs.readFileSync('app/generated/runtime-contracts.js','utf8'),ctx,{filename:'runtime-contracts.js'});
vm.runInContext(fs.readFileSync('app/core/core-services.js','utf8'),ctx,{filename:'core-services.js'});
vm.runInContext(fs.readFileSync('app/current-player-features.js','utf8'),ctx,{filename:'current-player-features.js'});
const result=ctx.FIECurrentFeatures.apply();
assert.strictEqual(result.matched,2,'only unique canonical identities should attach');
assert.strictEqual(result.withFeatures,2);
assert.strictEqual(result.identityUnavailable,1,'name-only research row must fail closed');
assert.strictEqual(result.identityAmbiguous,1,'duplicate governed rows for one live player must fail closed');
assert.strictEqual(live[0].currentResearchFeatures.snap_share,.75,'Sleeper bridge must attach');
assert.strictEqual(live[1].currentResearchFeatures.tackle_competition_index,.42,'canonical-only crosswalk fixture must attach');
assert.strictEqual(live[0].currentFeatureLineage.identityResolved,true);
assert.strictEqual(live[1].currentFeatureLineage.canonicalId,'canonical:int-202');
assert.strictEqual(live[2].currentResearchFeatures,null,'duplicate canonical rows must not silently overwrite');
assert.strictEqual(live[3].currentResearchFeatures,null,'display-name-only row must never activate');
const signal=ctx.FIECurrentFeatures.signalLineage(live[0]).find(x=>x.family==='Opportunity');
assert.strictEqual(signal.active,true,'resolved/leakage-safe/governed feature remains active');
console.log('PASS Tranche 3C canonical-only current-feature join and fail-closed ambiguity contract');
