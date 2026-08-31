/* FIE research → Value Finder bridge.
 * Filters already-rendered canonical Value Finder rows using report membership only.
 * It does not calculate FIE rank, VORP, ADP rank, optimizer score or projection.
 */
(function(){
'use strict';
const VERSION='1.0-research-vf-bridge';
let mode='ALL',generation=0,wrapped=false;
const modes=[['ALL','All Value Finder'],['TOP100','Top-100 Outliers'],['SLEEPERS','Sleepers >100'],['STRONG_VALUE','Strong Value'],['STRONG_FADE','Strong Fade']];
function keyset(rows){const s=new Set();for(const r of rows||[]){for(const v of [r?.sleeper_id,r?.player_id,r?.name])if(v!==null&&v!==undefined&&String(v).trim())s.add(String(v));}return s;}
async function membership(){const s=await window.FIEResearchReportService?.reportSummary?.();if(!s)return{};const out=s.outliers_top100||{},sleep=s.sleepers_gt100||{};const positive=out.positive||[],negative=out.negative||[],sleepers=Object.values(sleep).flat();return{
 TOP100:keyset([...positive,...negative]),SLEEPERS:keyset(sleepers),STRONG_VALUE:keyset([...positive,...sleepers].filter(r=>String(r.value_label||'')==='STRONG_VALUE'||String(r.outlier_strength||r.sleeper_strength||'')==='STRONG')),STRONG_FADE:keyset(negative.filter(r=>String(r.value_label||'')==='STRONG_FADE'||String(r.outlier_strength||'')==='STRONG'))
};}
function controls(box){let el=box.querySelector('[data-fie-research-vf-controls]');if(el)return el;el=document.createElement('div');el.dataset.fieResearchVfControls='1';el.style.cssText='display:flex;gap:6px;flex-wrap:wrap;margin:0 0 10px;padding:9px;border:1px solid #29415f;border-radius:10px;background:#0d1c31';el.innerHTML='<span style="align-self:center;color:#91a4bf;font-size:11px;font-weight:800">Research:</span>'+modes.map(([k,l])=>`<button type="button" data-fie-rvf="${k}" class="btn ghost" style="padding:6px 9px">${l}</button>`).join('');box.prepend(el);el.querySelectorAll('[data-fie-rvf]').forEach(b=>b.onclick=()=>{mode=b.dataset.fieRvf||'ALL';apply();});return el;}
async function apply(){const my=++generation,box=document.getElementById('valueFinderSummary');if(!box)return;const c=controls(box);c.querySelectorAll('[data-fie-rvf]').forEach(b=>{b.style.outline=(b.dataset.fieRvf===mode?'1px solid #67e8f9':'none');});const rows=[...box.querySelectorAll('tr[data-vf-id]')];if(mode==='ALL'){rows.forEach(r=>r.style.display='');return;}try{const sets=await membership();if(my!==generation)return;const allowed=sets[mode]||new Set();let shown=0;for(const tr of rows){const id=String(tr.dataset.vfId||'');const name=String(tr.querySelector('.vf-player')?.textContent||tr.children?.[1]?.textContent||'').trim();const yes=allowed.has(id)||allowed.has(name);tr.style.display=yes?'':'none';if(yes)shown++;}let note=box.querySelector('[data-fie-rvf-note]');if(!note){note=document.createElement('div');note.dataset.fieRvfNote='1';note.className='muted';note.style.cssText='font-size:11px;margin:6px 2px';c.after(note);}note.textContent=`Research overlay: ${mode.replaceAll('_',' ')} · ${shown} rows in the current canonical Value Finder universe.`;}catch(e){console.warn('FIE research Value Finder overlay unavailable',e);}}
function wrap(){if(wrapped||typeof window.renderValueFinder!=='function')return false;const base=window.renderValueFinder;window.renderValueFinder=function(){const r=base.apply(this,arguments);queueMicrotask(apply);return r;};wrapped=true;window.FIEResearchValueFinderBridge={VERSION,setMode:m=>{mode=String(m||'ALL');apply();},mode:()=>mode,apply};return true;}
function init(){if(!wrap()){let n=0;const t=setInterval(()=>{if(wrap()||++n>50)clearInterval(t);},100);}queueMicrotask(apply);}
window.addEventListener?.('fie:league-changing',()=>{generation++;mode='ALL';});window.addEventListener?.('fie:league-loaded',()=>queueMicrotask(apply));
if(document.readyState==='loading')document.addEventListener('DOMContentLoaded',init,{once:true});else init();
})();
