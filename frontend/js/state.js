/**
 * State store for Research Agent UI
 * Implements Resilient Hybrid Mode (Live API & Graceful Mock Mode fallback)
 */
class ResearchAgentState {
  constructor() {
    this.theme = (typeof localStorage !== 'undefined' && localStorage.getItem('ra-theme')) || 'light';
    this.runs = typeof MOCK_RUNS !== 'undefined' ? JSON.parse(JSON.stringify(MOCK_RUNS)) : [];
    this.selectedRunId = this.runs.length > 0 ? this.runs[0].id : null;
    this.messages = typeof MOCK_MESSAGES !== 'undefined' ? JSON.parse(JSON.stringify(MOCK_MESSAGES)) : [];
    this.isThinking = false;
    this.thinkingLabel = "Thinking…";
    this.thinkingOpen = true;
    this.progressLog = [];
    this.activeTab = 'papers'; // 'papers' | 'graph' | 'compare'
    this.paperFilter = 'all';  // 'all' | 'keep' | 'maybe' | 'skip'
    
    // In-app PDF Viewer state
    this.activePdfPaper = null;

    // UI Expanders
    this.expandedPapers = new Set(["2106.09685"]);
    this.expandedEvidence = new Set(["msg-02"]);
    this.expandedCitations = new Set();
    this.fetchingCitations = new Set();
    this.citationsByPaper = {};

    // Pipeline settings
    this.perQuery = 40;
    this.topK = 15;
    this.numQueries = 3;
    this.responseLength = 'standard'; // 'brief' | 'standard' | 'detailed'
    this.showCitationIds = false;

    // Graph UI State
    this.selectedNodeId = "";
    this.layoutMode = 'force'; // 'force' | 'radial'
    this.showMentions = true;
    this.showSimilar = true;

    // Compare tab state
    this.compareRunA = this.runs[0] ? this.runs[0].id : "";
    this.compareRunB = this.runs[1] ? this.runs[1].id : "";

    this.activeSearchTimer = null;
    this.activeAbortController = null;
    this.listeners = [];

    // Resilient Hybrid Mode (Backend Live API vs Mock Mode)
    this.isBackendLive = false;
    this.backendMode = 'mock'; // 'live' | 'mock'
    this.connectionStatus = '● arXiv connected (Mock Mode)';
    this.healthEndpoint = '/api/health';
    this.synthesizeEndpoint = '/api/synthesize';
    this.searchEndpoint = '/api/search';
    this.lastHealthCheck = null;
  }

  subscribe(listener) {
    this.listeners.push(listener);
    return () => {
      this.listeners = this.listeners.filter(l => l !== listener);
    };
  }

  notify(event, payload) {
    for (const listener of this.listeners) {
      listener(event, payload);
    }
  }

  // --- Theme ---
  setTheme(theme) {
    this.theme = theme;
    if (typeof localStorage !== 'undefined') {
      localStorage.setItem('ra-theme', theme);
    }
    if (typeof document !== 'undefined') {
      if (theme === 'dark') {
        document.documentElement.classList.add('dark');
      } else {
        document.documentElement.classList.remove('dark');
      }
    }
    this.notify('theme_change', theme);
  }

  toggleTheme() {
    this.setTheme(this.theme === 'dark' ? 'light' : 'dark');
  }

  // --- Runs & Selection ---
  getSelectedRun() {
    return this.runs.find(r => r.id === this.selectedRunId) || null;
  }

  selectRun(runId) {
    this.selectedRunId = runId;
    this.selectedNodeId = "";
    this.notify('run_selected', runId);
  }

  // --- Screening ---
  setPaperStatus(arxivId, status) {
    const run = this.getSelectedRun();
    if (!run) return;
    const paper = run.papers.find(p => p.arxiv_id === arxivId);
    if (paper) {
      paper.status = status;
      this.notify('paper_updated', paper);
    }
  }

  setPaperNote(arxivId, note) {
    const run = this.getSelectedRun();
    if (!run) return;
    const paper = run.papers.find(p => p.arxiv_id === arxivId);
    if (paper) {
      paper.note = note;
    }
  }

  togglePaperExpanded(arxivId) {
    if (this.expandedPapers.has(arxivId)) {
      this.expandedPapers.delete(arxivId);
    } else {
      this.expandedPapers.add(arxivId);
    }
    this.notify('papers_render');
  }

  toggleEvidenceExpanded(msgId) {
    if (this.expandedEvidence.has(msgId)) {
      this.expandedEvidence.delete(msgId);
    } else {
      this.expandedEvidence.add(msgId);
    }
    this.notify('messages_render');
  }

  toggleCitationChaining(arxivId) {
    if (this.expandedCitations.has(arxivId)) {
      this.expandedCitations.delete(arxivId);
    } else {
      this.expandedCitations.add(arxivId);
    }
    this.notify('papers_render');
  }

  // --- Filter ---
  setPaperFilter(filter) {
    this.paperFilter = filter;
    this.notify('papers_render');
  }

  // --- In-App PDF Reader ---
  openPdfViewer(paper) {
    this.activePdfPaper = paper;
    this.notify('pdf_viewer_open', paper);
  }

  closePdfViewer() {
    this.activePdfPaper = null;
    this.notify('pdf_viewer_close');
  }

  // --- Citation Chaining Fetch ---
  async fetchCitations(arxivId) {
    this.fetchingCitations.add(arxivId);
    this.notify('papers_render');

    if (this.isBackendLive && typeof fetch === 'function') {
      try {
        const res = await fetch(`/api/citations/${encodeURIComponent(arxivId)}`);
        if (res && res.ok) {
          const data = await res.json();
          this.citationsByPaper[arxivId] = {
            references: (data.references || []).map(r => ({ ...r, kind: 'reference' })),
            citations: (data.citations || []).map(c => ({ ...c, kind: 'citing' }))
          };
          this.fetchingCitations.delete(arxivId);
          this.notify('papers_render');
          return;
        }
      } catch (_) {
        // Fall back to mock citations
      }
    }

    setTimeout(() => {
      this.fetchingCitations.delete(arxivId);
      this.citationsByPaper[arxivId] = {
        references: [
          { title: "Layer Normalization", year: 2016, authors: "Ba, Kiros, Hinton", arxiv_id: "1607.06450", kind: "reference" },
          { title: "Deep Residual Learning for Image Recognition", year: 2016, authors: "He, Zhang, Ren, Sun", arxiv_id: "1512.03385", kind: "reference" }
        ],
        citations: [
          { title: "QLoRA: Efficient Finetuning of Quantized LLMs", year: 2023, authors: "Dettmers, Pagnoni, Holtzman, Zettlemoyer", arxiv_id: "2305.14314", kind: "citing" },
          { title: "Scaling Laws for Neural Language Models", year: 2020, authors: "Kaplan, McCandlish, Henighan et al.", arxiv_id: "2001.08361", kind: "citing" }
        ]
      };
      this.notify('papers_render');
    }, 1200);
  }

  addCitationPaper(sourceArxivId, entry) {
    const run = this.getSelectedRun();
    if (!run || !entry.arxiv_id) return;
    if (run.papers.some(p => p.arxiv_id === entry.arxiv_id)) return;

    const newPaper = {
      arxiv_id: entry.arxiv_id,
      title: entry.title,
      authors: [entry.authors],
      author_line: entry.authors,
      summary: `Discovered via citation chaining from ${sourceArxivId}.`,
      published: entry.year ? `${entry.year}-01-01` : "2024",
      pdf_url: `https://arxiv.org/pdf/${entry.arxiv_id}.pdf`,
      abs_url: `https://arxiv.org/abs/${entry.arxiv_id}`,
      primary_category: "cs.LG",
      relevance_score: 0.850,
      status: "unreviewed",
      note: `Added from citations of ${sourceArxivId}`
    };

    run.papers.push(newPaper);
    if (run.graph) {
      run.graph.nodes.push({
        id: entry.arxiv_id,
        label: `${entry.title} (${entry.arxiv_id})`,
        type: "paper",
        pdf_url: newPaper.pdf_url,
        abs_url: newPaper.abs_url
      });
      run.graph.edges.push({
        source: entry.arxiv_id,
        target: sourceArxivId,
        type: entry.kind === "citing" ? "MENTIONS" : "SIMILAR_TO"
      });
    }

    this.expandedPapers.add(entry.arxiv_id);
    this.notify('run_updated');
  }

  // --- Tabs ---
  setActiveTab(tab) {
    this.activeTab = tab;
    this.notify('tab_change', tab);
  }

  // --- Session ---
  clearSession() {
    this.runs = [];
    this.selectedRunId = null;
    this.messages = [];
    this.selectedNodeId = "";
    this.isThinking = false;
    this.progressLog = [];
    this.notify('session_cleared');
  }

  abortSearch() {
    if (this.activeAbortController) {
      try { this.activeAbortController.abort(); } catch (_) {}
      this.activeAbortController = null;
    }
    if (this.activeSearchTimer) {
      clearTimeout(this.activeSearchTimer);
      this.activeSearchTimer = null;
    }
    this.isThinking = false;
    this.progressLog.push("Search cancelled by user.");
    this.notify('search_aborted');
  }

  // --- BibTeX generation ---
  generateBibtex() {
    const run = this.getSelectedRun();
    if (!run || !run.papers) return "";
    return run.papers.map(p => {
      const firstAuthor = p.authors[0] ? p.authors[0].split(" ").pop().toLowerCase() : "author";
      const year = p.published ? p.published.substring(0, 4) : "2024";
      const tag = `${firstAuthor}${year}${p.arxiv_id.replace(/[^a-zA-Z0-9]/g, '')}`;
      return `@article{${tag},\n  title={${p.title}},\n  author={${p.authors.join(' and ')}},\n  journal={arXiv preprint arXiv:${p.arxiv_id}},\n  year={${year}}\n}`;
    }).join("\n\n");
  }

  // --- Resilient Hybrid Mode & Backend Connectivity ---
  async probeHealth(timeoutMs = 1500) {
    if (typeof fetch !== 'function') {
      this.isBackendLive = false;
      this.backendMode = 'mock';
      this.connectionStatus = '● arXiv connected (Mock Mode)';
      this.updateConnectionStatusUI();
      return false;
    }

    let controller = null;
    let timeoutId = null;
    if (typeof AbortController !== 'undefined') {
      controller = new AbortController();
      timeoutId = setTimeout(() => {
        try { controller.abort(); } catch (_) {}
      }, timeoutMs);
    }

    try {
      const response = await fetch(this.healthEndpoint, {
        method: 'GET',
        headers: { 'Accept': 'application/json' },
        signal: controller ? controller.signal : undefined
      });
      if (timeoutId) clearTimeout(timeoutId);

      if (response && (response.ok || response.status === 200)) {
        this.isBackendLive = true;
        this.backendMode = 'live';
        this.connectionStatus = '● arXiv connected (Live API)';
      } else {
        this.isBackendLive = false;
        this.backendMode = 'mock';
        this.connectionStatus = '● arXiv connected (Mock Mode)';
      }
    } catch (_) {
      if (timeoutId) clearTimeout(timeoutId);
      this.isBackendLive = false;
      this.backendMode = 'mock';
      this.connectionStatus = '● arXiv connected (Mock Mode)';
    }

    this.lastHealthCheck = Date.now();
    this.updateConnectionStatusUI();
    this.notify('backend_status_changed', {
      isLive: this.isBackendLive,
      mode: this.backendMode,
      status: this.connectionStatus
    });
    return this.isBackendLive;
  }

  checkBackendHealth(timeoutMs = 1500) {
    return this.probeHealth(timeoutMs);
  }

  checkHealth(timeoutMs = 1500) {
    return this.probeHealth(timeoutMs);
  }

  getConnectionStatus() {
    return this.connectionStatus;
  }

  isLive() {
    return this.isBackendLive;
  }

  getBackendMode() {
    return this.backendMode;
  }

  updateConnectionStatusUI() {
    if (typeof document === 'undefined') return;

    const textEl = document.getElementById('header-status-text') || 
                   document.getElementById('connection-status-text') || 
                   document.querySelector('.status-indicator span:last-child');
    const dotEl = document.getElementById('header-status-dot') || 
                  document.querySelector('.status-dot');
    const indicatorEl = document.getElementById('header-status-indicator') || 
                        document.querySelector('.status-indicator');

    const label = this.isBackendLive ? 'arXiv connected (Live API)' : 'arXiv connected (Mock Mode)';
    if (textEl) {
      textEl.textContent = label;
    }
    if (dotEl) {
      if (this.isBackendLive) {
        dotEl.style.backgroundColor = 'var(--accent-pine, #0284c7)';
        dotEl.classList.remove('status-dot-mock');
        dotEl.classList.add('status-dot-live');
      } else {
        dotEl.style.backgroundColor = 'var(--status-draft, #d97706)';
        dotEl.classList.remove('status-dot-live');
        dotEl.classList.add('status-dot-mock');
      }
    }
    if (indicatorEl) {
      indicatorEl.setAttribute('data-status', this.connectionStatus);
      indicatorEl.setAttribute('title', this.connectionStatus);
      indicatorEl.setAttribute('aria-label', this.connectionStatus);
    }
  }

  // --- Hybrid Query Execution & Synthesis ---
  async submitQuery(question, options = {}) {
    if (!question || typeof question !== 'string') return null;
    const trimmed = question.trim();
    if (!trimmed) return null;

    const onProgress = typeof options.onProgress === 'function' ? options.onProgress : () => {};
    const onComplete = typeof options.onComplete === 'function' ? options.onComplete : () => {};

    // Record user message if not already added by caller
    const lastMsg = this.messages[this.messages.length - 1];
    if (!lastMsg || lastMsg.role !== 'user' || lastMsg.content !== trimmed) {
      this.messages.push({
        id: `msg-${Date.now()}-u`,
        role: 'user',
        content: trimmed,
        intent: 'new_search'
      });
    }

    // Set Thinking state
    this.isThinking = true;
    this.thinkingLabel = "Routing inquiry and formulating search queries…";
    this.progressLog = [];
    this.notify('search_started', trimmed);
    onProgress(this.thinkingLabel);

    // Fast health probe with 1.5s timeout
    await this.probeHealth(1500).catch(() => false);

    let searchRun = null;

    // Attempt Live Backend Execution if reachable
    if (this.isBackendLive && typeof fetch === 'function') {
      try {
        searchRun = await this._executeLivePipeline(trimmed, onProgress);
      } catch (err) {
        console.warn('Backend query execution failed, falling back to Resilient Mock Mode:', err);
        this.isBackendLive = false;
        this.backendMode = 'mock';
        this.connectionStatus = '● arXiv connected (Mock Mode)';
        this.updateConnectionStatusUI();
      }
    }

    // Gracefully fall back to Mock Pipeline
    if (!searchRun) {
      searchRun = await this._executeMockPipeline(trimmed, onProgress);
    }

    // Commit search run to state
    this.runs.unshift(searchRun);
    if (this.runs.length > 10) this.runs.pop();
    this.selectedRunId = searchRun.id;

    // Add assistant response message with synthesis
    const assistantMsg = {
      id: `msg-${Date.now()}-a`,
      role: 'assistant',
      content: (searchRun.synthesis && searchRun.synthesis.summary) || "Synthesis brief complete.",
      search_run_id: searchRun.id,
      is_unsourced: !searchRun.synthesis || !searchRun.synthesis.citations || searchRun.synthesis.citations.length === 0,
      is_fallback: this.backendMode === 'mock',
      claims: (searchRun.synthesis && searchRun.synthesis.claims) || []
    };
    this.messages.push(assistantMsg);
    this.expandedEvidence.add(assistantMsg.id);

    this.isThinking = false;
    this.activeAbortController = null;
    this.notify('search_completed', { run: searchRun, message: assistantMsg });
    onComplete(searchRun, assistantMsg);
    return searchRun;
  }

  executeSearch(question, options = {}) {
    return this.submitQuery(question, options);
  }

  async _executeLivePipeline(question, onProgress) {
    if (typeof AbortController !== 'undefined') {
      this.activeAbortController = new AbortController();
    }
    const signal = this.activeAbortController ? this.activeAbortController.signal : undefined;

    onProgress("Submitting research query to Rezno backend…");

    const payload = {
      query: question,
      per_query: this.perQuery || 40,
      top_k: this.topK || 15,
      num_queries: this.numQueries || 3,
      response_length: this.responseLength || "standard"
    };

    let res = null;
    try {
      res = await fetch(this.searchEndpoint, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json', 'Accept': 'application/json' },
        body: JSON.stringify(payload),
        signal
      });
    } catch (searchErr) {
      if (searchErr && searchErr.name === 'AbortError') throw searchErr;
    }

    if (!res || !res.ok) {
      try {
        res = await fetch(this.synthesizeEndpoint, {
          method: 'POST',
          headers: { 'Content-Type': 'application/json', 'Accept': 'application/json' },
          body: JSON.stringify(payload),
          signal
        });
      } catch (synthErr) {
        if (synthErr && synthErr.name === 'AbortError') throw synthErr;
      }
    }

    if (!res || !res.ok) {
      throw new Error(`Live backend request failed: HTTP ${res ? res.status : 'offline'}`);
    }

    const data = await res.json();
    return this._normalizeRunData(data, question);
  }

  async _executeMockPipeline(question, onProgress) {
    const steps = [
      { label: "Planning parallel arXiv queries", delay: 250 },
      { label: `Querying arXiv API (depth: ${this.perQuery} papers)`, delay: 350 },
      { label: `Cross-encoder re-ranking top ${this.topK} candidates`, delay: 450 },
      { label: "Synthesizing executive brief and verifying claims", delay: 400 },
      { label: "Generating literature concept map", delay: 350 }
    ];

    for (const step of steps) {
      if (!this.isThinking) break;
      this.thinkingLabel = step.label;
      onProgress(step.label);
      await new Promise(r => {
        this.activeSearchTimer = setTimeout(r, step.delay);
      });
    }

    const lower = question.toLowerCase();
    const availableMocks = (typeof MOCK_RUNS !== 'undefined' && Array.isArray(MOCK_RUNS)) ? MOCK_RUNS : [];

    let matchedMock = null;
    if (lower.includes('attention') || lower.includes('lora') || lower.includes('peft') || lower.includes('fine-tuning')) {
      matchedMock = availableMocks.find(r => r.id === 'run-trans-01');
    } else if (lower.includes('quant') || lower.includes('4-bit') || lower.includes('compression') || lower.includes('gptq') || lower.includes('awq')) {
      matchedMock = availableMocks.find(r => r.id === 'run-quant-02');
    }

    const runId = `run-${Date.now()}`;
    const timestamp = new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' });

    if (matchedMock) {
      const cloned = JSON.parse(JSON.stringify(matchedMock));
      cloned.id = runId;
      cloned.query = question;
      cloned.timestamp = timestamp;
      return cloned;
    }

    const p1Id = "2401.01234";
    const p2Id = "2312.05678";
    return {
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
      timestamp,
      synthesis: {
        summary: `Recent investigations into **${question}** identify clear empirical trade-offs between computational overhead and representation accuracy. Cross-referencing retrieved literature highlights two pivotal strategies: first, localized sparse approximations limit memory footprint without compromising representation fidelity (${p1Id}); second, hybrid training formulations generalize effectively across standard academic benchmarks (${p2Id}).`,
        citations: [p1Id, p2Id],
        claims: [
          {
            claim: `Empirical evaluations on ${question} establish consistent improvements over classical baselines.`,
            arxiv_id: p1Id,
            supporting_sentence: "Experimental validation demonstrates that our proposed mechanism yields significant gains across all standardized test datasets."
          },
          {
            claim: "Sparse representations reduce memory scaling requirements.",
            arxiv_id: p2Id,
            supporting_sentence: "Memory consumption is reduced by substituting dense tensor products with bounded sparse matrices."
          }
        ]
      },
      papers: [
        {
          arxiv_id: p1Id,
          title: `Empirical Foundations and Architectural Paradigms for ${question}`,
          authors: ["Elena Rostova", "Marcus Vance", "David Chen"],
          author_line: "Elena Rostova, Marcus Vance, David Chen",
          summary: `A systematic investigation of modern approaches to ${question}, benchmarking execution latency, convergence rates, and parameter scalability.`,
          published: "2024-01-08",
          pdf_url: `https://arxiv.org/pdf/${p1Id}.pdf`,
          abs_url: `https://arxiv.org/abs/${p1Id}`,
          primary_category: "cs.AI",
          relevance_score: 0.958,
          status: "keep",
          note: "Directly relevant methodology."
        },
        {
          arxiv_id: p2Id,
          title: `Sparse Formulations and Memory Efficiency in Modern Neural Architectures`,
          authors: ["Siddharth Patel", "Chloe Martin"],
          author_line: "Siddharth Patel, Chloe Martin",
          summary: "Introduces bounded sparse tensor operators that accelerate inference and training across modern accelerators.",
          published: "2023-12-14",
          pdf_url: `https://arxiv.org/pdf/${p2Id}.pdf`,
          abs_url: `https://arxiv.org/abs/${p2Id}`,
          primary_category: "cs.LG",
          relevance_score: 0.884,
          status: "unreviewed",
          note: ""
        }
      ],
      graph: {
        nodes: [
          { id: p1Id, label: `Architectural Paradigms (${p1Id})`, type: "paper", pdf_url: `https://arxiv.org/pdf/${p1Id}.pdf`, abs_url: `https://arxiv.org/abs/${p1Id}` },
          { id: p2Id, label: `Sparse Formulations (${p2Id})`, type: "paper", pdf_url: `https://arxiv.org/pdf/${p2Id}.pdf`, abs_url: `https://arxiv.org/abs/${p2Id}` },
          { id: "c-core", label: question.substring(0, 30), type: "concept" },
          { id: "c-benchmarks", label: "Standardized Benchmarks", type: "concept" },
          { id: "c-sparse", label: "Sparse Tensor Operators", type: "concept" }
        ],
        edges: [
          { source: p1Id, target: "c-core", type: "MENTIONS" },
          { source: p1Id, target: "c-benchmarks", type: "MENTIONS" },
          { source: p2Id, target: "c-sparse", type: "MENTIONS" },
          { source: "c-sparse", target: "c-core", type: "SIMILAR_TO" },
          { source: p1Id, target: p2Id, type: "SIMILAR_TO" }
        ]
      }
    };
  }

  _normalizeRunData(data, question) {
    const runId = data.id || `run-${Date.now()}`;
    const papers = (data.papers || []).map((p, idx) => ({
      arxiv_id: p.arxiv_id || `paper-${idx}`,
      title: p.title || 'Untitled Academic Paper',
      authors: Array.isArray(p.authors) ? p.authors : [p.authors || 'Unknown Researcher'],
      author_line: p.author_line || (Array.isArray(p.authors) ? p.authors.join(', ') : (p.authors || 'Unknown')),
      summary: p.summary || '',
      published: p.published || new Date().toISOString().substring(0, 10),
      pdf_url: p.pdf_url || (p.arxiv_id ? `https://arxiv.org/pdf/${p.arxiv_id}.pdf` : '#'),
      abs_url: p.abs_url || (p.arxiv_id ? `https://arxiv.org/abs/${p.arxiv_id}` : '#'),
      primary_category: p.primary_category || 'cs.AI',
      relevance_score: typeof p.relevance_score === 'number' ? p.relevance_score : 0.85,
      status: p.status || 'unreviewed',
      note: p.note || ''
    }));

    const synthesis = data.synthesis || {};
    const summary = typeof synthesis === 'string' ? synthesis : (synthesis.summary || `Synthesized analysis for inquiry: "${question}".`);
    const citations = Array.isArray(synthesis.citations) ? synthesis.citations : papers.map(p => p.arxiv_id);
    const claims = Array.isArray(synthesis.claims) ? synthesis.claims : papers.slice(0, 2).map(p => ({
      claim: `Analysis of ${p.title} validates key algorithmic principles.`,
      arxiv_id: p.arxiv_id,
      supporting_sentence: p.summary ? p.summary.substring(0, 140) + '…' : 'Grounded empirical evidence.'
    }));

    let graph = data.graph;
    if (!graph || !Array.isArray(graph.nodes)) {
      const nodes = papers.map(p => ({
        id: p.arxiv_id,
        label: `${p.title.substring(0, 30)} (${p.arxiv_id})`,
        type: 'paper',
        pdf_url: p.pdf_url,
        abs_url: p.abs_url
      }));
      nodes.push({ id: 'c-core', label: question.substring(0, 30), type: 'concept' });
      const edges = papers.map(p => ({
        source: p.arxiv_id,
        target: 'c-core',
        type: 'MENTIONS'
      }));
      graph = { nodes, edges };
    }

    return {
      id: runId,
      query: data.query || question,
      queries: Array.isArray(data.queries) ? data.queries : [question],
      candidate_count: data.candidate_count || papers.length,
      status: data.status || data.search_status || "ok",
      search_error: data.search_error || null,
      timestamp: data.timestamp || new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' }),
      synthesis: {
        summary,
        citations,
        claims
      },
      papers,
      graph
    };
  }
}

const appStateInstance = new ResearchAgentState();
if (typeof window !== 'undefined') {
  window.appState = appStateInstance;
}
if (typeof globalThis !== 'undefined') {
  globalThis.appState = appStateInstance;
}
if (typeof module !== 'undefined' && module.exports) {
  module.exports = { ResearchAgentState, appState: appStateInstance };
}
