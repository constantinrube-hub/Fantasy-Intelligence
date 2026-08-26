/* V9.3 Decision UX runtime smoke test without a browser. */
'use strict';
const fs=require('fs'),vm=require('vm'),path=require('path');
const ROOT=path.resolve(__dirname,'..');
const docListeners={};
global.document={
  readyState:'loading',title:'',
  addEventListener:(name,fn)=>{docListeners[name]=fn;},
  getElementById:()=>null,querySelector:()=>null,querySelectorAll:()=>[],createElement:()=>({style:{},classList:{add(){},remove(){},toggle(){}},appendChild(){},querySelectorAll:()=>[]})
};
global.window={state:{league:null,rosters:[],users:[],activeTab:'leagueintel',transactions:{loaded:false,loading:false,errors:[]}},PLAYERS:[],FIE_RELEASE:{release:'9.3.1-completion',runtime:'9.3.1-foundation'},FIE:{}};
global.state=window.state;global.PLAYERS=window.PLAYERS;
window.addEventListener=()=>{};window.dispatchEvent=()=>{};window.openDrawer=()=>{};window.render=()=>{};
global.performance={now:()=>0};
vm.runInThisContext(fs.readFileSync(path.join(ROOT,'app/decision-ui.js'),'utf8'),{filename:'app/decision-ui.js'});
if(!window.FIEUX93)throw new Error('FIEUX93 did not register');
if(typeof docListeners.DOMContentLoaded!=='function')throw new Error('Decision UI did not register DOMContentLoaded bind');
docListeners.DOMContentLoaded();
if(document.title!=='Fantasy Intelligence Engine · 9.3.1-completion')throw new Error(`Release title did not synchronize: ${document.title}`);
if(window.FIE.VERSION!=='9.3.1-completion'||window.FIE.RUNTIME_VERSION!=='9.3.1-foundation')throw new Error('Generated release identity did not propagate');
window.FIEUX93.renderActiveTab();
window.state.activeTab='research6';window.FIEUX93.renderScarcityAudit();
console.log('PASS V9.3.1 decision UI runtime smoke: init, release sync, League Intel, scarcity hooks');
