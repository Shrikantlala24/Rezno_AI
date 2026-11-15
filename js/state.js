/**
 * State store for Research Agent UI
 */
class ResearchAgentState {
  constructor() {
    this.theme = localStorage.getItem('ra-theme') || 'light';
    this.runs = JSON.parse(JSON.stringify(MOCK_RUNS));
    this.selectedRunId = this.runs.length > 0 ? this.runs[0].id : null;
    this.messages = JSON.parse(JSON.stringify(MOCK_MESSAGES));
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
    this.listeners = [];
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
    localStorage.setItem('ra-theme', theme);
    if (theme === 'dark') {
      document.documentElement.classList.add('dark');
    } else {
      document.documentElement.classList.remove('dark');
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
  fetchCitations(arxivId) {
    this.fetchingCitations.add(arxivId);
    this.notify('papers_render');

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
}

window.appState = new ResearchAgentState();
