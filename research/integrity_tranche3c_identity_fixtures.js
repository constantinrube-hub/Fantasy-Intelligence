/* Permanent Tranche 3C canonical player identity fixtures. */
'use strict';
const fs=require('fs'),vm=require('vm'),assert=require('assert');
const ctx={console,window:null,PLAYERS:[],state:{},Date,Math,Map,Set,WeakMap,Promise};ctx.window=ctx;
vm.createContext(ctx);
vm.runInContext(fs.readFileSync('app/generated/runtime-contracts.js','utf8'),ctx,{filename:'runtime-contracts.js'});
vm.runInContext(fs.readFileSync('app/core/core-services.js','utf8'),ctx,{filename:'core-services.js'});
const I=ctx.FIECore.PlayerIdentity;

const offense={sleeperId:'101',player_id:'legacy-101',name:'Receiver One',position:'WR',team:'AAA'};
const idp={sleeperId:'202',name:'Linebacker Two',position:'LB',team:'BBB',gsis_id:'00-202'};
const dst={sleeperId:'DAL',name:'Dallas Cowboys',position:'DEF',team:'DAL'};
const kicker={sleeperId:'303',name:'Kicker Three',position:'K',team:'CCC'};
const crosswalk={internal_id:'int-404',gsis_id:'00-404',name:'Crosswalk Four',position:'RB',team:'DDD'};
const duplicateA={sleeperId:'501',name:'Chris Example',position:'WR',team:'EEE'};
const duplicateB={sleeperId:'502',name:'Chris Example',position:'WR',team:'FFF'};
ctx.PLAYERS=[offense,idp,dst,kicker,crosswalk,duplicateA,duplicateB];

assert.strictEqual(I.source,'FIECore.PlayerIdentity');
assert.strictEqual(I.governedId({sleeper_id:'snake',player_id:'legacy'}),'snake','sleeper_id must outrank legacy player_id');
assert.strictEqual(I.id({name:'No Id',position:'WR',team:'ZZZ'}).startsWith('synthetic:WR:ZZZ:'),true,'compatibility ID may remain synthetic');
assert.strictEqual(I.governedId({name:'No Id',position:'WR',team:'ZZZ'}),null,'governed identity may never be synthetic');

for(const [label,subject,expected] of [
  ['offense',{sleeper_id:'101'},offense],
  ['IDP',{gsis_id:'00-202'},idp],
  ['D/ST',{canonical_player_id:'DST:DAL',position_model:'DEF',team:'DAL'},dst],
  ['kicker',{sleeper_id:'303'},kicker],
  ['canonical crosswalk',{canonical_player_id:'int-404'},crosswalk],
  ['GSIS crosswalk',{gsis_id:'00-404'},crosswalk],
]){
  const r=I.resolve(subject,{players:ctx.PLAYERS});
  assert.strictEqual(r.status,'resolved',`${label} must resolve`);
  assert.strictEqual(r.player,expected,`${label} resolved wrong entity`);
  assert.ok(r.id,`${label} must expose canonical ID`);
}

const conflict=I.resolve({sleeper_id:'101',gsis_id:'00-202'},{players:ctx.PLAYERS});
assert.strictEqual(conflict.status,'ambiguous','conflicting stable aliases must fail ambiguous');
assert.strictEqual(conflict.reason,'canonical_alias_collision');

const dup=I.resolve({name:'Chris Example',position:'WR'},{players:ctx.PLAYERS});
assert.strictEqual(dup.status,'ambiguous','duplicate display-name collision must be explicit ambiguous');
assert.strictEqual(dup.reason,'display_name_collision_not_identity');

const loneName=I.resolve({name:'Receiver One',position:'WR'},{players:ctx.PLAYERS});
assert.strictEqual(loneName.status,'unavailable','single display-name match must not be promoted to canonical identity');
assert.strictEqual(loneName.reason,'display_name_not_canonical');

const missing=I.resolve({name:'Nobody',position:'WR'},{players:ctx.PLAYERS});
assert.strictEqual(missing.status,'unavailable');

assert.strictEqual(I.byId('101'),offense,'raw Sleeper string lookup remains compatible');
assert.strictEqual(I.positionForId('DAL'),'DEF','D/ST entity position canonicalization must survive');
console.log('PASS Tranche 3C offense/IDP/DST/K identity, crosswalk and ambiguity fixtures');
