/* Tranche 3C / C10-007 player-identity characterization.
   Baseline mode freezes the current fragmented ownership before any behavior change. */
'use strict';
const fs=require('fs'),assert=require('assert');
const mode=(process.argv.includes('--mode')?process.argv[process.argv.indexOf('--mode')+1]:'baseline');
const read=p=>fs.readFileSync(p,'utf8');
const compact=s=>String(s).replace(/\s+/g,'');

const core=read('app/core/core-services.js');
const currentFeatures=read('app/current-player-features.js');
const currentStore=read('app/current-snapshot-store.js');
const valueFinder=read('app/value-finder.js');

function functionBody(src,name){
  const re=new RegExp(`function\\s+${name}\\s*\\([^)]*\\)\\s*\\{`);
  const m=re.exec(src);
  assert(m,`missing function ${name}`);
  const start=src.indexOf('{',m.index);
  let depth=0;
  for(let i=start;i<src.length;i++){
    if(src[i]==='{')depth++;
    else if(src[i]==='}'){
      depth--;
      if(depth===0)return src.slice(start+1,i);
    }
  }
  throw new Error(`unterminated function ${name}`);
}
function sliceBetween(src,startToken,endToken){
  const a=src.indexOf(startToken);
  assert(a>=0,`missing ${startToken}`);
  const b=src.indexOf(endToken,a+startToken.length);
  assert(b>a,`missing ${endToken} after ${startToken}`);
  return src.slice(a,b);
}

const corePlayerId=compact(functionBody(core,'playerId'));
const synth=compact(functionBody(core,'synthesizePlayerId'));
const currentId=compact(functionBody(currentFeatures,'idOf'));
const storeId=compact(functionBody(currentStore,'idOf'));
const coreIdentity=compact(sliceBetween(core,'const PlayerIdentity={','const LeagueDemandService='));
const storeCompact=compact(currentStore);
const vfCompact=compact(valueFinder);

const observed={
  corePlayerId:{
    sleeperId:corePlayerId.includes('sleeperId'),
    sleeper_id:corePlayerId.includes('sleeper_id'),
    player_id:corePlayerId.includes('player_id'),
    playerId:corePlayerId.includes('playerId'),
    syntheticFallback:corePlayerId.includes('synthesizePlayerId')
  },
  syntheticStableId:synth.includes('`syn:${team}:${pos}:${name}`'),
  coreById:{
    sleeperId:coreIdentity.includes('sleeperId'),
    sleeper_id:coreIdentity.includes('sleeper_id'),
    player_id:coreIdentity.includes('player_id')
  },
  currentFeatures:{
    sleeperFirst:/sleeper_id\?\?p\?\.player_id\?\?p\?\.id/.test(currentId)
  },
  currentStore:{
    sleeperFirst:/sleeper_id\?\?p\?\.player_id\?\?p\?\.id/.test(storeId),
    rosterFilterPlayerFirst:
      storeCompact.includes("row?.player_id||row?.id||row?.sleeper_id") ||
      storeCompact.includes("row.player_id||row.id||row.sleeper_id")
  },
  valueFinder:{
    stableSleeperLookup:vfCompact.includes('m5Map.get(String(p.sleeperId))'),
    normalizedNameKey:vfCompact.includes('`n:${vfName('),
    normalizedNameFallback:
      vfCompact.includes("||m5Map.get(`n:${vfName(p.fullName||p.name||'')}`)")
  }
};

// Pure conflict fixture expresses the currently observed precedence mismatch.
const conflict={sleeper_id:'snake',player_id:'player',id:'generic'};
const currentCoreChoice=conflict.player_id;   // sleeper_id is not in current Core playerId chain.
const currentFeatureChoice=conflict.sleeper_id;
const conflictFixture={
  row:conflict,
  coreChoice:currentCoreChoice,
  currentFeatureChoice,
  diverges:currentCoreChoice!==currentFeatureChoice
};

if(mode==='baseline'){
  assert(observed.corePlayerId.sleeperId,'Core playerId should currently recognize sleeperId');
  assert(observed.corePlayerId.player_id,'Core playerId should currently recognize player_id');
  assert(!observed.corePlayerId.sleeper_id,'baseline expects Core playerId to omit sleeper_id');
  assert(observed.corePlayerId.syntheticFallback,'baseline expects synthetic playerId fallback');
  assert(observed.syntheticStableId,'baseline expects syn:team:position:name identifier');
  assert(observed.coreById.sleeperId && observed.coreById.player_id,
    'baseline expects Core PlayerIdentity.byId to use its local ID subset');
  assert(!observed.coreById.sleeper_id,
    'baseline expects Core PlayerIdentity.byId to omit sleeper_id');
  assert(observed.currentFeatures.sleeperFirst,
    'baseline expects current-player-features to prefer sleeper_id');
  assert(observed.currentStore.sleeperFirst,
    'baseline expects current snapshot idOf to prefer sleeper_id');
  assert(observed.currentStore.rosterFilterPlayerFirst,
    'baseline expects current snapshot roster filter to use a different precedence');
  assert(observed.valueFinder.stableSleeperLookup,
    'baseline expects Value Finder stable Sleeper lookup');
  assert(observed.valueFinder.normalizedNameKey && observed.valueFinder.normalizedNameFallback,
    'baseline expects Value Finder normalized-name fallback');
  assert(conflictFixture.diverges,'identity conflict fixture must reproduce divergent resolution');
  console.log('KNOWN_GAP_REPRODUCED player identity is fragmented across stable IDs, synthetic IDs and display-name fallback');
  console.log(JSON.stringify({mode,observed,conflictFixture}));
}else if(mode==='target'){
  // Future implementation target. This preflight does not run target mode.
  const c=compact(core);
  assert(c.includes('constPlayerIdentity={') || c.includes('PlayerIdentity={'));
  assert(c.includes("status:'unavailable'") || c.includes('status:"unavailable"'),
    'target must expose explicit unavailable identity state');
  assert(c.includes("status:'ambiguous'") || c.includes('status:"ambiguous"'),
    'target must expose explicit ambiguous identity state');
  assert(!vfCompact.includes("||m5Map.get(`n:${vfName(p.fullName||p.name||'')}`)"),
    'target must remove display-name fallback from governed current-feature joins');
  console.log('PASS Tranche 3C canonical player identity contract');
}else{
  throw new Error(`unknown mode ${mode}`);
}
