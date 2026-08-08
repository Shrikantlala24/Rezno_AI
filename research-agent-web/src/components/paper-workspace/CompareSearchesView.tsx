'use client';

import React, { useState } from 'react';
import { SearchRun } from '@/lib/schemas/paper';
import { compareSearches } from '@/lib/pipeline/compare';
import { IconChevronDown } from '@tabler/icons-react';

interface CompareSearchesViewProps {
  searchRuns: SearchRun[];
}

export function CompareSearchesView({ searchRuns }: CompareSearchesViewProps) {
  const [runAId, setRunAId] = useState<string>(searchRuns[0]?.id || '');
  const [runBId, setRunBId] = useState<string>(searchRuns[1]?.id || searchRuns[0]?.id || '');
  const [subTab, setSubTab] = useState<'papers' | 'concepts'>('papers');

  if (searchRuns.length < 2) {
    return (
      <div className="flex-1 flex flex-col items-center justify-center text-[var(--color-muted-foreground)] text-sm py-20 px-6 text-center">
        <p className="font-medium text-[var(--color-foreground)] mb-1">Second search run needed</p>
        <p className="text-xs">Perform at least two distinct research searches in this session to compare their paper overlap and shared concepts.</p>
      </div>
    );
  }

  const runA = searchRuns.find(r => r.id === runAId) || searchRuns[0];
  const runB = searchRuns.find(r => r.id === runBId) || searchRuns[1];

  const comparison = compareSearches(runA, runB);

  return (
    <div className="flex flex-col gap-4">
      <div className="grid grid-cols-2 gap-3">
        <div>
          <label className="text-[11px] text-[var(--color-muted-foreground)] block mb-1">Search Run A</label>
          <select 
            value={runAId} 
            onChange={(e) => setRunAId(e.target.value)}
            className="w-full border border-[var(--color-border)] rounded-lg p-2 text-[12px] bg-[var(--color-card)] text-[var(--color-foreground)] outline-none"
          >
            {searchRuns.map(r => (
              <option key={r.id} value={r.id}>Search #{r.id}: {r.query}</option>
            ))}
          </select>
        </div>
        <div>
          <label className="text-[11px] text-[var(--color-muted-foreground)] block mb-1">Search Run B</label>
          <select 
            value={runBId} 
            onChange={(e) => setRunBId(e.target.value)}
            className="w-full border border-[var(--color-border)] rounded-lg p-2 text-[12px] bg-[var(--color-card)] text-[var(--color-foreground)] outline-none"
          >
            {searchRuns.map(r => (
              <option key={r.id} value={r.id}>Search #{r.id}: {r.query}</option>
            ))}
          </select>
        </div>
      </div>

      <div className="flex gap-4 border-b border-[var(--color-border)] pt-2">
        <button 
          onClick={() => setSubTab('papers')} 
          className={`text-[12px] pb-2 cursor-pointer ${subTab === 'papers' ? 'font-medium border-b-2 border-[var(--color-foreground)]' : 'text-[var(--color-muted-foreground)]'}`}
        >
          Papers Comparison ({comparison.sharedPapers.length} shared)
        </button>
        <button 
          onClick={() => setSubTab('concepts')} 
          className={`text-[12px] pb-2 cursor-pointer ${subTab === 'concepts' ? 'font-medium border-b-2 border-[var(--color-foreground)]' : 'text-[var(--color-muted-foreground)]'}`}
        >
          Concepts Comparison ({comparison.sharedConcepts.length} shared)
        </button>
      </div>

      {subTab === 'papers' ? (
        <div className="flex flex-col gap-4">
          <div>
            <div className="text-[11px] font-mono uppercase text-[var(--color-muted-foreground)] mb-2">Shared Papers ({comparison.sharedPapers.length})</div>
            {comparison.sharedPapers.length === 0 ? (
              <div className="text-[12px] text-[var(--color-muted-foreground)] italic">No papers shared between these two runs.</div>
            ) : (
              comparison.sharedPapers.map(p => (
                <div key={p.arxivId} className="p-3 bg-[var(--color-card)] border border-[var(--color-border)] rounded-lg mb-2 text-[12px]">
                  <div className="font-mono font-semibold">{p.title}</div>
                  <div className="text-[11px] text-[var(--color-muted-foreground)] mt-1">{p.arxivId} • Score: {p.relevanceScore}</div>
                </div>
              ))
            )}
          </div>

          <div className="grid grid-cols-2 gap-4">
            <div>
              <div className="text-[11px] font-mono uppercase text-[var(--color-muted-foreground)] mb-2">Unique to Run A ({comparison.uniqueToARun.length})</div>
              {comparison.uniqueToARun.map(p => (
                <div key={p.arxivId} className="p-2.5 bg-[var(--color-card)] border border-[var(--color-border)] rounded-lg mb-2 text-[11.5px]">
                  <div className="font-semibold line-clamp-1">{p.title}</div>
                  <div className="text-[10.5px] text-[var(--color-muted-foreground)] mt-0.5">{p.arxivId}</div>
                </div>
              ))}
            </div>
            <div>
              <div className="text-[11px] font-mono uppercase text-[var(--color-muted-foreground)] mb-2">Unique to Run B ({comparison.uniqueToBRun.length})</div>
              {comparison.uniqueToBRun.map(p => (
                <div key={p.arxivId} className="p-2.5 bg-[var(--color-card)] border border-[var(--color-border)] rounded-lg mb-2 text-[11.5px]">
                  <div className="font-semibold line-clamp-1">{p.title}</div>
                  <div className="text-[10.5px] text-[var(--color-muted-foreground)] mt-0.5">{p.arxivId}</div>
                </div>
              ))}
            </div>
          </div>
        </div>
      ) : (
        <div className="flex flex-col gap-4">
          <div>
            <div className="text-[11px] font-mono uppercase text-[var(--color-muted-foreground)] mb-2">Shared Concepts ({comparison.sharedConcepts.length})</div>
            <div className="flex flex-wrap gap-1.5">
              {comparison.sharedConcepts.map(c => (
                <span key={c} className="font-mono text-[11px] bg-[var(--color-card)] border border-[var(--color-border)] rounded-md px-2.5 py-1">
                  {c}
                </span>
              ))}
            </div>
          </div>
          <div className="grid grid-cols-2 gap-4">
            <div>
              <div className="text-[11px] font-mono uppercase text-[var(--color-muted-foreground)] mb-2">Unique to Run A</div>
              <div className="flex flex-wrap gap-1.5">
                {comparison.uniqueToAConcepts.map(c => (
                  <span key={c} className="font-mono text-[11px] bg-[var(--color-card)] border border-[var(--color-border)] rounded-md px-2 py-0.5">
                    {c}
                  </span>
                ))}
              </div>
            </div>
            <div>
              <div className="text-[11px] font-mono uppercase text-[var(--color-muted-foreground)] mb-2">Unique to Run B</div>
              <div className="flex flex-wrap gap-1.5">
                {comparison.uniqueToBConcepts.map(c => (
                  <span key={c} className="font-mono text-[11px] bg-[var(--color-card)] border border-[var(--color-border)] rounded-md px-2 py-0.5">
                    {c}
                  </span>
                ))}
              </div>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
