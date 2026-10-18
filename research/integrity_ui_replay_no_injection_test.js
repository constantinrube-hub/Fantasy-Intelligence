#!/usr/bin/env node
/* Replay tests may read window.state for diagnostics but must never assign to it:
 * a test that sets state production never sets proves nothing (UI contract §7.7). */
'use strict';
const fs = require('fs'), path = require('path');
const dir = path.join(__dirname, 'ui_replay');
const bad = [];
for (const f of fs.readdirSync(dir).filter(f => f.endsWith('.js'))) {
  const text = fs.readFileSync(path.join(dir, f), 'utf8');
  const re = /\b(?:window\.)?state(?:\?\.|\.)[\w.?]*\s*(?:=(?!=)|\+=|-=)|\b(?:PLAYERS)\s*=(?!=)|localStorage\.setItem/g;
  let m; while ((m = re.exec(text))) bad.push(`${f}: ${m[0]}`);
}
if (bad.length) { console.error('UI replay state injection found:\n' + bad.join('\n')); process.exit(1); }
console.log('UI replay harness: no application-state injection');
