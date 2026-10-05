/* Deterministic full-app browser fixtures; no provider data is represented as live validation. */
'use strict';
const fs=require('fs'),path=require('path'),http=require('http'),assert=require('assert');
const {chromium}=require(process.env.FIE_UI_PLAYWRIGHT||'playwright');
const root=path.resolve(process.argv[2]||'dist'),out=path.resolve(process.env.FIE_UI_QA_OUTPUT||'editorial-weekly-qa');
fs.mkdirSync(out,{recursive:true});
const fixtures=[{roster_id:1,matchup_id:1,points:26.5,starters:['1001','1002','1003','1004','1005'],starters_points:[18.4,0,5.1,5,-2],players:['1001','1002','1003','1004','1005','1006'],players_points:{1001:18.4,1002:0,1003:5.1,1004:5,1005:-2,1006:14}}, {roster_id:2,matchup_id:1,points:24,starters:['1007'],starters_points:[24],players:['1007'],players_points:{1007:24}}];
(async()=>{
 const server=await new Promise(resolve=>{const s=http.createServer((req,res)=>{const u=new URL(req.url,'http://localhost'),f=path.resolve(root,'.'+(u.pathname==='/'?'/index.html':u.pathname));if(!f.startsWith(root+path.sep)){res.writeHead(403).end();return;}fs.readFile(f,(err,b)=>{if(err){res.writeHead(404).end();return;}res.setHeader('Content-Type',f.endsWith('.js')?'application/javascript':f.endsWith('.css')?'text/css':f.endsWith('.json')?'application/json':'text/html');res.end(b);});}).listen(0,'127.0.0.1',()=>resolve(s));});
 const browser=await chromium.launch({headless:true}),report={mode:'Explicit fictional provider fixtures in the real application. Not live league validation.',samples:[]};
 try{
 for(const width of [1440,390]){
  const context=await browser.newContext({viewport:{width,height:width===390?844:1000}}),page=await context.newPage();let nflWeek=4,fail=false,delay=0;
  await context.route('https://**/*',async route=>{const u=route.request().url();if(u.includes('/v1/state/nfl'))return route.fulfill({json:{season:'2026',display_week:nflWeek,season_type:'regular'}});if(u.includes('/matchups/')){if(delay)await new Promise(r=>setTimeout(r,delay));return fail?route.fulfill({status:503,body:'Unavailable'}):route.fulfill({json:fixtures});}return route.abort();});
  await page.goto(`http://127.0.0.1:${server.address().port}`,{waitUntil:'load'});
  await page.waitForFunction(()=>!!window.FIEWeeklyWorkspace&&!!window.FIEUX93);
  await page.evaluate(()=>{
   state.league={league_id:'999999999999999999',name:'Fictional QA league',season:'2026',roster_positions:['QB','RB','FLEX','K','DEF','BN'],scoring_settings:{pass_yd:0.04,pass_td:4,rush_yd:0.1,rec_yd:0.1,rec:1},settings:{type:0,best_ball:0}};
   state.rosters=[{roster_id:1,owner_id:'one',players:['1001','1002','1003','1004','1005','1006']},{roster_id:2,owner_id:'two',players:['1007']}];state.users=[{user_id:'one',display_name:'Your fictional team'},{user_id:'two',display_name:'Fictional opponent'}];
   const ps=[['1001','Alex Turner','QB',18.4],['1002','Sam Jordan','RB',10],['1003','Taylor Quinn','WR',9],['1004','Morgan Vale','K',7],['1005','Fictional defense','DEF',6],['1006','Jamie Lee','RB',12],['1007','Opponent QB','QB',20]];
   PLAYERS=ps.map(([sleeperId,name,position,weeklyProjection])=>({sleeperId,name,position,team:'BUF',ownerRosterId:sleeperId==='1007'?2:1,weeklyProjection,weeklyProjectionSource:'Browser estimate',leagueEligible:true,yearsExp:1,side:position==='DEF'?'DEF':'OFF'}));
   PLAYERS[0].gsisId='qa-gsis';state.selectedRoster=1;state.matched=true;state.weekly={...state.weekly,season:2026,week:3,loaded:true,schedule:[],weekly2026:[{player_id:'qa-gsis',season:2026,week:3,season_type:'REG',passing_yards:300,passing_tds:1}]};populateRosterPicker();document.getElementById('kLeague').textContent='Fictional QA league';document.getElementById('status').textContent='Fictional browser test data · not live league results';document.getElementById('weekSelect').value='3';state.projectionStatus={...state.projectionStatus,weekly:true,weeklyContext:{leagueId:state.league.league_id,season:2026,week:5}};FIEPortfolio.leave();activateTab('startsit');
  });
  await page.getByText('Reported matchup result',{exact:true}).waitFor();
  assert(await page.getByText('Win · +2.50 pts',{exact:true}).isVisible());
  assert(await page.getByRole('cell',{name:'0.00 pts',exact:true}).isVisible());
  assert(await page.getByRole('cell',{name:'-2.00 pts',exact:true}).isVisible());
  await page.evaluate(()=>scrollTo(0,0));
  const basic=await page.evaluate(()=>({firstActualRowTop:document.querySelector('#fieWeeklyWorkspace table tbody tr')?.getBoundingClientRect().top,documentWidth:document.documentElement.scrollWidth}));
  await page.screenshot({path:path.join(out,`basic-${width}.png`),fullPage:true});
  assert(basic.firstActualRowTop + 35 < (width===390?844:1000), 'First actual player row must enter the first viewport');
  assert.strictEqual(await page.locator('#fieWeeklyWorkspace .fie-expanded:visible').count(),0);
  await page.getByRole('button',{name:'Expand Alex Turner',exact:true}).click();
  assert(await page.getByText(/no served forecast bound/).first().isVisible());
  assert(await page.getByText(/Partial replay/).first().isVisible(),'Partial scoring is explicit');
  await page.getByRole('button',{name:'Expand Sam Jordan',exact:true}).click();
  assert.strictEqual(await page.locator('#fieWeeklyWorkspace .fie-expanded:visible').count(),1);
  const adv=page.getByRole('button',{name:'Advanced evidence for Alex Turner',exact:true});await adv.click();assert(await page.locator('dialog[open]').isVisible());await page.keyboard.press('Escape');assert(await adv.evaluate(e=>document.activeElement===e));
  await page.locator('#fieWeeklyWorkspace summary').filter({hasText:'Lineup review'}).click();
  await page.getByRole('rowheader',{name:'Hindsight legal best',exact:true}).waitFor();
  const measurement=await page.evaluate(()=>({documentWidth:document.documentElement.scrollWidth,viewport:innerWidth,actualRowTop:document.querySelector('#fieWeeklyWorkspace table tbody tr')?.getBoundingClientRect().top}));assert(measurement.documentWidth<=width+1,'Viewport overflow');
  await page.screenshot({path:path.join(out,`completed-${width}.png`),fullPage:true});report.samples.push({width,state:'completed',...basic,documentWidth:measurement.documentWidth,viewport:width});
  await page.locator('#weekSelect').selectOption('5');await page.getByRole('heading',{name:'Projected starters',exact:true}).waitFor().catch(async e=>{console.log(await page.evaluate(()=>({text:document.getElementById('fieWeeklyWorkspace').innerText,tab:state.activeTab,scope:state.weekly,ws:FIEUX93.weeklyDecisionState()})));throw e;});assert.strictEqual(await page.locator('#fieWeeklyWorkspace .fie-expanded:visible').count(),0);await page.screenshot({path:path.join(out,`upcoming-${width}.png`),fullPage:true});
  await page.locator('#weekSelect').selectOption('4');await page.getByText('Matchup points so far',{exact:true}).waitFor().catch(async()=>{await page.getByText(/Week timing cannot be verified/).waitFor();});
  // Cold period has no loaded schedule: unverified is the truthful current-week state.
  await page.screenshot({path:path.join(out,`current-${width}.png`),fullPage:true});
  await page.evaluate(()=>{activateTab('all');});await page.waitForFunction(()=>!document.body.classList.contains('fie-weekly-active'));assert(!(await page.locator('#fieWeeklyWorkspace').isVisible()));
  await page.evaluate(()=>activateTab('startsit'));fail=true;await page.getByRole('button',{name:'Refresh results',exact:true}).click();await page.getByText(/Matchup results unavailable: HTTP 503/).waitFor();await page.screenshot({path:path.join(out,`blocked-${width}.png`),fullPage:true});fail=false;
  await page.locator('#weekSelect').selectOption('3');await page.getByText('Reported matchup result',{exact:true}).waitFor();
  await page.evaluate(()=>{state.leagueRules.format='REDRAFT_BESTBALL';FIEWeeklyWorkspace.render();});await page.getByRole('heading',{name:'Reported automatic contribution',exact:true}).waitFor();
  await page.evaluate(()=>{state.leagueRules.format='REDRAFT';activateTab('dst');});await page.getByRole('heading',{name:'Reported D/ST points',exact:true}).waitFor();assert(await page.getByRole('cell',{name:'-2.00 pts',exact:true}).isVisible());
  await page.evaluate(()=>activateTab('kicker'));await page.getByRole('heading',{name:'Reported kicker points',exact:true}).waitFor();assert(await page.getByRole('cell',{name:'5.00 pts',exact:true}).isVisible());
  await page.evaluate(()=>{state.leagueRules.format='CHOPPED';activateTab('startsit');});await page.getByText('League scoring / survival context',{exact:true}).waitFor();assert(await page.getByText('Unverified',{exact:true}).isVisible());
  await context.close();
 }
 report.status='PASS';fs.writeFileSync(path.join(out,'comparison.json'),JSON.stringify(report,null,2));console.log(JSON.stringify(report));
 }finally{await browser.close();server.close();}
})().catch(e=>{console.error(e);process.exitCode=1;});
