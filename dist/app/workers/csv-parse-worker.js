/* FIE V9.3.4A cooperative CSV parser worker.
 * Keeps large nflverse/public CSV tokenization off the browser UI thread.
 */
'use strict';

function parseCSV(text) {
  const rows = [];
  let row = [];
  let field = '';
  let quoted = false;
  const raw = String(text || '').replace(/^\uFEFF/, '');

  for (let i = 0; i < raw.length; i++) {
    const c = raw[i];
    if (c === '"') {
      if (quoted && raw[i + 1] === '"') {
        field += '"';
        i++;
      } else {
        quoted = !quoted;
      }
      continue;
    }
    if (c === ',' && !quoted) {
      row.push(field);
      field = '';
      continue;
    }
    if ((c === '\n' || c === '\r') && !quoted) {
      if (c === '\r' && raw[i + 1] === '\n') i++;
      row.push(field);
      field = '';
      if (row.some(v => v !== '')) rows.push(row);
      row = [];
      continue;
    }
    field += c;
  }
  if (field !== '' || row.length) {
    row.push(field);
    if (row.some(v => v !== '')) rows.push(row);
  }
  if (!rows.length) return [];

  const headers = rows.shift().map((h, i) => i === 0 ? String(h).replace(/^\uFEFF/, '') : String(h));
  return rows.map(values => {
    const out = {};
    for (let i = 0; i < headers.length; i++) out[headers[i]] = values[i] ?? '';
    return out;
  });
}

self.onmessage = event => {
  const id = Number(event.data?.id);
  try {
    const rows = parseCSV(event.data?.text || '');
    self.postMessage({ id, rows });
  } catch (error) {
    self.postMessage({ id, error: String(error?.message || error) });
  }
};
