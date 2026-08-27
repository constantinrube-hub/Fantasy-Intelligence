/* Execute the real V9.3.2 season bootstrap and verify browser load order, strict
 * Season-0 semantics, and fail-soft startup when the external season helper is
 * temporarily unavailable at the edge/browser cache. */
'use strict';
const fs=require('fs'),vm=require('vm'),assert=require('assert');
const src=fs.readFileSync('index.html','utf8');
const svc=fs.readFileSync('app/core/season-context.js','utf8');

const serviceTag=src.indexOf('season-context.js?v=932-bootstrap-resilience');
const firstInline=src.indexOf('<script>',serviceTag+1);
const bootstrapStart=src.indexOf('/* V9.3.2 bootstrap season compatibility.',firstInline);
const bootstrapDef=src.indexOf('function activeSeason(){',bootstrapStart);
const universeDef=src.indexOf('function buildPlayerUniverse(){');
assert(serviceTag>=0,'season-context service must be requested by index.html');
assert(firstInline>serviceTag,'season-context request must precede the first inline runtime');
assert(bootstrapStart>firstInline&&bootstrapDef>bootstrapStart&&bootstrapDef<universeDef,'global activeSeason bootstrap must exist before buildPlayerUniverse');
assert(src.includes('window.activeSeason=activeSeason;'),'activeSeason must be exposed to staged/external runtime modules');
assert(src.includes('FIE_SEASON_CONTEXT_BOOTSTRAP_FALLBACK'),'inline startup fallback must be present');

function makeContext(){
  const elements={seasonSelect:{value:'',options:[]},weekSelect:{value:'',options:[]}};
  const ctx={console,document:{getElementById:id=>elements[id]||null},Date,Number,String,Math};
  ctx.window=ctx;ctx.state={league:{season:'2026'},weekly:{season:null,week:1}};ctx.$=id=>elements[id]||null;
  vm.createContext(ctx);
  return {ctx,elements};
}

const bootstrapEnd=src.indexOf('const esc=',bootstrapStart);
assert(bootstrapStart>=0&&bootstrapEnd>bootstrapStart,'cannot extract bootstrap activeSeason implementation');
const bootstrap=src.slice(bootstrapStart,bootstrapEnd);

// Exact browser failure that escaped the previous test: the external file does
// not initialize, but the inline application still has to load the league.
{
  const {ctx,elements}=makeContext();
  assert.strictEqual(ctx.FIESeasonContext,undefined);
  vm.runInContext(bootstrap,ctx);
  assert(ctx.FIESeasonContext?.resolve,'bootstrap did not install fail-soft season API');
  assert.strictEqual(ctx.FIE_SEASON_CONTEXT_BOOTSTRAP_FALLBACK,true);
  assert.strictEqual(ctx.activeSeason(),2026,'missing external season service must not block a loaded 2026 league');
  elements.seasonSelect.value='0';
  assert.strictEqual(ctx.activeSeason(),2026,'selector 0 must not override loaded Sleeper season in fallback mode');
  ctx.state.league=null;elements.seasonSelect.value='';ctx.state.weekly.season=2026;
  assert.strictEqual(ctx.activeSeason(),2026,'weekly season must survive blank selector in fallback mode');
}

// Normal path: canonical external service loads first and remains authoritative.
{
  const {ctx,elements}=makeContext();
  vm.runInContext(svc,ctx);
  const canonical=ctx.FIESeasonContext;
  assert(canonical,'season service did not initialize');
  assert.strictEqual(canonical.parse(null),null);
  assert.strictEqual(canonical.parse(''),null);
  assert.strictEqual(canonical.parse('0'),null);
  assert.strictEqual(canonical.parse(0),null);
  assert.strictEqual(canonical.parse('2026'),2026);
  vm.runInContext(bootstrap,ctx);
  assert.strictEqual(ctx.FIESeasonContext,canonical,'bootstrap must not replace a successfully loaded canonical service');
  assert.strictEqual(ctx.FIE_SEASON_CONTEXT_BOOTSTRAP_FALLBACK,undefined);
  assert.strictEqual(ctx.activeSeason(),2026,'blank season selector must not coerce to Season 0');
  elements.seasonSelect.value='0';
  assert.strictEqual(ctx.activeSeason(),2026,'selector value 0 must not override loaded Sleeper season');
  ctx.state.league=null;elements.seasonSelect.value='';ctx.state.weekly.season=2026;
  assert.strictEqual(ctx.activeSeason(),2026,'weekly state 2026 must survive blank selector');
  ctx.state.league={season:'2026'};elements.seasonSelect.value='2025';
  assert.strictEqual(ctx.activeSeason(),2026,'loaded Sleeper league season must remain authoritative');
}

// Later compatibility layer must delegate to the globally initialized API.
assert(src.includes('function activeSeason(){return window.activeSeason();}'),'V8.9 compatibility layer must delegate to global season API');
console.log('PASS V9.3.2 season bootstrap resilience: external helper optional at startup, loaded 2026 remains Season 2026');
