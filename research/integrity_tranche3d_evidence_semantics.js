#!/usr/bin/env node
'use strict';
const fs=require('fs'),vm=require('vm'),path=require('path');
const ROOT=path.resolve(__dirname,'..');
function assert(x,msg){if(!x)throw new Error(msg);}
function load(rel){vm.runInThisContext(fs.readFileSync(path.join(ROOT,rel),'utf8'),{filename:rel});}

global.window=global;
global.addEventListener=()=>{};
global.setTimeout=(fn)=>{fn();return 0;};
global.state={
  league:{league_id:'1391803939736801280',season:2026},
  weekly:{schedule:[]}
};
global.currentWeek=()=>1;
global.FIECore={Numeric:{finiteOrNull(v){if(v===null||v===undefined||String(v).trim()==='')return null;const n=Number(v);return Number.isFinite(n)?n:null;}},SeasonResolver:{resolve:()=>2026}};
let bundle={
  league_id:'1391803939736801280',season:2026,week:1,generated_at:'2026-09-03T12:00:00Z',
  players:[{sleeper_id:'1',week:1,season:2026,weekly_activation_eligible:true,decision_weekly_projection:12.5,p10:8,p90:16}]
};
global.FIE_M5={getCurrentBundle:()=>bundle};

load('app/core/projection-service.js');
const player={sleeperId:'1',team:'KC',position:'QB',engineSeasonProjection:170};
const baselineWeek=global.FIEProjectionResolver.week(player,{week:1,season:2026});
const baselineRange=global.FIEProjectionResolver.range(player,{week:1,season:2026});
assert(baselineWeek.value===12.5,'pre-adapter governed projection fixture drifted');
assert(baselineRange.low===8&&baselineRange.high===16&&baselineRange.calibrated===true,'pre-adapter calibrated range fixture drifted');

// Minimal public APIs representing the live surfaces that the canonical adapter enriches.
global.PLAYERS=[{sleeperId:'1',position:'QB',currentFeatureLineage:{source:'research current snapshot',asOfCompletedWeek:0,leakageSafe:true,activationEligible:true}}];
global.FIECurrentFeatures={
  apply(){return{matched:1};},
  lineage(p){return p.currentFeatureLineage||null;}
};
global.FIECurrentSnapshotStore={
  async load(){return{league_id:'1391803939736801280',season:2026,week:1,generated_at:'2026-09-03T12:00:00Z',players:[]};}
};
global.FIEDST={
  board(){return[
    {team:'KC',mean:9,low:6,high:13,source:'FIE empirical',active:true,estimate:false,bye:false,week:1,r:{p10:6,p90:13}},
    {team:'BUF',mean:7,low:5.46,high:8.54,source:'Baseline Estimate',active:false,estimate:true,bye:false,week:2,r:{}}
  ];}
};
global.FIEKicker={
  board(){return[
    {name:'K',mean:8,low:0,high:0,source:'Schedule',active:false,estimate:false,bye:true,week:7,r:{}}
  ];}
};

load('app/core/evidence-semantics.js');
const E=global.FIEEvidenceSemantics;
assert(E&&E.SCHEMA==='fie-evidence-v1','canonical evidence owner not installed');
assert(E.EvidenceStatus.OBSERVED==='observed','observed evidence status contract drifted');
assert(E.EvidenceStatus.MODELED_AVAILABLE==='modeled_available','modeled-available evidence status contract drifted');
assert(E.EvidenceStatus.MODELED_UNAVAILABLE==='modeled_unavailable','modeled-unavailable evidence status contract drifted');
assert(E.UncertaintyKind.CALIBRATED_RANGE==='calibrated_range','calibrated uncertainty contract drifted');
assert(E.UncertaintyKind.HEURISTIC_RANGE==='heuristic_range','heuristic uncertainty contract drifted');

// The adapter is metadata-only: legacy values and labels remain byte-for-byte semantic equivalents.
const governed=global.FIEProjectionResolver.week(player,{week:1,season:2026});
const calibrated=global.FIEProjectionResolver.range(player,{week:1,season:2026});
assert(governed.value===baselineWeek.value&&governed.source===baselineWeek.source&&governed.confidence===baselineWeek.confidence,'projection adapter changed governed value/source/confidence');
assert(calibrated.low===baselineRange.low&&calibrated.high===baselineRange.high&&calibrated.calibrated===baselineRange.calibrated,'projection adapter changed calibrated range');
assert(governed.evidence.evidenceStatus==='modeled_available','governed projection typed status incorrect');
assert(governed.evidence.asOf==='2026-09-03T12:00:00Z','projection asOf did not preserve current snapshot freshness');
assert(calibrated.evidence.uncertaintyKind==='calibrated_range','empirical range not typed calibrated');

bundle={league_id:'1391803939736801280',season:2026,week:1,generated_at:'2026-09-03T12:00:00Z',players:[]};
const seasonOnly={sleeperId:'2',team:'MIN',position:'WR',engineSeasonProjection:170};
const seasonBaseline=global.FIEProjectionResolver.week(seasonOnly,{week:1,season:2026});
assert(seasonBaseline.value===10&&seasonBaseline.source==='Season baseline','season /17 fallback value changed');
assert(seasonBaseline.evidence.fallback===true&&seasonBaseline.evidence.evidenceStatus==='modeled_available','season baseline not typed as modeled fallback');
const heuristic=global.FIEProjectionResolver.range(seasonOnly,{week:1,season:2026});
assert(Math.abs(heuristic.low-7.8)<1e-9&&Math.abs(heuristic.high-12.2)<1e-9,'heuristic range math changed');
assert(heuristic.evidence.uncertaintyKind==='heuristic_range','heuristic range not typed heuristic');

const unknown={sleeperId:'3',team:'LAC',position:'TE'};
const unavailable=global.FIEProjectionResolver.week(unknown,{week:1,season:2026});
assert(unavailable.value===null&&unavailable.availability==='unavailable','missing projection no longer null/unavailable');
assert(unavailable.evidence.evidenceStatus==='modeled_unavailable'&&unavailable.evidence.uncertaintyKind==='unavailable','missing projection evidence typing incorrect');

global.state.weekly.schedule=[{season:2026,week:1,game_type:'REG',home_team:'BUF',away_team:'MIA'}];
const bye={sleeperId:'4',team:'KC',position:'QB'};
const byeResult=global.FIEProjectionResolver.week(bye,{week:1,season:2026});
assert(byeResult.value===0&&byeResult.reason==='BYE'&&byeResult.isBye===true,'verified bye true-zero semantics changed');
assert(byeResult.evidence.evidenceStatus==='observed'&&byeResult.evidence.uncertaintyKind==='exact'&&byeResult.evidence.byeState==='bye','verified bye evidence typing incorrect');

const featureApply=global.FIECurrentFeatures.apply();
assert(featureApply.matched===1,'current-feature adapter changed apply result');
assert(global.PLAYERS[0].currentFeatureEvidence?.evidenceStatus==='observed','current features missing observed evidence');
assert(global.FIECurrentFeatures.lineage(global.PLAYERS[0]).evidence?.schemaVersion==='fie-evidence-v1','feature lineage missing canonical evidence');

(async()=>{
  const snap=await global.FIECurrentSnapshotStore.load('x');
  assert(snap.evidence?.evidenceStatus==='observed','current snapshot missing observed evidence');
  assert(snap.evidence?.asOf==='2026-09-03T12:00:00Z','current snapshot freshness not preserved');

  const dst=global.FIEDST.board();
  assert(dst[0].mean===9&&dst[0].low===6&&dst[0].high===13,'D/ST values changed by evidence adapter');
  assert(dst[0].evidence?.uncertaintyKind==='calibrated_range','D/ST empirical range not typed calibrated');
  assert(dst[1].evidence?.uncertaintyKind==='heuristic_range'&&dst[1].evidence?.fallback===true,'D/ST baseline estimate not typed heuristic fallback');

  const k=global.FIEKicker.board();
  assert(k[0].mean===8&&k[0].evidence?.evidenceStatus==='observed'&&k[0].evidence?.uncertaintyKind==='exact','kicker bye evidence contract incorrect');

  const snapshotSource=fs.readFileSync(path.join(ROOT,'app/current-snapshot-store.js'),'utf8');
  assert(snapshotSource.includes('app/core/evidence-semantics.js')&&snapshotSource.includes('bootEvidenceSemantics'),'browser evidence bootstrap missing');
  const distEvidence=fs.readFileSync(path.join(ROOT,'dist/app/core/evidence-semantics.js'),'utf8');
  assert(distEvidence===fs.readFileSync(path.join(ROOT,'app/core/evidence-semantics.js'),'utf8'),'source/dist evidence semantics mirror mismatch');
  const distSnapshot=fs.readFileSync(path.join(ROOT,'dist/app/current-snapshot-store.js'),'utf8');
  assert(distSnapshot===snapshotSource,'source/dist snapshot-store mirror mismatch');

  console.log('PASS Tranche 3D canonical typed evidence runtime adapters preserve projection, feature, snapshot, D/ST and kicker values');
})().catch(e=>{console.error(e);process.exit(1);});
