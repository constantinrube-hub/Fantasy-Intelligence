/* FIE V9.3.2 exclusive surface ownership. */
(function(){'use strict';
const known=['mainArea','modelPanel','teamPanel','tradePanel','draftAssistantPanel','draftAnalysisPanel','leagueIntelPanel','validationPanel','featuresPanel','homePanel','dstPanel','kickerPanel','valueFinderPanel','leagueRulesPanel','researchPanel','research2Panel','research3Panel','research4Panel','research5Panel','research6Panel','matchupSimPanel'];
function hide(id){const el=document.getElementById(id);if(!el)return;el.classList.remove('active');if(id==='matchupSimPanel')el.classList.add('hidden');}
function cleanupFor(tab){if(tab!=='matchupsim')hide('matchupSimPanel');}
function activate(tab){cleanupFor(tab);document.documentElement.dataset.fieTab=String(tab||'');return tab;}
function showOnly(id){for(const x of known)if(x!==id)hide(x);const el=document.getElementById(id);if(el){el.classList.remove('hidden');el.classList.add('active');}return el;}
window.FIESurfaceRouter={VERSION:'9.3.2',activate,cleanupFor,showOnly,known:[...known]};
})();
