(function(){
'use strict';

function cleanText(cell){return String(cell?.dataset?.sortValue ?? cell?.textContent ?? '').replace(/\s+/g,' ').trim();}
function numericValue(text){
  const t=String(text||'').trim();
  if(!t || t==='—' || t==='–' || /^n\/?a$/i.test(t))return null;
  const normalized=t.replace(/,/g,'').replace(/^[#$€£]\s*/,'').replace(/%/g,'').replace(/^\+/,'');
  const m=normalized.match(/^-?\d+(?:\.\d+)?/);
  if(!m)return null;
  const n=Number(m[0]);return Number.isFinite(n)?n:null;
}
function compareCells(a,b,dir){
  const at=cleanText(a),bt=cleanText(b),an=numericValue(at),bn=numericValue(bt);
  if(an!==null&&bn!==null)return (an-bn)*dir;
  if(an===null&&bn!==null)return 1;
  if(an!==null&&bn===null)return -1;
  return at.localeCompare(bt,undefined,{numeric:true,sensitivity:'base'})*dir;
}
function sortDomTable(table,index,th){
  const bodies=[...table.tBodies].filter(x=>x.rows.length>1);if(!bodies.length)return;
  const prev=Number(table.dataset.genericSortIndex),same=prev===index,dir=same?-(Number(table.dataset.genericSortDir)||1):1;
  table.dataset.genericSortIndex=String(index);table.dataset.genericSortDir=String(dir);
  table.querySelectorAll('thead th').forEach(h=>{h.classList.remove('fie-sort-asc','fie-sort-desc');h.removeAttribute('aria-sort');});
  th.classList.add(dir>0?'fie-sort-asc':'fie-sort-desc');th.setAttribute('aria-sort',dir>0?'ascending':'descending');
  for(const body of bodies){
    const rows=[...body.rows];
    rows.sort((ra,rb)=>compareCells(ra.cells[index],rb.cells[index],dir));
    rows.forEach(r=>body.appendChild(r));
  }
}
function eligibleHeader(th){
  if(!th||th.dataset.noSort!==undefined)return false;
  // Main player table and Draft Assistant have model-aware sorting already.
  if(th.dataset.sort||th.dataset.daSort)return false;
  const table=th.closest('table');if(!table||table.dataset.noSort!==undefined)return false;
  return Boolean(table.tBodies?.length);
}
function decorate(root=document){
  root.querySelectorAll('table thead th').forEach(th=>{
    if(!eligibleHeader(th)||th.dataset.genericSortable)return;
    th.dataset.genericSortable='1';th.classList.add('fie-sortable');th.title=th.title||'Click to sort table';
  });
}
function bind(){
  const style=document.createElement('style');style.textContent=`
    th.fie-sortable,th[data-da-sort]{cursor:pointer;user-select:none}
    th.fie-sortable:hover,th[data-da-sort]:hover{filter:brightness(1.12)}
    th.fie-sort-asc::after{content:' ▲';font-size:.72em;opacity:.8}
    th.fie-sort-desc::after{content:' ▼';font-size:.72em;opacity:.8}
  `;document.head.appendChild(style);
  decorate();
  document.addEventListener('click',e=>{
    const th=e.target.closest('th');if(!eligibleHeader(th))return;
    const row=[...th.parentElement.children],index=row.indexOf(th);if(index<0)return;
    sortDomTable(th.closest('table'),index,th);
  });
  const obs=new MutationObserver(muts=>{for(const m of muts)for(const n of m.addedNodes)if(n.nodeType===1)decorate(n.matches?.('table')?n:n);});
  obs.observe(document.body,{childList:true,subtree:true});
}
if(document.readyState==='loading')document.addEventListener('DOMContentLoaded',bind);else bind();
window.FIE_TABLE_SORT={decorate,sortDomTable};
})();
