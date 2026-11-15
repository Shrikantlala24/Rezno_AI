/**
 * Research Agent — UI Orchestrator
 */

// Global graph controller instance
let graphController = null;

// --- Enhanced Markdown Parser with Interactive Citation Linking ---
function renderMarkdown(md) {
  if (!md) return '';
  let html = md
    // Escape HTML
    .replace(/&/g, '&amp;')
    .replace(/</g, '&lt;')
    .replace(/>/g, '&gt;')
    // Headers
    .replace(/^### (.*$)/gim, '<h3 class="text-base font-semibold mt-3 mb-1">$1</h3>')
    .replace(/^## (.*$)/gim, '<h2 class="text-lg font-semibold mt-4 mb-2">$1</h2>')
    .replace(/^# (.*$)/gim, '<h1 class="text-xl font-bold mt-4 mb-2">$1</h1>')
    // Bold & italic
    .replace(/\*\*(.*?)\*\*/gim, '<strong class="font-semibold">$1</strong>')
    .replace(/\*(.*?)\*/gim, '<em class="italic">$1</em>')
    // Math formulas
    .replace(/\\\[([\s\S]*?)\\\]/g, '<span class="font-mono bg-[var(--secondary)] px-1 rounded">$1</span>')
    .replace(/\\\((.*?)\\\)/g, '<span class="font-mono bg-[var(--secondary)] px-1 rounded">$1</span>')
    // Code blocks & inline code
    .replace(/`([^`]+)`/gim, '<code class="bg-[var(--secondary)] px-1 py-0.5 rounded text-xs border border-[var(--border)]">$1</code>')
    // Unordered lists
    .replace(/^\s*\*\s+(.*$)/gim, '<li class="ml-4 list-disc text-sm my-1">$1</li>')
    .replace(/^\s*-\s+(.*$)/gim, '<li class="ml-4 list-disc text-sm my-1">$1</li>')
    // Paragraphs
    .replace(/\n\n/gim, '</p><p class="mb-2">');

  // Convert arXiv citation patterns like (2106.09685) or [2106.09685] into interactive buttons
  html = html.replace(/\b(\d{4}\.\d{4,5})\b/g, (match) => {
    return `<button class="ra-cite-pill" data-arxiv="${match}">${match} ↗</button>`;
  });

  return `<div class="ra-md text-sm leading-relaxed"><p>${html}</p></div>`;
}

// --- Initialize App on DOM Ready ---
document.addEventListener('DOMContentLoaded', () => {
  // Apply saved theme
  window.appState.setTheme(window.appState.theme);

  // Bind Header Theme Toggle
  const themeBtn = document.getElementById('ra-theme-toggle');
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

  // Bind Tab Bar
  const tabButtons = document.querySelectorAll('.ra-tab-btn');
  tabButtons.forEach(btn => {
    btn.addEventListener('click', (e) => {
      const tab = e.currentTarget.getAttribute('data-tab');
      window.appState.setActiveTab(tab);
    });
  });

  // Bind Composer
  bindComposer();

  // Bind Settings Popover
  bindSettingsPopover();

  // Bind PDF Drawer Close
  const pdfCloseBtn = document.getElementById('ra-pdf-close-btn');
  const pdfOverlay = document.getElementById('ra-pdf-drawer-overlay');
  if (pdfCloseBtn) {
    pdfCloseBtn.addEventListener('click', () => window.appState.closePdfViewer());
  }
  if (pdfOverlay) {
    pdfOverlay.addEventListener('click', (e) => {
      if (e.target === pdfOverlay) window.appState.closePdfViewer();
    });
  }

  // State Subscriptions
  window.appState.subscribe((event, payload) => {
    if (event === 'tab_change') {
      renderTabs();
    } else if (event === 'run_selected' || event === 'run_updated' || event === 'paper_updated') {
      renderRunStrip();
      renderActiveTabContent();
    } else if (event === 'papers_render') {
      renderPapersTab();
      updateTabCounts();
    } else if (event === 'messages_render' || event === 'search_aborted') {
      renderConversationRail();
      updateComposerButtonState();
    } else if (event === 'session_cleared') {
      renderAll();
    } else if (event === 'pdf_viewer_open') {
      handleOpenPdf(payload);
    } else if (event === 'pdf_viewer_close') {
      handleClosePdf();
    }
  });

  // Initial Render
  renderAll();
});

// --- Composer & Input Binding ---
function bindComposer() {
  const sendBtn = document.getElementById('ra-btn-send');
  const textarea = document.getElementById('ra-composer-input');
  if (sendBtn && textarea) {
    sendBtn.addEventListener('click', handleSendMessage);
    textarea.addEventListener('keydown', (e) => {
      if (e.key === 'Enter' && !e.shiftKey) {
        e.preventDefault();
        handleSendMessage();
      }
    });

    // Auto-grow textarea
    textarea.addEventListener('input', () => {
      textarea.style.height = 'auto';
      textarea.style.height = Math.min(textarea.scrollHeight, 180) + 'px';
    });
  }
}

function updateComposerButtonState() {
  const slot = document.getElementById('ra-composer-btn-slot');
  if (!slot) return;

  if (window.appState.isThinking) {
    slot.innerHTML = `
      <button class="ra-btn-stop" id="ra-btn-stop">
        <svg xmlns="http://www.w3.org/2000/svg" width="12" height="12" viewBox="0 0 24 24" fill="currentColor">
          <rect x="4" y="4" width="16" height="16" rx="2"/>
        </svg>
        <span>Stop</span>
      </button>
    `;
    const stopBtn = document.getElementById('ra-btn-stop');
    if (stopBtn) {
      stopBtn.addEventListener('click', () => {
        window.appState.abortSearch();
      });
    }
  } else {
    slot.innerHTML = `
      <button class="ra-btn-send" id="ra-btn-send">
        <svg xmlns="http://www.w3.org/2000/svg" width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
          <path d="m22 2-7 20-4-9-9-4Z"/><path d="M22 2 11 13"/>
        </svg>
        <span>Send</span>
      </button>
    `;
    const sendBtn = document.getElementById('ra-btn-send');
    if (sendBtn) {
      sendBtn.addEventListener('click', handleSendMessage);
    }
  }
}

// --- Theme Icon Update ---
function updateThemeIcon() {
  const btn = document.getElementById('ra-theme-toggle');
  if (!btn) return;
  const isDark = window.appState.theme === 'dark';
  btn.innerHTML = getIcon(isDark ? 'sun' : 'moon', 16);
  btn.title = `Switch to ${isDark ? 'light' : 'dark'} mode`;
}

// --- Master Render ---
function renderAll() {
  renderConversationRail();
  renderRunStrip();
  renderTabs();
  updateTabCounts();
  renderActiveTabContent();
}

function updateTabCounts() {
  const run = window.appState.getSelectedRun();
  const papersCount = run && run.papers ? run.papers.length : 0;
  const graphCount = run && run.graph && run.graph.nodes ? run.graph.nodes.length : 0;

  const pPill = document.getElementById('tab-pill-papers');
  if (pPill) pPill.textContent = papersCount;

  const gPill = document.getElementById('tab-pill-graph');
  if (gPill) gPill.textContent = graphCount;
}

// --- Render Conversation Rail ---
function renderConversationRail() {
  const container = document.getElementById('ra-conversation-scroll');
  if (!container) return;

  const messages = window.appState.messages;
  const isThinking = window.appState.isThinking;

  if (messages.length === 0 && !isThinking) {
    container.innerHTML = `
      <div class="ra-empty-state ra-fade-up">
        <div class="ra-empty-icon-box">
          ${getIcon('search', 20)}
        </div>
        <h2 class="ra-empty-title">What are you researching?</h2>
        <p class="ra-empty-desc">
          Ask a question. The agent generates search variants, retrieves and ranks papers, synthesizes the evidence, and maps the concepts around the result set.
        </p>
        <div class="ra-flow-steps">
          <span class="ra-step-pill">retrieve</span>
          <span class="ra-step-arrow">${getIcon('arrow-right', 12)}</span>
          <span class="ra-step-pill">rank</span>
          <span class="ra-step-arrow">${getIcon('arrow-right', 12)}</span>
          <span class="ra-step-pill">synthesize</span>
          <span class="ra-step-arrow">${getIcon('arrow-right', 12)}</span>
          <span class="ra-step-pill">map</span>
        </div>
      </div>
    `;
    return;
  }

  let html = `<div class="flex flex-col gap-2 pb-2">`;
  messages.forEach(msg => {
    const isUser = msg.role === 'user';
    html += `
      <div class="ra-message-row ra-fade-up" id="${msg.id}">
        <div class="ra-avatar ${isUser ? 'ra-avatar-user' : 'ra-avatar-assistant'}">
          ${getIcon(isUser ? 'user' : 'sparkles', 14)}
        </div>
        <div class="${isUser ? 'min-w-0 flex-1' : 'ra-assistant-body'}">
          ${isUser ? `
            <div class="ra-user-bubble">${escapeHtml(msg.content)}</div>
          ` : `
            <div>
              ${renderMarkdown(msg.content)}
              ${renderMessageFooters(msg)}
            </div>
          `}
        </div>
      </div>
    `;
  });

  // Thinking State Card
  if (isThinking) {
    const isOpen = window.appState.thinkingOpen;
    html += `
      <div class="ra-thinking-card ra-fade-up">
        <div class="ra-avatar ra-avatar-assistant">
          ${getIcon('sparkles', 14)}
        </div>
        <div class="ra-thinking-box">
          <button class="ra-thinking-toggle" id="ra-thinking-toggle-btn">
            <div class="ra-spinner"></div>
            <span class="ra-thinking-label">${escapeHtml(window.appState.thinkingLabel)}</span>
            <span class="ml-auto transition-transform ${isOpen ? 'rotate-90' : ''}" style="color:var(--muted-foreground)">
              ${getIcon('chevron-right', 12)}
            </span>
          </button>
          ${isOpen ? `
            <div class="ra-thinking-log ra-scroll" id="ra-thinking-log">
              ${window.appState.progressLog.map(line => `
                <div class="ra-progress-line">
                  <span class="ra-progress-bullet"></span>
                  <span class="min-w-0 break-words">${escapeHtml(line)}</span>
                </div>
              `).join('')}
            </div>
          ` : ''}
        </div>
      </div>
    `;
  }

  html += `</div>`;
  container.innerHTML = html;

  // Bind interactive citation badges to cross-highlight right rail
  container.querySelectorAll('.ra-cite-pill').forEach(pill => {
    pill.addEventListener('click', (e) => {
      const arxivId = e.currentTarget.getAttribute('data-arxiv');
      crossHighlightPaper(arxivId);
    });
  });

  // Re-bind evidence accordions
  container.querySelectorAll('.ra-evidence-toggle').forEach(btn => {
    btn.addEventListener('click', (e) => {
      const msgId = e.currentTarget.getAttribute('data-msg-id');
      window.appState.toggleEvidenceExpanded(msgId);
    });
  });

  // Re-bind thinking toggle
  const thinkingToggleBtn = document.getElementById('ra-thinking-toggle-btn');
  if (thinkingToggleBtn) {
    thinkingToggleBtn.addEventListener('click', () => {
      window.appState.thinkingOpen = !window.appState.thinkingOpen;
      renderConversationRail();
    });
  }

  // Auto-scroll
  container.scrollTop = container.scrollHeight;
}

// Cross-Rail Highlighting interaction
function crossHighlightPaper(arxivId) {
  if (window.appState.activeTab === 'graph') {
    if (graphController) {
      graphController.focusNode(arxivId);
    }
  } else {
    // Switch to Papers tab
    window.appState.setActiveTab('papers');
    window.appState.expandedPapers.add(arxivId);
    renderPapersTab();

    setTimeout(() => {
      const targetCard = document.getElementById(`paper-card-${arxivId}`);
      if (targetCard) {
        targetCard.scrollIntoView({ behavior: 'smooth', block: 'center' });
        targetCard.classList.remove('highlight-pulse');
        void targetCard.offsetWidth; // trigger reflow
        targetCard.classList.add('highlight-pulse');
      }
    }, 100);
  }
}

function renderMessageFooters(msg) {
  if (msg.is_unsourced) {
    return `
      <p class="ra-unsourced-note">
        ${msg.is_fallback ? 'LIVE WEB SEARCH · ROUTER FALLBACK · NOT FROM RETRIEVED PAPERS' : 'LIVE WEB SEARCH · NOT FROM RETRIEVED PAPERS'}
      </p>
    `;
  }

  if (msg.claims && msg.claims.length > 0) {
    const isExpanded = window.appState.expandedEvidence.has(msg.id);
    return `
      <div class="ra-evidence-block">
        <button class="ra-evidence-toggle" data-msg-id="${msg.id}">
          <span class="transition-transform duration-150 ${isExpanded ? 'rotate-90' : ''}">
            ${getIcon('chevron-right', 12)}
          </span>
          <span>Evidence · ${msg.claims.length} supporting ${msg.claims.length === 1 ? 'claim' : 'claims'}</span>
        </button>
        ${isExpanded ? `
          <div class="ra-claims-list">
            ${msg.claims.map(claim => `
              <div class="ra-claim-row">
                <p class="ra-claim-text">${escapeHtml(claim.claim)}</p>
                <p class="ra-claim-meta">
                  <button class="ra-cite-pill" data-arxiv="${escapeHtml(claim.arxiv_id)}">${escapeHtml(claim.arxiv_id)} ↗</button>
                  <span> · </span>
                  <span class="italic">“${escapeHtml(claim.supporting_sentence)}”</span>
                </p>
              </div>
            `).join('')}
          </div>
        ` : ''}
      </div>
    `;
  }
  return '';
}

// --- Render Unified Command Strip ---
function renderRunStrip() {
  const pill = document.getElementById('ra-strip-run-info');
  if (!pill) return;

  const run = window.appState.getSelectedRun();
  if (run) {
    pill.innerHTML = `
      <span>Run: <strong>${escapeHtml(run.query.substring(0, 26))}…</strong></span>
      <span>·</span>
      <span>${escapeHtml(run.timestamp)}</span>
    `;
  } else {
    pill.innerHTML = `<span>No active run</span>`;
  }

  renderSubBar();
}

// --- Render Sub-Bar (Filters & Run Selector) ---
function renderSubBar() {
  const container = document.getElementById('ra-sub-bar');
  if (!container) return;

  const run = window.appState.getSelectedRun();
  const runs = window.appState.runs;

  if (window.appState.activeTab === 'papers') {
    const currentFilter = window.appState.paperFilter;
    const keptCount = run ? run.papers.filter(p => p.status === 'keep').length : 0;
    const maybeCount = run ? run.papers.filter(p => p.status === 'maybe').length : 0;
    const skipCount = run ? run.papers.filter(p => p.status === 'skip').length : 0;

    container.innerHTML = `
      <div class="ra-filter-chips">
        <button class="ra-filter-chip ${currentFilter === 'all' ? 'active' : ''}" data-filter="all">All (${run ? run.papers.length : 0})</button>
        <button class="ra-filter-chip ${currentFilter === 'keep' ? 'active' : ''}" data-filter="keep">Kept (${keptCount})</button>
        <button class="ra-filter-chip ${currentFilter === 'maybe' ? 'active' : ''}" data-filter="maybe">Maybe (${maybeCount})</button>
        <button class="ra-filter-chip ${currentFilter === 'skip' ? 'active' : ''}" data-filter="skip">Skipped (${skipCount})</button>
      </div>
      <div class="flex items-center gap-2">
        ${runs.length > 1 ? `
          <select class="ra-select text-xs h-7 max-w-[200px]" id="ra-quick-run-select">
            ${runs.map(r => `
              <option value="${r.id}" ${r.id === window.appState.selectedRunId ? 'selected' : ''}>
                ${escapeHtml(r.query)}
              </option>
            `).join('')}
          </select>
        ` : ''}
        <button class="ra-btn-outline h-7 text-xs px-2" id="ra-btn-download-bibtex">
          ${getIcon('download', 12)}
          <span>BibTeX</span>
        </button>
      </div>
    `;

    // Bind filters
    container.querySelectorAll('.ra-filter-chip').forEach(chip => {
      chip.addEventListener('click', (e) => {
        window.appState.setPaperFilter(e.currentTarget.getAttribute('data-filter'));
      });
    });

    // Quick run select
    const qSelect = document.getElementById('ra-quick-run-select');
    if (qSelect) {
      qSelect.addEventListener('change', (e) => {
        window.appState.selectRun(e.target.value);
      });
    }

    // Download BibTeX button
    const bibBtn = document.getElementById('ra-btn-download-bibtex');
    if (bibBtn) {
      bibBtn.addEventListener('click', () => {
        const bibtex = window.appState.generateBibtex();
        const blob = new Blob([bibtex], { type: 'text/plain;charset=utf-8' });
        const url = URL.createObjectURL(blob);
        const link = document.createElement('a');
        link.href = url;
        link.download = `references-${Date.now()}.bib`;
        link.click();
      });
    }
  } else {
    // For Graph or Compare tab, clear sub-bar or show minimal switcher
    container.innerHTML = runs.length > 1 ? `
      <div class="flex items-center gap-2 ml-auto">
        <span class="text-xs text-[var(--muted-foreground)]">Run:</span>
        <select class="ra-select text-xs h-7 max-w-[240px]" id="ra-quick-run-select">
          ${runs.map(r => `
            <option value="${r.id}" ${r.id === window.appState.selectedRunId ? 'selected' : ''}>
              ${escapeHtml(r.query)}
            </option>
          `).join('')}
        </select>
      </div>
    ` : '';

    const qSelect = document.getElementById('ra-quick-run-select');
    if (qSelect) {
      qSelect.addEventListener('change', (e) => {
        window.appState.selectRun(e.target.value);
      });
    }
  }
}

// --- Render Tabs Navigation ---
function renderTabs() {
  const buttons = document.querySelectorAll('.ra-tab-btn');
  buttons.forEach(btn => {
    const tab = btn.getAttribute('data-tab');
    if (tab === window.appState.activeTab) {
      btn.classList.add('active');
      if (!btn.querySelector('.ra-tab-indicator')) {
        const indicator = document.createElement('span');
        indicator.className = 'ra-tab-indicator';
        btn.appendChild(indicator);
      }
    } else {
      btn.classList.remove('active');
      const indicator = btn.querySelector('.ra-tab-indicator');
      if (indicator) indicator.remove();
    }
  });

  renderActiveTabContent();
  renderSubBar();
}

function renderActiveTabContent() {
  const contentArea = document.getElementById('ra-tab-content');
  if (!contentArea) return;

  const activeTab = window.appState.activeTab;
  if (activeTab === 'papers') {
    renderPapersTab();
  } else if (activeTab === 'graph') {
    renderGraphTab();
  } else if (activeTab === 'compare') {
    renderCompareTab();
  }
}

// --- Papers Tab ---
function renderPapersTab() {
  const container = document.getElementById('ra-tab-content');
  if (!container || window.appState.activeTab !== 'papers') return;

  const run = window.appState.getSelectedRun();
  if (!run || !run.papers || run.papers.length === 0) {
    container.innerHTML = `
      <div class="ra-dotgrid flex min-h-[260px] flex-col items-center justify-center rounded-[var(--radius-xl)] border border-[var(--border)] bg-[var(--card)] p-8 text-center">
        <div class="ra-empty-icon-box">${getIcon('file-text', 18)}</div>
        <p class="mb-2 text-lg tracking-[-0.02em] text-[var(--foreground)]">No papers in this workspace yet.</p>
        <p class="mx-auto max-w-[380px] text-sm leading-relaxed text-[var(--muted-foreground)]">
          Run a research question to populate the ranked evidence set.
        </p>
      </div>
    `;
    return;
  }

  // Filter papers
  let papers = run.papers;
  const filter = window.appState.paperFilter;
  if (filter !== 'all') {
    papers = papers.filter(p => p.status === filter);
  }

  let html = `<div class="ra-papers-list">`;

  papers.forEach((paper, index) => {
    const isExpanded = window.appState.expandedPapers.has(paper.arxiv_id);
    const cardClass = `card-${paper.status}`;
    html += `
      <div class="ra-paper-card ${cardClass}" id="paper-card-${paper.arxiv_id}">
        <div class="flex items-center justify-between pr-2">
          <button class="ra-paper-header-btn flex-1" data-arxiv-id="${paper.arxiv_id}">
            <span class="transition-transform duration-150 ${isExpanded ? 'rotate-90' : ''}">
              ${getIcon('chevron-right', 12)}
            </span>
            <span class="text-xs uppercase tracking-[0.09em] text-[var(--muted-foreground)]">${index + 1}</span>
            <span class="min-w-0 flex-1 truncate text-left text-sm font-medium text-[var(--foreground)]">${escapeHtml(paper.title)}</span>
          </button>
          
          <!-- Quick Screening Actions right on collapsed row -->
          <div class="flex items-center gap-1 shrink-0">
            <button class="ra-filter-chip text-xs ${paper.status === 'keep' ? 'active' : ''}" data-arxiv-id="${paper.arxiv_id}" data-action-status="keep">Keep</button>
            <button class="ra-filter-chip text-xs ${paper.status === 'maybe' ? 'active' : ''}" data-arxiv-id="${paper.arxiv_id}" data-action-status="maybe">Maybe</button>
            <button class="ra-filter-chip text-xs ${paper.status === 'skip' ? 'active' : ''}" data-arxiv-id="${paper.arxiv_id}" data-action-status="skip">Skip</button>
          </div>
        </div>
        ${isExpanded ? renderPaperBody(paper, index) : ''}
      </div>
    `;
  });

  html += `</div>`;
  container.innerHTML = html;

  // Bind card header toggles
  container.querySelectorAll('.ra-paper-header-btn').forEach(btn => {
    btn.addEventListener('click', (e) => {
      const arxivId = e.currentTarget.getAttribute('data-arxiv-id');
      window.appState.togglePaperExpanded(arxivId);
    });
  });

  // Bind quick screening buttons on row
  container.querySelectorAll('[data-action-status]').forEach(btn => {
    btn.addEventListener('click', (e) => {
      e.stopPropagation();
      const arxivId = e.currentTarget.getAttribute('data-arxiv-id');
      const status = e.currentTarget.getAttribute('data-action-status');
      window.appState.setPaperStatus(arxivId, status);
      renderPapersTab();
      renderSubBar();
    });
  });

  // Bind full screening buttons in body
  container.querySelectorAll('.ra-btn-screening').forEach(btn => {
    btn.addEventListener('click', (e) => {
      const arxivId = e.currentTarget.getAttribute('data-arxiv-id');
      const status = e.currentTarget.getAttribute('data-status');
      window.appState.setPaperStatus(arxivId, status);
      renderPapersTab();
      renderSubBar();
    });
  });

  // Bind In-App PDF Reader triggers
  container.querySelectorAll('.ra-btn-open-pdf').forEach(btn => {
    btn.addEventListener('click', (e) => {
      const arxivId = e.currentTarget.getAttribute('data-arxiv-id');
      const p = run.papers.find(item => item.arxiv_id === arxivId);
      if (p) window.appState.openPdfViewer(p);
    });
  });

  // Bind note inputs
  container.querySelectorAll('.ra-paper-input').forEach(input => {
    input.addEventListener('change', (e) => {
      const arxivId = e.currentTarget.getAttribute('data-arxiv-id');
      window.appState.setPaperNote(arxivId, e.target.value);
    });
  });

  // Citation Chaining toggles
  container.querySelectorAll('.ra-citations-toggle').forEach(btn => {
    btn.addEventListener('click', (e) => {
      const arxivId = e.currentTarget.getAttribute('data-arxiv-id');
      window.appState.toggleCitationChaining(arxivId);
    });
  });

  container.querySelectorAll('.ra-btn-fetch-citations').forEach(btn => {
    btn.addEventListener('click', (e) => {
      const arxivId = e.currentTarget.getAttribute('data-arxiv-id');
      window.appState.fetchCitations(arxivId);
    });
  });

  container.querySelectorAll('.ra-btn-add-citation').forEach(btn => {
    btn.addEventListener('click', (e) => {
      const sourceArxivId = e.currentTarget.getAttribute('data-source-id');
      const kind = e.currentTarget.getAttribute('data-kind');
      const idx = parseInt(e.currentTarget.getAttribute('data-index'), 10);
      const data = window.appState.citationsByPaper[sourceArxivId];
      if (data) {
        const list = kind === 'citing' ? data.citations : data.references;
        if (list && list[idx]) {
          window.appState.addCitationPaper(sourceArxivId, list[idx]);
        }
      }
    });
  });
}

function renderPaperBody(paper, index) {
  const isCitationsExpanded = window.appState.expandedCitations.has(paper.arxiv_id);
  const isFetching = window.appState.fetchingCitations.has(paper.arxiv_id);
  const citationData = window.appState.citationsByPaper[paper.arxiv_id];

  return `
    <div class="ra-paper-body">
      <div class="ra-paper-meta-card">
        <div class="flex items-start justify-between gap-3">
          <div class="min-w-0 flex-1">
            <p class="text-xs uppercase tracking-[0.09em] text-[var(--muted-foreground)] mb-1">
              ${index + 1} · ${escapeHtml(paper.primary_category)} · ${escapeHtml(paper.published)}
            </p>
            <h3 class="ra-paper-title">${escapeHtml(paper.title)}</h3>
            <p class="text-xs text-[var(--muted-foreground)] font-mono">${escapeHtml(paper.arxiv_id)}</p>
            <p class="text-xs text-[var(--muted-foreground)] mt-1">${escapeHtml(paper.author_line)}</p>
          </div>
          <span class="text-sm font-semibold text-[var(--foreground)] shrink-0">${paper.relevance_score ? paper.relevance_score.toFixed(3) : '0.000'}</span>
        </div>
        
        <!-- Actions & Links -->
        <div class="flex items-center justify-between border-t border-[var(--border)] pt-2 mt-3">
          <div class="flex items-center gap-3">
            <button class="ra-btn-outline h-7 text-xs px-2 ra-btn-open-pdf" data-arxiv-id="${paper.arxiv_id}">
              ${getIcon('file-text', 12)}
              <span>Read in App</span>
            </button>
            <a class="ra-paper-link" href="${paper.abs_url}" target="_blank">Abstract ↗</a>
          </div>
          <span class="ra-screening-badge ra-badge-${paper.status}">
            ${paper.status}
          </span>
        </div>
      </div>

      <p class="ra-paper-summary">${escapeHtml(paper.summary)}</p>

      <div class="ra-screening-row">
        <div class="flex flex-wrap items-center gap-2">
          <button class="ra-btn-pill ra-btn-screening ${paper.status === 'keep' ? 'active' : ''}" data-arxiv-id="${paper.arxiv_id}" data-status="keep">Keep</button>
          <button class="ra-btn-pill ra-btn-screening ${paper.status === 'maybe' ? 'active' : ''}" data-arxiv-id="${paper.arxiv_id}" data-status="maybe">Maybe</button>
          <button class="ra-btn-pill ra-btn-screening ${paper.status === 'skip' ? 'active' : ''}" data-arxiv-id="${paper.arxiv_id}" data-status="skip">Skip</button>
        </div>
      </div>

      <input class="ra-paper-input" type="text" placeholder="Add a short screening note…" value="${escapeHtml(paper.note || '')}" data-arxiv-id="${paper.arxiv_id}">

      <!-- Citation Chaining Panel -->
      <div class="ra-citations-panel">
        <button class="ra-citations-toggle" data-arxiv-id="${paper.arxiv_id}">
          <span class="transition-transform duration-150 ${isCitationsExpanded ? 'rotate-90' : ''}">
            ${getIcon('chevron-right', 12)}
          </span>
          <span>Citation chaining</span>
        </button>
        ${isCitationsExpanded ? `
          <div class="p-3">
            <button class="ra-btn-outline ra-btn-fetch-citations text-xs h-8" data-arxiv-id="${paper.arxiv_id}" ${isFetching ? 'disabled' : ''}>
              ${isFetching ? '<div class="ra-spinner"></div>' : getIcon('link', 14)}
              <span>${isFetching ? 'Fetching citation data…' : 'Fetch references and citing papers'}</span>
            </button>
            ${!citationData ? `
              <p class="mt-2 text-xs text-[var(--muted-foreground)]">
                Pull references and forward citations from Semantic Scholar.
              </p>
            ` : renderCitationLists(paper.arxiv_id, citationData)}
          </div>
        ` : ''}
      </div>
    </div>
  `;
}

function renderCitationLists(sourceId, data) {
  return `
    <div class="mt-3 flex flex-col gap-3">
      <!-- References -->
      <div class="rounded-[var(--radius-md)] border border-[var(--border)] bg-[var(--card)] overflow-hidden">
        <p class="px-3 py-2 text-xs uppercase tracking-[0.09em] text-[var(--muted-foreground)]">
          References · ${data.references ? data.references.length : 0}
        </p>
        <div class="border-t border-[var(--border)]">
          ${(data.references || []).map((ref, idx) => `
            <div class="flex items-start justify-between gap-2 p-2 border-t border-[var(--border)] first:border-t-0">
              <div class="min-w-0 flex-1">
                <p class="text-sm font-medium leading-snug">${escapeHtml(ref.title)}</p>
                <p class="text-xs text-[var(--muted-foreground)]">${ref.year} · ${escapeHtml(ref.authors)}</p>
              </div>
              ${ref.arxiv_id ? `
                <button class="ra-btn-pill ra-btn-add-citation text-xs h-7 px-3" data-source-id="${sourceId}" data-kind="reference" data-index="${idx}">Add</button>
              ` : '<span class="text-xs text-[var(--muted-foreground)]">no arxiv id</span>'}
            </div>
          `).join('')}
        </div>
      </div>

      <!-- Citing Papers -->
      <div class="rounded-[var(--radius-md)] border border-[var(--border)] bg-[var(--card)] overflow-hidden">
        <p class="px-3 py-2 text-xs uppercase tracking-[0.09em] text-[var(--muted-foreground)]">
          Citing papers · ${data.citations ? data.citations.length : 0}
        </p>
        <div class="border-t border-[var(--border)]">
          ${(data.citations || []).map((cite, idx) => `
            <div class="flex items-start justify-between gap-2 p-2 border-t border-[var(--border)] first:border-t-0">
              <div class="min-w-0 flex-1">
                <p class="text-sm font-medium leading-snug">${escapeHtml(cite.title)}</p>
                <p class="text-xs text-[var(--muted-foreground)]">${cite.year} · ${escapeHtml(cite.authors)}</p>
              </div>
              ${cite.arxiv_id ? `
                <button class="ra-btn-pill ra-btn-add-citation text-xs h-7 px-3" data-source-id="${sourceId}" data-kind="citing" data-index="${idx}">Add</button>
              ` : '<span class="text-xs text-[var(--muted-foreground)]">no arxiv id</span>'}
            </div>
          `).join('')}
        </div>
      </div>
    </div>
  `;
}

// --- Concept Graph Tab with Floating HUD ---
function renderGraphTab() {
  const container = document.getElementById('ra-tab-content');
  if (!container || window.appState.activeTab !== 'graph') return;

  const run = window.appState.getSelectedRun();
  if (!run || !run.graph || !run.graph.nodes || run.graph.nodes.length === 0) {
    container.innerHTML = `
      <div class="ra-dotgrid flex min-h-[260px] flex-col items-center justify-center rounded-[var(--radius-xl)] border border-dashed border-[var(--border)] p-8 text-center">
        <div class="ra-empty-icon-box">${getIcon('share-2', 18)}</div>
        <p class="mb-2 text-lg tracking-[-0.02em] text-[var(--foreground)]">The concept graph appears after a search.</p>
        <p class="mx-auto max-w-[380px] text-sm leading-relaxed text-[var(--muted-foreground)]">
          Paper and concept nodes are mapped once a run completes.
        </p>
      </div>
    `;
    return;
  }

  container.innerHTML = `
    <div class="flex flex-col w-full">
      <!-- Canvas Wrap with Floating HUD -->
      <div class="ra-canvas-wrap" id="ra-canvas-wrap">
        
        <!-- Floating HUD -->
        <div class="ra-graph-hud">
          <button class="ra-hud-btn ${window.appState.layoutMode === 'force' ? 'active' : ''}" id="btn-layout-force">Force</button>
          <button class="ra-hud-btn ${window.appState.layoutMode === 'radial' ? 'active' : ''}" id="btn-layout-radial">Radial</button>
          <span class="w-[1px] h-3 bg-[var(--border)]"></span>
          <button class="ra-hud-icon-btn" id="btn-graph-zoom-in" title="Zoom In">+</button>
          <button class="ra-hud-icon-btn" id="btn-graph-zoom-out" title="Zoom Out">-</button>
          <button class="ra-hud-icon-btn" id="btn-graph-fit" title="Zoom to Fit">⊡</button>
          <span class="w-[1px] h-3 bg-[var(--border)]"></span>
          <button class="ra-hud-icon-btn" id="btn-graph-download" title="Download Image">
            ${getIcon('download', 12)}
          </button>
          <button class="ra-hud-icon-btn" id="btn-graph-fullscreen" title="Fullscreen">
            ${getIcon('maximize-2', 12)}
          </button>
        </div>

        <div id="ra-graph-canvas" class="ra-canvas-container"></div>
      </div>

      <!-- Selected Node Drawer -->
      <div id="ra-node-selection-drawer" style="display:none;"></div>

      <!-- Legend -->
      <div class="flex items-center gap-3 pt-3">
        <div class="flex items-center gap-1 text-xs text-[var(--muted-foreground)] uppercase tracking-[0.08em]">
          <span class="w-[10px] h-[10px] rounded-full bg-[var(--graph-paper)]"></span>
          <span>Papers</span>
        </div>
        <div class="flex items-center gap-1 text-xs text-[var(--muted-foreground)] uppercase tracking-[0.08em]">
          <span class="w-[8px] h-[8px] rounded-full bg-[var(--graph-concept)]"></span>
          <span>Concepts</span>
        </div>
        <button class="ra-filter-chip text-xs ${window.appState.showMentions ? 'active' : ''}" id="chip-toggle-mentions">
          Mentions
        </button>
        <button class="ra-filter-chip text-xs ${window.appState.showSimilar ? 'active' : ''}" id="chip-toggle-similar">
          Similar
        </button>
      </div>
    </div>
  `;

  // Attach ForceGraph
  setTimeout(() => {
    graphController = new ConceptGraphController('ra-graph-canvas');
    graphController.layoutMode = window.appState.layoutMode;
    graphController.showMentions = window.appState.showMentions;
    graphController.showSimilar = window.appState.showSimilar;
    graphController.updateData(run.graph);

    // Bind HUD buttons
    const btnForce = document.getElementById('btn-layout-force');
    const btnRadial = document.getElementById('btn-layout-radial');
    if (btnForce && btnRadial) {
      btnForce.addEventListener('click', () => {
        window.appState.layoutMode = 'force';
        btnForce.classList.add('active');
        btnRadial.classList.remove('active');
        graphController.setLayoutMode('force');
      });
      btnRadial.addEventListener('click', () => {
        window.appState.layoutMode = 'radial';
        btnRadial.classList.add('active');
        btnForce.classList.remove('active');
        graphController.setLayoutMode('radial');
      });
    }

    const zoomInBtn = document.getElementById('btn-graph-zoom-in');
    if (zoomInBtn) zoomInBtn.addEventListener('click', () => graphController.zoomIn());

    const zoomOutBtn = document.getElementById('btn-graph-zoom-out');
    if (zoomOutBtn) zoomOutBtn.addEventListener('click', () => graphController.zoomOut());

    const fitBtn = document.getElementById('btn-graph-fit');
    if (fitBtn) fitBtn.addEventListener('click', () => graphController.zoomToFit());

    const dlBtn = document.getElementById('btn-graph-download');
    if (dlBtn) dlBtn.addEventListener('click', () => graphController.downloadImage());

    const fsBtn = document.getElementById('btn-graph-fullscreen');
    if (fsBtn) fsBtn.addEventListener('click', () => graphController.toggleFullscreen());

    // Legend chips
    const mentionsChip = document.getElementById('chip-toggle-mentions');
    if (mentionsChip) {
      mentionsChip.addEventListener('click', () => {
        window.appState.showMentions = !window.appState.showMentions;
        mentionsChip.classList.toggle('active', window.appState.showMentions);
        graphController.toggleMentions(window.appState.showMentions);
      });
    }
    const similarChip = document.getElementById('chip-toggle-similar');
    if (similarChip) {
      similarChip.addEventListener('click', () => {
        window.appState.showSimilar = !window.appState.showSimilar;
        similarChip.classList.toggle('active', window.appState.showSimilar);
        graphController.toggleSimilar(window.appState.showSimilar);
      });
    }
  }, 10);
}

// Global hook for graph node selection drawer
window.renderNodeSelectionPanel = function(node) {
  const drawer = document.getElementById('ra-node-selection-drawer');
  if (!drawer) return;
  if (!node) {
    drawer.style.display = 'none';
    drawer.innerHTML = '';
    return;
  }

  drawer.style.display = 'block';
  drawer.className = 'ra-selection-panel ra-fade-up';
  drawer.innerHTML = `
    <div class="min-w-0 flex-1">
      <p class="text-xs uppercase tracking-[0.09em] text-[var(--muted-foreground)]">
        ${node.type} node · ${node.degree || 0} connections
      </p>
      <p class="mt-1 break-words text-sm font-semibold leading-snug text-[var(--foreground)]">
        ${escapeHtml(node.label || node.id)}
      </p>
      ${node.type === 'paper' ? `
        <div class="mt-2 flex flex-wrap items-center gap-3">
          <button class="ra-btn-outline h-7 text-xs px-2 ra-btn-open-pdf-modal">
            ${getIcon('file-text', 12)}
            <span>Read in App</span>
          </button>
          <button class="ra-btn-outline h-7 text-xs px-2" id="ra-btn-view-in-papers">
            View in Papers Tab
          </button>
          ${node.abs_url ? `<a class="text-xs text-[var(--link)] hover:underline" href="${node.abs_url}" target="_blank">Abstract ↗</a>` : ''}
        </div>
      ` : ''}
    </div>
    <button class="ra-icon-btn h-7 w-7" id="ra-btn-clear-selection" title="Clear selection">
      ${getIcon('x', 14)}
    </button>
  `;

  const closeBtn = document.getElementById('ra-btn-clear-selection');
  if (closeBtn) {
    closeBtn.addEventListener('click', () => {
      if (graphController) graphController.clearSelection();
    });
  }

  const readModalBtn = drawer.querySelector('.ra-btn-open-pdf-modal');
  if (readModalBtn) {
    readModalBtn.addEventListener('click', () => {
      const run = window.appState.getSelectedRun();
      const p = run.papers.find(item => item.arxiv_id === node.id);
      if (p) window.appState.openPdfViewer(p);
    });
  }

  const viewPapersBtn = document.getElementById('ra-btn-view-in-papers');
  if (viewPapersBtn) {
    viewPapersBtn.addEventListener('click', () => {
      crossHighlightPaper(node.id);
    });
  }
};

// --- In-App PDF Reader Open / Close Handlers ---
function handleOpenPdf(paper) {
  const overlay = document.getElementById('ra-pdf-drawer-overlay');
  const iframe = document.getElementById('ra-pdf-iframe');
  const titleEl = document.getElementById('ra-pdf-drawer-title');
  const idEl = document.getElementById('ra-pdf-drawer-id');
  const extLink = document.getElementById('ra-pdf-external-link');

  if (!overlay || !paper) return;

  titleEl.textContent = paper.title;
  idEl.textContent = `arXiv:${paper.arxiv_id}`;
  extLink.href = paper.pdf_url;
  iframe.src = paper.pdf_url;

  overlay.classList.add('open');
}

function handleClosePdf() {
  const overlay = document.getElementById('ra-pdf-drawer-overlay');
  const iframe = document.getElementById('ra-pdf-iframe');
  if (overlay) overlay.classList.remove('open');
  if (iframe) iframe.src = 'about:blank';
}

// --- Compare Tab ---
function renderCompareTab() {
  const container = document.getElementById('ra-tab-content');
  if (!container || window.appState.activeTab !== 'compare') return;

  const runs = window.appState.runs;
  if (runs.length < 2) {
    container.innerHTML = `
      <div class="ra-dotgrid flex min-h-[260px] flex-col items-center justify-center rounded-[var(--radius-xl)] border border-dashed border-[var(--border)] p-8 text-center">
        <div class="ra-empty-icon-box">${getIcon('columns-3', 18)}</div>
        <p class="mb-2 text-lg tracking-[-0.02em] text-[var(--foreground)]">Nothing to compare yet.</p>
        <p class="mx-auto max-w-[380px] text-sm leading-relaxed text-[var(--muted-foreground)]">
          Run at least two searches to compare result sets, shared papers, and shared concepts.
        </p>
      </div>
    `;
    return;
  }

  const runA = runs.find(r => r.id === window.appState.compareRunA) || runs[0];
  const runB = runs.find(r => r.id === window.appState.compareRunB) || runs[1];

  const papersA = runA.papers || [];
  const papersB = runB.papers || [];

  const mapA = new Map(papersA.map(p => [p.arxiv_id, p]));
  const mapB = new Map(papersB.map(p => [p.arxiv_id, p]));

  const sharedPapers = papersA.filter(p => mapB.has(p.arxiv_id));
  const onlyA = papersA.filter(p => !mapB.has(p.arxiv_id));
  const onlyB = papersB.filter(p => !mapA.has(p.arxiv_id));

  const conceptsA = (runA.graph && runA.graph.nodes ? runA.graph.nodes : []).filter(n => n.type === 'concept').map(n => n.label || n.id);
  const conceptsB = new Set((runB.graph && runB.graph.nodes ? runB.graph.nodes : []).filter(n => n.type === 'concept').map(n => n.label || n.id));
  const sharedConcepts = conceptsA.filter(c => conceptsB.has(c));

  container.innerHTML = `
    <div class="flex flex-col w-full gap-4">
      <!-- Run Selectors -->
      <div class="ra-compare-grid">
        <div class="w-full">
          <label class="mb-2 block text-xs uppercase tracking-[0.1em] text-[var(--muted-foreground)]">Run A</label>
          <select class="ra-select w-full h-8" id="ra-select-compare-a">
            ${runs.map(r => `
              <option value="${r.id}" ${r.id === runA.id ? 'selected' : ''}>${escapeHtml(r.query)}</option>
            `).join('')}
          </select>
          <p class="mt-2 text-xs text-[var(--muted-foreground)] truncate">${escapeHtml(runA.query)}</p>
        </div>
        <div class="w-full">
          <label class="mb-2 block text-xs uppercase tracking-[0.1em] text-[var(--muted-foreground)]">Run B</label>
          <select class="ra-select w-full h-8" id="ra-select-compare-b">
            ${runs.map(r => `
              <option value="${r.id}" ${r.id === runB.id ? 'selected' : ''}>${escapeHtml(r.query)}</option>
            `).join('')}
          </select>
          <p class="mt-2 text-xs text-[var(--muted-foreground)] truncate">${escapeHtml(runB.query)}</p>
        </div>
      </div>

      <!-- Metrics -->
      <div class="ra-metrics-grid">
        <div class="ra-metric-tile">
          <p class="text-xs uppercase tracking-[0.1em] text-[var(--muted-foreground)]">Shared papers</p>
          <p class="ra-metric-value text-[var(--graph-paper)]">${sharedPapers.length}</p>
        </div>
        <div class="ra-metric-tile">
          <p class="text-xs uppercase tracking-[0.1em] text-[var(--muted-foreground)]">Unique to A</p>
          <p class="ra-metric-value text-[var(--foreground)]">${onlyA.length}</p>
        </div>
        <div class="ra-metric-tile">
          <p class="text-xs uppercase tracking-[0.1em] text-[var(--muted-foreground)]">Unique to B</p>
          <p class="ra-metric-value text-[var(--foreground)]">${onlyB.length}</p>
        </div>
      </div>

      <!-- Overlap Paper Lists -->
      <div class="rounded-[var(--radius-lg)] border border-[var(--border)] bg-[var(--secondary)] overflow-hidden">
        <p class="px-3 py-2 text-xs uppercase tracking-[0.09em] text-[var(--muted-foreground)]">Papers in both</p>
        <div class="border-t border-[var(--border)]">
          ${sharedPapers.length > 0 ? sharedPapers.map(p => `
            <div class="flex items-start gap-3 p-3 border-t border-[var(--border)] first:border-t-0">
              <span class="shrink-0 text-xs text-[var(--muted-foreground)] font-mono">${escapeHtml(p.arxiv_id)}</span>
              <span class="text-sm text-[var(--foreground)] font-medium leading-snug">${escapeHtml(p.title)}</span>
            </div>
          `).join('') : '<p class="p-3 text-xs text-[var(--muted-foreground)]">No papers overlap between these runs.</p>'}
        </div>
      </div>

      <!-- Unique Lists -->
      <div class="grid grid-cols-1 min-[900px]:grid-cols-2 gap-3">
        <div class="rounded-[var(--radius-lg)] border border-[var(--border)] bg-[var(--secondary)] overflow-hidden">
          <p class="px-3 py-2 text-xs uppercase tracking-[0.09em] text-[var(--muted-foreground)]">Unique to run A</p>
          <div class="border-t border-[var(--border)]">
            ${onlyA.length > 0 ? onlyA.map(p => `
              <div class="p-2 border-t border-[var(--border)] first:border-t-0 text-sm truncate">${escapeHtml(p.title)}</div>
            `).join('') : '<p class="p-3 text-xs text-[var(--muted-foreground)]">Every paper in run A also appears in run B.</p>'}
          </div>
        </div>
        <div class="rounded-[var(--radius-lg)] border border-[var(--border)] bg-[var(--secondary)] overflow-hidden">
          <p class="px-3 py-2 text-xs uppercase tracking-[0.09em] text-[var(--muted-foreground)]">Unique to run B</p>
          <div class="border-t border-[var(--border)]">
            ${onlyB.length > 0 ? onlyB.map(p => `
              <div class="p-2 border-t border-[var(--border)] first:border-t-0 text-sm truncate">${escapeHtml(p.title)}</div>
            `).join('') : '<p class="p-3 text-xs text-[var(--muted-foreground)]">Every paper in run B also appears in run A.</p>'}
          </div>
        </div>
      </div>

      <!-- Shared Concepts -->
      <div class="rounded-[var(--radius-lg)] border border-[var(--border)] bg-[var(--card)] p-3">
        <p class="text-xs uppercase tracking-[0.09em] text-[var(--muted-foreground)] mb-2">
          Shared concepts · ${sharedConcepts.length}
        </p>
        ${sharedConcepts.length > 0 ? `
          <div class="ra-concept-tags">
            ${sharedConcepts.map(c => `
              <span class="ra-concept-tag">${escapeHtml(c)}</span>
            `).join('')}
          </div>
        ` : '<p class="text-xs text-[var(--muted-foreground)]">These two runs share no concepts.</p>'}
      </div>
    </div>
  `;

  const selectA = document.getElementById('ra-select-compare-a');
  const selectB = document.getElementById('ra-select-compare-b');
  if (selectA) {
    selectA.addEventListener('change', (e) => {
      window.appState.compareRunA = e.target.value;
      renderCompareTab();
    });
  }
  if (selectB) {
    selectB.addEventListener('change', (e) => {
      window.appState.compareRunB = e.target.value;
      renderCompareTab();
    });
  }
}

// --- Settings Popover Bindings ---
function bindSettingsPopover() {
  const triggerBtn = document.getElementById('ra-settings-trigger');
  const popover = document.getElementById('ra-settings-popover');
  const overlay = document.getElementById('ra-settings-overlay');

  if (!triggerBtn || !popover || !overlay) return;

  triggerBtn.addEventListener('click', () => {
    const isOpen = popover.classList.contains('open');
    if (isOpen) {
      popover.classList.remove('open');
      overlay.classList.remove('open');
    } else {
      updateSettingsPopoverContent();
      popover.classList.add('open');
      overlay.classList.add('open');
    }
  });

  overlay.addEventListener('click', () => {
    popover.classList.remove('open');
    overlay.classList.remove('open');
  });
}

function updateSettingsPopoverContent() {
  const popover = document.getElementById('ra-settings-popover');
  if (!popover) return;

  const run = window.appState.getSelectedRun();
  const citationIds = (run && run.synthesis && run.synthesis.citations) ? run.synthesis.citations : [];

  popover.innerHTML = `
    <div>
      <p class="text-sm font-medium tracking-[-0.01em] text-[var(--foreground)]">Settings</p>
      <p class="mt-1 text-xs uppercase tracking-[0.09em] text-[var(--muted-foreground)]">Research controls · response · session</p>

      <!-- Pipeline Controls -->
      <p class="mb-2 mt-4 text-xs uppercase tracking-[0.11em] text-[var(--muted-foreground)]">Pipeline controls</p>
      
      <!-- Slider: Papers per query -->
      <div class="mb-4">
        <div class="mb-2 flex items-center justify-between text-sm">
          <span>Papers per query</span>
          <span class="text-[var(--muted-foreground)]" id="lbl-per-query">${window.appState.perQuery}</span>
        </div>
        <input class="ra-slider" type="range" min="10" max="150" step="10" value="${window.appState.perQuery}" id="slider-per-query">
        <p class="mt-1 text-xs text-[var(--muted-foreground)]">Candidate retrieval depth for every generated query.</p>
      </div>

      <!-- Slider: Ranking top-k -->
      <div class="mb-4">
        <div class="mb-2 flex items-center justify-between text-sm">
          <span>Ranking top-k</span>
          <span class="text-[var(--muted-foreground)]" id="lbl-top-k">${window.appState.topK}</span>
        </div>
        <input class="ra-slider" type="range" min="5" max="50" step="5" value="${window.appState.topK}" id="slider-top-k">
        <p class="mt-1 text-xs text-[var(--muted-foreground)]">Number of papers retained after ranking.</p>
      </div>

      <!-- Slider: Query variants -->
      <div class="mb-4">
        <div class="mb-2 flex items-center justify-between text-sm">
          <span>Query variants</span>
          <span class="text-[var(--muted-foreground)]" id="lbl-num-queries">${window.appState.numQueries}</span>
        </div>
        <input class="ra-slider" type="range" min="1" max="6" step="1" value="${window.appState.numQueries}" id="slider-num-queries">
        <p class="mt-1 text-xs text-[var(--muted-foreground)]">Parallel formulations used to widen retrieval.</p>
      </div>

      <!-- Response Length -->
      <p class="mb-2 mt-4 text-xs uppercase tracking-[0.11em] text-[var(--muted-foreground)]">Response</p>
      <div class="flex items-center gap-1 rounded-full border border-[var(--border)] bg-[var(--secondary)] p-[3px]">
        <button class="ra-hud-btn flex-1 ${window.appState.responseLength === 'brief' ? 'active' : ''}" data-len="brief">Brief</button>
        <button class="ra-hud-btn flex-1 ${window.appState.responseLength === 'standard' ? 'active' : ''}" data-len="standard">Standard</button>
        <button class="ra-hud-btn flex-1 ${window.appState.responseLength === 'detailed' ? 'active' : ''}" data-len="detailed">Detailed</button>
      </div>
      <p class="mt-2 text-xs text-[var(--muted-foreground)]" id="lbl-response-hint">
        ${window.appState.responseLength === 'brief' ? '1–2 sentences · tight evidence.' : (window.appState.responseLength === 'detailed' ? '5–8 sentences · expanded evidence.' : '3–5 sentences · balanced evidence.')}
      </p>

      <!-- Session Section -->
      <p class="mb-2 mt-4 text-xs uppercase tracking-[0.11em] text-[var(--muted-foreground)]">Session</p>
      <div class="grid grid-cols-2 gap-2">
        <div class="ra-metric-tile">
          <p class="text-xs uppercase tracking-[0.1em] text-[var(--muted-foreground)]">Messages</p>
          <p class="mt-1 text-xl font-medium">${window.appState.messages.length}</p>
        </div>
        <div class="ra-metric-tile">
          <p class="text-xs uppercase tracking-[0.1em] text-[var(--muted-foreground)]">Runs</p>
          <p class="mt-1 text-xl font-medium">${window.appState.runs.length}</p>
        </div>
      </div>

      ${citationIds.length > 0 ? `
        <div class="mt-3 overflow-hidden rounded-[var(--radius-lg)] border border-[var(--border)] bg-[var(--secondary)]">
          <button class="flex w-full items-center gap-2 px-3 py-2 text-xs uppercase tracking-[0.08em] text-[var(--muted-foreground)] hover:bg-[var(--accent)]" id="btn-toggle-citation-ids">
            <span class="transition-transform duration-150 ${window.appState.showCitationIds ? 'rotate-90' : ''}">
              ${getIcon('chevron-right', 12)}
            </span>
            <span>Citation IDs · ${citationIds.length}</span>
          </button>
          ${window.appState.showCitationIds ? `
            <div class="max-h-[140px] overflow-y-auto border-t border-[var(--border)] p-2 text-xs font-mono">
              ${citationIds.map(id => `<div>${escapeHtml(id)}</div>`).join('')}
            </div>
          ` : ''}
        </div>
      ` : ''}

      <button class="mt-4 flex h-9 w-full items-center justify-center gap-2 rounded-[var(--radius-md)] border border-[var(--border)] bg-[var(--card)] text-sm hover:bg-[var(--accent)]" id="btn-clear-session">
        ${getIcon('trash-2', 14)}
        <span>Clear session</span>
      </button>
    </div>
  `;

  // Bind sliders
  const sPerQuery = document.getElementById('slider-per-query');
  if (sPerQuery) {
    sPerQuery.addEventListener('input', (e) => {
      window.appState.perQuery = parseInt(e.target.value, 10);
      document.getElementById('lbl-per-query').textContent = window.appState.perQuery;
    });
  }
  const sTopK = document.getElementById('slider-top-k');
  if (sTopK) {
    sTopK.addEventListener('input', (e) => {
      window.appState.topK = parseInt(e.target.value, 10);
      document.getElementById('lbl-top-k').textContent = window.appState.topK;
    });
  }
  const sNumQueries = document.getElementById('slider-num-queries');
  if (sNumQueries) {
    sNumQueries.addEventListener('input', (e) => {
      window.appState.numQueries = parseInt(e.target.value, 10);
      document.getElementById('lbl-num-queries').textContent = window.appState.numQueries;
    });
  }

  // Response buttons
  popover.querySelectorAll('[data-len]').forEach(btn => {
    btn.addEventListener('click', (e) => {
      window.appState.responseLength = e.currentTarget.getAttribute('data-len');
      updateSettingsPopoverContent();
    });
  });

  // Toggle citation IDs
  const cBtn = document.getElementById('btn-toggle-citation-ids');
  if (cBtn) {
    cBtn.addEventListener('click', () => {
      window.appState.showCitationIds = !window.appState.showCitationIds;
      updateSettingsPopoverContent();
    });
  }

  // Clear session
  const clearBtn = document.getElementById('btn-clear-session');
  if (clearBtn) {
    clearBtn.addEventListener('click', () => {
      if (confirm('Clear entire research session? All turns and runs will be reset.')) {
        window.appState.clearSession();
        document.getElementById('ra-settings-popover').classList.remove('open');
        document.getElementById('ra-settings-overlay').classList.remove('open');
      }
    });
  }
}

// --- Submit User Question Workflow ---
function handleSendMessage() {
  const textarea = document.getElementById('ra-composer-input');
  if (!textarea) return;
  const question = textarea.value.trim();
  if (!question || window.appState.isThinking) return;

  textarea.value = '';
  textarea.style.height = 'auto';

  // 1. Append User Message
  const userMsg = {
    id: `msg-${Date.now()}-u`,
    role: 'user',
    content: question,
    intent: 'new_search'
  };
  window.appState.messages.push(userMsg);

  // 2. Set Thinking in-progress state
  window.appState.isThinking = true;
  window.appState.thinkingLabel = "Thinking…";
  window.appState.thinkingOpen = true;
  window.appState.progressLog = [];

  updateComposerButtonState();
  renderConversationRail();

  // Progress Pipeline Simulation
  const steps = [
    { label: "Route: new research search", delay: 400 },
    { label: `Planning ${window.appState.numQueries} arXiv query variations`, delay: 900 },
    { label: `Querying arXiv API (depth: ${window.appState.perQuery} per query)`, delay: 1700 },
    { label: `Ranking candidate papers (top-k: ${window.appState.topK})`, delay: 2500 },
    { label: "Synthesizing grounded answer and claims", delay: 3300 },
    { label: "Constructing multi-relational concept graph", delay: 4000 }
  ];

  steps.forEach(step => {
    setTimeout(() => {
      if (!window.appState.isThinking) return;
      window.appState.progressLog.push(step.label);
      window.appState.thinkingLabel = step.label;
      renderConversationRail();
    }, step.delay);
  });

  // Final completion
  window.appState.activeSearchTimer = setTimeout(() => {
    if (!window.appState.isThinking) return;

    const runId = `run-${Date.now()}`;
    const newRun = {
      id: runId,
      query: question,
      queries: [
        question,
        `${question} survey and empirical analysis`,
        `${question} benchmarks and state of the art`
      ],
      candidate_count: 58,
      status: "ok",
      search_error: null,
      timestamp: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' }),
      synthesis: {
        summary: `Recent investigations into **${question}** reveal distinct algorithmic trade-offs between computational overhead and empirical accuracy. Cross-referencing retrieved literature highlights two pivotal strategies: first, localized sparse approximations limit memory footprint without compromising representation fidelity (2401.01234); second, hybrid training formulations generalize effectively across standard academic benchmarks (2312.05678).`,
        citations: ["2401.01234", "2312.05678"],
        claims: [
          {
            claim: `Empirical evaluations on ${question} establish consistent improvements over classical baselines.`,
            arxiv_id: "2401.01234",
            supporting_sentence: "Experimental validation demonstrates that our proposed mechanism yields significant gains across all standardized test datasets."
          },
          {
            claim: "Sparse representations reduce memory scaling requirements.",
            arxiv_id: "2312.05678",
            supporting_sentence: "Memory consumption is reduced by substituting dense tensor products with bounded sparse matrices."
          }
        ]
      },
      papers: [
        {
          arxiv_id: "2401.01234",
          title: `Empirical Foundations and Architectural Paradigms for ${question}`,
          authors: ["Elena Rostova", "Marcus Vance", "David Chen"],
          author_line: "Elena Rostova, Marcus Vance, David Chen",
          summary: `A systematic investigation of modern approaches to ${question}, benchmarking execution latency, convergence rates, and parameter scalability.`,
          published: "2024-01-08",
          pdf_url: "https://arxiv.org/pdf/2401.01234.pdf",
          abs_url: "https://arxiv.org/abs/2401.01234",
          primary_category: "cs.AI",
          relevance_score: 0.958,
          status: "keep",
          note: "Directly answers the prompt."
        },
        {
          arxiv_id: "2312.05678",
          title: `Sparse Formulations and Memory Efficiency in Modern Neural Architectures`,
          authors: ["Siddharth Patel", "Chloe Martin"],
          author_line: "Siddharth Patel, Chloe Martin",
          summary: "Introduces bounded sparse tensor operators that accelerate inference and training across modern accelerators.",
          published: "2023-12-14",
          pdf_url: "https://arxiv.org/pdf/2312.05678.pdf",
          abs_url: "https://arxiv.org/abs/2312.05678",
          primary_category: "cs.LG",
          relevance_score: 0.884,
          status: "unreviewed",
          note: ""
        }
      ],
      graph: {
        nodes: [
          { id: "2401.01234", label: `Architectural Paradigms (2401.01234)`, type: "paper", pdf_url: "https://arxiv.org/pdf/2401.01234.pdf", abs_url: "https://arxiv.org/abs/2401.01234" },
          { id: "2312.05678", label: "Sparse Formulations (2312.05678)", type: "paper", pdf_url: "https://arxiv.org/pdf/2312.05678.pdf", abs_url: "https://arxiv.org/abs/2312.05678" },
          { id: "c-core", label: question.substring(0, 30), type: "concept" },
          { id: "c-benchmarks", label: "Standardized Benchmarks", type: "concept" },
          { id: "c-sparse", label: "Sparse Tensor Operators", type: "concept" }
        ],
        edges: [
          { source: "2401.01234", target: "c-core", type: "MENTIONS" },
          { source: "2401.01234", target: "c-benchmarks", type: "MENTIONS" },
          { source: "2312.05678", target: "c-sparse", type: "MENTIONS" },
          { source: "c-sparse", target: "c-core", type: "SIMILAR_TO" },
          { source: "2401.01234", target: "2312.05678", type: "SIMILAR_TO" }
        ]
      }
    };

    window.appState.runs.unshift(newRun);
    if (window.appState.runs.length > 10) window.appState.runs.pop();
    window.appState.selectedRunId = runId;

    const assistantMsg = {
      id: `msg-${Date.now()}-a`,
      role: 'assistant',
      content: newRun.synthesis.summary,
      search_run_id: runId,
      is_unsourced: false,
      is_fallback: false,
      claims: newRun.synthesis.claims
    };
    window.appState.messages.push(assistantMsg);
    window.appState.expandedEvidence.add(assistantMsg.id);

    window.appState.isThinking = false;
    updateComposerButtonState();
    renderAll();
  }, 4600);
}

// Escape helper
function escapeHtml(str) {
  if (!str) return '';
  return String(str)
    .replace(/&/g, '&amp;')
    .replace(/</g, '&lt;')
    .replace(/>/g, '&gt;')
    .replace(/"/g, '&quot;')
    .replace(/'/g, '&#039;');
}
