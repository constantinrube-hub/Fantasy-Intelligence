import { FIE_RELEASE } from "../../../release.js";

const UPSTREAM='https://github.com/nflverse/nflverse-data/releases/download/contracts/historical_contracts.csv.gz';
const TTL=86400;

function withCacheStatus(response,status){
  const headers=new Headers(response.headers);headers.set('X-FIE-Cache',status);headers.set('X-FIE-Source','nflverse:contracts');headers.set('X-FIE-Release',FIE_RELEASE.release);return new Response(response.body,{status:response.status,statusText:response.statusText,headers});
}
export async function onRequestGet(context){
  const cache=caches.default,cacheKey=new Request(new URL(context.request.url).toString(),{method:'GET'}),cached=await cache.match(cacheKey);if(cached)return withCacheStatus(cached,'HIT');
  const controller=new AbortController(),timer=setTimeout(()=>controller.abort('upstream timeout'),20000);let upstream;
  try{upstream=await fetch(UPSTREAM,{redirect:'follow',signal:controller.signal,headers:{'User-Agent':`Fantasy-Intelligence-Engine/${FIE_RELEASE.release}`,Accept:'application/gzip,application/octet-stream,*/*'}});}catch(error){return Response.json({error:'Contracts upstream fetch failed.',detail:String(error?.message||error)},{status:502,headers:{'Cache-Control':'no-store','X-FIE-Cache':'MISS','X-FIE-Source':'nflverse:contracts','X-FIE-Release':FIE_RELEASE.release}});}finally{clearTimeout(timer);}
  if(!upstream.ok)return Response.json({error:`Contracts upstream returned ${upstream.status}.`},{status:upstream.status,headers:{'Cache-Control':'no-store','X-FIE-Cache':'MISS','X-FIE-Source':'nflverse:contracts','X-FIE-Release':FIE_RELEASE.release}});
  if(!upstream.body||typeof DecompressionStream!=='function')return Response.json({error:'Gzip decompression unavailable in runtime.'},{status:500,headers:{'Cache-Control':'no-store'}});
  const body=upstream.body.pipeThrough(new DecompressionStream('gzip')),headers=new Headers();headers.set('Content-Type','text/csv; charset=utf-8');headers.set('Cache-Control',`public, max-age=60, s-maxage=${TTL}`);headers.set('X-FIE-Cache','MISS');headers.set('X-FIE-Source','nflverse:contracts');headers.set('X-FIE-Fetched-At',new Date().toISOString());headers.set('X-FIE-Release',FIE_RELEASE.release);
  const response=new Response(body,{status:200,headers});context.waitUntil(cache.put(cacheKey,response.clone()));return response;
}
export function onRequest(context){if(context.request.method!=='GET')return new Response('Method Not Allowed',{status:405,headers:{Allow:'GET'}});return onRequestGet(context);}
