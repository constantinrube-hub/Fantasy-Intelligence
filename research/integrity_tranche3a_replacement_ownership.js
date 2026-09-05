/* Tranche 3A preflight/target: one-owner replacement, scarcity and VOR contract. */
'use strict';
const fs=require('fs'),vm=require('vm'),assert=require('assert');
const mode=(process.argv.includes('--mode')?process.argv[process.argv.indexOf('--mode')+1]:'baseline');
const FORMATS=['REDRAFT','DYNASTY','CHOPPED','REDRAFT_BESTBALL','DYNASTY_BESTBALL','CHOPPED_BESTBALL'];

const league={league_id:'tranche3a-fixture',total_rosters:2,roster_positions:['QB','RB','WR','TE','FLEX','SUPER_FLEX','BN'],settings:{teams:2}};
const make=(pos,n,start,step)=>Array.from({length:n},(_,i)=>({
  sleeperId:`${pos}${i+1}`,name:`${pos}${i+1}`,position:pos,team:'T',
  leagueEligible:true,availability:'FA',engineSeasonProjection:start-i*step,
  sleeperSeasonProjection:start-i*step,weeklyProjection:(start-i*step)/17,
  modelScore:90-i*2,projectedVOR:0
}));
const players=[...make('QB',8,340,25),...make('RB',12,300,16),...make('WR',12,295,15),...make('TE',9,240,14)];
const ownedTargets={QB:2,RB:1,WR:1,TE:1};

const listeners={};
const state={
  league,rosters:[{roster_id:1},{roster_id:2}],
  replacement:{ownershipInfluence:0,benchInfluence:0},
  projectionStatus:{season:true},
  weekly:{week:1,weekly2025:[],weekly2026:[],snaps2026:[],team2025:[],team2026:[]},
  validation:{snapshots:{}},featureLearning:{byPosition:{},matchupByPosition:{}},
  weights:{fa:0},trending:{},modelHealth:{}
};
const ctx={console,window:null,state,PLAYERS:players,performance:{now:()=>0},document:{getElementById:()=>null},
  setTimeout:()=>0,clearTimeout:()=>{},requestIdleCallback:undefined,Date,Math,Number,String,Object,Array,Set,Map,JSON,Promise,
  CustomEvent:class{constructor(type,o={}){this.type=type;this.detail=o.detail;}}
};
ctx.window=ctx;ctx.addEventListener=(n,f)=>(listeners[n]??=[]).push(f);ctx.dispatchEvent=()=>true;
ctx.FIE934A2={installed:true,report:()=>({})};
ctx.FIE89={playerDecisionValue:p=>p.modelScore||0,marketEdgeValue:()=>null};
ctx.weightedModel=p=>p.modelScore||0;ctx.scoringFit=()=>50;
ctx.replacementScoreFor=()=>({level:null,advantage:null,score:null,adjustment:0});
ctx.optimizeLineup=()=>{};ctx.renderReplacementSummary=()=>{};ctx.renderHealthDiagnostics=()=>{};ctx.loadValidationSnapshots=()=>{};

vm.createContext(ctx);
for(const file of ['app/generated/runtime-contracts.js','app/core/core-services.js','app/v9.3.4a3-score-performance.js','app/v9.3.4d-starter-economics.js'])
  vm.runInContext(fs.readFileSync(file,'utf8'),ctx,{filename:file});

assert.ok(ctx.FIE934A3?.installed,'A3 not installed');
assert.ok(ctx.FIE934D?.installed,'D not installed');

function setOwned(enabled){
  const seen={};
  for(const p of players){
    seen[p.position]=(seen[p.position]||0)+1;
    p.availability=enabled && seen[p.position]<=Number(ownedTargets[p.position]||0)?'OWNED':'FA';
    delete p.ownerRosterId;
  }
}
function coreProfiles(){
  const out={};
  for(const pos of ['QB','RB','WR','TE']){
    out[pos]=ctx.FIECore.ReplacementService.profile(pos,{
      league,players,state,valueFn:p=>Number(p.engineSeasonProjection)
    });
  }
  return out;
}
function snapshot({ownershipInfluence=0,benchInfluence=0,owned=false}={}){
  state.replacement.ownershipInfluence=ownershipInfluence;
  state.replacement.benchInfluence=benchInfluence;
  setOwned(owned);
  ctx.computeReplacementLevels();
  ctx.computeProjectedReplacementLevels();
  const core=coreProfiles();
  const d=ctx.FIE934D.computeEconomics(players,league,state.rosters);
  const a3={};
  for(const pos of ['QB','RB','WR','TE']){
    const r=state.replacementLevels[pos]||{},pr=state.projectedReplacementLevels[pos]||{};
    a3[pos]={cutoff:r.cutoff,effectiveOwned:r.effectiveOwned,actualOwned:r.actualOwned,projectedCutoff:pr.cutoff,projectedPoints:pr.points};
  }
  const de={};
  for(const pos of ['QB','RB','WR','TE']){
    const r=d.replacementByPosition[pos]||{};
    de[pos]={
      replacementRank:r.replacementRank??null,
      structuralCutoff:r.structuralCutoff??null,
      sourceCutoff:r.sourceCutoff??null,
      source:r.source??null
    };
  }
  return {core,a3,d:de};
}

const zero=snapshot();
const owned=snapshot({ownershipInfluence:100,owned:true});
const positions=['QB','RB','WR','TE'];

const summary={
  mode,
  zero:Object.fromEntries(positions.map(pos=>[pos,{
    coreCutoff:zero.core[pos].cutoff,
    a3Cutoff:zero.a3[pos].cutoff,
    a3ProjectedCutoff:zero.a3[pos].projectedCutoff,
    dReplacementRank:zero.d[pos].replacementRank,
    dStructuralCutoff:zero.d[pos].structuralCutoff,
    coreSource:zero.core[pos].source??null
  }])),
  ownership100:Object.fromEntries(positions.map(pos=>[pos,{
    coreCutoff:owned.core[pos].cutoff,
    a3Cutoff:owned.a3[pos].cutoff,
    actualOwned:owned.a3[pos].actualOwned
  }]))
};

for(const pos of positions){
  assert.strictEqual(zero.a3[pos].projectedCutoff,zero.core[pos].cutoff,`${pos}: zero-influence Core/A3 projected cutoff must agree`);
  assert.strictEqual(owned.core[pos].cutoff,zero.core[pos].cutoff,`${pos}: Core structural cutoff must not move with ownership`);
}

if(mode==='baseline'){
  const dMismatches=positions.filter(pos=>zero.d[pos].replacementRank!==zero.core[pos].cutoff);
  assert.ok(dMismatches.length>0,'baseline must reproduce D replacement convention divergence');
  assert.ok(dMismatches.every(pos=>zero.d[pos].replacementRank===zero.core[pos].cutoff+1),
    `baseline D relation changed unexpectedly: ${JSON.stringify(summary.zero)}`);

  const ownershipFeedback=positions.filter(pos=>owned.a3[pos].cutoff!==owned.core[pos].cutoff);
  assert.ok(ownershipFeedback.length>0,'baseline must reproduce A3 ownership-feedback cutoff divergence');

  const tagged=players.filter(p=>p.projectedVORSource||p.projectedReplacementSource||p.projectedReplacementCutoff!==undefined);
  assert.strictEqual(tagged.length,0,'baseline unexpectedly already carries canonical VOR provenance');

  console.log('KNOWN_GAP_REPRODUCED Core, A3 and D do not share one replacement/VOR owner');
}else if(mode==='target'){
  const RS=ctx.FIECore.ReplacementService;
  assert.strictEqual(typeof RS.profiles,'function','target requires batched canonical replacement profiles');
  assert.strictEqual(typeof RS.projectedLevels,'function','target requires canonical projected replacement levels');
  assert.strictEqual(typeof RS.applyProjectionVOR,'function','target requires canonical VOR application/provenance');

  for(const pos of positions){
    const c=zero.core[pos],a=zero.a3[pos],d=zero.d[pos];
    assert.strictEqual(c.source,'FIECore.ReplacementService',`${pos}: missing canonical source`);
    assert.strictEqual(c.structuralCutoff,c.cutoff,`${pos}: structural cutoff provenance mismatch`);
    assert.strictEqual(c.sourceCutoff,c.cutoff,`${pos}: source cutoff provenance mismatch`);
    assert.strictEqual(c.ownershipAffectsCutoff,false,`${pos}: ownership must not alter football replacement cutoff`);
    assert.strictEqual(a.cutoff,c.cutoff,`${pos}: A3 cutoff not canonical`);
    assert.strictEqual(a.projectedCutoff,c.cutoff,`${pos}: A3 projected cutoff not canonical`);
    assert.strictEqual(d.replacementRank,c.cutoff,`${pos}: D replacement row not canonical`);
    assert.strictEqual(d.structuralCutoff,c.cutoff,`${pos}: D missing structural cutoff`);
    assert.strictEqual(d.sourceCutoff,c.cutoff,`${pos}: D missing source cutoff`);
    assert.strictEqual(d.source,'FIECore.ReplacementService',`${pos}: D source not canonical`);
    assert.strictEqual(owned.a3[pos].cutoff,c.cutoff,`${pos}: A3 ownership feedback still changes cutoff`);
  }

  // VOR must carry explicit canonical source/cutoff provenance.
  for(const p of players.filter(p=>positions.includes(p.position))){
    assert.strictEqual(p.projectedVORSource,'FIECore.ReplacementService',`${p.sleeperId}: missing VOR source`);
    assert.ok(Number.isInteger(Number(p.projectedReplacementCutoff))&&Number(p.projectedReplacementCutoff)>=1,
      `${p.sleeperId}: missing replacement cutoff provenance`);
    const lev=state.projectedReplacementLevels[p.position];
    assert.strictEqual(Number(p.projectedReplacementCutoff),Number(lev.cutoff),`${p.sleeperId}: VOR cutoff drift`);
    assert.ok(Math.abs(Number(p.projectedVOR)-(Number(p.engineSeasonProjection)-Number(lev.points)))<1e-9,
      `${p.sleeperId}: VOR is not derived from canonical replacement points`);
  }

  // Same structural roster fixture must not acquire hidden format-specific replacement semantics.
  const expected=Object.fromEntries(positions.map(pos=>[pos,zero.core[pos].cutoff]));
  for(const format of FORMATS){
    const lf={...league,format,__fieFormat:format};
    for(const pos of positions){
      const p=RS.profile(pos,{league:lf,players,state,valueFn:x=>Number(x.engineSeasonProjection)});
      assert.strictEqual(p.cutoff,expected[pos],`${format}/${pos}: hidden format-specific replacement cutoff`);
    }
  }
  console.log('PASS Tranche 3A one-owner replacement/scarcity/VOR contract');
}else{
  throw new Error(`unknown mode ${mode}`);
}
console.log(JSON.stringify(summary));
