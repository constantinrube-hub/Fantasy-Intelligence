/* FIE game state per player (UI v10 R1) — UI contract §5.6.
 * Kickoff from the nflverse schedule (gameday + gametime, America/New_York); state is decided
 * per game, never per week: pregame (swappable) → live (locked) → final (result present).
 * More than 4 h after kickoff without a result the state is "ended_unconfirmed", never "final".
 */
(function(){
'use strict';
const VERSION='10.1.0',FOUR_H=4*3600e3;
function parseCsv(text){
  const rows=[];let row=[],cell='',q=false;
  for(let i=0;i<text.length;i++){const c=text[i];
    if(q){if(c==='"'){if(text[i+1]==='"'){cell+='"';i++;}else q=false;}else cell+=c;continue;}
    if(c==='"')q=true;else if(c===','){row.push(cell);cell='';}else if(c==='\n'){row.push(cell);rows.push(row);row=[];cell='';}else if(c!=='\r')cell+=c;}
  if(cell!==''||row.length){row.push(cell);rows.push(row);}
  const head=rows.shift()||[];return rows.filter(r=>r.length>1).map(r=>Object.fromEntries(head.map((h,i)=>[h,r[i]??''])));
}
/** America/New_York wall time → UTC epoch ms (DST-correct via Intl, no library). */
function easternToUtc(date,time){
  if(!date)return null;const [y,m,d]=date.split('-').map(Number),[hh,mm]=(time||'13:00').split(':').map(Number);
  for(const off of [4,5]){const t=Date.UTC(y,m-1,d,hh+off,mm||0);
    const f=new Intl.DateTimeFormat('en-US',{timeZone:'America/New_York',year:'numeric',month:'2-digit',day:'2-digit',hour:'2-digit',minute:'2-digit',hourCycle:'h23'}).formatToParts(new Date(t));
    const g=k=>Number(f.find(x=>x.type===k)?.value);if(g('year')===y&&g('month')===m&&g('day')===d&&g('hour')===hh&&g('minute')===(mm||0))return t;}
  return Date.UTC(y,m-1,d,hh+4,mm||0);
}
const TEAM_ALIAS={LA:'LAR',LAR:'LAR',JAC:'JAX',WSH:'WAS',OAK:'LV',SD:'LAC',STL:'LAR'};
function team(t){const x=String(t||'').toUpperCase();return TEAM_ALIAS[x]||x;}
/** Build an index {season, week} → team → game from schedule rows (CSV text or parsed rows). */
function index(rowsOrCsv){
  const rows=typeof rowsOrCsv==='string'?parseCsv(rowsOrCsv):(rowsOrCsv||[]),games=new Map(),weeks=new Set();
  for(const r of rows){if(String(r.game_type||'REG').toUpperCase()!=='REG')continue;const season=Number(r.season),week=Number(r.week);if(!season||!week)continue;
    const home=team(r.home_team),away=team(r.away_team),kickoff=easternToUtc(r.gameday,r.gametime);
    const final=String(r.result??'').trim()!==''||String(r.home_score??'').trim()!=='';
    const g={season,week,home,away,kickoff,final,homeScore:r.home_score===''?null:Number(r.home_score),awayScore:r.away_score===''?null:Number(r.away_score),gameId:r.game_id||null};
    games.set(`${season}:${week}:${home}`,g);games.set(`${season}:${week}:${away}`,g);weeks.add(`${season}:${week}`);}
  return{games,weeks,size:rows.length};
}
function gameFor(idx,teamCode,week,season){return idx?.games?.get(`${season}:${week}:${team(teamCode)}`)||null;}
function published(idx,week,season){return !!idx?.weeks?.has(`${season}:${week}`);}
/** Per-player game info. now = epoch ms. */
function forTeam(idx,teamCode,{week,season,now=Date.now()}){
  if(!teamCode)return{state:'unknown',locked:false,kickoff:null,opp:null,homeAway:null,bye:false};
  const g=gameFor(idx,teamCode,week,season);
  if(!g)return{state:published(idx,week,season)?'bye':'unknown',locked:false,kickoff:null,opp:null,homeAway:null,bye:published(idx,week,season)};
  const t=team(teamCode),home=g.home===t,opp=home?g.away:g.home,started=g.kickoff!==null&&now>=g.kickoff;
  const state=g.final?'final':!started?'pregame':now-g.kickoff>FOUR_H?'ended_unconfirmed':'live';
  return{state,locked:started||g.final,kickoff:g.kickoff,opp,homeAway:home?'vs':'@',bye:false,gameId:g.gameId};
}
window.FIEGameState={VERSION,parseCsv,easternToUtc,index,gameFor,forTeam,team,published};
})();
