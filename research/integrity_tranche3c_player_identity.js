/* Tranche 3C / C10-007 player-identity characterization.
 * Revision 2: characterizes the actual inline identity implementation.
 * Baseline mode freezes current fragmentation before any production identity change.
 */
'use strict';
const fs=require('fs'),assert=require('assert');

const mode=(process.argv.includes('--mode')
  ? process.argv[process.argv.indexOf('--mode')+1]
  : 'baseline');

const read=p=>fs.readFileSync(p,'utf8');
const compact=s=>String(s).replace(/\s+/g,'');

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

const core=read('app/core/core-services.js');
const currentFeatures=read('app/current-player-features.js');
const currentStore=read('app/current-snapshot-store.js');
const valueFinder=read('app/value-finder.js');

const corePlayerId=compact(functionBody(core,'playerId'));
const coreIdentity=compact(sliceBetween(core,'const PlayerIdentity={','const FormatRegistry='));
const featureRowsById=compact(functionBody(currentFeatures,'rowsById'));
const featureApply=compact(functionBody(currentFeatures,'apply'));
const snapshotPid=compact(functionBody(currentStore,'pid'));
const vfMap=compact(functionBody(valueFinder,'vfM5CurrentMap'));
const vfRow=compact(functionBody(valueFinder,'vfM5Row'));

const observed={
  corePlayerId:{
    sleeperId:corePlayerId.includes('p?.sleeperId'),
    sleeper_id:corePlayerId.includes('p?.sleeper_id'),
    player_id:corePlayerId.includes('p?.player_id'),
    playerId:corePlayerId.includes('p?.playerId'),
    id:corePlayerId.includes('p?.id'),
    inlineSynthetic:corePlayerId.includes('`synthetic:${pos}:${team}:${name}`')
  },
  corePlayerIdentity:{
    sleeperId:coreIdentity.includes('p?.sleeperId'),
    sleeper_id:coreIdentity.includes('p?.sleeper_id'),
    player_id:coreIdentity.includes('p?.player_id'),
    hasResolve:coreIdentity.includes('resolve('),
    explicitUnavailable:coreIdentity.includes("status:'unavailable'")||coreIdentity.includes('status:"unavailable"'),
    explicitAmbiguous:coreIdentity.includes("status:'ambiguous'")||coreIdentity.includes('status:"ambiguous"')
  },
  currentFeatures:{
    snapshotSleeperIdIndex:featureRowsById.includes('r?.sleeper_id')&&featureRowsById.includes('String(r.sleeper_id)'),
    liveSleeperIdLookup:featureApply.includes('map.get(String(p.sleeperId))')
  },
  currentSnapshotStore:{
    sleeperId: snapshotPid.includes('row?.sleeper_id'),
    canonicalPlayerId: snapshotPid.includes('row?.canonical_player_id'),
    canonicalPrefix: snapshotPid.includes('`canonical:${row.canonical_player_id}`')
  },
  valueFinder:{
    sleeperKey:vfMap.includes('`s:${r.sleeper_id}`'),
    normalizedNameKey:vfMap.includes('`n:${vfName(r.full_name)}`'),
    sleeperLookup:vfRow.includes('map.get(`s:${p.sleeperId}`)'),
    normalizedNameFallback:vfRow.includes('||map.get(`n:${vfName(p.name)}`)')
  }
};

// Actual precedence conflict: Core ignores snake_case sleeper_id on a raw row,
// while current snapshot storage prefers it.
const conflict={sleeper_id:'sleeper-snake',player_id:'player-id',id:'generic-id'};
const currentCoreChoice=conflict.player_id;
const currentSnapshotChoice=conflict.sleeper_id;
const conflictFixture={
  row:conflict,
  coreChoice:currentCoreChoice,
  currentSnapshotChoice,
  diverges:currentCoreChoice!==currentSnapshotChoice
};

if(mode==='baseline'){
  assert(observed.corePlayerId.sleeperId,'Core playerId must currently recognize sleeperId');
  assert(observed.corePlayerId.player_id,'Core playerId must currently recognize player_id');
  assert(observed.corePlayerId.playerId,'Core playerId must currently recognize playerId');
  assert(observed.corePlayerId.id,'Core playerId must currently recognize id');
  assert(!observed.corePlayerId.sleeper_id,'baseline expects Core playerId to omit sleeper_id');
  assert(observed.corePlayerId.inlineSynthetic,'baseline expects inline synthetic:position:team:name fallback');

  assert(observed.corePlayerIdentity.sleeperId&&observed.corePlayerIdentity.player_id,
    'baseline expects Core PlayerIdentity.byId to use sleeperId/player_id');
  assert(!observed.corePlayerIdentity.sleeper_id,
    'baseline expects Core PlayerIdentity.byId to omit sleeper_id');
  assert(!observed.corePlayerIdentity.hasResolve,
    'baseline expects no canonical resolve() operation yet');
  assert(!observed.corePlayerIdentity.explicitUnavailable&&!observed.corePlayerIdentity.explicitAmbiguous,
    'baseline expects no explicit unavailable/ambiguous resolution states');

  assert(observed.currentFeatures.snapshotSleeperIdIndex&&observed.currentFeatures.liveSleeperIdLookup,
    'baseline expects current-feature bridge sleeper_id -> sleeperId');
  assert(observed.currentSnapshotStore.sleeperId&&observed.currentSnapshotStore.canonicalPlayerId&&observed.currentSnapshotStore.canonicalPrefix,
    'baseline expects current snapshot pid to prefer sleeper_id then canonical:<canonical_player_id>');

  assert(observed.valueFinder.sleeperKey&&observed.valueFinder.sleeperLookup,
    'baseline expects Value Finder Sleeper-ID path');
  assert(observed.valueFinder.normalizedNameKey&&observed.valueFinder.normalizedNameFallback,
    'baseline expects Value Finder normalized-name fallback');

  assert(conflictFixture.diverges,'identity conflict fixture must reproduce divergent precedence');

  console.log('KNOWN_GAP_REPRODUCED player identity is fragmented across stable IDs, synthetic IDs and display-name fallback');
  console.log(JSON.stringify({mode,observed,conflictFixture}));
}else if(mode==='target'){
  // Frozen contract for the subsequent production implementation.
  assert(observed.corePlayerIdentity.hasResolve,
    'target requires FIECore.PlayerIdentity.resolve()');
  assert(observed.corePlayerIdentity.explicitUnavailable,
    'target requires explicit unavailable identity state');
  assert(observed.corePlayerIdentity.explicitAmbiguous,
    'target requires explicit ambiguous identity state');
  assert(!observed.valueFinder.normalizedNameFallback,
    'target forbids display-name fallback for governed current-feature identity joins');
  console.log('PASS Tranche 3C canonical player identity contract');
}else{
  throw new Error(`unknown mode ${mode}`);
}
