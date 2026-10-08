'use strict';
const fs=require('fs'),vm=require('vm'),assert=require('assert');
const timers=new Map();let nextTimer=0;
const sandbox={console,Math,Date,Map,Set,Promise,setTimeout:fn=>{timers.set(++nextTimer,fn);return nextTimer;},clearTimeout:id=>timers.delete(id),
 state:{league:{league_id:'1',roster_positions:['QB']},rosters:[]},
 document:{readyState:'loading',addEventListener(){},getElementById(){return null;}},
 window:{addEventListener(){},FIELeagueProfileResolver:{resolve(){return{format:'REDRAFT'};}},playerDecisionValue(){return null;}}};
vm.createContext(sandbox);vm.runInContext(fs.readFileSync('app/decision-engines.js','utf8'),sandbox);
const internals=sandbox.window.FIEDecisionEngines.__formatInternals;
const record=internals.workerPlayerRecord({sleeperId:'123',name:'Unknown',position:'QB',engineSeasonProjection:null,sleeperSeasonProjection:null,seasonScore:null,weeklyProjection:null},{marketOf(){return 1;},decisionMap:new Map()});
assert.equal(record.mean,null,'Missing projection became zero at serialization');
class Worker{
 constructor(mode){this.mode=mode;this.listeners={message:new Set(),error:new Set()};}
 addEventListener(kind,fn){this.listeners[kind].add(fn);}
 removeEventListener(kind,fn){this.listeners[kind].delete(fn);}
 postMessage(msg){this.msg=msg;if(this.mode==='clone')throw new Error('clone rejected');}
 emit(kind,payload){for(const fn of [...this.listeners[kind]])fn(payload);}
 clean(){return this.listeners.message.size===0&&this.listeners.error.size===0&&timers.size===0;}
}
async function main(){
 for(const mode of ['success','worker-error','load-error','cancel','clone','timeout']){
  const worker=new Worker(mode),job={id:'job'};
  const pending=internals.receiveDraftBatch(worker,job,{},['123'],0,8);
  if(mode==='success'){
   worker.emit('message',{data:{type:'batch',jobId:'stale',results:[]}});assert(!worker.clean(),'Stale job resolved the batch');
   worker.emit('message',{data:{type:'batch',jobId:'job',results:[{id:'123',values:[1]}]}});
   assert.equal((await pending).results[0].values[0],1);
  }else{
   if(mode==='worker-error')worker.emit('message',{data:{type:'error',jobId:'job',error:'missing projection'}});
   if(mode==='load-error')worker.emit('error',{});
   if(mode==='cancel')job.rejectPending(new Error('cancelled'));
   if(mode==='timeout')[...timers.values()][0]();
   await assert.rejects(pending);
  }
  assert(worker.clean(),`Listeners/timer leaked after ${mode}`);assert.equal(job.rejectPending,null);
 }
 console.log('PASS draft worker lifecycle: missing projection serialization, stale-job isolation, immediate errors/cancellation, timeout/clone cleanup');
}
main().catch(error=>{console.error(error);process.exitCode=1;});
