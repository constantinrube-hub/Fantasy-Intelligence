/* Tranche 3B target: ResearchReportService routes all primary JSON transport through FIEDataClient. */
'use strict';
const fs=require('fs'),vm=require('vm'),assert=require('assert');
const code=fs.readFileSync('app/core/research-report-service.js','utf8');
assert.ok(!/(?<![\w.$])fetch\s*\(/.test(code),'ResearchReportService must not own raw browser fetch');
assert.ok(code.includes('FIEDataClient'),'ResearchReportService must visibly depend on canonical FIEDataClient');

const league='1391803939736801280',calls=[];
const readinessPath=`data/research/leagues/${league}/performance/2026/research_pipeline/final_model_readiness.json`;
const ctx={console,window:null,state:{},FIELeagueContext:{current:()=>({leagueId:league})},addEventListener(){}};
ctx.window=ctx;
ctx.FIEDataClient={
  async json(path,opts={}){
    calls.push({path:String(path),opts:{...opts}});
    if(String(path)===`data/research/leagues/${league}/app/core.json`){
      return {league_id:league,research:{readiness:readinessPath}};
    }
    if(String(path)===readinessPath){
      return {league_id:league,positions:{QB:{status:'ready'}}};
    }
    throw new Error(`unexpected DataClient path ${path}`);
  }
};
vm.createContext(ctx);vm.runInContext(code,ctx,{filename:'research-report-service.js'});
(async()=>{
  const out=await ctx.FIEResearchReportService.readiness();
  assert.strictEqual(out.positions.QB.status,'ready');
  assert.strictEqual(calls.length,2,'core + readiness should each route once through FIEDataClient');
  for(const call of calls){
    assert.strictEqual(call.opts.cache,'no-store','report service retains network-fresh semantics');
    assert.strictEqual(call.opts.persist,false,'research report transport must not create persistent transport cache');
    assert.strictEqual(call.opts.sourceId,'research-report','research transport diagnostics sourceId missing');
  }
  console.log('PASS Tranche 3B ResearchReportService canonical DataClient transport contract');
})().catch(e=>{console.error(e);process.exit(1);});
