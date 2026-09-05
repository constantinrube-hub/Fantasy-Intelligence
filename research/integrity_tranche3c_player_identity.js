/* Permanent Tranche 3C / C10-007 canonical identity source contract. */
'use strict';
const fs=require('fs'),assert=require('assert');
const mode=(process.argv.includes('--mode')?process.argv[process.argv.indexOf('--mode')+1]:'target');
if(mode!=='target')throw new Error('Current Tranche 3C integrity test is target-only; historical baseline is pinned in the preflight workflow.');
const read=p=>fs.readFileSync(p,'utf8'),compact=s=>String(s).replace(/\s+/g,'');
const core=compact(read('app/core/core-services.js'));
const features=compact(read('app/current-player-features.js'));
const store=compact(read('app/current-snapshot-store.js'));
const vf=compact(read('app/value-finder.js'));
const dst=compact(read('app/dst-intelligence.js'));
const kicker=compact(read('app/kicker-intelligence.js'));
const py=read('research/current_snapshot_storage.py');

assert(core.includes("source:'FIECore.PlayerIdentity'"));
for(const token of ["field:'sleeperId'","field:'sleeper_id'","field:'player_id'","field:'playerId'","field:'canonical_player_id'","field:'internal_id'","field:'gsis_id'","field:'pfr_id'","field:'fantasypros_id'"]){
  assert(core.includes(token),`missing identity alias ${token}`);
}
assert(core.includes('governedId(subject)'));
assert(core.includes('resolve(subject,{players='));
assert(core.includes("status:'resolved'"));
assert(core.includes("status:'unavailable'"));
assert(core.includes("status:'ambiguous'"));
assert(core.includes('display_name_collision_not_identity'));
assert(core.includes('display_name_not_canonical'));
assert(core.includes('synthetic:${pos}:${team}:${name}'),'compatibility synthetic IDs remain available for non-governed bookkeeping');

assert(features.includes('identity.resolve(row,{players:live,index:idx})'));
assert(features.includes('identityResolved:true'));
assert(features.includes('p.currentFeatureLineage.identityResolved===true'));
assert(store.includes('FIECore?.PlayerIdentity?.governedId?.(row)'));
assert(vf.includes('identity.resolve(p,{players:ctx.rows,index:ctx.index})'));
assert(!vf.includes('map.get(`n:${vfName(p.name)}`)'),'Value Finder governed current join must not use normalized-name fallback');
assert(!vf.includes('m.set(`n:${vfName(r.full_name)}`'),'Value Finder must not build governed name identity keys');
assert(dst.includes('identity.resolve(p,{players:ctx.rows,index:ctx.index})'),'D/ST must use canonical identity resolver');
assert(kicker.includes('identity.resolve(p,{players:ctx.rows,index:ctx.index})'),'Kicker must use canonical identity resolver');
assert(py.includes('Current snapshot row lacks governed Sleeper/canonical crosswalk identity'));
assert(!py.includes('full_name')&&!py.includes('name-position'),'Python storage identity must not use display names');
console.log('PASS Tranche 3C canonical PlayerIdentity ownership and governed consumer contract');
