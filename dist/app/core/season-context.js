/* Fantasy Intelligence Engine V9.3.2 early season bootstrap resolver.
 *
 * This module intentionally does NOT write window.FIESeasonContext. That name is
 * owned by runtime-foundation.js for the active/prior/week/snapshot facade. The
 * canonical post-bootstrap resolver lives at FIECore.SeasonResolver (numeric.js).
 */
(function(){
'use strict';
function parse(value){
  if(value===null||value===undefined)return null;
  if(typeof value==='string'&&value.trim()==='')return null;
  const n=Number(value);
  return Number.isInteger(n)&&n>1900&&n<2200?n:null;
}
function fallback(now=new Date()){
  const y=now.getUTCFullYear(),m=now.getUTCMonth()+1;
  return m<=2?y-1:y;
}
function resolve({leagueSeason=null,selectorValue=null,weeklySeason=null,now=null}={}){
  return parse(leagueSeason)??parse(selectorValue)??parse(weeklySeason)??fallback(now||new Date());
}
const API=Object.freeze({parse,resolve,fallback});
window.FIESeasonBootstrapResolver=API;
})();
