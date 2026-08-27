/* Execute the real V9.3.2 season service and verify bootstrap ordering/scope. */
'use strict';
const fs=require('fs'),vm=require('vm'),assert=require('assert');
const src=fs.readFileSync('index.html','utf8');
const svc=fs.readFileSync('app/core/season-context.js','utf8');

// The regression that escaped V9.3.2: buildPlayerUniverse was in the first
// inline script while activeSeason existed only inside a later V8.9 IIFE.
// Block that entire class of load-order/scope failures.
const serviceTag=src.indexOf('<script src="app/core/season-context.js"></script>');
const firstInline=src.indexOf('<script>',serviceTag+1);
const bootstrapDef=src.indexOf('function activeSeason(){',firstInline);
const universeDef=src.indexOf('function buildPlayerUniverse(){');
assert(serviceTag>=0,'season-context service must be loaded by index.html');
assert(firstInline>serviceTag,'season-context service must load before the first inline runtime');
assert(bootstrapDef>firstInline&&bootstrapDef<universeDef,'global activeSeason bootstrap must exist before buildPlayerUniverse');
assert(src.includes('window.activeSeason=activeSeason;'),'activeSeason must be exposed to staged/external runtime modules');

const elements={seasonSelect:{value:'',options:[]},weekSelect:{value:'',options:[]}};
const ctx={console,document:{getElementById:id=>elements[id]||null},Date,Number,String,Math};ctx.window=ctx;vm.createContext(ctx);
vm.runInContext(svc,ctx);
assert(ctx.FIESeasonContext,'season service did not initialize');
assert.strictEqual(ctx.FIESeasonContext.parse(null),null);
assert.strictEqual(ctx.FIESeasonContext.parse(''),null);
assert.strictEqual(ctx.FIESeasonContext.parse('0'),null);
assert.strictEqual(ctx.FIESeasonContext.parse(0),null);
assert.strictEqual(ctx.FIESeasonContext.parse('2026'),2026);

ctx.state={league:{season:'2026'},weekly:{season:null,week:1}};
ctx.$=id=>elements[id]||null;
const start=src.indexOf('/* V9.3.2 bootstrap season compatibility:');
const end=src.indexOf('const esc=',start);
assert(start>=0&&end>start,'cannot extract bootstrap activeSeason implementation');
vm.runInContext(src.slice(start,end),ctx);
assert.strictEqual(ctx.activeSeason(),2026,'blank season selector must not coerce to Season 0');
elements.seasonSelect.value='0';
assert.strictEqual(ctx.activeSeason(),2026,'selector value 0 must not override loaded Sleeper season');
ctx.state.league=null;elements.seasonSelect.value='';ctx.state.weekly.season=2026;
assert.strictEqual(ctx.activeSeason(),2026,'weekly state 2026 must survive blank selector');
ctx.state.league={season:'2026'};elements.seasonSelect.value='2025';
assert.strictEqual(ctx.activeSeason(),2026,'loaded Sleeper league season must remain authoritative');

// Ensure later compatibility layer delegates to the globally initialized API
// rather than reintroducing a private, divergent resolver.
assert(src.includes('function activeSeason(){return window.activeSeason();}'),'V8.9 compatibility layer must delegate to global season API');
console.log('PASS V9.3.2 season bootstrap: activeSeason exists before league-universe build and resolves loaded 2026 without Season 0');
