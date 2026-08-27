/* Fantasy Intelligence Engine V9.3.2 season context.
 * Loaded before the legacy inline application so every startup path has one
 * strict, globally available season parser/resolver. Missing/blank/zero values
 * never become a valid NFL season.
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
window.FIESeasonContext=API;
})();
