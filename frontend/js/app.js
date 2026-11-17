/**
 * Rezno AI — Primary Application & Component Orchestrator
 */

let graphController = null;

// --- Clean Academic Markdown Parser with In-Text Citation Linking ---
function renderAcademicMarkdown(md) {
  if (!md) return '';
  let html = md
    .replace(/&/g, '&amp;')
    .replace(/</g, '&lt;')
    .replace(/>/g, '&gt;')
    .replace(/^### (.*$)/gim, '<h4 class="text-sm font-semibold mt-3 mb-1 text-[var(--text-main)]">$1</h4>')
    .replace(/^## (.*$)/gim, '<h3 class="text-base font-semibold mt-4 mb-2 text-[var(--text-main)]">$1</h3>')
    .replace(/\*\*(.*?)\*\*/gim, '<strong>$1</strong>')
    .replace(/\*(.*?)\*/gim, '<em>$1</em>')
    .replace(/\\\[([\s\S]*?)\\\]/g, '<span class="font-mono bg-[var(--bg-subtle)] px-1 py-0.5 rounded text-xs">$1</span>')
    .replace(/\\\((.*?)\\\)/g, '<span class="font-mono bg-[var(--bg-subtle)] px-1 py-0.5 rounded text-xs">$1</span>')
    .replace(/`([^`]+)`/gim, '<code class="font-mono bg-[var(--bg-subtle)] px-1 py-0.5 rounded text-xs border border-[var(--border-subtle)]">$1</code>')
    .replace(/^\s*\*\s+(.*$)/gim, '<li class="ml-4 list-disc text-sm my-1">$1</li>')
    .replace(/^\s*-\s+(.*$)/gim, '<li class="ml-4 list-disc text-sm my-1">$1</li>')
    .replace(/\n\n/gim, '</p><p>');

  // Transform citations (e.g. 2106.09685) into interactive jump buttons
  html = html.replace(/\b(\d{4}\.\d{4,5})\b/g, (match) => {
    return `<button class="cite-badge" data-arxiv="${match}">[${match}]</button>`;
  });

  return `<div class="synthesis-prose"><p>${html}</p></div>`;
}

// --- DOM Bootstrapping ---
document.addEventListener('DOMContentLoaded', () => {
  // Apply saved theme
  window.appState.setTheme(window.appState.theme);

  // Bind Header Theme Toggle
  const themeBtn = document.getElementById('theme-toggle-btn');
  if (themeBtn) {
    themeBtn.addEventListener('click', () => {
      window.appState.toggleTheme();
      updateThemeIcon();
      if (graphController) {
        const run = window.appState.getSelectedRun();
        graphController.initGraph();
        if (run && run.graph) graphController.updateData(run.graph);
      }
    });
  }
  updateThemeIcon();

  // Bind Desk Tabs
  const tabButtons = document.querySelectorAll('.desk-tab-btn');
  tabButtons.forEach(btn => {
    btn.addEventListener('click', (e) => {
      const tab = e.currentTarget.getAttribute('data-tab');
      window.appState.setActiveTab(tab);
    });
  });

  // Bind Composer Input
  bindComposer();

  // Bind Settings Popover
  bindSettingsPopover();

  // Bind PDF Drawer Close
  const pdfCloseBtn = document.getElementById('pdf-drawer-close');
  const pdfOverlay = document.getElementById('pdf-drawer-overlay');
  if (pdfCloseBtn) {
    pdfCloseBtn.addEventListener('click', () => window.appState.closePdfViewer());
  }
  if (pdfOverlay) {
    pdfOverlay.addEventListener('click', (e) => {
      if (e.target === pdfOverlay) window.appState.closePdfViewer();
    });
  }

  // Subscribe to Application State
  window.appState.subscribe((event, payload) => {
    if (event === 'tab_change') {
      renderTabs();
    } else if (event === 'run_selected' || event === 'run_updated' || event === 'paper_updated') {
      updateDeskToolbar();
      renderActiveTabContent();
    } else if (event === 'papers_render') {
      renderLiteratureTab();
      updateTabCounts();
    } else if (event === 'messages_render' || event === 'search_aborted') {
      renderConversationThread();
      updateComposerButtonState();
    } else if (event === 'session_cleared') {
      renderAll();
    } else if (event === 'pdf_viewer_open') {
      handleOpenPdf(payload);
    } else if (event === 'pdf_viewer_close') {
      handleClosePdf();
    } else if (event === 'backend_status_changed') {
      window.appState.updateConnectionStatusUI();
    }
  });

  // Initial Full Render
  renderAll();

  // Initialize Resilient Hybrid Mode backend health probe
  window.appState.updateConnectionStatusUI();
  if (typeof window.appState.probeHealth === 'function') {
    window.appState.probeHealth().catch(() => {});
  }
});

// --- Composer & Input Handling ---
function bindComposer() {
  const sendBtn = document.getElementById('btn-send-query');
  const textarea = document.getElementById('composer-input');
  if (sendBtn && textarea) {
    sendBtn.addEventListener('click', handleSendMessage);
    textarea.addEventListener('keydown', (e) => {
      if (e.key === 'Enter' && !e.shiftKey) {
        e.preventDefault();
        handleSendMessage();
      }
    });

    textarea.addEventListener('input', () => {
      textarea.style.height = 'auto';
      textarea.style.height = Math.min(textarea.scrollHeight, 160) + 'px';
    });
  }
}

function updateComposerButtonState() {
  const slot = document.getElementById('composer-btn-slot');
  if (!slot) return;

  if (window.appState.isThinking) {
    slot.innerHTML = `
      <button class="btn-stop" id="btn-stop-search">
        <svg width="10" height="10" viewBox="0 0 24 24" fill="currentColor">
          <rect x="4" y="4" width="16" height="16" rx="2"/>
        </svg>
        <span>Stop</span>
      </button>
    `;
    const stopBtn = document.getElementById('btn-stop-search');
    if (stopBtn) {
      stopBtn.addEventListener('click', () => {
        window.appState.abortSearch();
      });
    }
  } else {
    slot.innerHTML = `
      <button class="btn-send" id="btn-send-query">
        <svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round">
          <line x1="22" y1="2" x2="11" y2="13"/>
          <polygon points="22 2 15 22 11 13 2 9 22 2"/>
        </svg>
        <span>Synthesize</span>
      </button>
    `;
    const sendBtn = document.getElementById('btn-send-query');
    if (sendBtn) {
      sendBtn.addEventListener('click', handleSendMessage);
    }
  }
}

function updateThemeIcon() {
  const btn = document.getElementById('theme-toggle-btn');
  if (!btn) return;
  const isDark = window.appState.theme === 'dark';
  btn.innerHTML = getIcon(isDark ? 'sun' : 'moon', 15);
}

// --- Master View Render ---
function renderAll() {
  renderConversationThread();
  updateDeskToolbar();
  renderTabs();
  updateTabCounts();
  renderActiveTabContent();
}

function updateTabCounts() {
  const run = window.appState.getSelectedRun();
  const papersCount = run && run.papers ? run.papers.length : 0;
  const graphCount = run && run.graph && run.graph.nodes ? run.graph.nodes.length : 0;

  const pBadge = document.getElementById('badge-papers-count');
  if (pBadge) pBadge.textContent = papersCount;

  const gBadge = document.getElementById('badge-graph-count');
  if (gBadge) gBadge.textContent = graphCount;

  const qCounter = document.getElementById('session-run-counter');
  if (qCounter) {
    const runCount = window.appState.runs.length;
    qCounter.textContent = `${runCount} ${runCount === 1 ? 'query' : 'queries'}`;
  }
}

// --- Left Rail: Conversation Thread Component ---
function renderConversationThread() {
  const container = document.getElementById('conversation-stream');
  if (!container) return;

  const messages = window.appState.messages;
  const isThinking = window.appState.isThinking;

  if (messages.length === 0 && !isThinking) {
    container.innerHTML = `
      <div class="thread-empty">
        <div class="thread-empty-icon">${getIcon('book-open', 20)}</div>
        <h3 class="thread-empty-title">What are you researching?</h3>
        <p class="thread-empty-text">
          Enter a research problem. The agent plans multi-angle queries, retrieves and ranks literature from arXiv, and synthesizes grounded insights with full source traceability.
        </p>
        <div class="thread-workflow-steps">
          <span class="workflow-pill">Retrieve</span>
          <span class="workflow-arrow">→</span>
          <span class="workflow-pill">Rank</span>
          <span class="workflow-arrow">→</span>
          <span class="workflow-pill">Synthesize</span>
          <span class="workflow-arrow">→</span>
          <span class="workflow-pill">Concept Map</span>
        </div>
      </div>
    `;
    return;
  }

  let html = '';
  messages.forEach(msg => {
    if (msg.role === 'user') {
      html += `
        <div class="inquiry-card" id="${msg.id}">
          <div class="inquiry-label">Research Inquiry</div>
          <div class="inquiry-text">${escapeHtml(msg.content)}</div>
        </div>
      `;
    } else {
      html += `
        <article class="synthesis-card" id="${msg.id}">
          <div class="synthesis-head">
            <span class="synthesis-title">Executive Literature Brief</span>
            <span class="synthesis-tag">Grounded in arXiv</span>
          </div>
          ${renderAcademicMarkdown(msg.content)}
          ${renderEvidenceMatrix(msg)}
        </article>
      `;
    }
  });

  if (isThinking) {
    html += `
      <div class="progress-card">
        <div class="spinner-indicator"></div>
        <div class="progress-message">${escapeHtml(window.appState.thinkingLabel)}</div>
      </div>
    `;
  }

  container.innerHTML = html;

  // Bind interactive citation badges to cross-highlight paper cards & graph nodes
  container.querySelectorAll('.cite-badge').forEach(badge => {
    badge.addEventListener('click', (e) => {
      const arxivId = e.currentTarget.getAttribute('data-arxiv');
      crossHighlightLiterature(arxivId);
    });
  });

  // Bind Evidence Accordions
  container.querySelectorAll('.evidence-toggle').forEach(btn => {
    btn.addEventListener('click', (e) => {
      const msgId = e.currentTarget.getAttribute('data-msg-id');
      window.appState.toggleEvidenceExpanded(msgId);
    });
  });

  // Auto-scroll
  container.scrollTop = container.scrollHeight;
}

function renderEvidenceMatrix(msg) {
  if (msg.is_unsourced) {
    return `<div class="mt-2 text-xs text-[var(--text-faint)] italic">Synthesis generated via web search fallback.</div>`;
  }

  if (msg.claims && msg.claims.length > 0) {
    const isExpanded = window.appState.expandedEvidence.has(msg.id);
    return `
      <div class="evidence-matrix">
        <button class="evidence-toggle" data-msg-id="${msg.id}">
          <span>Verified Claims (${msg.claims.length})</span>
          <span class="text-xs">${isExpanded ? 'Hide ▲' : 'Inspect ▼'}</span>
        </button>
        ${isExpanded ? `
          <div class="evidence-list">
            ${msg.claims.map(claim => `
              <div class="evidence-item">
                <div class="evidence-claim">${escapeHtml(claim.claim)}</div>
                <div class="evidence-quote">
                  <button class="cite-badge" data-arxiv="${escapeHtml(claim.arxiv_id)}">[${escapeHtml(claim.arxiv_id)}]</button>
                  <span>"${escapeHtml(claim.supporting_sentence)}"</span>
                </div>
              </div>
            `).join('')}
          </div>
        ` : ''}
      </div>
    `;
  }
  return '';
}

// Cross-Rail Highlighting interaction
function crossHighlightLiterature(arxivId) {
  if (window.appState.activeTab === 'graph') {
    if (graphController) {
      graphController.focusNode(arxivId);
    }
  } else {
    window.appState.setActiveTab('papers');
    window.appState.expandedPapers.add(arxivId);
    renderLiteratureTab();

    setTimeout(() => {
      const targetCard = document.getElementById(`paper-item-${arxivId}`);
      if (targetCard) {
        targetCard.scrollIntoView({ behavior: 'smooth', block: 'center' });
        targetCard.classList.remove('highlight-pulse');
        void targetCard.offsetWidth;
        targetCard.classList.add('highlight-pulse');
      }
    }, 80);
  }
}

// --- Right Rail: Evidence Desk Toolbar ---
function updateDeskToolbar() {
  const runSelect = document.getElementById('desk-run-select');
  if (!runSelect) return;

  const runs = window.appState.runs;
  if (runs.length === 0) {
    runSelect.innerHTML = `<option value="">No active research run</option>`;
    return;
  }

  runSelect.innerHTML = runs.map(r => `
    <option value="${r.id}" ${r.id === window.appState.selectedRunId ? 'selected' : ''}>
      ${escapeHtml(r.query.length > 32 ? r.query.substring(0, 31) + '…' : r.query)}
    </option>
  `).join('');

  runSelect.onchange = (e) => {
    window.appState.selectRun(e.target.value);
  };

  renderSubBar();
}

function renderSubBar() {
  const container = document.getElementById('desk-subbar');
  if (!container) return;

  const run = window.appState.getSelectedRun();

  if (window.appState.activeTab === 'papers') {
    const currentFilter = window.appState.paperFilter;
    const keptCount = run ? run.papers.filter(p => p.status === 'keep').length : 0;
    const maybeCount = run ? run.papers.filter(p => p.status === 'maybe').length : 0;
    const skipCount = run ? run.papers.filter(p => p.status === 'skip').length : 0;
    const totalCount = run && run.papers ? run.papers.length : 0;

    container.innerHTML = `
      <div class="filter-group">
        <button class="filter-chip ${currentFilter === 'all' ? 'active' : ''}" data-filter="all">All (${totalCount})</button>
        <button class="filter-chip ${currentFilter === 'keep' ? 'active' : ''}" data-filter="keep">Keep (${keptCount})</button>
        <button class="filter-chip ${currentFilter === 'maybe' ? 'active' : ''}" data-filter="maybe">Review (${maybeCount})</button>
        <button class="filter-chip ${currentFilter === 'skip' ? 'active' : ''}" data-filter="skip">Discard (${skipCount})</button>
      </div>
      <button class="btn-secondary" id="btn-export-bibtex">
        ${getIcon('download', 12)}
        <span>Export BibTeX</span>
      </button>
    `;

    container.querySelectorAll('.filter-chip').forEach(chip => {
      chip.addEventListener('click', (e) => {
        window.appState.setPaperFilter(e.currentTarget.getAttribute('data-filter'));
      });
    });

    const bibBtn = document.getElementById('btn-export-bibtex');
    if (bibBtn) {
      bibBtn.addEventListener('click', () => {
        const bibtex = window.appState.generateBibtex();
        const blob = new Blob([bibtex], { type: 'text/plain;charset=utf-8' });
        const url = URL.createObjectURL(blob);
        const link = document.createElement('a');
        link.href = url;
        link.download = `rezno-bibliography-${Date.now()}.bib`;
        link.click();
      });
    }
  } else {
    container.innerHTML = '';
  }
}

// --- Tabs Management ---
function renderTabs() {
  const buttons = document.querySelectorAll('.desk-tab-btn');
  buttons.forEach(btn => {
    const tab = btn.getAttribute('data-tab');
    btn.classList.toggle('active', tab === window.appState.activeTab);
  });

  renderActiveTabContent();
  renderSubBar();
}

function renderActiveTabContent() {
  const content = document.getElementById('desk-content');
  if (!content) return;

  const tab = window.appState.activeTab;
  if (tab === 'papers') {
    renderLiteratureTab();
  } else if (tab === 'graph') {
    renderConceptMapTab();
  } else if (tab === 'compare') {
    renderCompareTab();
  }
}

// --- Tab 1: Literature View ---
function renderLiteratureTab() {
  const container = document.getElementById('desk-content');
  if (!container || window.appState.activeTab !== 'papers') return;

  const run = window.appState.getSelectedRun();
  if (!run || !run.papers || run.papers.length === 0) {
    container.innerHTML = `
      <div class="thread-empty">
        <div class="thread-empty-icon">${getIcon('file-text', 20)}</div>
        <h3 class="thread-empty-title">No literature retrieved</h3>
        <p class="thread-empty-text">Run a search inquiry to retrieve candidate research papers.</p>
      </div>
    `;
    return;
  }

  let papers = run.papers;
  const filter = window.appState.paperFilter;
  if (filter !== 'all') {
    papers = papers.filter(p => p.status === filter);
  }

  let html = `<div class="papers-grid">`;

  papers.forEach(paper => {
    const isKept = paper.status === 'keep';
    const isMaybe = paper.status === 'maybe';
    const isSkip = paper.status === 'skip';

    html += `
      <article class="paper-card ${isKept ? 'is-kept' : ''} ${isMaybe ? 'is-maybe' : ''} ${isSkip ? 'is-skip' : ''}" id="paper-item-${paper.arxiv_id}">
        
        <div class="paper-meta-row">
          <div class="paper-tag-group">
            <span class="badge-category">${escapeHtml(paper.primary_category)}</span>
            <span class="text-xs text-[var(--text-faint)]">${escapeHtml(paper.published)}</span>
            <span class="text-xs font-mono text-[var(--text-faint)]">arXiv:${escapeHtml(paper.arxiv_id)}</span>
          </div>
          <span class="badge-score">${(paper.relevance_score * 100).toFixed(0)}% match</span>
        </div>

        <h3 class="paper-title">${escapeHtml(paper.title)}</h3>
        <div class="paper-authors">${escapeHtml(paper.author_line)}</div>
        <p class="paper-abstract">${escapeHtml(paper.summary)}</p>

        <div class="paper-actions-bar">
          <div class="triage-group">
            <button class="btn-triage ${isKept ? 'active-keep' : ''}" data-arxiv="${paper.arxiv_id}" data-triage="keep">Keep</button>
            <button class="btn-triage ${isMaybe ? 'active-maybe' : ''}" data-arxiv="${paper.arxiv_id}" data-triage="maybe">Review</button>
            <button class="btn-triage ${isSkip ? 'active-skip' : ''}" data-arxiv="${paper.arxiv_id}" data-triage="skip">Discard</button>
          </div>

          <div class="paper-links-group">
            <button class="btn-preview btn-open-paper-pdf" data-arxiv="${paper.arxiv_id}">
              ${getIcon('file-text', 12)}
              <span>Read PDF</span>
            </button>
            <a class="paper-ext-link" href="${paper.abs_url}" target="_blank" rel="noopener">Abstract ↗</a>
          </div>
        </div>

        <input 
          class="screening-note-input" 
          type="text" 
          placeholder="Add methodology notes or tags for this paper…" 
          value="${escapeHtml(paper.note || '')}" 
          data-arxiv="${paper.arxiv_id}"
        >
      </article>
    `;
  });

  html += `</div>`;
  container.innerHTML = html;

  // Bind Triage Buttons
  container.querySelectorAll('.btn-triage').forEach(btn => {
    btn.addEventListener('click', (e) => {
      const arxivId = e.currentTarget.getAttribute('data-arxiv');
      const status = e.currentTarget.getAttribute('data-triage');
      window.appState.setPaperStatus(arxivId, status);
      renderLiteratureTab();
      renderSubBar();
    });
  });

  // Bind PDF Reader Trigger
  container.querySelectorAll('.btn-open-paper-pdf').forEach(btn => {
    btn.addEventListener('click', (e) => {
      const arxivId = e.currentTarget.getAttribute('data-arxiv');
      const p = run.papers.find(item => item.arxiv_id === arxivId);
      if (p) window.appState.openPdfViewer(p);
    });
  });

  // Bind Note Input
  container.querySelectorAll('.screening-note-input').forEach(input => {
    input.addEventListener('change', (e) => {
      const arxivId = e.currentTarget.getAttribute('data-arxiv');
      window.appState.setPaperNote(arxivId, e.target.value);
    });
  });
}

// --- Tab 2: Concept Map View ---
function renderConceptMapTab() {
  const container = document.getElementById('desk-content');
  if (!container || window.appState.activeTab !== 'graph') return;

  const run = window.appState.getSelectedRun();
  if (!run || !run.graph || !run.graph.nodes || run.graph.nodes.length === 0) {
    container.innerHTML = `
      <div class="thread-empty">
        <div class="thread-empty-icon">${getIcon('share-2', 20)}</div>
        <h3 class="thread-empty-title">Concept Map Empty</h3>
        <p class="thread-empty-text">Run a search query to generate literature concept relationships.</p>
      </div>
    `;
    return;
  }

  container.innerHTML = `
    <div class="flex flex-col w-full">
      <div class="graph-canvas-frame" id="graph-frame">
        
        <!-- Floating HUD -->
        <div class="graph-hud">
          <button class="hud-btn ${window.appState.layoutMode === 'force' ? 'active' : ''}" id="btn-force-layout">Force</button>
          <button class="hud-btn ${window.appState.layoutMode === 'radial' ? 'active' : ''}" id="btn-radial-layout">Radial</button>
          <span class="hud-separator"></span>
          <button class="hud-icon-btn" id="btn-zoom-in" title="Zoom in">+</button>
          <button class="hud-icon-btn" id="btn-zoom-out" title="Zoom out">-</button>
          <button class="hud-icon-btn" id="btn-zoom-fit" title="Zoom to fit">⊡</button>
          <span class="hud-separator"></span>
          <button class="hud-icon-btn" id="btn-download-map" title="Download image">
            ${getIcon('download', 12)}
          </button>
          <button class="hud-icon-btn" id="btn-fullscreen-map" title="Fullscreen">
            ${getIcon('maximize-2', 12)}
          </button>
        </div>

        <div id="graph-canvas-container" class="canvas-dotgrid" style="width:100%; height:100%;"></div>
      </div>

      <!-- Selected Node Drawer -->
      <div id="graph-node-drawer" style="display:none;"></div>

      <!-- Legend -->
      <div class="graph-legend-bar">
        <span class="legend-swatch">
          <span class="swatch-dot" style="background-color: var(--accent-pine);"></span>
          <span>Papers</span>
        </span>
        <span class="legend-swatch">
          <span class="swatch-dot" style="background-color: #52637a;"></span>
          <span>Concepts</span>
        </span>
        <button class="filter-chip ${window.appState.showMentions ? 'active' : ''}" id="toggle-mentions-link">
          Mentions
        </button>
        <button class="filter-chip ${window.appState.showSimilar ? 'active' : ''}" id="toggle-similar-link">
          Similar
        </button>
      </div>
    </div>
  `;

  setTimeout(() => {
    graphController = new ConceptGraphController('graph-canvas-container');
    graphController.layoutMode = window.appState.layoutMode;
    graphController.showMentions = window.appState.showMentions;
    graphController.showSimilar = window.appState.showSimilar;
    graphController.updateData(run.graph);

    // Bind HUD controls
    const fBtn = document.getElementById('btn-force-layout');
    const rBtn = document.getElementById('btn-radial-layout');
    if (fBtn && rBtn) {
      fBtn.addEventListener('click', () => {
        window.appState.layoutMode = 'force';
        fBtn.classList.add('active');
        rBtn.classList.remove('active');
        graphController.setLayoutMode('force');
      });
      rBtn.addEventListener('click', () => {
        window.appState.layoutMode = 'radial';
        rBtn.classList.add('active');
        fBtn.classList.remove('active');
        graphController.setLayoutMode('radial');
      });
    }

    const zIn = document.getElementById('btn-zoom-in');
    if (zIn) zIn.addEventListener('click', () => graphController.zoomIn());

    const zOut = document.getElementById('btn-zoom-out');
    if (zOut) zOut.addEventListener('click', () => graphController.zoomOut());

    const zFit = document.getElementById('btn-zoom-fit');
    if (zFit) zFit.addEventListener('click', () => graphController.zoomToFit());

    const dl = document.getElementById('btn-download-map');
    if (dl) dl.addEventListener('click', () => graphController.downloadImage());

    const fs = document.getElementById('btn-fullscreen-map');
    if (fs) fs.addEventListener('click', () => graphController.toggleFullscreen());

    // Legend toggles
    const menBtn = document.getElementById('toggle-mentions-link');
    if (menBtn) {
      menBtn.addEventListener('click', () => {
        window.appState.showMentions = !window.appState.showMentions;
        menBtn.classList.toggle('active', window.appState.showMentions);
        graphController.toggleMentions(window.appState.showMentions);
      });
    }

    const simBtn = document.getElementById('toggle-similar-link');
    if (simBtn) {
      simBtn.addEventListener('click', () => {
        window.appState.showSimilar = !window.appState.showSimilar;
        simBtn.classList.toggle('active', window.appState.showSimilar);
        graphController.toggleSimilar(window.appState.showSimilar);
      });
    }
  }, 10);
}

// Global hook for Concept Graph node selection drawer
window.renderNodeSelectionPanel = function(node) {
  const drawer = document.getElementById('graph-node-drawer');
  if (!drawer) return;
  if (!node) {
    drawer.style.display = 'none';
    drawer.innerHTML = '';
    return;
  }

  drawer.style.display = 'flex';
  drawer.className = 'node-drawer';
  drawer.innerHTML = `
    <div class="min-w-0 flex-1">
      <div class="flex items-center gap-2 mb-1">
        <span class="badge-category">${node.type}</span>
        <span class="text-xs text-[var(--text-faint)] font-mono">${node.degree || 0} connections</span>
      </div>
      <div class="font-semibold text-sm mb-2">${escapeHtml(node.label || node.id)}</div>
      ${node.type === 'paper' ? `
        <div class="flex items-center gap-2">
          <button class="btn-preview btn-drawer-pdf">Read PDF in App</button>
          <button class="btn-secondary btn-drawer-jump">View in Literature Desk</button>
          ${node.abs_url ? `<a class="paper-ext-link ml-2" href="${node.abs_url}" target="_blank">Abstract ↗</a>` : ''}
        </div>
      ` : ''}
    </div>
    <button class="btn-icon" id="btn-close-node-drawer" title="Deselect">
      ${getIcon('x', 12)}
    </button>
  `;

  const closeBtn = document.getElementById('btn-close-node-drawer');
  if (closeBtn) {
    closeBtn.addEventListener('click', () => {
      if (graphController) graphController.clearSelection();
    });
  }

  const pdfBtn = drawer.querySelector('.btn-drawer-pdf');
  if (pdfBtn) {
    pdfBtn.addEventListener('click', () => {
      const run = window.appState.getSelectedRun();
      const p = run.papers.find(item => item.arxiv_id === node.id);
      if (p) window.appState.openPdfViewer(p);
    });
  }

  const jumpBtn = drawer.querySelector('.btn-drawer-jump');
  if (jumpBtn) {
    jumpBtn.addEventListener('click', () => {
      crossHighlightLiterature(node.id);
    });
  }
};

// --- In-App PDF Reader Handlers ---
function handleOpenPdf(paper) {
  const overlay = document.getElementById('pdf-drawer-overlay');
  const iframe = document.getElementById('pdf-frame');
  const title = document.getElementById('pdf-drawer-title');
  const idEl = document.getElementById('pdf-drawer-id');
  const anchor = document.getElementById('pdf-external-anchor');

  if (!overlay || !paper) return;

  title.textContent = paper.title;
  idEl.textContent = `arXiv:${paper.arxiv_id}`;
  anchor.href = paper.pdf_url;
  iframe.src = paper.pdf_url;

  overlay.classList.add('is-open');
}

function handleClosePdf() {
  const overlay = document.getElementById('pdf-drawer-overlay');
  const iframe = document.getElementById('pdf-frame');
  if (overlay) overlay.classList.remove('is-open');
  if (iframe) iframe.src = 'about:blank';
}

// --- Tab 3: Compare Runs View ---
function renderCompareTab() {
  const container = document.getElementById('desk-content');
  if (!container || window.appState.activeTab !== 'compare') return;

  const runs = window.appState.runs;
  if (runs.length < 2) {
    container.innerHTML = `
      <div class="thread-empty">
        <div class="thread-empty-icon">${getIcon('share-2', 20)}</div>
        <h3 class="thread-empty-title">Comparative Analysis Needs 2+ Runs</h3>
        <p class="thread-empty-text">Run at least two search queries to cross-examine overlapping literature and concept divergence.</p>
      </div>
    `;
    return;
  }

  const runA = runs.find(r => r.id === window.appState.compareRunA) || runs[0];
  const runB = runs.find(r => r.id === window.appState.compareRunB) || runs[1];

  const papersA = runA.papers || [];
  const papersB = runB.papers || [];
  const mapB = new Map(papersB.map(p => [p.arxiv_id, p]));
  const mapA = new Map(papersA.map(p => [p.arxiv_id, p]));

  const shared = papersA.filter(p => mapB.has(p.arxiv_id));
  const uniqueA = papersA.filter(p => !mapB.has(p.arxiv_id));
  const uniqueB = papersB.filter(p => !mapA.has(p.arxiv_id));

  const conceptsA = (runA.graph && runA.graph.nodes ? runA.graph.nodes : []).filter(n => n.type === 'concept').map(n => n.label || n.id);
  const conceptsB = new Set((runB.graph && runB.graph.nodes ? runB.graph.nodes : []).filter(n => n.type === 'concept').map(n => n.label || n.id));
  const sharedConcepts = conceptsA.filter(c => conceptsB.has(c));

  container.innerHTML = `
    <div class="flex flex-col gap-4">
      <div class="grid grid-cols-2 gap-3">
        <div>
          <label class="block text-xs font-semibold mb-1 text-[var(--text-muted)]">Run A</label>
          <select class="run-select w-full" id="select-comp-a">
            ${runs.map(r => `<option value="${r.id}" ${r.id === runA.id ? 'selected' : ''}>${escapeHtml(r.query)}</option>`).join('')}
          </select>
        </div>
        <div>
          <label class="block text-xs font-semibold mb-1 text-[var(--text-muted)]">Run B</label>
          <select class="run-select w-full" id="select-comp-b">
            ${runs.map(r => `<option value="${r.id}" ${r.id === runB.id ? 'selected' : ''}>${escapeHtml(r.query)}</option>`).join('')}
          </select>
        </div>
      </div>

      <div class="grid grid-cols-3 gap-3">
        <div class="p-3 bg-[var(--bg-surface)] border border-[var(--border-subtle)] rounded-[var(--radius-md)]">
          <div class="text-xs text-[var(--text-faint)]">Co-occurring Papers</div>
          <div class="text-xl font-semibold text-[var(--accent-pine)] mt-1">${shared.length}</div>
        </div>
        <div class="p-3 bg-[var(--bg-surface)] border border-[var(--border-subtle)] rounded-[var(--radius-md)]">
          <div class="text-xs text-[var(--text-faint)]">Unique to Run A</div>
          <div class="text-xl font-semibold mt-1">${uniqueA.length}</div>
        </div>
        <div class="p-3 bg-[var(--bg-surface)] border border-[var(--border-subtle)] rounded-[var(--radius-md)]">
          <div class="text-xs text-[var(--text-faint)]">Unique to Run B</div>
          <div class="text-xl font-semibold mt-1">${uniqueB.length}</div>
        </div>
      </div>

      <div class="p-3 bg-[var(--bg-surface)] border border-[var(--border-subtle)] rounded-[var(--radius-md)]">
        <div class="text-xs font-semibold mb-2 text-[var(--text-muted)]">Converging Concepts (${sharedConcepts.length})</div>
        <div class="flex flex-wrap gap-2">
          ${sharedConcepts.length > 0 ? sharedConcepts.map(c => `
            <span class="workflow-pill">${escapeHtml(c)}</span>
          `).join('') : '<span class="text-xs text-[var(--text-faint)]">No shared concepts detected.</span>'}
        </div>
      </div>
    </div>
  `;

  const sA = document.getElementById('select-comp-a');
  const sB = document.getElementById('select-comp-b');
  if (sA) {
    sA.addEventListener('change', (e) => {
      window.appState.compareRunA = e.target.value;
      renderCompareTab();
    });
  }
  if (sB) {
    sB.addEventListener('change', (e) => {
      window.appState.compareRunB = e.target.value;
      renderCompareTab();
    });
  }
}

// --- Settings Popover Component ---
function bindSettingsPopover() {
  const trigger = document.getElementById('settings-toggle-btn');
  const popover = document.getElementById('settings-popover');
  const backdrop = document.getElementById('popover-backdrop');

  if (!trigger || !popover || !backdrop) return;

  trigger.addEventListener('click', () => {
    const isOpen = popover.classList.contains('is-open');
    if (isOpen) {
      popover.classList.remove('is-open');
      backdrop.classList.remove('is-open');
    } else {
      renderSettingsDialog();
      popover.classList.add('is-open');
      backdrop.classList.add('is-open');
    }
  });

  backdrop.addEventListener('click', () => {
    popover.classList.remove('is-open');
    backdrop.classList.remove('is-open');
  });
}

function renderSettingsDialog() {
  const popover = document.getElementById('settings-popover');
  if (!popover) return;

  popover.innerHTML = `
    <div>
      <h3 class="text-sm font-semibold mb-1">Pipeline & Synthesis Parameters</h3>
      <p class="text-xs text-[var(--text-faint)] mb-4">Adjust candidate retrieval depth and model synthesis scope.</p>

      <div class="setting-row">
        <div class="setting-label-row">
          <span>Candidate papers per query</span>
          <span class="font-mono text-xs text-[var(--accent-pine)]" id="lbl-val-per-query">${window.appState.perQuery}</span>
        </div>
        <input class="slider-input" type="range" min="10" max="150" step="10" value="${window.appState.perQuery}" id="slide-per-query">
        <div class="setting-help">Number of initial arXiv search records fetched per query variant.</div>
      </div>

      <div class="setting-row">
        <div class="setting-label-row">
          <span>Ranking Top-K</span>
          <span class="font-mono text-xs text-[var(--accent-pine)]" id="lbl-val-top-k">${window.appState.topK}</span>
        </div>
        <input class="slider-input" type="range" min="5" max="50" step="5" value="${window.appState.topK}" id="slide-top-k">
        <div class="setting-help">Re-ranked candidates retained for the synthesis prompt.</div>
      </div>

      <div class="setting-row">
        <div class="setting-label-row">
          <span>Query formulations</span>
          <span class="font-mono text-xs text-[var(--accent-pine)]" id="lbl-val-queries">${window.appState.numQueries}</span>
        </div>
        <input class="slider-input" type="range" min="1" max="6" step="1" value="${window.appState.numQueries}" id="slide-queries">
        <div class="setting-help">Parallel LLM search query variations generated.</div>
      </div>

      <button class="btn-secondary w-full justify-center mt-3 text-red-600" id="btn-clear-all-session">
        ${getIcon('trash-2', 12)}
        <span>Clear Session History</span>
      </button>
    </div>
  `;

  // Bind sliders
  const sP = document.getElementById('slide-per-query');
  if (sP) {
    sP.addEventListener('input', (e) => {
      window.appState.perQuery = parseInt(e.target.value, 10);
      document.getElementById('lbl-val-per-query').textContent = window.appState.perQuery;
    });
  }

  const sK = document.getElementById('slide-top-k');
  if (sK) {
    sK.addEventListener('input', (e) => {
      window.appState.topK = parseInt(e.target.value, 10);
      document.getElementById('lbl-val-top-k').textContent = window.appState.topK;
    });
  }

  const sQ = document.getElementById('slide-queries');
  if (sQ) {
    sQ.addEventListener('input', (e) => {
      window.appState.numQueries = parseInt(e.target.value, 10);
      document.getElementById('lbl-val-queries').textContent = window.appState.numQueries;
    });
  }

  const clearBtn = document.getElementById('btn-clear-all-session');
  if (clearBtn) {
    clearBtn.addEventListener('click', () => {
      if (confirm('Clear research session? All queries and screening progress will be reset.')) {
        window.appState.clearSession();
        document.getElementById('settings-popover').classList.remove('is-open');
        document.getElementById('popover-backdrop').classList.remove('is-open');
      }
    });
  }
}

// --- Synthesize Search Workflow Execution ---
function handleSendMessage() {
  const textarea = document.getElementById('composer-input');
  if (!textarea) return;
  const question = textarea.value.trim();
  if (!question || window.appState.isThinking) return;

  textarea.value = '';
  textarea.style.height = 'auto';

  // 1. Add User Question Turn
  const userMsg = {
    id: `msg-${Date.now()}-u`,
    role: 'user',
    content: question,
    intent: 'new_search'
  };
  window.appState.messages.push(userMsg);

  // 2. Set Thinking in-progress State
  window.appState.isThinking = true;
  window.appState.thinkingLabel = "Routing inquiry and formulating search queries…";
  window.appState.progressLog = [];

  updateComposerButtonState();
  renderConversationThread();

  // 3. Delegate to Resilient Hybrid State (Live Backend with automatic Mock fallback)
  window.appState.submitQuery(question, {
    onProgress: (label) => {
      window.appState.thinkingLabel = label;
      renderConversationThread();
    },
    onComplete: () => {
      updateComposerButtonState();
      renderAll();
    },
    onError: () => {
      updateComposerButtonState();
      renderAll();
    }
  }).catch((err) => {
    console.error("Query execution error (guaranteed zero crash):", err);
    window.appState.isThinking = false;
    updateComposerButtonState();
    renderAll();
  });
}

function escapeHtml(str) {
  if (!str) return '';
  return String(str)
    .replace(/&/g, '&amp;')
    .replace(/</g, '&lt;')
    .replace(/>/g, '&gt;')
    .replace(/"/g, '&quot;')
    .replace(/'/g, '&#039;');
}
