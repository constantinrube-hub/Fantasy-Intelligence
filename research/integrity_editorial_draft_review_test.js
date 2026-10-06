'use strict';
const assert=require('assert'),vm=require('vm'),fs=require('fs');
const state={league:{league_id:'a',season:'2026'},selectedRoster:1,rosters:[{roster_id:1}],draftIntel:{loaded:true,loading:false,error:null,selectedDraftId:'d',draft:{draft_id:'d',league_id:'a',season:'2026',status:'complete',type:'auction'},picks:[{pick_no:1,player_id:'p',roster_id:1,round:1,metadata:{first_name:'Recorded',last_name:'Name',position:'RB',amount:0}}]}};
const window={state,PLAYERS:[{sleeperId:'p',name:'Today Name',position:'WR',engineSeasonProjection:900,marketADP:1}]};vm.runInNewContext(fs.readFileSync('app/ui/draft-review-workspace.js','utf8'),{window,document:{getElementById:()=>null},console});const u=window.FIEDraftReviewWorkspace,i=state.draftIntel;
assert(u.claims('draftanalysis'));assert(u.claims('draftassistant'));assert(!u.claims('team'));assert(u.health().ready);assert(u.ledger().ok);
const r=u.records()[0];assert.equal(r.name,'Recorded Name');assert.equal(r.position,'RB');assert.equal(r.cost,0);assert.equal(r.identity,'Provider pick metadata');assert.equal(r.p.name,'Today Name');assert(!('draftTimeRank' in r));
delete i.picks[0].metadata.amount;assert.equal(u.records()[0].cost,null);i.picks[0].metadata.amount='not numeric';assert.equal(u.records()[0].cost,null);i.draft.type='snake';i.picks[0].metadata.amount=10;assert.equal(u.records()[0].cost,null);
i.picks.push({pick_no:3,player_id:'q',roster_id:1});assert(!u.ledger().ok);i.picks.pop();i.picks.push({pick_no:2,player_id:'p',roster_id:1});assert(!u.ledger().ok);i.picks.pop();delete i.picks[0].roster_id;assert(!u.ledger().ok);i.picks[0].roster_id=1;
for(const [key,value]of [['league_id','b'],['season','2025']]){const old=i.draft[key];i.draft[key]=value;assert(!u.health().ready);i.draft[key]=old;}
i.selectedDraftId='other';assert(!u.health().ready);i.selectedDraftId='d';i.loading=true;assert(!u.health().ready);i.loading=false;i.error='failed';assert(!u.health().ready);i.error=null;state.selectedRoster=99;assert(!u.health().ready);state.selectedRoster=1;
i.draft.status='drafting';assert(!u.claims('draft'));assert(!u.health().ready);i.draft.status='pre_draft';assert(!u.claims('valuefinder'));i.draft.status='complete';
const nav=u.navigation('draft',{tabs:[]});assert.equal(nav.tabs[0][0],'draftanalysis');assert(nav.desc.includes('Historical grades require'));assert.equal(u.navigation('team',{x:1}).x,1);
window.PLAYERS=[];delete i.picks[0].metadata.first_name;delete i.picks[0].metadata.last_name;assert.match(u.records()[0].name,/Unresolved/);
console.log('Editorial post-draft scope, observed identity/price and no historical imputation PASS');
