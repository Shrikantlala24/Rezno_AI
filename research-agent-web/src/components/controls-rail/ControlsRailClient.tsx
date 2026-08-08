'use client';

import React from 'react';
import { 
  IconChevronLeft, 
  IconFileText, 
  IconExternalLink, 
  IconTrash 
} from '@tabler/icons-react';
import { SearchRun } from '@/types';

interface ControlsRailProps {
  papersPerVariant: number;
  setPapersPerVariant: (val: number) => void;
  rankingTopK: number;
  setRankingTopK: (val: number) => void;
  queryVariantsCount: number;
  setQueryVariantsCount: (val: number) => void;
  responseLength: 'Brief' | 'Standard' | 'Detailed';
  setResponseLength: (len: 'Brief' | 'Standard' | 'Detailed') => void;
  messageCount: number;
  searchRun: SearchRun;
  onClearSession: () => void;
}

export function ControlsRailClient({
  papersPerVariant,
  setPapersPerVariant,
  rankingTopK,
  setRankingTopK,
  queryVariantsCount,
  setQueryVariantsCount,
  responseLength,
  setResponseLength,
  messageCount,
  searchRun,
  onClearSession,
}: ControlsRailProps) {
  return (
    <section className="w-[280px] border-r border-[var(--color-border)] p-6 flex flex-col gap-6 shrink-0 bg-[var(--color-sidebar)] overflow-y-auto">
      <div>
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-2">
            <div className="w-[26px] h-[26px] rounded-md bg-[var(--color-foreground)] text-[var(--color-background)] font-mono text-[13px] font-semibold flex items-center justify-center">
              R
            </div>
            <span className="font-mono text-[16px] font-semibold tracking-tight">Research Agent</span>
          </div>
          <button className="text-[var(--color-muted-foreground)] hover:text-[var(--color-foreground)] cursor-pointer">
            <IconChevronLeft className="w-4 h-4 stroke-[1.6]" />
          </button>
        </div>
        <p className="text-[11.5px] text-[var(--color-muted-foreground)] leading-relaxed mt-2.5">
          arXiv search, ranking, synthesis, and citation intelligence.
        </p>
      </div>

      {/* Pipeline Controls */}
      <div>
        <div className="font-mono text-[10.5px] tracking-wider uppercase text-[var(--color-muted-foreground)] mb-3.5">
          Pipeline controls
        </div>

        <div className="mb-4">
          <div className="flex justify-between items-center mb-2">
            <span className="text-[12.5px] text-[var(--color-foreground)]">Papers per query variant</span>
            <span className="font-mono text-[12px] border border-[var(--color-border)] rounded-[5px] px-2 py-0.5 bg-[var(--color-card)]">
              {papersPerVariant}
            </span>
          </div>
          <input 
            type="range" 
            min="10" 
            max="100" 
            value={papersPerVariant} 
            onChange={(e) => setPapersPerVariant(Number(e.target.value))}
            className="w-full accent-[var(--color-primary)] cursor-pointer h-[3px] bg-[var(--color-card)] rounded-[2px]" 
          />
          <div className="flex justify-between text-[10.5px] text-[var(--color-muted-foreground)] mt-1.5 font-mono">
            <span>10</span><span>100</span>
          </div>
        </div>

        <div className="mb-4">
          <div className="flex justify-between items-center mb-2">
            <span className="text-[12.5px] text-[var(--color-foreground)]">Ranking top-k</span>
            <span className="font-mono text-[12px] border border-[var(--color-border)] rounded-[5px] px-2 py-0.5 bg-[var(--color-card)]">
              {rankingTopK}
            </span>
          </div>
          <input 
            type="range" 
            min="1" 
            max="20" 
            value={rankingTopK} 
            onChange={(e) => setRankingTopK(Number(e.target.value))}
            className="w-full accent-[var(--color-primary)] cursor-pointer h-[3px] bg-[var(--color-card)] rounded-[2px]" 
          />
          <div className="flex justify-between text-[10.5px] text-[var(--color-muted-foreground)] mt-1.5 font-mono">
            <span>1</span><span>20</span>
          </div>
        </div>

        <div>
          <div className="flex justify-between items-center mb-2">
            <span className="text-[12.5px] text-[var(--color-foreground)]">Query variants count</span>
            <span className="font-mono text-[12px] border border-[var(--color-border)] rounded-[5px] px-2 py-0.5 bg-[var(--color-card)]">
              {queryVariantsCount}
            </span>
          </div>
          <input 
            type="range" 
            min="1" 
            max="5" 
            value={queryVariantsCount} 
            onChange={(e) => setQueryVariantsCount(Number(e.target.value))}
            className="w-full accent-[var(--color-primary)] cursor-pointer h-[3px] bg-[var(--color-card)] rounded-[2px]" 
          />
          <div className="flex justify-between text-[10.5px] text-[var(--color-muted-foreground)] mt-1.5 font-mono">
            <span>1</span><span>5</span>
          </div>
        </div>
      </div>

      {/* Response Length */}
      <div>
        <div className="font-mono text-[10.5px] tracking-wider uppercase text-[var(--color-muted-foreground)] mb-3.5">
          Response length
        </div>
        <div className="flex border border-[var(--color-border)] rounded-lg overflow-hidden bg-[var(--color-card)]">
          {(['Brief', 'Standard', 'Detailed'] as const).map((len) => (
            <button
              key={len}
              onClick={() => setResponseLength(len)}
              className={`flex-1 text-center text-[12px] py-2 transition-colors cursor-pointer ${responseLength === len ? 'bg-[var(--color-foreground)] text-[var(--color-background)] font-medium' : 'text-[var(--color-muted-foreground)] hover:text-[var(--color-foreground)]'}`}
            >
              {len}
            </button>
          ))}
        </div>
      </div>

      {/* Session Overview */}
      <div>
        <div className="font-mono text-[10.5px] tracking-wider uppercase text-[var(--color-muted-foreground)] mb-3.5">
          Session overview
        </div>
        <div className="flex gap-2.5">
          <div className="flex-1 bg-[var(--color-secondary)] border border-[var(--color-border)] rounded-lg p-3">
            <div className="text-[10.5px] text-[var(--color-muted-foreground)] mb-1">Messages</div>
            <div className="font-mono text-[21px] font-semibold">{messageCount}</div>
          </div>
          <div className="flex-1 bg-[var(--color-secondary)] border border-[var(--color-border)] rounded-lg p-3">
            <div className="text-[10.5px] text-[var(--color-muted-foreground)] mb-1">Search runs</div>
            <div className="font-mono text-[21px] font-semibold">1</div>
          </div>
        </div>
      </div>

      {/* Citations List */}
      <div>
        <div className="font-mono text-[10.5px] tracking-wider uppercase text-[var(--color-muted-foreground)] mb-3.5">
          Citations (selected search)
        </div>
        <div className="flex flex-col gap-0.5">
          {searchRun.papers.map((p) => (
            <a
              key={p.arxivId}
              href={p.absUrl}
              target="_blank"
              rel="noreferrer"
              className="flex items-center justify-between px-1.5 py-1.5 rounded-md font-mono text-[12px] text-[var(--color-foreground)] hover:bg-[var(--color-secondary)] group transition-colors"
            >
              <span className="flex items-center gap-2">
                <IconFileText className="w-3.5 h-3.5 text-[var(--color-muted-foreground)] group-hover:text-[var(--color-foreground)]" />
                {p.arxivId}
              </span>
              <IconExternalLink className="w-3.5 h-3.5 text-[var(--color-muted-foreground)] group-hover:text-[var(--color-foreground)]" />
            </a>
          ))}
        </div>
      </div>

      <div className="mt-auto pt-4">
        <button 
          onClick={onClearSession}
          className="font-sans text-[12.5px] text-[var(--color-foreground)] bg-[var(--color-background)] border border-[var(--color-border)] rounded-lg py-2.5 px-3 w-full flex items-center justify-center gap-2 hover:bg-[var(--color-secondary)] transition-colors cursor-pointer"
        >
          <IconTrash className="w-3.5 h-3.5 text-[var(--color-muted-foreground)]" />
          Clear session
        </button>
      </div>
    </section>
  );
}
