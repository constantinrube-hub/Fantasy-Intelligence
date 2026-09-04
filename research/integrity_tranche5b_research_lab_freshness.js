#!/usr/bin/env node
'use strict';
const fs=require('fs'),path=require('path'),vm=require('vm'),assert=require('assert');
const ROOT=path.resolve(__dirname,'..');
const expected=JSON.parse(fs.readFileSync(path.join(ROOT,'config/research-lab-ux-contract.json'),'utf8'));
const elements=new Map();
const document={
 readyState:'complete',
 getElementById:id=>elements.get(id)||null,
 addEventListener:()=>{}
};
const context={window:{addEventListener:()=>{},FIE_M5:{getCurrentBundle:()=>null}},document,console,Date,Object,Number,String,Math};
context.window.window=context.window;context.window.document=document;
vm.createContext(context);
vm.runInContext(fs.readFileSync(path.join(ROOT,'app/core/research-lab-ux.js'),'utf8'),context);
const api=context.window.FIEFreshness,ux=context.window.FIEResearchLabUX;
assert(api&&ux,'Research/Lab UX APIs missing');
assert.deepStrictEqual(JSON.parse(JSON.stringify(api.contract)),expected,'browser contract must exactly mirror JSON contract');
assert(Object.isFrozen(api.contract)&&Object.isFrozen(api.contract.navigation_groups),'contract must be immutable');
const now=Date.parse('2026-09-04T12:00:00Z');
assert.strictEqual(api.describe({asOf:'2026-09-04T10:00:00Z',maxAgeHours:8,now}).state,'current');
assert.strictEqual(api.describe({asOf:'2026-09-04T05:30:00Z',maxAgeHours:8,now}).state,'aging');
assert.strictEqual(api.describe({asOf:'2026-09-03T12:00:00Z',maxAgeHours:8,now}).state,'stale');
assert.strictEqual(api.describe({asOf:'2026-09-04T10:00:00Z',available:false,maxAgeHours:8,now}).state,'unavailable','availability must fail closed before timestamp freshness');
assert.strictEqual(api.describe({asOf:'not-a-time',available:true,maxAgeHours:8,now}).state,'unknown');
assert.strictEqual(api.describe({asOf:'2026-09-05T12:00:00Z',available:true,maxAgeHours:8,now}).state,'unknown','future timestamps cannot be current');
assert.strictEqual(api.weeklyLabel({asOf:null,available:false}),'Unavailable','missing week/season must not become Season 0');
assert.strictEqual(api.isFresh({asOf:'2026-09-04T05:30:00Z',maxAgeHours:8,now}),true);
assert.strictEqual(api.isFresh({asOf:'2026-09-03T12:00:00Z',maxAgeHours:8,now}),false);
assert(api.weeklyLabel({season:2026,week:1,asOf:'2026-09-04T10:00:00Z',maxAgeHours:8,now}).startsWith('Season 2026 · Week 1 · Current'));
for(const key of ['score','rank','recommendation','activation'])assert(!Object.prototype.hasOwnProperty.call(api.describe({}),key),`display presenter must not emit ${key}`);
const index=fs.readFileSync(path.join(ROOT,'index.html'),'utf8'),report=fs.readFileSync(path.join(ROOT,'app/research-report-ui.js'),'utf8'),runtime=fs.readFileSync(path.join(ROOT,'app/runtime-foundation.js'),'utf8');
assert(index.includes('data-fie-research-report')&&report.includes('[data-fie-research-report]'),'League Research Report entry point is not integrated');
assert(index.indexOf('app/core/research-lab-ux.js')<index.indexOf('app/runtime-foundation.js'),'freshness presenter must load before runtime diagnostics');
assert(index.includes("window.FIEFreshness?.weeklyLabel")&&index.includes("window.FIEFreshness?.isFresh"),'M5/M6 do not use shared freshness');
assert(report.includes('window.FIEFreshness?.timestampLabel')&&runtime.includes('window.FIEFreshness?.timestampLabel'),'report/runtime freshness not unified');
console.log('PASS Tranche 5B grouped Research/Lab IA and display-only freshness contract');
