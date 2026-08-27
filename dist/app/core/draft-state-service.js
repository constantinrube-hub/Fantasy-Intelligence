/* FIE V9.3.2 single live-draft state contract. */
(function(){'use strict';
function state(){const s=window.state||{},picks=s.draftIntel?.picks||[],draft=s.draftIntel?.draft||null;return{leagueId:String(s.league?.league_id||''),draftId:String(draft?.draft_id||''),loaded:s.draftIntel?.loaded===true,status:s.draftIntel?.loading?'loading':s.draftIntel?.loaded?'synced':'unavailable',pickCount:picks.length,pickedPlayerIds:new Set(picks.map(x=>String(x.player_id||x.playerId||'')).filter(Boolean)),lastSync:s.draftIntel?.lastUpdated||s.draftIntel?.updatedAt||null};}
function isDrafted(id){return state().pickedPlayerIds.has(String(id||''));}
function label(){const x=state();return x.loaded?`Draft ${x.draftId||'active'} · ${x.pickCount} picks synced`:'Draft state unavailable';}
window.FIEDraftStateService={VERSION:'9.3.2',state,isDrafted,label};
})();
