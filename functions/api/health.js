import { FIE_RELEASE } from "../release.js";
export function onRequestGet() {
  return Response.json({ok:true,app:"Fantasy Intelligence Engine",version:FIE_RELEASE.release,runtimeVersion:FIE_RELEASE.runtime,stage:FIE_RELEASE.stage,runtime:"Cloudflare Pages Functions",proxy:"allowlisted",cache:{sleeperPlayersSeconds:86400,seasonProjectionsSeconds:3600,weeklyProjectionsSeconds:900,liveNflverseSeconds:3600},timestamp:new Date().toISOString()},{headers:{"Cache-Control":"no-store","X-FIE-Cache":"HEALTH","X-FIE-Source":"cloudflare-pages-functions","X-FIE-Release":FIE_RELEASE.release,"X-FIE-Fetched-At":new Date().toISOString()}});
}
export function onRequest(context){if(context.request.method!=="GET")return new Response("Method Not Allowed",{status:405,headers:{Allow:"GET"}});return onRequestGet();}
