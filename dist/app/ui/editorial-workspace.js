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
  let reader, previousFocus, serial = 0, readerTrail = [];
  const detailList = entries => {
    const dl = el('dl', 'fie-detail-list');
    for (const [label, value] of entries || []) {
      dl.append(el('dt', '', label), el('dd', '', value == null ? 'Unavailable' : value));
    }
    return dl;
  };
  function closeReader() { if (reader?.open) reader.close(); }
  function openReader({ title, context, entries, note, content, level }, trigger) {
    if (!reader) {
      reader = el('dialog', 'fie-reader');
      reader.id = 'fieEvidenceReader';
      reader.setAttribute('aria-labelledby', 'fieEvidenceTitle');
      document.body.append(reader);
      reader.addEventListener('keydown', event => {
        if (event.key !== 'Tab') return;
        const controls = [...reader.querySelectorAll('button,a[href],input,select,textarea,summary,[tabindex]')].filter(x => !x.disabled && x.tabIndex >= 0 && x.getClientRects().length);
        if (!controls.length) return;
        const first = controls[0], last = controls[controls.length - 1];
        if (event.shiftKey && document.activeElement === first) { event.preventDefault(); last.focus(); }
        else if (!event.shiftKey && document.activeElement === last) { event.preventDefault(); first.focus(); }
      });
      reader.addEventListener('close', () => {
        readerTrail = [];
        if (previousFocus?.isConnected) previousFocus.focus();
        else byId('sectionTitle')?.focus();
      });
    }
    const origin = trigger || document.activeElement;
    if (reader.open && reader.contains?.(origin)) readerTrail.push({ nodes: [...reader.childNodes], focus: origin, scroll: reader.scrollTop });
    else { readerTrail = []; previousFocus = origin; }
    reader.replaceChildren();
    reader.append(el('p', 'fie-level', level || 'Advanced · evidence & method'));
    const header = el('div', 'fie-reader-header');
    const heading = el('h2', '', title);
    heading.id = 'fieEvidenceTitle';
    const close = el('button', '', 'Close');
    close.type = 'button'; close.autofocus = true;
    close.addEventListener('click', closeReader);
    const actions = el('div', 'fie-actions');
    if (readerTrail.length) {
      const back = el('button', '', 'Back to previous details'); back.type = 'button';
      back.addEventListener('click', () => {
        const frame = readerTrail.pop(); if (!frame) return;
        reader.replaceChildren(...frame.nodes); reader.scrollTop = frame.scroll;
        if (frame.focus?.isConnected) frame.focus.focus();
      }); actions.append(back);
    }
    actions.append(close); header.append(heading, actions); reader.append(header);
    if (context) reader.append(el('p', '', context));
    if(content) reader.append(content);
    else reader.append(detailList(entries));
    if (note) reader.append(el('p', '', note));
    reader.scrollTop = 0;
    if (!reader.open) reader.showModal();
    close.focus();
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
    const table = el('table'); table.setAttribute('role', 'table');
    const tableCaption = el('caption', '', caption || title);
    tableCaption.style.cssText = 'text-align:left;padding:8px 12px;font-size:12px;color:var(--muted)';
    table.append(tableCaption);
    const thead = el('thead'), headerRow = el('tr'); thead.setAttribute('role','rowgroup'); headerRow.setAttribute('role','row');
    for (const column of columns) {
      const th = el('th', column.numeric ? 'fie-numeric' : '', column.label);
      th.scope = 'col'; th.setAttribute('role','columnheader'); headerRow.append(th);
    }
    const actionHeading = el('th', '', 'Details'); actionHeading.scope = 'col'; actionHeading.setAttribute('role','columnheader');
    headerRow.append(actionHeading); thead.append(headerRow); table.append(thead);
    const tbody = el('tbody'); tbody.setAttribute('role','rowgroup');
    for (const row of rows) {
      const tr = el('tr'); tr.setAttribute('role','row');
      columns.forEach((column, index) => {
        const cell = el(index === 0 ? 'th' : 'td', column.numeric ? 'fie-numeric' : '');
        cell.setAttribute('role', index === 0 ? 'rowheader' : 'cell');
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
      const expanded = el('tr', 'fie-expanded'); expanded.setAttribute('role','row'); expanded.hidden = true;
      expanded.id = `fie-expanded-${++serial}`;
      expand.dataset.fieExpand = ''; expand.setAttribute('aria-expanded', 'false');
      expand.setAttribute('aria-controls', expanded.id);
      expand.setAttribute('aria-label', `Expand ${row.title || row[columns[0].key]}`);
      const content = el('td'); content.setAttribute('role','cell'); content.colSpan = columns.length + 1;
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
    if (!['portfolio','reports'].includes(currentView()) && s?.league?.league_id) params.set('league', s.league.league_id);
    // Period and roster belong to the existing controls; never infer a historical projection.
    if (['startsit', 'dst', 'kicker', 'matchupsim', 'waivers'].includes(currentView())) {
      for (const [key, id] of [['season', 'seasonSelect'], ['week', 'weekSelect'], ['roster', 'weeklyRosterPicker']]) {
        if (byId(id)?.value) params.set(key, byId(id).value);
      }
    }
    if(['home','team','myroster'].includes(currentView()) && byId('weeklyRosterPicker')?.value) params.set('roster',byId('weeklyRosterPicker').value);
    if(currentView()==='waivers' && window.FIEWaiverWorkspace) params.set('waiver',window.FIEWaiverWorkspace.lens);
    return params.toString();
  }
  let restoring = false, restorePending = false, queued = false, lastContext = '', lastView = ''; 
  function syncRoute(replace = false) {
    if (restoring) return;
    const serialized = routeSnapshot();
    const context = serialized.replace(/(^|&)view=[^&]*/g, '');
    const view = currentView();
    if ((lastContext && lastContext !== context) || (lastView && lastView !== view)) clearDisclosures();
    lastContext = context; lastView = view;
    document.querySelectorAll('#primaryNav button').forEach(b => {if(b.classList.contains('active')) b.setAttribute('aria-current','page');else b.removeAttribute('aria-current');});
    document.querySelectorAll('#subnav button').forEach(b => {if(b.classList.contains('active')) b.setAttribute('aria-current','page');else b.removeAttribute('aria-current');});
    const name = byId('kLeague')?.textContent || 'All leagues';
    if (byId('fieContextName')) byId('fieContextName').textContent = ['portfolio','reports'].includes(currentView()) ? 'All leagues' : name;
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
        if(view==='waivers')window.FIEWaiverWorkspace?.setLens(params.get('waiver'));
        window.activateTab?.(view);
      }
    } catch (error) {
      const status = byId('fieRouteNotice');
      if (status) { status.hidden = false; status.textContent = 'Requested view could not be restored. Review the loaded league and retry with its existing load control.'; }
    } finally {
      restoring = false;
      if (restorePending) { restorePending = false; restoreRoute(); }
      else syncRoute(true);
    }
  }
  function setupShell() {
    const shell = document.querySelector('.shell'); if (!shell || !byId('primaryNav')) return;
    const skip = el('a','fie-skip-link','Skip to workspace content'); skip.href = '#sectionTitle';
    const heading = byId('sectionTitle'); if(heading)heading.tabIndex = -1;
    skip.addEventListener('click', event => {event.preventDefault();heading?.focus();heading?.scrollIntoView({block:'start'});});
    shell.prepend(skip);
    const routeNotice = el('p','fie-route-notice'); routeNotice.id = 'fieRouteNotice'; routeNotice.hidden = true; routeNotice.setAttribute('role','status');
    byId('sectionHero')?.before(routeNotice);
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
    document.addEventListener('click', event => {if(event.target.closest?.('#primaryNav button,#subnav button')){byId('fieRouteNotice').hidden = true;clearDisclosures();queueSync();}});
    window.addEventListener('fie:league-changing', clearDisclosures);
    window.addEventListener('fie:league-loaded', () => {if(byId('fieRouteNotice'))byId('fieRouteNotice').hidden = true;queueSync();});
    window.addEventListener('popstate', restoreRoute);
    // Hash edits are supported too; serialize restores so popstate/hashchange cannot overlap.
    window.addEventListener('hashchange', restoreRoute);
    if (new URLSearchParams(location.hash.slice(1)).has('view')) restoreRoute(); else syncRoute(true);
  }
  document.documentElement.dataset.fieAppearance = 'light';
  window.FIEEditorial = Object.freeze({ VERSION: 'editorial-p07', createTable, openReader, closeReader, clearDisclosures, syncRoute });
  if (document.readyState === 'loading') document.addEventListener('DOMContentLoaded', setupShell);
  else setupShell();
})();
