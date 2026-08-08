'use client';

import React, { useState } from 'react';
import { 
  IconChevronDown, 
  IconChevronRight, 
  IconBookmark, 
  IconDownload, 
  IconSearch 
} from '@tabler/icons-react';
import { SearchRun } from '@/lib/schemas/paper';
import { ConceptGraphView } from './ConceptGraphView';
import { CompareSearchesView } from './CompareSearchesView';

interface PaperWorkspaceProps {
  searchRuns: SearchRun[];
  activeSearchRunId: string;
  onSelectSearchRun: (id: string) => void;
}

export function PaperWorkspaceClient({ searchRuns, activeSearchRunId, onSelectSearchRun }: PaperWorkspaceProps) {
  const [activeTab, setActiveTab] = useState<'Papers' | 'Concept graph' | 'Compare searches'>('Papers');
  const [expandedPaperIdx, setExpandedPaperIdx] = useState<number>(0);
  const [screeningState, setScreeningState] = useState<'Keep' | 'Maybe' | 'Skip'>('Keep');
  const [notesText, setNotesText] = useState('');
  const [citationsData, setCitationsData] = useState<{ references: any[]; citations: any[] } | null>(null);

  const searchRun = searchRuns.find(r => r.id === activeSearchRunId) || searchRuns[0] || {
    id: 'run-1',
    query: 'context engineering',
    queries: [],
    candidateCount: 0,
    papers: [],
    insights: [],
    graph: null,
    synthesis: null,
    timestamp: '13:18:43'
  };

  const focusedPaper = searchRun.papers[expandedPaperIdx] || searchRun.papers[0];

  const handleFetchCitations = async (arxivId: string) => {
    try {
      const res = await fetch(`/api/citations/${arxivId}`);
      const data = await res.json();
      setCitationsData(data);
    } catch {
      setCitationsData({ references: [], citations: [] });
    }
  };

  const handleExportBibtex = async () => {
    try {
      const res = await fetch('/api/bibtex', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ papers: searchRun.papers })
      });
      const data = await res.json();
      const blob = new Blob([data.bibtex], { type: 'text/plain' });
      const url = URL.createObjectURL(blob);
      const a = document.createElement('a');
      a.href = url;
      a.download = `search_${searchRun.id}_papers.bib`;
      a.click();
    } catch {
      alert('BibTeX export failed');
    }
  };

  return (
    <aside className="w-[540px] p-6 flex flex-col bg-[var(--color-background)] overflow-y-auto">
      <div className="text-[11px] text-[var(--color-muted-foreground)] mb-2">Select search run</div>
      
      <select 
        value={searchRun.id}
        onChange={(e) => onSelectSearchRun(e.target.value)}
        className="w-full border border-[var(--color-border)] rounded-[9px] p-2.5 text-[12.5px] mb-4 bg-[var(--color-card)] text-[var(--color-foreground)] outline-none cursor-pointer"
      >
        {searchRuns.map(r => (
          <option key={r.id} value={r.id}>Search #{r.id} ({r.timestamp}): {r.query}</option>
        ))}
      </select>

      <div className="flex gap-5 border-b border-[var(--color-border)] mb-4">
        {(['Papers', 'Concept graph', 'Compare searches'] as const).map((tab) => (
          <button
            key={tab}
            onClick={() => setActiveTab(tab)}
            className={`text-[12.5px] pb-2.5 transition-colors relative cursor-pointer ${activeTab === tab ? 'text-[var(--color-foreground)] font-medium after:absolute after:bottom-0 after:left-0 after:right-0 after:h-[2px] after:bg-[var(--color-foreground)]' : 'text-[var(--color-muted-foreground)] hover:text-[var(--color-foreground)]'}`}
          >
            {tab}
          </button>
        ))}
      </div>

      {activeTab === 'Papers' ? (
        <div>
          <div className="flex justify-between items-center mb-3">
            <span className="text-[12px] text-[var(--color-muted-foreground)]">Top {searchRun.papers.length} papers for: {searchRun.query}</span>
            <button onClick={handleExportBibtex} className="text-[11.5px] border border-[var(--color-border)] rounded-lg px-2.5 py-1.5 flex items-center gap-1.5 bg-[var(--color-card)] hover:bg-[var(--color-secondary)] transition-colors cursor-pointer">
              <IconDownload className="w-3.5 h-3.5 text-[var(--color-muted-foreground)]" />
              Export BibTeX
            </button>
          </div>

          {focusedPaper ? (
            <div className="bg-[var(--color-card)] border border-[var(--color-border)] rounded-xl p-4 mb-3.5">
              <div className="flex justify-between items-start gap-3 mb-2.5">
                <h3 className="font-mono text-[14.5px] font-semibold leading-[1.4]">{focusedPaper.title}</h3>
                <IconBookmark className="w-4 h-4 text-[var(--color-primary)] shrink-0 fill-[var(--color-primary)]" />
              </div>

              <div className="flex gap-2 items-center mb-3">
                <span className="font-mono text-[11px] px-2 py-0.5 rounded-[5px] border border-[var(--color-border)] bg-[var(--color-background)]">
                  {focusedPaper.arxivId}
                </span>
                <span className="font-mono text-[11px] px-2 py-0.5 rounded-[5px] border border-[var(--color-border)] bg-[var(--color-background)]">
                  {focusedPaper.primaryCategory}
                </span>
                <span className="font-mono text-[12px] text-[#8B6F4E] font-semibold ml-auto">
                  {focusedPaper.relevanceScore}
                </span>
              </div>

              <p className="text-[12.5px] text-[var(--color-muted-foreground)] leading-relaxed mb-3">
                {focusedPaper.summary}
              </p>

              <div className="flex gap-4 text-[11.5px] text-[var(--color-foreground)] font-medium mb-4">
                <button className="flex items-center gap-1 hover:underline cursor-pointer">abstract ▾</button>
                <a href={focusedPaper.pdfUrl} target="_blank" rel="noreferrer" className="flex items-center gap-1 text-[var(--color-primary)] hover:underline">
                  pdf ↗
                </a>
              </div>

              <div className="text-[10.5px] tracking-wider uppercase text-[var(--color-muted-foreground)] mb-2 font-mono">
                Screening state
              </div>

              <div className="flex gap-4 items-center mb-3">
                <div className="flex border border-[var(--color-border)] rounded-full p-0.5 bg-[var(--color-background)]">
                  {(['Keep', 'Maybe', 'Skip'] as const).map((st) => (
                    <button
                      key={st}
                      onClick={() => setScreeningState(st)}
                      className={`text-[12px] px-3.5 py-1 rounded-full transition-colors cursor-pointer ${screeningState === st ? 'bg-[#8B6F4E] text-white font-medium' : 'text-[var(--color-muted-foreground)] hover:text-[var(--color-foreground)]'}`}
                    >
                      {st}
                    </button>
                  ))}
                </div>

                <input 
                  type="text" 
                  value={notesText} 
                  onChange={(e) => setNotesText(e.target.value)}
                  placeholder="Notes..."
                  className="flex-1 border border-[var(--color-border)] rounded-lg px-3 py-1.5 text-[12px] bg-[var(--color-background)] text-[var(--color-foreground)] outline-none focus:border-[var(--color-primary)]"
                />
              </div>

              <div className="border-t border-[var(--color-border)] pt-3 mt-3">
                <div className="flex justify-between items-center mb-2.5">
                  <span className="text-[12.5px] font-medium">Citation chaining (Semantic Scholar)</span>
                  <button onClick={() => handleFetchCitations(focusedPaper.arxivId)} className="text-[11.5px] border border-[var(--color-border)] rounded-lg px-2.5 py-1.5 flex items-center gap-1.5 bg-[var(--color-background)] hover:bg-[var(--color-secondary)] transition-colors cursor-pointer">
                    <IconSearch className="w-3.5 h-3.5 text-[var(--color-muted-foreground)]" />
                    Fetch citations &amp; references
                  </button>
                </div>

                <div className="grid grid-cols-2 gap-4 mt-3">
                  <div>
                    <div className="text-[11px] text-[var(--color-muted-foreground)] mb-2">References ({citationsData ? citationsData.references.length : 3})</div>
                    <div className="flex flex-col gap-1.5 max-h-[160px] overflow-y-auto">
                      {(citationsData ? citationsData.references.slice(0, 5) : [
                        { title: 'Attention Is All You Need', arxivId: '1706.03762' },
                        { title: 'Rethinking Transformer Positional Encoding', arxivId: '2003.08933' },
                        { title: 'Long Range Arena', arxivId: '2011.04006' }
                      ]).map((r: any, ri: number) => (
                        <div key={ri} className="flex justify-between items-start text-[12px] py-1 border-b border-[var(--color-border)]">
                          <span className="line-clamp-1">{r.title}</span>
                          <button className="text-[11px] text-[var(--color-primary)] font-medium shrink-0 ml-2 cursor-pointer">+ Add</button>
                        </div>
                      ))}
                    </div>
                  </div>

                  <div>
                    <div className="text-[11px] text-[var(--color-muted-foreground)] mb-2">Citing papers ({citationsData ? citationsData.citations.length : 3})</div>
                    <div className="flex flex-col gap-1.5 max-h-[160px] overflow-y-auto">
                      {(citationsData ? citationsData.citations.slice(0, 5) : [
                        { title: 'Needle In A Haystack: Pressure Testing LLMs', arxivId: '2310.12345' },
                        { title: 'RULER: What\'s the Real Context Window?', arxivId: '2404.06654' },
                        { title: 'Don\'t Trust, Verify', arxivId: '2403.01234' }
                      ]).map((c: any, ci: number) => (
                        <div key={ci} className="flex justify-between items-start text-[12px] py-1 border-b border-[var(--color-border)]">
                          <span className="line-clamp-1">{c.title}</span>
                          <button className="text-[11px] text-[var(--color-primary)] font-medium shrink-0 ml-2 cursor-pointer">+ Add</button>
                        </div>
                      ))}
                    </div>
                  </div>
                </div>
              </div>

            </div>
          ) : (
            <div className="text-[12px] text-[var(--color-muted-foreground)] py-10 text-center">No papers in this search run.</div>
          )}

          {searchRun.papers.map((p, idx) => {
            if (idx === expandedPaperIdx) return null;
            return (
              <div 
                key={p.arxivId}
                onClick={() => setExpandedPaperIdx(idx)}
                className="border border-[var(--color-border)] rounded-[9px] p-3.5 flex items-center justify-between text-[12.5px] mb-2 bg-[var(--color-background)] hover:border-[var(--color-primary)] cursor-pointer transition-colors"
              >
                <div className="flex items-center gap-3">
                  <span className="font-mono text-[11px] text-[var(--color-muted-foreground)]">{idx + 1}</span>
                  <span className="font-medium line-clamp-1">{p.title}</span>
                </div>
                <IconChevronRight className="w-4 h-4 text-[var(--color-muted-foreground)]" />
              </div>
            );
          })}
        </div>
      ) : activeTab === 'Concept graph' ? (
        <ConceptGraphView graph={searchRun.graph || null} />
      ) : (
        <CompareSearchesView searchRuns={searchRuns} />
      )}
    </aside>
  );
}
