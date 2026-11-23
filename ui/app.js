const PLUGINS = [
  { id: 'discord-presence', name: 'Discord Presence', desc: 'Shows your current Roblox activity in Discord Rich Presence.', caps: ['presence', 'game-state'], enabled: true },
  { id: 'flag-inspector', name: 'Flag Inspector', desc: 'Inspect and understand Roblox FastFlags and conflicts.', caps: ['flags.read'], enabled: true },
  { id: 'fps-flex', name: 'FPS Flex', desc: 'Adjust frame pacing and FPS behavior with safe controls.', caps: ['performance'], enabled: false },
  { id: 'hide-gui', name: 'Hide GUI', desc: 'Toggle in-game GUI elements for cleaner capture or play.', caps: ['ui.overlay'], enabled: false },
];

const LIBRARY = [
  { id: 'doors', name: 'DOORS', genre: 'Horror', status: 'Ready', note: 'Demoed on Cordial', color: ['#3b1d2f', '#ff4d6d'] },
  { id: 'tunneler', name: 'TUNNELER', genre: 'VR / Action', status: 'VR Ready', note: 'Quest build supported', color: ['#2b1d3b', '#8b5cf6'] },
  { id: 'frontend', name: 'Roblox App', genre: 'Launcher', status: 'Ready', note: 'Sign in and browse', color: ['#1d2f3b', '#38bdf8'] },
  { id: 'studio', name: 'Roblox Studio', genre: 'Create', status: 'Experimental', note: 'May vary by build', color: ['#2e2a1d', '#f59e0b'] },
];

const VIEW_META = {
  home: ['Launcher', 'Home', 'Run Roblox natively on Linux with Cordial.'],
  library: ['Launcher', 'Library', 'Your experiences and quick-launch entries.'],
  plugins: ['Plugins', 'Plugins', 'Manage bundled Cordial plugins and brokered capabilities.'],
  settings: ['Settings', 'Settings', 'Tune runtime, appearance, and launcher behavior.'],
  logs: ['Diagnostics', 'Logs', 'Preview launcher events and system checks.'],
};

const state = {
  view: 'home',
  system: null,
  logs: [],
  theme: localStorage.getItem('cordial-theme') || 'mango',
  compact: localStorage.getItem('cordial-compact') === '1',
};

const $ = (s, c=document) => c.querySelector(s);
const $$ = (s, c=document) => Array.from(c.querySelectorAll(s));
const esc = (str='') => String(str).replace(/[&<>"']/g, m => ({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[m]));

function log(msg, level='info') {
  const entry = { ts: new Date(), msg, level };
  state.logs.unshift(entry);
  state.logs = state.logs.slice(0, 100);
  renderLogs();
}

function toast(msg) {
  const t = $('#toast');
  t.textContent = msg;
  t.classList.add('show');
  clearTimeout(toast._timer);
  toast._timer = setTimeout(() => t.classList.remove('show'), 2400);
  log(msg);
}

function setTheme(theme) {
  state.theme = theme;
  document.documentElement.setAttribute('data-theme', theme);
  localStorage.setItem('cordial-theme', theme);
  const sel = $('#themeSelect');
  if (sel) sel.value = theme;
}

function setCompact(on) {
  state.compact = !!on;
  document.documentElement.classList.toggle('compact', state.compact);
  localStorage.setItem('cordial-compact', state.compact ? '1' : '0');
  const t = $('#compactToggle');
  if (t) t.checked = state.compact;
}

function setView(view) {
  if (!VIEW_META[view]) return;
  state.view = view;
  $$('.view').forEach(v => v.classList.toggle('active', v.id === `view-${view}`));
  $$('.nav-item[data-view]').forEach(b => b.classList.toggle('active', b.dataset.view === view));
  const [eyebrow, title, sub] = VIEW_META[view];
  $('#eyebrow').textContent = eyebrow;
  $('#pageTitle').textContent = title;
  $('#pageSubtitle').textContent = sub;
  $('.content').scrollTop = 0;
}

function renderPlugins() {
  $('#pluginCountPill').textContent = String(PLUGINS.length);
  $('#pluginMeta').textContent = `${PLUGINS.length} bundled`;
  $('#pluginGrid').innerHTML = PLUGINS.map(p => `
    <article class="plugin-card">
      <div class="plugin-top">
        <div>
          <h4>${esc(p.name)}</h4>
          <p>${esc(p.desc)}</p>
        </div>
        <label class="switch"><input type="checkbox" data-plugin="${esc(p.id)}" ${p.enabled ? 'checked' : ''}><span></span></label>
      </div>
      <div class="caps">${p.caps.map(c => `<span class="cap">${esc(c)}</span>`).join('')}</div>
      <div class="plugin-foot"><span class="muted mono">${esc(p.id)}</span><span class="pill ${p.enabled ? 'pill-ok' : ''}">${p.enabled ? 'Enabled' : 'Disabled'}</span></div>
    </article>
  `).join('');
}

function renderLibrary(filter='') {
  const q = filter.trim().toLowerCase();
  const items = LIBRARY.filter(x => !q || x.name.toLowerCase().includes(q) || x.genre.toLowerCase().includes(q));
  $('#libraryGrid').innerHTML = items.map(x => `
    <article class="lib-card">
      <div class="lib-art" style="background:linear-gradient(135deg, ${x.color[0]}, ${x.color[1]});">
        <span class="lib-art-title">${esc(x.name)}</span>
      </div>
      <div class="lib-body">
        <div class="lib-top"><h4>${esc(x.name)}</h4><span class="pill">${esc(x.status)}</span></div>
        <p class="muted">${esc(x.genre)} · ${esc(x.note)}</p>
        <div class="lib-actions">
          <button class="btn btn-primary btn-sm" data-action="launch" data-game="${esc(x.name)}">Launch</button>
          <button class="btn btn-ghost btn-sm" data-action="details" data-game="${esc(x.name)}">Details</button>
        </div>
      </div>
    </article>
  `).join('') || `<div class="empty">No library entries match "${esc(filter)}".</div>`;
}

function renderLogs() {
  const shell = $('#logShell');
  if (!state.logs.length) {
    shell.innerHTML = `<div class="log-empty">No events yet.</div>`;
    return;
  }
  shell.innerHTML = state.logs.map(e => `
    <div class="log-line log-${esc(e.level)}">
      <span class="log-ts">${e.ts.toLocaleTimeString()}</span>
      <span class="log-lvl">${esc(e.level.toUpperCase())}</span>
      <span class="log-msg">${esc(e.msg)}</span>
    </div>
  `).join('');
}

function systemBadgeText(sys) {
  if (!sys) return 'Checking system…';
  if (!sys.supported) return 'Unsupported device';
  return `${sys.os?.distro || 'Linux'} · ${sys.arch}`;
}

function renderSystem() {
  const sys = state.system;
  const supported = !!sys?.supported;
  $('#deviceMiniDot').className = 'device-mini-dot ' + (supported ? 'ok' : 'bad');
  $('#deviceMiniTitle').textContent = sys ? (supported ? (sys.os?.distro || 'Linux') : 'Unsupported device') : 'Detecting device…';
  $('#deviceMiniSub').textContent = sys ? `${sys.arch || '?'} · ${sys.session?.wayland ? 'Wayland' : sys.session?.x11 ? 'X11' : 'No display detected'}` : 'Checking Linux support';
  $('#statusChipDot').className = 'chip-dot ' + (supported ? 'ok' : 'bad');
  $('#statusChipText').textContent = systemBadgeText(sys);
  $('#kpiArch').textContent = sys?.arch || '—';
  $('#kpiSession').textContent = sys?.session?.wayland ? 'Wayland' : sys?.session?.x11 ? 'X11' : (sys ? 'None' : '—');

  const checks = sys?.checks || {};
  const items = [
    ['Linux OS', !!checks.linux],
    ['Supported arch (x86_64/aarch64)', !!checks.arch],
    ['Wayland or X11 session', !!(checks.wayland_session || checks.x11_session)],
    ['Flatpak (recommended)', !!checks.flatpak],
    ['Rust toolchain (source builds)', !!checks.cargo],
    ['ffmpeg (recording)', !!checks.ffmpeg],
  ];
  $('#checklist').innerHTML = items.map(([label, ok]) => `
    <div class="check ${ok ? 'ok' : 'no'}"><span class="check-dot"></span><span class="check-label">${esc(label)}</span><span class="check-val">${ok ? 'OK' : 'Missing'}</span></div>
  `).join('');

  const pill = $('#readinessPill');
  pill.textContent = supported ? 'Supported' : 'Unsupported';
  pill.className = 'pill ' + (supported ? 'pill-ok' : 'pill-bad');
  $('#readinessSub').textContent = sys ? (supported ? 'This device can run the Cordial UI and target runtime.' : (sys.blockers?.[0] || 'Unsupported device.')) : 'Waiting for device detection…';

  const notes = [...(sys?.blockers || []), ...(sys?.notes || [])];
  $('#panelNote').textContent = notes[0] || 'Device looks good for Cordial. Use Flatpak for the recommended install path.';
}

async function fetchSystem() {
  $('#statusChipText').textContent = 'Checking system…';
  try {
    const r = await fetch('/api/system', { cache: 'no-store' });
    if (!r.ok) throw new Error(`HTTP ${r.status}`);
    state.system = await r.json();
    log(`System detected: ${systemBadgeText(state.system)}`, state.system.supported ? 'info' : 'warn');
  } catch (e) {
    state.system = { supported: false, arch: 'unknown', os: { distro: 'Unknown' }, session: {}, checks: {}, blockers: ['Could not reach /api/system.'], notes: [] };
    log(`System detection failed: ${e.message}`, 'error');
  }
  renderSystem();
}

function wire() {
  $('#nav').addEventListener('click', e => {
    const b = e.target.closest('[data-view]');
    if (b) setView(b.dataset.view);
  });
  document.addEventListener('click', e => {
    const goto = e.target.closest('[data-goto]');
    if (goto) { setView(goto.dataset.goto); return; }
    const action = e.target.closest('[data-action]');
    if (!action) return;
    const a = action.dataset.action;
    if (a === 'launch') {
      const game = action.dataset.game ? ` (${action.dataset.game})` : '';
      if (state.system && !state.system.supported) { toast('This device is not supported by Cordial yet.'); return; }
      toast(`Launch requested${game}. Connect this UI to cordial-shell to start Roblox.`);
      log(`Launch requested${game}`, 'info');
    } else if (a === 'check') {
      toast('Refreshing system status…');
      fetchSystem();
    } else if (a === 'details') {
      toast(`${action.dataset.game}: entry managed by Cordial launcher UI.`);
    }
  });
  $('#refreshBtn').addEventListener('click', () => { toast('Refreshing system status…'); fetchSystem(); });
  $('#launchBtn').addEventListener('click', () => $('#launchBtn').blur() || document.querySelector('[data-action="launch"]').click());
  $('#themeSelect').addEventListener('change', e => { setTheme(e.target.value); toast(`Theme: ${e.target.selectedOptions[0].textContent}`); });
  $('#compactToggle').addEventListener('change', e => { setCompact(e.target.checked); toast(e.target.checked ? 'Compact mode enabled' : 'Compact mode disabled'); });
  $('#clearLogsBtn').addEventListener('click', () => { state.logs = []; renderLogs(); toast('Logs cleared'); });
  $('#libSearch').addEventListener('input', e => renderLibrary(e.target.value));
  $('#pluginGrid').addEventListener('change', e => {
    const cb = e.target.closest('[data-plugin]');
    if (!cb) return;
    const p = PLUGINS.find(x => x.id === cb.dataset.plugin);
    if (p) { p.enabled = cb.checked; renderPlugins(); toast(`${p.name} ${p.enabled ? 'enabled' : 'disabled'}`); }
  });
}

async function init() {
  setTheme(state.theme);
  setCompact(state.compact);
  renderPlugins();
  renderLibrary();
  renderLogs();
  wire();
  setView('home');
  log('Cordial launcher UI initialized');
  await fetchSystem();
}

init();
