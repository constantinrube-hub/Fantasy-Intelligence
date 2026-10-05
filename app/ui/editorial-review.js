/* Explicitly fictional fixtures. Never consumed by the application. */
(function () {
  'use strict';
  document.getElementById('weeklyExample').append(FIEEditorial.createTable({
    title: 'Prior-week matchup · player results',
    caption: 'Fictional fixture · Example league · Week 3 · completed matchup',
    description: 'Basic · player, lineup slot and actual points. The completed result leads; projections belong in the explanation.',
    columns: [{key:'player',label:'Player'}, {key:'slot',label:'Slot'}, {key:'points',label:'Actual points',numeric:true}],
    rows: [
      {player:'Alex Turner',slot:'WR',points:'18.40',title:'Alex Turner · Week 3',
        expanded:[['Scoring breakdown','6 receptions, 94 receiving yards, 1 receiving TD (fictional half-PPR scoring).'],['Pregame projection','Unavailable — no immutable pregame capture in this fixture.'],['Difference from projection','Unavailable; never reconstructed using the completed result.'],['Optimal lineup comparison','Advanced; requires all eligible player outcomes and the exact legal roster.']],
        advanced:[['Actual-points source','Fictional UI fixture; not a provider capture.'],['Receptions','6 × 0.5 = 3.00 points'],['Receiving yards','94 × 0.1 = 9.40 points'],['Receiving touchdowns','1 × 6 = 6.00 points'],['Projected best lineup','Unavailable — no point-in-time forecast capture.'],['Hindsight optimal lineup','Unavailable — fixture lacks the full roster and slot assignment.']],
        note:'Projected best and hindsight optimal are separate comparisons. Neither is inferred from this row.'},
      {player:'Sam Jordan',slot:'RB',points:'9.20',title:'Sam Jordan · Week 3',expanded:[['Actual-points source','Fictional UI fixture.'],['Scoring breakdown','Unavailable in this fixture.'],['Pregame projection','Unavailable — no capture.']],advanced:[['Capture identity','Fictional fixture only'],['Exact scoring replay','Unavailable'],['Projected and optimal lineup','Unavailable']]}
    ]
  }));
  document.getElementById('waiverExample').append(FIEEditorial.createTable({
    title: 'Waiver evidence · decision gates',
    caption: 'Fictional fixture · Example league · offensive waiver evidence',
    description: 'Basic · each independent gate and the material blocker. A research result does not imply a usable recommendation.',
    columns:[{key:'scope',label:'Scope'},{key:'forecast',label:'Forecast'},{key:'ranking',label:'Ranking'},{key:'recommendation',label:'Recommendation'},{key:'transaction',label:'Transaction'},{key:'blocker',label:'Blocker'}],
    rows:[{scope:'TE · exact league profile',title:'TE · independent waiver gates',forecast:{label:'Blocked',tone:'blocked'},ranking:{label:'Blocked',tone:'blocked'},recommendation:{label:'Blocked',tone:'blocked'},transaction:{label:'Blocked',tone:'blocked'},blocker:'Exact-scoring evidence incomplete',
      expanded:[['Why it is blocked','This fictional example lacks complete attributed scoring events.'],['What remains usable','No forecast, ordered ranking, recommendation or execution is authorized by this fixture.'],['What is needed','Complete exact-profile replay and the separate eligibility evidence for each gate.']],
      advanced:[['Evidence identity','Fictional UI fixture; no research artifact binding.'],['Model authority','No promotion; existing champion is unchanged.'],['Profile / period / source hash','Unavailable in this fixture.'],['Missing attribution','Shown as missing, never treated as zero.'],['Forecast gate','Blocked'],['Ranking gate','Blocked'],['Recommendation gate','Blocked'],['Transaction gate','Blocked']],note:'Real league-specific evidence and overarching research documents will be connected in the approved Waivers / Research phases. This page demonstrates disclosure behavior only.'}]
  }));
})();
