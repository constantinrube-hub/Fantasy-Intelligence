/* FIE pure scoring core (UI v10 R1).
 *
 * League-explicit port of the canonical classic scorer: index.html › "Canonical league scoring
 * compiler" (scoreLeagueStats / scoreSleeperProjectionStatsV89, which V8.9 rebinds onto
 * window.scoreSleeperProjectionStats). The classic version reads the *loaded* league from
 * `state.league`; this version takes the scoring settings explicitly, so the Overview can score
 * every league without loading it into the classic runtime.
 *
 * Behaviour copied deliberately, including quirks (parity is enforced against the real classic
 * function by research/integrity_v10_core_test.js):
 *   · position relevance from FIERuntimeContracts.scoring_rule_families (e.g. player return
 *     yards `pr_yd` do not score for a team DEF; `bonus_rec_te` only for TEs);
 *   · derived values: position reception bonuses, tackles = solo + assist, incompletions,
 *     D/ST points/yards-allowed buckets and yardage milestones (weekly period only);
 *   · the period is inferred from the stats object (`week` / `game_id` present → weekly), so Sleeper
 *     projection stat objects score in the "season" period exactly as in classic;
 *   · if no rule is supported, fall back to Sleeper's published pts_ppr / pts_half_ppr / pts_std by
 *     the league's reception weight (≥ .75 PPR, ≥ .25 half, else standard).
 * Pure: no DOM, no state, no network. Requires FIERuntimeContracts (app/generated/runtime-contracts.js).
 */
(function(){
'use strict';
const VERSION='10.1.0';
const PUBLIC_ALIASES={
 pass_yd:['passing_yards'],pass_td:['passing_tds'],pass_int:['interceptions','passing_interceptions'],pass_cmp:['completions'],pass_att:['attempts','passing_attempts'],pass_2pt:['passing_2pt_conversions'],pass_fd:['passing_first_downs'],
 rush_yd:['rushing_yards'],rush_td:['rushing_tds'],rush_att:['carries','rushing_attempts'],rush_2pt:['rushing_2pt_conversions'],rush_fd:['rushing_first_downs'],
 rec:['receptions'],rec_tgt:['targets'],rec_yd:['receiving_yards'],rec_td:['receiving_tds'],rec_2pt:['receiving_2pt_conversions'],rec_fd:['receiving_first_downs'],
 fum:['fumbles'],fum_lost:['fumbles_lost','rushing_fumbles_lost','receiving_fumbles_lost','sack_fumbles_lost'],
 tkl_solo:['tackles_solo','def_tackles_solo','solo_tackles'],tkl_ast:['tackles_with_assist','tackles_with_assists','def_tackles_assist','assists','tackles_assists'],tkl:['tackles'],tkl_loss:['tackles_for_loss','def_tackles_for_loss','tfl'],qb_hit:['def_qb_hits','qb_hits'],
 sack:['def_sacks','sacks'],sack_yd:['sack_yards'],int:['def_interceptions','interceptions_defense'],int_ret_yd:['def_interception_yards'],pass_def:['def_pass_defended','passes_defended'],ff:['def_fumbles_forced','fumbles_forced'],fum_rec:['def_fumbles','fumble_recoveries'],fum_rec_yd:['fumble_recovery_yards'],
 def_td:['def_tds','defensive_tds'],safe:['safeties'],blk_kick:['blocked_kicks'],blk_kick_ret_yd:['blocked_kick_return_yards'],def_4_and_stop:['fourth_down_stops'],def_pass_def:['passes_defended','def_pass_defended'],
 def_st_td:['special_teams_tds','st_td'],def_st_ff:['special_teams_ff','st_ff'],def_st_fum_rec:['special_teams_fum_rec','st_fum_rec'],def_kr_yd:['kick_return_yards','kr_yd'],def_pr_yd:['punt_return_yards','pr_yd'],def_fg_ret_yd:['missed_fg_return_yards','fg_ret_yd'],points_allowed:['pts_allow'],yards_allowed:['yds_allow'],
 kr_yd:['kick_return_yards'],pr_yd:['punt_return_yards'],kr_td:['kick_return_tds'],pr_td:['punt_return_tds']
};
const DIRECT_RULES=new Set([
 'pass_yd','pass_td','pass_int','pass_2pt','pass_fd','pass_cmp','pass_att','pass_inc','pass_sack','pass_sack_yd',
 'rush_yd','rush_td','rush_2pt','rush_fd','rush_att','rec','rec_tgt','rec_yd','rec_td','rec_2pt','rec_fd','fum','fum_lost',
 'tkl','tkl_solo','tkl_ast','tkl_loss','qb_hit','sack','sack_yd','int','int_ret_yd','pass_def','ff','fum_rec','fum_rec_yd','fum_ret_yd','def_td','safe','blk_kick','blk_kick_ret_yd','def_4_and_stop','def_pass_def','def_st_td','def_st_ff','def_st_fum_rec','def_kr_yd','def_pr_yd','def_fg_ret_yd',
 'kr_yd','pr_yd','kr_td','pr_td','fgm','fgm_0_19','fgm_20_29','fgm_30_39','fgm_40_49','fgm_50p','fgmiss','xpm','xpmiss'
]);
function num(v){const n=Number(v);return Number.isFinite(n)?n:null;}
function contracts(){return window.FIERuntimeContracts||{};}
function lookup(stats,key,mode){
  if(stats&&stats[key]!==undefined&&Number.isFinite(Number(stats[key])))return{value:Number(stats[key]),supported:true,source:key};
  if(mode==='public')for(const a of PUBLIC_ALIASES[key]||[]){if(stats?.[a]!==undefined&&Number.isFinite(Number(stats[a])))return{value:Number(stats[a]),supported:true,source:a};}
  return{value:0,supported:false,source:null};
}
function milestone(stats,key,mode){
  if(mode==='season')return null;
  const m=String(key).match(/^bonus_(pass|rush|rec)_yd_(\d+)$/);if(!m)return null;
  const statKey=m[1]==='pass'?'pass_yd':m[1]==='rush'?'rush_yd':'rec_yd',x=lookup(stats,statKey,mode);
  return x.supported?{value:x.value>=Number(m[2])?1:0,supported:true,source:`derived:${statKey}>=${m[2]}`}:{value:0,supported:false};
}
// Memoised per contracts object: the rule families are static, compiling their regexes per call made
// scoring 9,000 projection rows take seconds (found building waivers, R2). Output is unchanged.
let specCache=new Map(),specFor=null,relCache=new Map();
function ruleSpec(key){const c=contracts();if(specFor!==c){specFor=c;specCache=new Map();relCache=new Map();}if(specCache.has(key))return specCache.get(key);const r=ruleSpecRaw(key);specCache.set(key,r);return r;}
function ruleSpecRaw(key){const rules=contracts().scoring_rule_families||[];for(const r of rules){const k=String(key||'').toLowerCase(),kind=r.match,pat=r.pattern;let ok=false;if(kind==='exact')ok=k===String(pat).toLowerCase();else if(kind==='prefix')ok=k.startsWith(String(pat).toLowerCase());else if(kind==='regex'){try{ok=new RegExp(String(pat),'i').test(k);}catch{}}else if(kind==='exact_set')ok=(pat||[]).map(x=>String(x).toLowerCase()).includes(k);if(ok)return r;}return null;}
function relevant(key,position){if(!position)return true;const ck=key+'|'+position;if(ruleSpec(key),relCache.has(ck))return relCache.get(ck);const v=relevantRaw(key,position);relCache.set(ck,v);return v;}
function relevantRaw(key,position){const r=ruleSpec(key);if(!r)return true;const aliases=contracts().position_aliases||{},cp=x=>aliases[String(x||'').toUpperCase()]||String(x||'').toUpperCase(),pos=cp(position);return(r.positions||[]).map(cp).includes(pos);}
function dstBucket(stats,key,mode){if(mode==='season')return null;const k=String(key||'').toLowerCase(),isPts=k.startsWith('pts_allow_'),isYds=k.startsWith('yds_allow_');if(!isPts&&!isYds)return null;const base=isPts?'points_allowed':'yards_allowed',aliases=isPts?['pts_allow','points_allowed']:['yds_allow','yards_allowed'];let found=null;for(const a of aliases){if(stats?.[a]!==undefined&&Number.isFinite(Number(stats[a]))){found=Number(stats[a]);break;}}if(found===null)return{value:0,supported:false,source:`missing:${base}`};const tok=k.replace(isPts?'pts_allow_':'yds_allow_','');let hit=false;if(tok==='0')hit=found===0;else if(/^[0-9]+p$/.test(tok))hit=found>=Number(tok.slice(0,-1));else{const m=tok.match(/^(\d+)_(\d+)$/);if(m)hit=found>=Number(m[1])&&found<=Number(m[2]);else return{value:0,supported:false,source:'invalid-bucket'};}return{value:hit?1:0,supported:true,source:`derived:${base}_bucket`};}
function ruleValue(stats,key,position,mode){
  if(!relevant(key,position))return{value:0,supported:true,source:'irrelevant-position-zero'};
  const b=dstBucket(stats,key,mode);if(b)return b;
  if(key==='rec_te'||key==='bonus_rec_te'){const r=lookup(stats,'rec',mode);return{value:(position==='TE'?r.value:0),supported:r.supported,source:'derived:TE receptions'};}
  if(['rec_rb','bonus_rec_rb','rec_wr','bonus_rec_wr'].includes(key)){const r=lookup(stats,'rec',mode),pos=key.includes('_rb')?'RB':'WR';return{value:position===pos?r.value:0,supported:r.supported,source:`derived:${pos} receptions`};}
  if(key==='tkl'){const direct=lookup(stats,'tkl',mode);if(direct.supported)return direct;const solo=lookup(stats,'tkl_solo',mode),ast=lookup(stats,'tkl_ast',mode);if(solo.supported&&ast.supported)return{value:solo.value+ast.value,supported:true,source:'derived:solo+assist tackles'};}
  if(key==='pass_inc'){const att=lookup(stats,'pass_att',mode),cmp=lookup(stats,'pass_cmp',mode);if(att.supported&&cmp.supported)return{value:Math.max(0,att.value-cmp.value),supported:true,source:'derived:attempts-completions'};}
  const bonus=milestone(stats,key,mode);if(bonus)return bonus;
  const x=lookup(stats,key,mode);if(x.supported)return x;
  if(DIRECT_RULES.has(key)&&mode==='sleeper')return{value:0,supported:true,source:'known-linear-zero'};
  return{value:0,supported:false,source:null};
}
function inferPeriod(stats){return(stats?.week!==undefined||stats?.game_id!==undefined)?'weekly':'season';}
function fallbackKey(scoring){const rec=num(scoring?.rec)??0;return rec>=.75?'pts_ppr':rec>=.25?'pts_half_ppr':'pts_std';}
/** Full evaluation: points plus per-rule contributions (Advanced layer, audits). */
function evaluate(stats,scoring,position,{mode='sleeper',period=inferPeriod(stats)}={}){
  if(!stats)return{points:null,rows:[],supported:[],unsupported:[],fallback:null};
  const active=Object.entries(scoring||{}).filter(([,v])=>Number.isFinite(Number(v))&&Number(v)!==0);
  const rows=[],supported=[],unsupported=[];let points=null;
  if(active.length){points=0;const m=period==='season'?'season':mode;
    for(const [key,raw] of active){const weight=Number(raw),rv=ruleValue(stats,key,position,m);if(rv.supported){points+=rv.value*weight;supported.push(key);if(rv.value)rows.push({key,stat:rv.value,weight,points:rv.value*weight,source:rv.source});}else unsupported.push(key);}}
  if(points!==null&&supported.length)return{points,rows:rows.sort((a,b)=>Math.abs(b.points)-Math.abs(a.points)),supported,unsupported,fallback:null};
  const k=fallbackKey(scoring),x=Number(stats?.[k]);
  return{points:Number.isFinite(x)?x:null,rows:[],supported,unsupported,fallback:k};
}
/** Same value as window.scoreSleeperProjectionStats(stats, {position}) with state.league = league. */
function score(stats,scoring,position){return evaluate(stats,scoring,position,{mode:'sleeper'}).points;}
function breakdown(stats,scoring,position){return evaluate(stats,scoring,position,{mode:'sleeper'}).rows;}
/** Sleeper's own published total for the league's reception setting (label + value). */
function published(stats,scoring){const k=fallbackKey(scoring),v=num(stats?.[k]);return v===null?null:{key:k,label:k==='pts_ppr'?'Sleeper (PPR)':k==='pts_half_ppr'?'Sleeper (half PPR)':'Sleeper (standard)',value:v};}
window.FIEScoringCore={VERSION,score,evaluate,breakdown,published,fallbackKey};
})();
