/* Xyvora UI Preview - device detection, themes, and client-side UI behavior. */

const THEMES = [
  { id: 'xyvora', name: 'Xyvora' },
  { id: 'cipher', name: 'Cipher' },
  { id: 'midnight', name: 'Midnight' },
  { id: 'ocean', name: 'Ocean' },
];

const GAMES = [
  {
    id: 'phantom-drift',
    title: 'Phantom Drift',
    category: 'racing',
    rating: 96,
    players: '27.4k playing',
    thumb: ['#1b4332', '#2d6a4f', '#081c15'],
    description: 'High-speed street racing with neon-soaked tracks and deep car tuning.',
    lastPlayed: '2 hours ago',
    installed: true,
  },
  {
    id: 'blox-frontier',
    title: 'Blox Frontier',
    category: 'adventure',
    rating: 94,
    players: '18.1k playing',
    thumb: ['#3a5a40', '#588157', '#1b2a1b'],
    description: 'Explore a vast open world, build camps, and survive the wild frontier.',
    lastPlayed: 'Yesterday',
    installed: true,
  },
  {
    id: 'tower-defense-x',
    title: 'Tower Defense X',
    category: 'sim',
    rating: 92,
    players: '45.2k playing',
    thumb: ['#264653', '#2a9d8f', '#1a1f2b'],
    description: 'Strategize, build, and defend your base against endless waves.',
    lastPlayed: '3 days ago',
    installed: true,
  },
  {
    id: 'arsenal-reborn',
    title: 'Arsenal Reborn',
    category: 'shooter',
    rating: 91,
    players: '62.8k playing',
    thumb: ['#5a3a31', '#c46b4e', '#211410'],
    description: 'Fast-paced FPS action with rotating weapons and competitive modes.',
    lastPlayed: 'Last week',
    installed: true,
  },
  {
    id: 'cafe-life',
    title: 'Cafe Life Roleplay',
    category: 'roleplay',
    rating: 89,
    players: '12.3k playing',
    thumb: ['#5e503f', '#a9927d', '#2a2118'],
    description: 'Run your own cafe, meet friends, and build your story in the city.',
    lastPlayed: '5 days ago',
    installed: false,
  },
  {
    id: 'velocity-legends',
    title: 'Velocity Legends',
    category: 'racing',
    rating: 93,
    players: '21.0k playing',
    thumb: ['#1d3557', '#457b9d', '#0f1a24'],
    description: 'Arcade racing with wild tracks, boosts, and ranked seasons.',
    lastPlayed: null,
    installed: false,
  },
  {
    id: 'island-tycoon',
    title: 'Island Tycoon',
    category: 'sim',
    rating: 90,
    players: '33.9k playing',
    thumb: ['#1b6b6a', '#4ecdc4', '#0f2424'],
    description: 'Build your dream island empire, automate production, and trade.',
    lastPlayed: null,
    installed: false,
  },
  {
    id: 'shadow-ops',
    title: 'Shadow Ops',
    category: 'shooter',
    rating: 88,
    players: '15.6k playing',
    thumb: ['#2b2d42', '#5c6378', '#14151f'],
    description: 'Tactical squad-based missions with stealth and high-stakes objectives.',
    lastPlayed: null,
    installed: false,
  },
];

const FRIENDS = [
  { name: 'Aria', initial: 'A', color: ['#59f06d', '#1a9952'], status: 'online', game: 'Phantom Drift' },
  { name: 'Mason', initial: 'M', color: ['#60a5fa', '#2563eb'], status: 'online', game: 'Tower Defense X' },
  { name: 'Juno', initial: 'J', color: ['#f472b6', '#db2777'], status: 'online', game: 'Blox Frontier' },
  { name: 'Kai', initial: 'K', color: ['#fbbf24', '#d97706'], status: 'offline', game: null },
  { name: 'Riley', initial: 'R', color: ['#a78bfa', '#7c3aed'], status: 'offline', game: null },
];

const VIEW_META = {
  home: { title: 'Home', subtitle: 'Welcome back. Pick up where you left off.' },
  discover: { title: 'Discover', subtitle: 'Find new experiences to play on Linux.' },
  library: { title: 'Library', subtitle: 'Your installed and recently played experiences.' },
  friends: { title: 'Friends', subtitle: 'See who is online and jump into their game.' },
  messages: { title: 'Messages', subtitle: 'Chat with your friends from Xyvora.' },
  settings: { title: 'Settings', subtitle: 'Configure Xyvora for your Linux setup.' },
};

const state = {
  view: 'home',
  filter: 'all',
  search: '',
  theme: 'xyvora',
  system: null,
};

const $ = (sel, ctx = document) => ctx.querySelector(sel);
const $$ = (sel, ctx = document) => Array.from(ctx.querySelectorAll(sel));

function escapeHtml(str) {
  return String(str)
    .replace(/&/g, '&amp;')
    .replace(/</g, '&lt;')
    .replace(/>/g, '&gt;')
    .replace(/"/g, '&quot;')
    .replace(/'/g, '&#39;');
}

function thumbStyle(colors) {
  const [a, b, c] = colors;
  return `background:
    radial-gradient(120% 90% at 20% 15%, ${a}cc, transparent 55%),
    radial-gradient(90% 80% at 85% 80%, ${b}b3, transparent 55%),
    linear-gradient(160deg, ${a}, ${c});`;
}

function avatarStyle(colors) {
  return `background: linear-gradient(135deg, ${colors[0]}, ${colors[1]});`;
}

function applyTheme(themeId, persist = true) {
  const theme = THEMES.find((t) => t.id === themeId) ? themeId : 'xyvora';
  state.theme = theme;
  document.documentElement.setAttribute('data-theme', theme);
  if (persist) {
    try { localStorage.setItem('xyvora-theme', theme); } catch (_) { /* ignore */ }
  }
  $$('.theme-option').forEach((btn) => {
    const active = btn.dataset.theme === theme;
    btn.classList.toggle('active', active);
    btn.setAttribute('aria-checked', active ? 'true' : 'false');
  });
}

function loadSavedTheme() {
  let saved = 'xyvora';
  try { saved = localStorage.getItem('xyvora-theme') || 'xyvora'; } catch (_) { /* ignore */ }
  applyTheme(saved, false);
}

function clientSideSystemFallback() {
  const ua = navigator.userAgent || '';
  const platform = navigator.platform || '';
  const isLinux = /Linux/i.test(ua) || /Linux/i.test(platform);
  const isAndroid = /Android/i.test(ua);
  // Treat Android browser as unsupported for this Linux client preview unless it's Linux.
  const supported = isLinux && !isAndroid;
  const archGuess = /aarch64|arm64/i.test(ua) ? 'arm64' : (/x86_64|Win64|amd64/i.test(ua) ? 'x86_64' : 'unknown');
  return {
    supported,
    os: {
      system: supported ? 'linux' : (isAndroid ? 'android' : 'unknown'),
      distro_id: supported ? 'linux' : 'unknown',
      distro_name: supported ? 'Linux' : (isAndroid ? 'Android' : 'Unknown OS'),
      distro_version: '',
      family: supported ? 'linux' : 'unknown',
    },
    arch: archGuess,
    machine: archGuess,
    capabilities: {
      android_runtime: supported,
      vulkan: supported,
      opengl: supported,
      proton: supported,
      wine: supported,
      waydroid: false,
    },
    runtimes: supported ? [
      { id: 'android-waydroid', label: 'Android Runtime (Waydroid)', available: true, recommended: true, detected: false },
      { id: 'proton', label: 'Proton - Experimental', available: true, recommended: false, detected: false },
      { id: 'wine', label: 'Wine / Wine-GE', available: true, recommended: false, detected: false },
    ] : [],
    renderers: supported ? [
      { id: 'vulkan', label: 'Vulkan (Recommended)', available: true, detected: false },
      { id: 'opengl', label: 'OpenGL', available: true, detected: false },
    ] : [],
    package_hint: 'Install Waydroid and Vulkan tools using your distro package manager.',
    support_message: supported ? '' : "Sorry, this device isn't supported yet. Xyvora currently supports Linux devices.",
  };
}

async function detectSystem() {
  try {
    const res = await fetch('/api/system', { headers: { 'Accept': 'application/json' } });
    if (!res.ok) throw new Error(`HTTP ${res.status}`);
    const data = await res.json();
    if (!data || typeof data !== 'object') throw new Error('Invalid system payload');
    return data;
  } catch (_) {
    return clientSideSystemFallback();
  }
}

function prettyDistro(sys) {
  if (!sys?.os) return 'Unknown';
  const name = sys.os.distro_name || 'Linux';
  const ver = sys.os.distro_version ? ` ${sys.os.distro_version}` : '';
  return `${name}${ver}`;
}

function supportLabel(sys) {
  if (!sys) return 'Detecting…';
  return sys.supported ? 'Supported' : 'Not supported';
}

function renderSystemUI() {
  const sys = state.system;
  if (!sys) return;

  const supported = !!sys.supported;
  const distro = prettyDistro(sys);
  const arch = sys.arch || sys.machine || 'unknown';
  const deviceText = supported ? `${sys.os.distro_name || 'Linux'} · ${arch}` : `${sys.os.distro_name || 'Unknown OS'} · ${arch}`;

  const badge = $('#deviceBadge');
  const badgeDot = $('#deviceBadgeDot');
  badge.classList.toggle('unsupported', !supported);
  badgeDot.style.background = supported ? 'var(--accent)' : '#ff6b6b';
  $('#deviceBadgeText').textContent = deviceText;

  $('#userStatusText').textContent = supported ? `Online · ${sys.os.distro_name || 'Linux'}` : `Unsupported device`;
  $('#userStatusDot').style.background = supported ? 'var(--accent)' : '#ff6b6b';
  $('#userStatusDot').style.boxShadow = supported ? '' : '0 0 0 3px rgba(255,107,107,0.15)';

  $('#heroStatDevice').textContent = sys.os?.family === 'arch' ? 'Arch Linux' : (sys.os?.distro_name || (supported ? 'Linux' : 'Unsupported'));
  $('#heroStatArch').textContent = arch;
  $('#heroStatRuntime').textContent = supported ? 'Android' : 'N/A';

  const statusPill = $('#systemStatusPill');
  statusPill.textContent = supported ? 'Ready' : 'Unsupported';
  statusPill.classList.toggle('pill-good', supported);
  statusPill.classList.toggle('pill-bad', !supported);

  const cap = sys.capabilities || {};
  const runtimeStatus = supported
    ? (cap.waydroid ? 'Android Runtime (Waydroid) detected' : 'Android Runtime (Waydroid) available')
    : 'Not available on this device';
  const graphicsStatus = supported
    ? [cap.vulkan ? 'Vulkan' : null, cap.opengl ? 'OpenGL' : null].filter(Boolean).join(' / ') || 'Compatibility mode'
    : 'Not available';

  $('#systemStatusRows').innerHTML = `
    <div class="status-row"><span>Device</span><span class="${supported ? 'status-ok' : 'status-bad'}">${escapeHtml(distro)}</span></div>
    <div class="status-row"><span>Architecture</span><span class="status-ok">${escapeHtml(arch)}</span></div>
    <div class="status-row"><span>Runtime</span><span class="${supported ? 'status-ok' : 'status-bad'}">${escapeHtml(runtimeStatus)}</span></div>
    <div class="status-row"><span>Graphics</span><span class="${supported ? 'status-ok' : 'status-bad'}">${escapeHtml(graphicsStatus)}</span></div>
  `;

  $('#deviceInfoCard').innerHTML = `
    <div class="status-row"><span>Status</span><span class="${supported ? 'status-ok' : 'status-bad'}">${escapeHtml(supportLabel(sys))}</span></div>
    <div class="status-row"><span>OS</span><span class="status-ok">${escapeHtml((sys.os?.system || 'unknown').toUpperCase())}</span></div>
    <div class="status-row"><span>Distro</span><span class="status-ok">${escapeHtml(distro)}</span></div>
    <div class="status-row"><span>Architecture</span><span class="status-ok">${escapeHtml(arch)}</span></div>
  `;

  $('#deviceSupportNote').textContent = supported
    ? `Xyvora supports this Linux device. Showing options available for ${distro} (${arch}).`
    : (sys.support_message || "Sorry, this device isn't supported yet. Xyvora currently supports Linux devices.");

  renderRuntimeOptions();
  renderUnsupportedOverlay();
}

function renderRuntimeOptions() {
  const sys = state.system;
  const rendererSelect = $('#rendererSelect');
  const runtimeSelect = $('#runtimeSelect');
  if (!rendererSelect || !runtimeSelect) return;

  const renderers = (sys?.renderers || []).filter((r) => r.available);
  const runtimes = (sys?.runtimes || []).filter((r) => r.available);

  rendererSelect.innerHTML = renderers.length
    ? renderers.map((r, i) => `<option value="${escapeHtml(r.id)}" ${i === 0 ? 'selected' : ''}>${escapeHtml(r.label)}${r.detected ? ' · Detected' : ''}</option>`).join('')
    : '<option value="none">No compatible renderer</option>';
  rendererSelect.disabled = renderers.length === 0;

  runtimeSelect.innerHTML = runtimes.length
    ? runtimes.map((r) => `<option value="${escapeHtml(r.id)}" ${r.recommended ? 'selected' : ''}>${escapeHtml(r.label)}${r.detected ? ' · Detected' : ''}</option>`).join('')
    : '<option value="none">No compatible runtime</option>';
  runtimeSelect.disabled = runtimes.length === 0;

  const hint = $('#runtimeHint');
  if (hint) {
    hint.textContent = sys?.supported
      ? `Android Runtime (Waydroid) is the default for Xyvora on Linux. ${sys.package_hint || ''}`
      : (sys?.support_message || 'No compatible runtime is available for this device.');
  }
}

function renderUnsupportedOverlay() {
  const sys = state.system;
  const overlay = $('#unsupportedOverlay');
  if (!overlay || !sys) return;
  if (sys.supported) {
    overlay.hidden = true;
    return;
  }
  overlay.hidden = false;
  $('#unsupportedCopy').textContent = sys.support_message || "Sorry, this device isn't supported yet. Xyvora currently supports Linux devices.";
  $('#unsupportedDetails').innerHTML = `
    <div class="status-row"><span>Detected OS</span><span class="status-bad">${escapeHtml(sys.os?.distro_name || sys.os?.system || 'Unknown')}</span></div>
    <div class="status-row"><span>Architecture</span><span class="status-bad">${escapeHtml(sys.arch || 'Unknown')}</span></div>
    <div class="status-row"><span>Supported</span><span class="status-ok">Linux (all distros)</span></div>
  `;
}

/* ---- Existing UI rendering ---- */

function gameCard(game, { compact = false } = {}) {
  return `
    <article class="game-card" data-game-id="${escapeHtml(game.id)}" data-category="${escapeHtml(game.category)}">
      <div class="game-thumb">
        <div class="thumb-art" style="${thumbStyle(game.thumb)}"></div>
        <div class="thumb-overlay"></div>
        <button class="thumb-play" data-play="${escapeHtml(game.id)}" aria-label="Play ${escapeHtml(game.title)}">
          <svg viewBox="0 0 24 24"><polygon points="5,3 19,12 5,21"/></svg>
        </button>
      </div>
      <div class="game-body">
        <h4 class="game-title" title="${escapeHtml(game.title)}">${escapeHtml(game.title)}</h4>
        <div class="game-meta">
          <span class="rating">
            <svg width="12" height="12" viewBox="0 0 24 24" fill="currentColor" aria-hidden="true" style="vertical-align:-1px"><path d="M12 2l3.09 6.26L22 9.27l-5 4.87 1.18 6.88L12 17.77l-6.18 3.25L7 14.14 2 9.27l6.91-1.01L12 2z"/></svg>
            ${game.rating}%
          </span>
          <span class="meta-dot"></span>
          <span>${escapeHtml(game.category.charAt(0).toUpperCase() + game.category.slice(1))}</span>
        </div>
        <div class="card-footer">
          <span class="player-count">${escapeHtml(game.players)}</span>
          <button class="card-action" data-play="${escapeHtml(game.id)}">${compact ? 'Play' : 'Launch'}</button>
        </div>
      </div>
    </article>
  `;
}

function renderHome() {
  const continueGames = GAMES.filter((g) => g.installed).slice(0, 4);
  const popular = [...GAMES].sort((a, b) => b.rating - a.rating).slice(0, 4);

  $('#continueGrid').innerHTML = continueGames.map((g) => gameCard(g)).join('');
  $('#popularGrid').innerHTML = popular.map((g) => gameCard(g, { compact: true })).join('');

  $('#friendList').innerHTML = FRIENDS.map((f) => `
    <li class="friend-item">
      <div class="friend-avatar" style="${avatarStyle(f.color)}">
        ${escapeHtml(f.initial)}
        ${f.status === 'online' ? '<span class="online-dot"></span>' : ''}
      </div>
      <div class="friend-info">
        <div class="friend-name">${escapeHtml(f.name)}</div>
        <div class="friend-game">${f.status === 'online' ? `Playing ${escapeHtml(f.game)}` : 'Offline'}</div>
      </div>
      ${f.status === 'online' ? `<button class="friend-join" data-join="${escapeHtml(f.name)}">Join</button>` : ''}
    </li>
  `).join('');
}

function renderDiscover() {
  const q = state.search.trim().toLowerCase();
  const filtered = GAMES.filter((g) => {
    const matchesFilter = state.filter === 'all' || g.category === state.filter;
    const matchesSearch = !q || g.title.toLowerCase().includes(q) || g.category.toLowerCase().includes(q);
    return matchesFilter && matchesSearch;
  });

  const grid = $('#discoverGrid');
  if (filtered.length === 0) {
    grid.innerHTML = `
      <div style="grid-column:1/-1;padding:28px;border:1px dashed rgba(255,255,255,0.12);border-radius:14px;color:var(--text-muted);text-align:center;">
        No experiences match your search.
      </div>
    `;
    return;
  }
  grid.innerHTML = filtered.map((g) => gameCard(g)).join('');
}

function renderLibrary() {
  const q = state.search.trim().toLowerCase();
  const items = GAMES
    .filter((g) => g.installed)
    .filter((g) => !q || g.title.toLowerCase().includes(q));

  const list = $('#libraryList');
  if (items.length === 0) {
    list.innerHTML = `
      <div style="padding:28px;border:1px dashed rgba(255,255,255,0.12);border-radius:14px;color:var(--text-muted);text-align:center;">
        No installed experiences match your search.
      </div>
    `;
    return;
  }

  list.innerHTML = items.map((g) => `
    <article class="library-item">
      <div class="library-thumb">
        <div class="thumb-art" style="${thumbStyle(g.thumb)}"></div>
      </div>
      <div class="library-info">
        <h4 class="library-title">${escapeHtml(g.title)}</h4>
        <p class="library-desc">${escapeHtml(g.description)}</p>
        <div class="library-meta">
          <span>
            <svg width="12" height="12" viewBox="0 0 24 24" fill="currentColor" aria-hidden="true"><path d="M12 2l3.09 6.26L22 9.27l-5 4.87 1.18 6.88L12 17.77l-6.18 3.25L7 14.14 2 9.27l6.91-1.01L12 2z"/></svg>
            ${g.rating}% rating
          </span>
          <span>${escapeHtml(g.players)}</span>
          <span>Last played ${escapeHtml(g.lastPlayed || 'Never')}</span>
        </div>
      </div>
      <div class="library-actions">
        <button class="primary-btn small" data-play="${escapeHtml(g.id)}">Play</button>
        <button class="ghost-btn" style="height:36px;padding:0 14px;font-size:0.82rem;border-radius:9px" data-action="details" data-game="${escapeHtml(g.id)}">Details</button>
      </div>
    </article>
  `).join('');
}

function renderFriends() {
  $('#friendsPage').innerHTML = FRIENDS.map((f) => `
    <article class="friend-card ${f.status === 'offline' ? 'offline' : ''}">
      <div class="friend-avatar" style="${avatarStyle(f.color)}">
        ${escapeHtml(f.initial)}
        ${f.status === 'online' ? '<span class="online-dot"></span>' : ''}
      </div>
      <div class="friend-info">
        <div class="friend-name">${escapeHtml(f.name)}</div>
        ${f.status === 'online'
          ? `<div class="friend-game">Playing ${escapeHtml(f.game)}</div>`
          : `<div class="offline-label">Offline</div>`}
      </div>
      ${f.status === 'online'
        ? `<button class="friend-join" data-join="${escapeHtml(f.name)}">Join</button>`
        : `<button class="card-action" disabled style="opacity:.5;cursor:not-allowed;">Offline</button>`}
    </article>
  `).join('');
}

function renderAll() {
  renderHome();
  renderDiscover();
  renderLibrary();
  renderFriends();
}

function setView(view) {
  if (!VIEW_META[view]) return;
  state.view = view;

  $$('.view').forEach((el) => el.classList.toggle('active', el.id === `view-${view}`));
  $$('.nav-item[data-view]').forEach((btn) => {
    const active = btn.dataset.view === view;
    btn.classList.toggle('active', active);
    if (active) btn.setAttribute('aria-current', 'page');
    else btn.removeAttribute('aria-current');
  });

  $('#pageTitle').textContent = VIEW_META[view].title;
  $('#pageSubtitle').textContent = VIEW_META[view].subtitle;

  if (view === 'discover') renderDiscover();
  if (view === 'library') renderLibrary();

  $('.content').scrollTop = 0;
}

let toastTimer;
function showToast(message) {
  const toast = $('#toast');
  toast.textContent = message;
  toast.classList.add('show');
  clearTimeout(toastTimer);
  toastTimer = setTimeout(() => toast.classList.remove('show'), 2600);
}

function playGame(id) {
  const game = GAMES.find((g) => g.id === id);
  if (!game) return;
  if (state.system && !state.system.supported) {
    showToast("Sorry, this device isn't supported yet.");
    return;
  }
  const runtime = $('#runtimeSelect')?.selectedOptions?.[0]?.textContent || 'Android Runtime (Waydroid)';
  showToast(`Launching ${game.title} with ${runtime.replace(/ · Detected$/, '')}... (UI preview)`);
}

function wireEvents() {
  $('#sidebarNav').addEventListener('click', (e) => {
    const btn = e.target.closest('[data-view]');
    if (btn) setView(btn.dataset.view);
  });

  $$('.sidebar-footer [data-view]').forEach((btn) => {
    btn.addEventListener('click', () => setView(btn.dataset.view));
  });

  $$('[data-goto]').forEach((btn) => {
    btn.addEventListener('click', () => setView(btn.dataset.goto));
  });

  $('#discoverFilters').addEventListener('click', (e) => {
    const chip = e.target.closest('[data-filter]');
    if (!chip) return;
    state.filter = chip.dataset.filter;
    $$('.filter-chip').forEach((c) => c.classList.toggle('active', c === chip));
    renderDiscover();
  });

  $('#searchInput').addEventListener('input', (e) => {
    state.search = e.target.value;
    if (state.view === 'home' && state.search.trim()) setView('discover');
    renderDiscover();
    renderLibrary();
  });

  $('#themePicker').addEventListener('click', (e) => {
    const btn = e.target.closest('[data-theme]');
    if (!btn) return;
    applyTheme(btn.dataset.theme, true);
    const name = THEMES.find((t) => t.id === btn.dataset.theme)?.name || btn.dataset.theme;
    showToast(`Theme set to ${name}.`);
  });

  document.addEventListener('click', (e) => {
    const play = e.target.closest('[data-play]');
    if (play) {
      e.preventDefault();
      playGame(play.dataset.play);
      return;
    }
    const join = e.target.closest('[data-join]');
    if (join) {
      e.preventDefault();
      showToast(`Joining ${join.dataset.join}'s session... (UI preview)`);
      return;
    }
    const action = e.target.closest('[data-action]');
    if (action) {
      const kind = action.dataset.action;
      if (kind === 'play-featured') playGame('phantom-drift');
      if (kind === 'details') {
        const g = GAMES.find((x) => x.id === action.dataset.game);
        if (g) showToast(`${g.title}: ${g.description}`);
      }
    }
  });

  $('#notifBtn').addEventListener('click', () => {
    showToast('No new notifications. You are all caught up.');
  });

  $('#launchBtn').addEventListener('click', () => playGame('phantom-drift'));
}

async function init() {
  loadSavedTheme();
  renderAll();
  wireEvents();
  setView('home');

  state.system = await detectSystem();
  renderSystemUI();
}

if (document.readyState === 'loading') {
  document.addEventListener('DOMContentLoaded', init);
} else {
  init();
}
