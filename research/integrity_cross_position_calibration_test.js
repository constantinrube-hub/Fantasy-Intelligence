/* Runtime integrity for FIE 9.3.3 cross-position scarcity/VOR calibration. */
'use strict';
const fs=require('fs'),vm=require('vm'),assert=require('assert');
const code=fs.readFileSync('app/core/value-calibration-guard.js','utf8');
const baseRows=[
 {id:'qb',position:'QB',format:'REDRAFT',baseValue:80,vor:75,scarcity:90,p:{name:'QB A'}},
 {id:'te',position:'TE',format:'REDRAFT',baseValue:68,vor:null,scarcity:85,p:{name:'TE A'}},
];
const service={rows:()=>baseRows.map(x=>({...x})),rowFor(){},invalidate(){}};
const listeners={};
const ctx={console,window:null,document:{readyState:'complete',addEventListener(){}},setInterval,clearInterval,state:{league:{league_id:'1',total_rosters:12},rosters:Array(12),modelHealth:{recomputeCount:1},projectionStatus:{seasonCount:1,weeklyCount:1},weekly:{week:1}},PLAYERS:[1,2],FIEDraftBaseValueService:service};
ctx.window=ctx;vm.createContext(ctx);vm.runInContext(code,ctx,{filename:'value-calibration-guard.js'});
assert.ok(ctx.FIEDraftBaseValueService.__fieCalibrationInstalled,'guard should install');
const rows=ctx.FIEDraftBaseValueService.rows(true),qb=rows.find(x=>x.id==='qb'),te=rows.find(x=>x.id==='te');
assert.strictEqual(qb.duplicateScarcityRemoved,true,'valid VOR should remove duplicate scarcity term');
assert.ok(qb.baseValue<qb.rawCanonicalBaseValue,'high duplicate scarcity should no longer inflate base value');
assert.strictEqual(te.duplicateScarcityRemoved,false,'missing VOR must retain scarcity fallback');
assert.strictEqual(te.baseValue,68,'fallback row base value must remain unchanged');
console.log('PASS cross-position calibration: VOR de-duplicates scarcity; scarcity remains fallback');
