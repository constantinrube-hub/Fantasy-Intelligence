/* FIE V9.3.2 strict numeric + season semantics.
 * Missing data must never silently become zero. Zero remains a legitimate value.
 */
(function(){
'use strict';
function finiteOrNull(value){
  if(value===null||value===undefined)return null;
  if(typeof value==='string'&&value.trim()==='')return null;
  const n=Number(value);
  return Number.isFinite(n)?n:null;
}
function integerOrNull(value){const n=finiteOrNull(value);return n===null?null:Math.trunc(n);}
function positiveIntOrNull(value){const n=integerOrNull(value);return n!==null&&n>0?n:null;}
function optionalCap(value){
  const n=finiteOrNull(value);
  return n!==null&&n>=0?Math.trunc(n):null;
}
function coalesce(){for(const x of arguments){const n=finiteOrNull(x);if(n!==null)return n;}return null;}
function utcFootballSeason(){const d=new Date(),y=d.getUTCFullYear(),m=d.getUTCMonth()+1;return m<=2?y-1:y;}
const SeasonResolver={
  resolve({league=window.state?.league,selected=document.getElementById('seasonSelect')?.value,weekly=window.state?.weekly?.season,fallback=null}={}){
    // League season is authoritative once a league is loaded. A blank select must never become 0.
    const fromLeague=positiveIntOrNull(league?.season);if(fromLeague!==null)return fromLeague;
    const fromSelected=positiveIntOrNull(selected);if(fromSelected!==null)return fromSelected;
    const fromWeekly=positiveIntOrNull(weekly);if(fromWeekly!==null)return fromWeekly;
    const fromFallback=positiveIntOrNull(fallback);if(fromFallback!==null)return fromFallback;
    return utcFootballSeason();
  },
  syncSelect(season,select=document.getElementById('seasonSelect')){
    const s=positiveIntOrNull(season);if(!select||s===null)return null;
    for(const o of [...select.options])if(positiveIntOrNull(o.value)===null)o.remove();
    if(![...select.options].some(o=>positiveIntOrNull(o.value)===s)){
      const o=document.createElement('option');o.value=String(s);o.textContent=String(s);select.appendChild(o);
    }
    select.value=String(s);return s;
  }
};
window.FIECore=window.FIECore||{};
Object.assign(window.FIECore,{Numeric:{finiteOrNull,integerOrNull,positiveIntOrNull,optionalCap,coalesce},SeasonResolver});
window.FIENumeric=window.FIECore.Numeric;
})();
