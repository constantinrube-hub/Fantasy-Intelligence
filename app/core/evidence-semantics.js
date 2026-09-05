/* FIE Tranche 3D / C10-009 canonical evidence semantics.
 * Adds typed evidence metadata without changing football-model values.
 */
(function(g){
'use strict';
if(g.FIEEvidenceSemantics?.VERSION)return;
const VERSION='1.0.0';
const SCHEMA='fie-evidence-v1';
const EvidenceStatus=Object.freeze({
  OBSERVED:'observed',
  MODELED_AVAILABLE:'modeled_available',
  MODELED_UNAVAILABLE:'modeled_unavailable'
});
const UncertaintyKind=Object.freeze({
  CALIBRATED_RANGE:'calibrated_range',
  HEURISTIC_RANGE:'heuristic_range',
  EXACT:'exact',
  UNAVAILABLE:'unavailable',
  NOT_APPLICABLE:'not_applicable'
});
const Availability=Object.freeze({AVAILABLE:'available',UNAVAILABLE:'unavailable'});
const ByeState=Object.freeze({BYE:'bye',NOT_BYE:'not_bye',UNKNOWN:'unknown'});
const MARK='__fieEvidenceSemanticsWrapped';
function finite(v){if(v===null||v===undefined||(typeof v==='string'&&v.trim()===''))return null;const n=Number(v);return Number.isFinite(n)?n:null;}
function text(v){if(v===null||v===undefined)return null;const s=String(v).trim();return s||null;}
function firstAsOf(...xs){
  for(const x of xs){if(!x||typeof x!=='object')continue;for(const k of ['asOf','as_of','generated_at','generatedAt','updated_at','updatedAt','captured_at','capturedAt']){const v=text(x[k]);if(v)return v;}}
  return null;
}
function leagueProvenance(meta={}){
  const state=g.state||{};const league=state.league||{};
  const p={
    leagueId:text(meta.leagueId??league.league_id),
    season:finite(meta.season??league.season),
    week:finite(meta.week),
    position:text(meta.position),
    governed:meta.governed===true
  };
  if(meta.completedWeek!==undefined)p.completedWeek=finite(meta.completedWeek);
  if(meta.storageFormat!==undefined)p.storageFormat=text(meta.storageFormat);
  return p;
}
function create(meta={}){
  const availability=meta.availability===Availability.UNAVAILABLE?Availability.UNAVAILABLE:Availability.AVAILABLE;
  let evidenceStatus=meta.evidenceStatus||meta.status;
  if(!Object.values(EvidenceStatus).includes(evidenceStatus))evidenceStatus=availability===Availability.UNAVAILABLE?EvidenceStatus.MODELED_UNAVAILABLE:(meta.observed===true?EvidenceStatus.OBSERVED:EvidenceStatus.MODELED_AVAILABLE);
  let uncertaintyKind=meta.uncertaintyKind;
  if(!Object.values(UncertaintyKind).includes(uncertaintyKind))uncertaintyKind=availability===Availability.UNAVAILABLE?UncertaintyKind.UNAVAILABLE:UncertaintyKind.NOT_APPLICABLE;
  const byeState=Object.values(ByeState).includes(meta.byeState)?meta.byeState:ByeState.UNKNOWN;
  return Object.freeze({
    schemaVersion:SCHEMA,
    evidenceStatus,
    source:text(meta.source)||'Unavailable',
    asOf:text(meta.asOf),
    confidence:meta.confidence??null,
    reason:text(meta.reason),
    fallback:meta.fallback===true,
    uncertaintyKind,
    availability,
    byeState,
    low:finite(meta.low),
    high:finite(meta.high),
    leagueLocalProvenance:Object.freeze(leagueProvenance(meta.leagueLocalProvenance||meta))
  });
}
function currentBundle(){try{return g.FIE_M5?.getCurrentBundle?.()||null;}catch{return null;}}
function projectionAsOf(subject){return firstAsOf(currentBundle(),subject);}
function projectionEvidence(result,subject,opts={},range=false){
  const unavailable=result?.availability==='unavailable'||(range&&finite(result?.low)===null&&finite(result?.high)===null);
  const bye=result?.isBye===true||result?.reason==='BYE';
  let uncertaintyKind=UncertaintyKind.NOT_APPLICABLE;
  if(bye)uncertaintyKind=UncertaintyKind.EXACT;
  else if(unavailable)uncertaintyKind=UncertaintyKind.UNAVAILABLE;
  else if(range&&result?.calibrated===true)uncertaintyKind=UncertaintyKind.CALIBRATED_RANGE;
  else if(range)uncertaintyKind=UncertaintyKind.HEURISTIC_RANGE;
  const fallback=result?.estimate===true||/season baseline|weekly fallback|heuristic fallback|heuristic range/i.test(String(result?.source||''));
  return create({
    evidenceStatus:bye?EvidenceStatus.OBSERVED:(unavailable?EvidenceStatus.MODELED_UNAVAILABLE:EvidenceStatus.MODELED_AVAILABLE),
    source:result?.source,
    asOf:projectionAsOf(subject),
    confidence:result?.confidence??(range?(result?.calibrated===true?'calibrated':'estimate'):null),
    reason:bye?'BYE':unavailable?'projection_unavailable':fallback?'fallback_projection':'projection_available',
    fallback,
    uncertaintyKind,
    availability:unavailable?Availability.UNAVAILABLE:Availability.AVAILABLE,
    byeState:bye?ByeState.BYE:(subject?.team?ByeState.NOT_BYE:ByeState.UNKNOWN),
    low:range?result?.low:null,
    high:range?result?.high:null,
    leagueId:g.state?.league?.league_id,
    season:result?.season??opts?.season,
    week:result?.week??opts?.week,
    governed:result?.governed===true,
    position:subject?.position||subject?.position_model
  });
}
function featureEvidence(player){
  const line=player?.currentFeatureLineage;if(!line)return null;const bundle=currentBundle();
  return create({
    evidenceStatus:EvidenceStatus.OBSERVED,
    source:line.source||'research current snapshot',
    asOf:firstAsOf(bundle),
    confidence:line.activationEligible===true&&line.leakageSafe===true?'governed':'diagnostic',
    reason:line.leakageSafe===true?'leakage_safe_current_features':'diagnostic_current_features',
    fallback:false,
    uncertaintyKind:UncertaintyKind.NOT_APPLICABLE,
    availability:Availability.AVAILABLE,
    byeState:ByeState.UNKNOWN,
    leagueId:g.state?.league?.league_id,
    season:bundle?.season,
    week:bundle?.week,
    completedWeek:line.asOfCompletedWeek,
    governed:line.activationEligible===true,
    position:player?.position
  });
}
function snapshotEvidence(snapshot){
  const unavailable=!snapshot||typeof snapshot!=='object';
  return create({
    evidenceStatus:unavailable?EvidenceStatus.MODELED_UNAVAILABLE:EvidenceStatus.OBSERVED,
    source:'FIECurrentSnapshotStore',
    asOf:firstAsOf(snapshot),
    confidence:unavailable?'none':'artifact',
    reason:unavailable?'snapshot_unavailable':'hydrated_current_snapshot',
    fallback:false,
    uncertaintyKind:unavailable?UncertaintyKind.UNAVAILABLE:UncertaintyKind.NOT_APPLICABLE,
    availability:unavailable?Availability.UNAVAILABLE:Availability.AVAILABLE,
    byeState:ByeState.UNKNOWN,
    leagueId:snapshot?.league_id||g.state?.league?.league_id,
    season:snapshot?.season,
    week:snapshot?.week,
    storageFormat:snapshot?.__storage?.format,
    governed:true
  });
}
function specialistEvidence(row,position){
  const bundle=currentBundle();const unavailable=finite(row?.mean)===null;const bye=row?.bye===true;
  let uncertaintyKind=UncertaintyKind.NOT_APPLICABLE;
  if(bye)uncertaintyKind=UncertaintyKind.EXACT;
  else if(unavailable)uncertaintyKind=UncertaintyKind.UNAVAILABLE;
  else if(finite(row?.low)!==null||finite(row?.high)!==null){
    const empirical=/empirical|calibrat/i.test(String(row?.source||''))||finite(row?.r?.p10)!==null||finite(row?.r?.p90)!==null;
    uncertaintyKind=empirical&&!row?.estimate?UncertaintyKind.CALIBRATED_RANGE:UncertaintyKind.HEURISTIC_RANGE;
  }
  return create({
    evidenceStatus:bye?EvidenceStatus.OBSERVED:(unavailable?EvidenceStatus.MODELED_UNAVAILABLE:EvidenceStatus.MODELED_AVAILABLE),
    source:row?.source,
    asOf:firstAsOf(row?.r,bundle),
    confidence:bye?'exact schedule':row?.active?'governed/current':row?.estimate?'estimate':'baseline',
    reason:bye?'BYE':unavailable?'specialist_projection_unavailable':row?.estimate?'specialist_baseline_estimate':'specialist_projection_available',
    fallback:row?.estimate===true,
    uncertaintyKind,
    availability:unavailable?Availability.UNAVAILABLE:Availability.AVAILABLE,
    byeState:bye?ByeState.BYE:ByeState.NOT_BYE,
    low:row?.low,
    high:row?.high,
    leagueId:g.state?.league?.league_id,
    season:bundle?.season,
    week:row?.week??bundle?.week,
    governed:row?.active===true,
    position
  });
}
function decorateSpecialistRow(row,position){if(!row||typeof row!=='object')return row;row.evidence=specialistEvidence(row,position);row.asOf=row.evidence.asOf;return row;}
function wrapMethod(obj,key,wrapper){if(!obj||typeof obj[key]!=='function'||obj[key][MARK])return false;const original=obj[key];const wrapped=wrapper(original);Object.defineProperty(wrapped,MARK,{value:true});obj[key]=wrapped;return true;}
function installProjection(){const api=g.FIEProjectionResolver;if(!api)return false;let changed=false;
  changed=wrapMethod(api,'week',orig=>function(subject,opts={}){const result=orig.apply(this,arguments);if(!result||typeof result!=='object')return result;const evidence=projectionEvidence(result,subject,opts,false);return{...result,asOf:evidence.asOf,evidence};})||changed;
  changed=wrapMethod(api,'range',orig=>function(subject,opts={}){const result=orig.apply(this,arguments);if(!result||typeof result!=='object')return result;let weekly=null;try{weekly=api.week?.(subject,opts)||null;}catch{}const merged={...result,isBye:weekly?.isBye===true,reason:weekly?.reason,availability:(result.low===null&&result.high===null)?'unavailable':'available',week:weekly?.week,season:weekly?.season,governed:weekly?.governed};const evidence=projectionEvidence(merged,subject,opts,true);return{...result,asOf:evidence.asOf,evidence};})||changed;
  return changed;
}
function installFeatures(){const api=g.FIECurrentFeatures;if(!api)return false;let changed=false;
  changed=wrapMethod(api,'apply',orig=>function(){const result=orig.apply(this,arguments);for(const p of (g.PLAYERS||[])){const evidence=featureEvidence(p);if(!evidence)continue;p.currentFeatureEvidence=evidence;if(p.currentFeatureLineage&&typeof p.currentFeatureLineage==='object')p.currentFeatureLineage.evidence=evidence;}return result;})||changed;
  changed=wrapMethod(api,'lineage',orig=>function(player){const line=orig.apply(this,arguments);if(!line)return line;const evidence=player?.currentFeatureEvidence||featureEvidence(player);return evidence&&line.evidence!==evidence?{...line,evidence}:line;})||changed;
  return changed;
}
function installSnapshot(){const api=g.FIECurrentSnapshotStore;if(!api)return false;return wrapMethod(api,'load',orig=>async function(){const snapshot=await orig.apply(this,arguments);if(snapshot&&typeof snapshot==='object')snapshot.evidence=snapshotEvidence(snapshot);return snapshot;});}
function installSpecialists(){let changed=false;
  for(const [name,pos] of [['FIEDST','DEF'],['FIEKicker','K']]){const api=g[name];if(!api)continue;changed=wrapMethod(api,'board',orig=>function(){const rows=orig.apply(this,arguments);if(Array.isArray(rows))for(const row of rows)decorateSpecialistRow(row,pos);return rows;})||changed;}
  return changed;
}
function attachRuntimeAdapters(){return{projection:installProjection(),features:installFeatures(),snapshot:installSnapshot(),specialists:installSpecialists()};}
function describe(e){if(!e)return'Unavailable evidence';const u=e.uncertaintyKind===UncertaintyKind.CALIBRATED_RANGE?'calibrated range':e.uncertaintyKind===UncertaintyKind.HEURISTIC_RANGE?'heuristic range':e.uncertaintyKind===UncertaintyKind.EXACT?'exact':e.uncertaintyKind===UncertaintyKind.UNAVAILABLE?'uncertainty unavailable':'point evidence';return`${e.evidenceStatus} · ${e.source} · ${u}`;}
const API=Object.freeze({VERSION,SCHEMA,EvidenceStatus,UncertaintyKind,Availability,ByeState,create,projectionEvidence,featureEvidence,snapshotEvidence,specialistEvidence,decorateSpecialistRow,attachRuntimeAdapters,describe});
g.FIEEvidenceSemantics=API;
attachRuntimeAdapters();
if(typeof g.addEventListener==='function'){
  g.addEventListener('DOMContentLoaded',attachRuntimeAdapters,{once:true});
  g.addEventListener('load',attachRuntimeAdapters,{once:true});
  g.addEventListener('fie:league-changing',attachRuntimeAdapters);
}
if(typeof g.setTimeout==='function')for(const ms of [0,25,100,400,1200])g.setTimeout(attachRuntimeAdapters,ms);
})(window);
