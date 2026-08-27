/* Execute the real V9.3.2 season bootstrap and verify strict Season-0 semantics,
 * browser load order, canonical handoff, and the namespace collision that caused
 * the 2026-08-27 live regressions. */
'use strict';
const fs=require('fs'),vm=require('vm'),assert=require('assert');
const src=fs.readFileSync('index.html','utf8');
const bootstrapSvc=fs.readFileSync('app/core/season-context.js','utf8');
const numericSvc=fs.readFileSync('app/core/numeric.js','utf8');
const runtimeSrc=fs.readFileSync('app/runtime-foundation.js','utf8');

const serviceTag=src.indexOf('season-context.js?v=932-season-namespace-fix');
const firstInline=src.indexOf('<script>',serviceTag+1);
const bootstrapStart=src.indexOf('/* V9.3.2 season bootstrap compatibility.',firstInline);
const bootstrapDef=src.indexOf('function activeSeason(){',bootstrapStart);
const universeDef=src.indexOf('function buildPlayerUniverse(){');
assert(serviceTag>=0,'season bootstrap helper must be requested by index.html');
assert(firstInline>serviceTag,'season bootstrap helper request must precede the first inline runtime');
assert(bootstrapStart>firstInline&&bootstrapDef>bootstrapStart&&bootstrapDef<universeDef,'global activeSeason bootstrap must exist before buildPlayerUniverse');
assert(src.includes('window.activeSeason=activeSeason;'),'activeSeason must be exposed to staged/external runtime modules');
assert(!src.includes('window.FIESeasonContext.resolve({'),'startup code must not call runtime FIESeasonContext as the resolver');
assert(src.includes('window.FIECore?.SeasonResolver?.resolve'),'activeSeason must prefer canonical FIECore.SeasonResolver once loaded');
assert(runtimeSrc.includes('window.FIESeasonContext=SeasonContext'),'runtime foundation remains owner of FIESeasonContext');
assert(runtimeSrc.includes('resolve({league=window.state?.league'),'runtime FIESeasonContext must expose compatibility resolve during cache rollovers');

function makeContext(){
  const elements={seasonSelect:{value:'',options:[]},weekSelect:{value:'',options:[]}};
  const ctx={console,document:{getElementById:id=>elements[id]||null,createElement:()=>({})},Date,Number,String,Math,Object,Array};
  ctx.window=ctx;ctx.state={league:{season:'2026'},weekly:{season:null,week:1}};ctx.$=id=>elements[id]||null;
  vm.createContext(ctx);
  return {ctx,elements};
}
const bootstrapEnd=src.indexOf('const esc=',bootstrapStart);
assert(bootstrapStart>=0&&bootstrapEnd>bootstrapStart,'cannot extract bootstrap activeSeason implementation');
const bootstrap=src.slice(bootstrapStart,bootstrapEnd);

// 1. Earliest browser phase: no helper and no FIECore yet. League loading must work.
{
  const {ctx,elements}=makeContext();
  assert.strictEqual(ctx.FIESeasonBootstrapResolver,undefined);
  vm.runInContext(bootstrap,ctx);
  assert(ctx.FIESeasonBootstrapResolver?.resolve,'inline bootstrap did not install strict early resolver');
  assert.strictEqual(ctx.FIESeasonContext,undefined,'bootstrap must not claim runtime FIESeasonContext namespace');
  assert.strictEqual(ctx.activeSeason(),2026);
  elements.seasonSelect.value='0';
  assert.strictEqual(ctx.activeSeason(),2026,'selector 0 must not override loaded Sleeper season');
}

// 2. External early helper path: it uses a separate namespace and matches fallback semantics.
{
  const {ctx,elements}=makeContext();
  vm.runInContext(bootstrapSvc,ctx);
  assert(ctx.FIESeasonBootstrapResolver?.resolve,'external bootstrap resolver did not initialize');
  assert.strictEqual(ctx.FIESeasonContext,undefined,'external helper must not overwrite runtime FIESeasonContext');
  vm.runInContext(bootstrap,ctx);
  assert.strictEqual(ctx.activeSeason(),2026);
  elements.seasonSelect.value='0';assert.strictEqual(ctx.activeSeason(),2026);
}

// 3. Canonical handoff: numeric.js installs FIECore.SeasonResolver and activeSeason uses it.
{
  const {ctx,elements}=makeContext();
  vm.runInContext(bootstrapSvc,ctx);vm.runInContext(bootstrap,ctx);vm.runInContext(numericSvc,ctx);
  assert(ctx.FIECore?.SeasonResolver?.resolve,'canonical FIECore.SeasonResolver missing');
  assert.strictEqual(ctx.activeSeason(),2026);
  elements.seasonSelect.value='0';assert.strictEqual(ctx.activeSeason(),2026);
  ctx.state.league=null;elements.seasonSelect.value='';ctx.state.weekly.season=2026;
  assert.strictEqual(ctx.activeSeason(),2026,'weekly 2026 must survive blank selector');
}

// 4. Exact live collision regression: runtime foundation owns FIESeasonContext and may
// replace any earlier value. activeSeason must remain independent from that namespace.
{
  const {ctx}=makeContext();
  vm.runInContext(bootstrapSvc,ctx);vm.runInContext(bootstrap,ctx);vm.runInContext(numericSvc,ctx);
  const early=ctx.FIESeasonBootstrapResolver;
  ctx.FIESeasonContext=Object.freeze({active:()=>2026,prior:()=>2025,week:()=>1,snapshot:()=>({active:2026})});
  assert.strictEqual(ctx.FIESeasonContext.resolve,undefined,'fixture must reproduce the old runtime facade without resolve');
  assert.strictEqual(ctx.activeSeason(),2026,'runtime FIESeasonContext replacement must not break activeSeason');
  assert.strictEqual(ctx.FIESeasonBootstrapResolver,early,'runtime facade must not replace bootstrap resolver');
}

// 5. Canonical and bootstrap parsers agree on the problematic null/blank/zero cases.
{
  const {ctx}=makeContext();vm.runInContext(bootstrapSvc,ctx);vm.runInContext(numericSvc,ctx);
  const b=ctx.FIESeasonBootstrapResolver,c=ctx.FIECore.SeasonResolver;
  for(const x of [null,undefined,'', ' ',0,'0']){
    const bv=b.resolve({leagueSeason:x,selectorValue:x,weeklySeason:'2026'});
    const cv=c.resolve({league:{season:x},selected:x,weekly:'2026'});
    assert.strictEqual(bv,cv,`bootstrap/canonical season mismatch for ${String(x)}`);
  }
}

assert(src.includes('function activeSeason(){return window.activeSeason();}'),'V8.9 compatibility layer must delegate to global activeSeason');
console.log('PASS V9.3.2 season namespace regression: bootstrap resolver, canonical resolver and runtime context cannot overwrite each other; loaded 2026 remains Season 2026');
