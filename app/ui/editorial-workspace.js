/* Presentation-only primitives and shell. No scoring or eligibility calculations. */
(function () {
  'use strict';
  const el = (tag, cls, text) => {
    const node = document.createElement(tag);
    if (cls) node.className = cls;
    if (text != null) node.textContent = String(text);
    return node;
  };
  const byId = id => document.getElementById(id);
  let reader, previousFocus, serial = 0;
  const detailList = entries => {
    const dl = el('dl', 'fie-detail-list');
    for (const [label, value] of entries || []) {
      dl.append(el('dt', '', label), el('dd', '', value == null ? 'Unavailable' : value));
    }
    return dl;
  };
  function closeReader() { if (reader?.open) reader.close(); }
  function openReader({ title, context, entries, note }, trigger) {
    if (!reader) {
      reader = el('dialog', 'fie-reader');
      reader.id = 'fieEvidenceReader';
      reader.setAttribute('aria-labelledby', 'fieEvidenceTitle');
      document.body.append(reader);
      reader.addEventListener('close', () => {
        if (previousFocus?.isConnected) previousFocus.focus();
      });
    }
    previousFocus = trigger || document.activeElement;
    reader.replaceChildren();
    reader.append(el('p', 'fie-level', 'Advanced · evidence & method'));
    const header = el('div', 'fie-reader-header');
    const heading = el('h2', '', title);
    heading.id = 'fieEvidenceTitle';
    const close = el('button', '', 'Close');
    close.type = 'button'; close.autofocus = true;
    close.addEventListener('click', closeReader);
    header.append(heading, close); reader.append(header);
    if (context) reader.append(el('p', '', context));
    reader.append(detailList(entries));
    if (note) reader.append(el('p', '', note));
    if (!reader.open) reader.showModal();
  }
  function clearDisclosures() {
    closeReader();
    document.querySelectorAll('.fie-expanded').forEach(row => { row.hidden = true; });
    document.querySelectorAll('[data-fie-expand]').forEach(button => {
      button.setAttribute('aria-expanded', 'false'); button.textContent = 'Expand';
    });
  }
  function createTable({ title, description, columns, rows, caption }) {
    const section = el('section', 'fie-disclosure');
    const header = el('div', 'fie-disclosure-heading');
    const heading = el('h2', '', title); heading.id = `fie-table-${++serial}`;
    section.setAttribute('aria-labelledby', heading.id);
    header.append(heading, el('p', '', description || 'Basic · key information. Expand a row for explanation, or open Advanced for evidence.'));
    section.append(header);
    const scroll = el('div', 'fie-table-scroll');
    scroll.tabIndex = 0; scroll.setAttribute('role', 'region');
    scroll.setAttribute('aria-label', `${title} table; scroll horizontally for all columns`);
    const table = el('table');
    const tableCaption = el('caption', '', caption || title);
    tableCaption.style.cssText = 'text-align:left;padding:8px 12px;font-size:12px;color:var(--muted)';
    table.append(tableCaption);
    const thead = el('thead'), headerRow = el('tr');
    for (const column of columns) {
      const th = el('th', column.numeric ? 'fie-numeric' : '', column.label);
      th.scope = 'col'; headerRow.append(th);
    }
    const actionHeading = el('th', '', 'Details'); actionHeading.scope = 'col';
    headerRow.append(actionHeading); thead.append(headerRow); table.append(thead);
    const tbody = el('tbody');
    for (const row of rows) {
      const tr = el('tr');
      columns.forEach((column, index) => {
        const cell = el(index === 0 ? 'th' : 'td', column.numeric ? 'fie-numeric' : '');
        if (index === 0) cell.scope = 'row';
        const value = row[column.key];
        if (value && typeof value === 'object' && 'label' in value) {
          const status = el('span', 'fie-status', value.label);
          status.dataset.tone = value.tone || 'research'; cell.append(status);
        } else cell.textContent = value == null ? 'Unavailable' : String(value);
        tr.append(cell);
      });
      const actionsCell = el('td'), actions = el('div', 'fie-actions');
      const expand = el('button', '', 'Expand'); expand.type = 'button';
      const expanded = el('tr', 'fie-expanded'); expanded.hidden = true;
      expanded.id = `fie-expanded-${++serial}`;
      expand.dataset.fieExpand = ''; expand.setAttribute('aria-expanded', 'false');
      expand.setAttribute('aria-controls', expanded.id);
      expand.setAttribute('aria-label', `Expand ${row.title || row[columns[0].key]}`);
      const content = el('td'); content.colSpan = columns.length + 1;
      content.append(el('p', 'fie-level', 'Expanded · explanation'), detailList(row.expanded));
      expanded.append(content);
      expand.addEventListener('click', () => {
        const opening = expanded.hidden;
        section.querySelectorAll('.fie-expanded').forEach(other => { other.hidden = true; });
        section.querySelectorAll('[data-fie-expand]').forEach(other => {
          other.setAttribute('aria-expanded', 'false'); other.textContent = 'Expand';
        });
        expanded.hidden = !opening; expand.setAttribute('aria-expanded', String(opening));
        expand.textContent = opening ? 'Collapse' : 'Expand';
      });
      const advanced = el('button', '', 'Advanced'); advanced.type = 'button';
      advanced.setAttribute('aria-label', `Advanced evidence for ${row.title || row[columns[0].key]}`);
      advanced.addEventListener('click', () => openReader({
        title: row.title || String(row[columns[0].key]), context: row.context || caption,
        entries: row.advanced, note: row.note
      }, advanced));
      actions.append(expand, advanced); actionsCell.append(actions); tr.append(actionsCell);
      tbody.append(tr, expanded);
    }
    table.append(tbody); scroll.append(table); section.append(scroll); return section;
  }
  function runtimeState() { return typeof state !== 'undefined' ? state : window.state; }
  function currentView() {
    const s = runtimeState();
    return s?.portfolioMode || window.FIEPortfolio?.mode ? 'portfolio' : (s?.activeTab || 'home');
  }
  function allowedViews() {
    const config = window.FIE_WORKSPACE_SECTIONS || {};
    return new Set(['portfolio', 'home', ...Object.values(config).flatMap(x => [...x.tabs.map(t => t[0]), ...(x.routes || [])])]);
  }
  function routeSnapshot() {
    const s = runtimeState(), params = new URLSearchParams();
    params.set('view', currentView());
    if (currentView() !== 'portfolio' && s?.league?.league_id) params.set('league', s.league.league_id);
    // Period and roster belong to the existing controls; never infer a historical projection.
    if (['startsit', 'dst', 'kicker', 'matchupsim', 'waivers'].includes(currentView())) {
      for (const [key, id] of [['season', 'seasonSelect'], ['week', 'weekSelect'], ['roster', 'weeklyRosterPicker']]) {
        if (byId(id)?.value) params.set(key, byId(id).value);
      }
    }
    return params.toString();
  }
  let restoring = false, restorePending = false, queued = false, lastContext = '';
  function syncRoute(replace = false) {
    if (restoring) return;
    const serialized = routeSnapshot();
    const context = serialized.replace(/(^|&)view=[^&]*/g, '');
    if (lastContext && lastContext !== context) clearDisclosures();
    lastContext = context;
    const name = byId('kLeague')?.textContent || 'All leagues';
    if (byId('fieContextName')) byId('fieContextName').textContent = currentView() === 'portfolio' ? 'All leagues' : name;
    const section = window.sectionForTab?.(currentView()) || 'home';
    if (byId('fieMobileNavigation')) byId('fieMobileNavigation').value = currentView() === 'portfolio' ? 'portfolio' : section;
    if (location.hash.slice(1) !== serialized) history[replace ? 'replaceState' : 'pushState'](null, '', `#${serialized}`);
  }
  function queueSync() {
    if (queued) return;
    queued = true;
    queueMicrotask(() => { queued = false; syncRoute(); });
  }
  async function restoreRoute() {
    if (restoring) { restorePending = true; return; }
    const params = new URLSearchParams(location.hash.slice(1)), view = params.get('view');
    if (!allowedViews().has(view)) { syncRoute(true); return; }
    restoring = true; clearDisclosures();
    try {
      const league = params.get('league'), s = runtimeState();
      if (league && !/^\d{10,25}$/.test(league)) return;
      if (view === 'portfolio') window.FIEPortfolio?.show?.();
      else {
        window.FIEPortfolio?.leave?.();
        if (league && String(s?.league?.league_id) !== league) {
          if (byId('leagueInput')) byId('leagueInput').value = league;
          const saved = byId('savedLeagueSelect');
          if (saved && Array.from(saved.options).some(option => option.value === league)) saved.value = league;
          await window.FIELeagueController?.switchLeague(league, { route: view });
          // A blocked load must not label the previous league with the requested route.
          if (String(runtimeState()?.league?.league_id) !== league) return;
        }
        if (window.FIEPortfolio) window.FIEPortfolio.mode = false;
        if (runtimeState()) runtimeState().portfolioMode = false;
        for (const [key, id] of [['season', 'seasonSelect'], ['week', 'weekSelect'], ['roster', 'weeklyRosterPicker']]) {
          const control = byId(id), value = params.get(key);
          if (control && value && Array.from(control.options).some(option => option.value === value)) {
            if (control.value !== value) { control.value = value; control.dispatchEvent(new Event('change', { bubbles: true })); }
          }
        }
        window.activateTab?.(view);
      }
    } finally {
      restoring = false;
      if (restorePending) { restorePending = false; restoreRoute(); }
      else syncRoute(true);
    }
  }
  function setupShell() {
    const shell = document.querySelector('.shell'); if (!shell || !byId('primaryNav')) return;
    const context = el('div', 'fie-context'); context.setAttribute('aria-label', 'League context');
    const name = el('span', 'fie-context-name', 'All leagues'); name.id = 'fieContextName'; context.append(name);
    const saved = byId('savedLeagueSelect');
    if (saved) {
      const field = saved.closest('.field');
      field.querySelector('label')?.setAttribute('for', 'savedLeagueSelect');
      context.append(field, byId('loadSavedLeagueBtn'));
    }
    const manage = el('button', 'btn ghost', 'Manage leagues'); manage.type = 'button';
    context.append(manage);
    shell.querySelector('.hero').after(context);
    const connections = el('details', 'fie-utility'); connections.id = 'fieLeagueManagement';
    connections.append(el('summary', '', 'League connection & saved settings'), document.querySelector('.connect'));
    context.after(connections);
    manage.setAttribute('aria-controls', connections.id); manage.setAttribute('aria-expanded', 'false');
    connections.addEventListener('toggle', () => manage.setAttribute('aria-expanded', String(connections.open)));
    manage.addEventListener('click', () => { connections.open = !connections.open; if (connections.open) byId('leagueInput')?.focus(); });
    const status = byId('status');
    if (status) { status.classList.add('fie-context-status'); status.setAttribute('role', 'status'); connections.after(status); }
    // Keep the canonical scoring-health warning visible even when setup is closed.
    const health = byId('fieDataHealth');
    if (health) { health.style.fontSize = '12px'; (status || connections).after(health); }
    document.addEventListener('click', event => {
      if (event.target.closest('#portfolioAddBtn')) connections.open = true;
    }, true);
    const coverage = el('details', 'fie-utility'); coverage.id = 'fieDataCoverage';
    coverage.append(el('summary', '', 'Data coverage & release information'), document.querySelector('.kpis'));
    const release = el('div', 'fie-release');
    document.querySelectorAll('.hero > .badge').forEach(badge => release.append(badge));
    coverage.append(release); (health || status || connections).after(coverage);
    const mobile = el('select', 'fie-mobile-nav'); mobile.id = 'fieMobileNavigation';
    mobile.setAttribute('aria-label', 'Workspace section');
    const all = el('option', '', 'All leagues'); all.value = 'portfolio'; mobile.append(all);
    document.querySelectorAll('#primaryNav .primary-tab').forEach(button => {
      const option = el('option', '', button.querySelector('span:last-child')?.textContent || button.textContent);
      option.value = button.dataset.section; mobile.append(option);
    });
    mobile.addEventListener('change', () => {
      if (mobile.value === 'portfolio') { window.FIEPortfolio?.show?.(); queueSync(); }
      else document.querySelector(`#primaryNav [data-section="${mobile.value}"]`)?.click();
    });
    byId('appLayoutV82').before(mobile);
    new MutationObserver(queueSync).observe(document.documentElement, { attributes: true, attributeFilter: ['data-fie-tab'] });
    const panel = byId('portfolioPanel');
    if (panel) new MutationObserver(queueSync).observe(panel, { attributes: true, attributeFilter: ['class'] });
    if (byId('kLeague')) new MutationObserver(queueSync).observe(byId('kLeague'), { childList: true, subtree: true, characterData: true });
    if (byId('sectionTitle')) new MutationObserver(queueSync).observe(byId('sectionTitle'), { childList: true, subtree: true, characterData: true });
    document.addEventListener('change', event => { if (['seasonSelect', 'weekSelect', 'weeklyRosterPicker'].includes(event.target.id)) { clearDisclosures(); queueSync(); } });
    byId('portfolioHomeBtn')?.addEventListener('click', queueSync);
    window.addEventListener('fie:league-changing', clearDisclosures);
    window.addEventListener('fie:league-loaded', queueSync);
    window.addEventListener('popstate', restoreRoute);
    // Hash edits are supported too; serialize restores so popstate/hashchange cannot overlap.
    window.addEventListener('hashchange', restoreRoute);
    if (new URLSearchParams(location.hash.slice(1)).has('view')) restoreRoute(); else syncRoute(true);
  }
  document.documentElement.dataset.fieAppearance = 'light';
  window.FIEEditorial = Object.freeze({ VERSION: 'editorial-p01', createTable, openReader, closeReader, clearDisclosures });
  if (document.readyState === 'loading') document.addEventListener('DOMContentLoaded', setupShell);
  else setupShell();
})();
