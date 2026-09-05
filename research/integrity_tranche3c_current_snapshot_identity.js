/* Permanent Tranche 3C browser current-snapshot identity hydration parity. */
'use strict';
const fs=require('fs'),vm=require('vm'),assert=require('assert');
const manifest={
  league_id:'fixture',scoring_signature:'sig',storage:{
    format:'fie-current-split-v1',player_base:'base.json',scoring_overlay:'overlay.json',player_count:3,
    included_player_ids:['canonical:int-1','gsis:00-2','canonical:DST:DAL']
  }
};
const base={players:[
  {canonical_player_id:'int-1',position_model:'WR',full_name:'Canonical One'},
  {gsis_id:'00-2',position_model:'LB',full_name:'GSIS Two'},
  {canonical_player_id:'DST:DAL',position_model:'DEF',team:'DAL',full_name:'Dallas Cowboys'}
]};
const overlay={scoring_signature:'sig',scoring_settings:{},projections:{
  'canonical:int-1':[10,9],
  'gsis:00-2':[8,7],
  'canonical:DST:DAL':[6,5]
}};
const data={'manifest.json':manifest,'base.json':base,'overlay.json':overlay};
const ctx={console,window:null,document:{readyState:'loading',addEventListener(){},querySelector(){return null},createElement(){return{}},head:{appendChild(){}}},Date,Math,Map,Set,WeakMap,Promise,state:{},PLAYERS:[]};ctx.window=ctx;
ctx.FIEDataClient={response:async url=>{const key=String(url).replace(/[?].*$/,'');const body=data[key];if(!body)return{ok:false,status:404,json:async()=>({})};return{ok:true,status:200,json:async()=>JSON.parse(JSON.stringify(body))};}};
vm.createContext(ctx);
vm.runInContext(fs.readFileSync('app/generated/runtime-contracts.js','utf8'),ctx,{filename:'runtime-contracts.js'});
vm.runInContext(fs.readFileSync('app/core/core-services.js','utf8'),ctx,{filename:'core-services.js'});
vm.runInContext(fs.readFileSync('app/current-snapshot-store.js','utf8'),ctx,{filename:'current-snapshot-store.js'});
(async()=>{
  const out=await ctx.FIECurrentSnapshotStore.load('manifest.json');
  assert.strictEqual(out.players.length,3);
  assert.deepStrictEqual(Array.from(out.players,x=>x.decision_weekly_projection),[10,8,6]);
  assert.deepStrictEqual(Array.from(out.players,x=>x.sleeper_weekly_projection),[9,7,5]);
  console.log('PASS Tranche 3C browser/Python governed current-snapshot identity parity');
})().catch(e=>{console.error(e);process.exit(1);});
