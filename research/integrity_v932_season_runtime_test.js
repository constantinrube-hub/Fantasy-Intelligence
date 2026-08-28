/* V9.3.2 lineage season-runtime regression against modular services. */
'use strict';
const fs=require('fs'),vm=require('vm'),assert=require('assert');

const bootstrapSvc=fs.readFileSync('app/core/season-context.js','utf8');
const numericSvc=fs.readFileSync('app/core/numeric.js','utf8');
const runtimeSrc=fs.readFileSync('app/runtime-foundation.js','utf8');

function makeContext(){
  const elements={seasonSelect:{value:'',options:[]},weekSelect:{value:'',options:[]}};
  const ctx={
    console,Date,Number,String,Math,Object,Array,Map,Set,JSON,
    document:{getElementById:id=>elements[id]||null,createElement:()=>({})},
    state:{league:{season:'2026'},weekly:{season:null,week:1}}
  };
  ctx.window=ctx;
  vm.createContext(ctx);
  return {ctx,elements};
}

// Early bootstrap helper owns only the bootstrap namespace.
{
  const {ctx,elements}=makeContext();
  vm.runInContext(bootstrapSvc,ctx,{filename:'season-context.js'});
  assert(ctx.FIESeasonBootstrapResolver?.resolve,'bootstrap resolver missing');
  assert.strictEqual(ctx.FIESeasonContext,undefined,'bootstrap helper must not claim runtime FIESeasonContext');
  assert.strictEqual(ctx.FIESeasonBootstrapResolver.resolve({
    leagueSeason:'2026',selectorValue:'',weeklySeason:null
  }),2026);
  assert.strictEqual(ctx.FIESeasonBootstrapResolver.resolve({
    leagueSeason:'2026',selectorValue:'0',weeklySeason:null
  }),2026);
}

// Canonical numeric service installs FIECore.SeasonResolver and agrees on null,
// blank and zero selector semantics.
{
  const {ctx,elements}=makeContext();
  vm.runInContext(bootstrapSvc,ctx,{filename:'season-context.js'});
  vm.runInContext(numericSvc,ctx,{filename:'numeric.js'});
  assert(ctx.FIECore?.SeasonResolver?.resolve,'canonical SeasonResolver missing');
  assert.strictEqual(ctx.FIECore.SeasonResolver.resolve(),2026);
  elements.seasonSelect.value='0';
  assert.strictEqual(ctx.FIECore.SeasonResolver.resolve(),2026);
  ctx.state.league=null;
  elements.seasonSelect.value='';
  ctx.state.weekly.season=2026;
  assert.strictEqual(ctx.FIECore.SeasonResolver.resolve(),2026);

  const b=ctx.FIESeasonBootstrapResolver,c=ctx.FIECore.SeasonResolver;
  for(const x of [null,undefined,'',' ',0,'0']){
    const bv=b.resolve({leagueSeason:x,selectorValue:x,weeklySeason:'2026'});
    const cv=c.resolve({league:{season:x},selected:x,weekly:'2026'});
    assert.strictEqual(bv,cv,`bootstrap/canonical mismatch for ${String(x)}`);
  }
}

// Runtime foundation remains the owner of the runtime FIESeasonContext facade.
assert(runtimeSrc.includes('window.FIESeasonContext=SeasonContext'),
       'runtime foundation must own FIESeasonContext');
assert(runtimeSrc.includes('resolve({league=window.state?.league'),
       'runtime FIESeasonContext must expose compatibility resolve');

console.log('PASS V9.3.2 lineage season runtime: modular bootstrap/canonical/runtime namespaces agree');
