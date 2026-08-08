'use client';

import React, { useState } from 'react';
import { 
  IconSearch, 
  IconMessageCircle, 
  IconLayoutDashboard, 
  IconNetwork, 
  IconChartBar, 
  IconBookmark, 
  IconSettings, 
  IconUser 
} from '@tabler/icons-react';
import { SearchRun, ChatMessage } from '@/types';
import { ControlsRailClient } from '@/components/controls-rail/ControlsRailClient';
import { ConversationClient } from '@/components/conversation/ConversationClient';
import { PaperWorkspaceClient } from '@/components/paper-workspace/PaperWorkspaceClient';

const INITIAL_SEARCH_RUN: SearchRun = {
  id: '1',
  query: 'context engineering',
  queries: ['context engineering llm', 'retrieval augmented generation context window'],
  candidateCount: 4,
  timestamp: '13:18:43',
  insights: [
    { arxivId: '2307.03172v1', concepts: ['large language models', 'context window', 'position bias', 'retrieval-augmented generation'] }
  ],
  graph: {
    nodes: [
      { id: '2307.03172v1', label: 'Lost in the Middle: How Language Models Use Long Contexts', type: 'paper' },
      { id: 'concept::large language models', label: 'large language models', type: 'concept' },
      { id: 'concept::context window', label: 'context window', type: 'concept' },
      { id: 'concept::position bias', label: 'position bias', type: 'concept' }
    ],
    edges: [
      { source: '2307.03172v1', target: 'concept::large language models', type: 'MENTIONS' },
      { source: '2307.03172v1', target: 'concept::context window', type: 'MENTIONS' },
      { source: '2307.03172v1', target: 'concept::position bias', type: 'MENTIONS' }
    ]
  },
  synthesis: {
    summary: 'Context engineering refers to the deliberate design and arrangement of information provided to language models.',
    citations: ['2307.03172v1'],
    claims: []
  },
  papers: [
    {
      arxivId: '2307.03172v1',
      title: 'Lost in the Middle: How Language Models Use Long Contexts',
      authors: ['Nelson F. Liu', 'Kevin Lin'],
      summary: 'We study how language models utilize long input contexts and find that accuracy degrades when relevant information is placed in the middle...',
      published: '2023-07-06',
      pdfUrl: 'https://arxiv.org/pdf/2307.03172',
      absUrl: 'https://arxiv.org/abs/2307.03172',
      primaryCategory: 'cs.CL',
      categories: ['cs.CL'],
      relevanceScore: 0.95,
      status: 'keep',
      note: 'Strong empirical study.'
    }
  ]
};

const INITIAL_MESSAGES: ChatMessage[] = [
  {
    role: 'assistant',
    content: 'Welcome to Research Agent. Type a research query below to plan queries, search arXiv, rank papers, and synthesize grounded answers.',
    claims: [],
    responseLength: 'standard',
    timestamp: '13:17'
  }
];

export function ResearchWorkspace() {
  const [papersPerVariant, setPapersPerVariant] = useState(30);
  const [rankingTopK, setRankingTopK] = useState(5);
  const [queryVariantsCount, setQueryVariantsCount] = useState(2);
  const [responseLength, setResponseLength] = useState<'Brief' | 'Standard' | 'Detailed'>('Standard');
  
  const [messages, setMessages] = useState<ChatMessage[]>(INITIAL_MESSAGES);
  const [searchRuns, setSearchRuns] = useState<SearchRun[]>([INITIAL_SEARCH_RUN]);
  const [activeSearchRunId, setActiveSearchRunId] = useState<string>('1');
  const [isLoading, setIsLoading] = useState(false);
  const [activeNav, setActiveNav] = useState<'search' | 'chat' | 'dashboard' | 'network' | 'chart' | 'bookmark'>('search');

  const handleClearSession = () => {
    setMessages(INITIAL_MESSAGES);
    setSearchRuns([INITIAL_SEARCH_RUN]);
    setActiveSearchRunId('1');
  };

  const handleSendMessage = async (content: string) => {
    const userMsg: ChatMessage = {
      role: 'user',
      content,
      claims: [],
      responseLength: responseLength.toLowerCase() as any,
      timestamp: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })
    };

    setMessages(prev => [...prev, userMsg]);
    setIsLoading(true);

    try {
      const activeRun = searchRuns.find(r => r.id === activeSearchRunId) || searchRuns[0];
      let intent = 'new_search';
      if (activeRun && activeRun.papers.length > 0) {
        const routeRes = await fetch('/api/route', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({
            message: content,
            papers: activeRun.papers,
            history: messages
          })
        });
        const routeData = await routeRes.json();
        intent = routeData.intent || 'new_search';
      }

      if (intent === 'new_search') {
        const searchRes = await fetch('/api/search', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({
            query: content,
            topK: rankingTopK,
            responseLength: responseLength.toLowerCase()
          })
        });
        const searchData = await searchRes.json();
        const newRunId = String(searchRuns.length + 1);
        const newRun: SearchRun = { ...searchData, id: newRunId };
        
        setSearchRuns(prev => [newRun, ...prev]);
        setActiveSearchRunId(newRunId);

        const summaryText = newRun.synthesis?.summary || `Retrieved ${newRun.papers.length} papers for "${content}".`;
        const assistantMsg: ChatMessage = {
          role: 'assistant',
          content: summaryText,
          claims: newRun.synthesis?.claims || [],
          searchRunId: newRunId,
          responseLength: responseLength.toLowerCase() as any,
          timestamp: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })
        };
        setMessages(prev => [...prev, assistantMsg]);
      } else if (intent === 'follow_up_grounded') {
        const fgRes = await fetch('/api/follow-up/grounded', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({
            question: content,
            history: messages,
            papers: activeRun.papers,
            concepts: activeRun.insights?.flatMap(i => i.concepts) || [],
            responseLength: responseLength.toLowerCase()
          })
        });
        const fgData = await fgRes.json();

        const assistantMsg: ChatMessage = {
          role: 'assistant',
          content: fgData.summary || 'Grounded follow-up complete.',
          claims: fgData.claims || [],
          responseLength: responseLength.toLowerCase() as any,
          timestamp: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })
        };
        setMessages(prev => [...prev, assistantMsg]);
      } else {
        const genRes = await fetch('/api/follow-up/general', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({
            question: content,
            history: messages
          })
        });
        const genData = await genRes.json();

        const assistantMsg: ChatMessage = {
          role: 'assistant',
          content: genData.answer || 'Answer generated.',
          claims: [],
          isUnsourced: true,
          responseLength: responseLength.toLowerCase() as any,
          timestamp: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })
        };
        setMessages(prev => [...prev, assistantMsg]);
      }
    } catch (e: any) {
      const errorMsg: ChatMessage = {
        role: 'assistant',
        content: `Error processing request: ${e.message || 'Unknown error'}`,
        claims: [],
        responseLength: responseLength.toLowerCase() as any,
        timestamp: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })
      };
      setMessages(prev => [...prev, errorMsg]);
    } finally {
      setIsLoading(false);
    }
  };

  const activeSearchRun = searchRuns.find(r => r.id === activeSearchRunId) || searchRuns[0];

  return (
    <div className="flex min-h-screen bg-[var(--color-background)] text-[var(--color-foreground)] antialiased font-sans selection:bg-[#8B6F4E]/30">
      
      {/* 1. ICON RAIL */}
      <aside className="w-[64px] border-r border-[var(--color-border)] flex flex-col items-center py-5 gap-2 shrink-0 select-none bg-[var(--color-sidebar)]">
        <button onClick={() => setActiveNav('search')} title="Search" className={`w-9 h-9 rounded-lg flex items-center justify-center transition-colors cursor-pointer ${activeNav === 'search' ? 'bg-[var(--color-card)] text-[var(--color-foreground)]' : 'text-[var(--color-muted-foreground)] hover:text-[var(--color-foreground)]'}`}>
          <IconSearch className="w-4 h-4 stroke-[1.6]" />
        </button>
        <button onClick={() => setActiveNav('chat')} title="Chat" className={`w-9 h-9 rounded-lg flex items-center justify-center transition-colors cursor-pointer ${activeNav === 'chat' ? 'bg-[var(--color-card)] text-[var(--color-foreground)]' : 'text-[var(--color-muted-foreground)] hover:text-[var(--color-foreground)]'}`}>
          <IconMessageCircle className="w-4 h-4 stroke-[1.6]" />
        </button>
        <button onClick={() => setActiveNav('dashboard')} title="Dashboard" className={`w-9 h-9 rounded-lg flex items-center justify-center transition-colors cursor-pointer ${activeNav === 'dashboard' ? 'bg-[var(--color-card)] text-[var(--color-foreground)]' : 'text-[var(--color-muted-foreground)] hover:text-[var(--color-foreground)]'}`}>
          <IconLayoutDashboard className="w-4 h-4 stroke-[1.6]" />
        </button>
        <button onClick={() => setActiveNav('network')} title="Concept Graph" className={`w-9 h-9 rounded-lg flex items-center justify-center transition-colors cursor-pointer ${activeNav === 'network' ? 'bg-[var(--color-card)] text-[var(--color-foreground)]' : 'text-[var(--color-muted-foreground)] hover:text-[var(--color-foreground)]'}`}>
          <IconNetwork className="w-4 h-4 stroke-[1.6]" />
        </button>
        <button onClick={() => setActiveNav('chart')} title="Analytics" className={`w-9 h-9 rounded-lg flex items-center justify-center transition-colors cursor-pointer ${activeNav === 'chart' ? 'bg-[var(--color-card)] text-[var(--color-foreground)]' : 'text-[var(--color-muted-foreground)] hover:text-[var(--color-foreground)]'}`}>
          <IconChartBar className="w-4 h-4 stroke-[1.6]" />
        </button>
        <button onClick={() => setActiveNav('bookmark')} title="Bookmarks" className={`w-9 h-9 rounded-lg flex items-center justify-center transition-colors cursor-pointer ${activeNav === 'bookmark' ? 'bg-[var(--color-card)] text-[var(--color-foreground)]' : 'text-[var(--color-muted-foreground)] hover:text-[var(--color-foreground)]'}`}>
          <IconBookmark className="w-4 h-4 stroke-[1.6]" />
        </button>

        <div className="flex-1" />

        <button title="Settings" className="w-9 h-9 rounded-lg flex items-center justify-center text-[var(--color-muted-foreground)] hover:text-[var(--color-foreground)] cursor-pointer">
          <IconSettings className="w-4 h-4 stroke-[1.6]" />
        </button>
        <button title="User Profile" className="w-9 h-9 rounded-lg flex items-center justify-center text-[var(--color-muted-foreground)] hover:text-[var(--color-foreground)] cursor-pointer">
          <IconUser className="w-4 h-4 stroke-[1.6]" />
        </button>
        <div className="w-7 h-7 rounded-full bg-[var(--color-foreground)] mt-2 flex items-center justify-center text-[var(--color-background)] font-mono text-xs font-bold">
          R
        </div>
      </aside>

      {/* 2. CONTROLS RAIL */}
      <ControlsRailClient
        papersPerVariant={papersPerVariant}
        setPapersPerVariant={setPapersPerVariant}
        rankingTopK={rankingTopK}
        setRankingTopK={setRankingTopK}
        queryVariantsCount={queryVariantsCount}
        setQueryVariantsCount={setQueryVariantsCount}
        responseLength={responseLength}
        setResponseLength={setResponseLength}
        messageCount={messages.length}
        searchRun={activeSearchRun}
        onClearSession={handleClearSession}
      />

      {/* 3. CONVERSATION COLUMN */}
      <div className="flex-1 flex flex-col relative">
        <ConversationClient
          messages={messages}
          onSendMessage={handleSendMessage}
          responseLength={responseLength}
        />
        {isLoading && (
          <div className="absolute inset-0 bg-[var(--color-background)]/60 backdrop-blur-[1px] flex items-center justify-center z-20">
            <div className="flex items-center gap-3 bg-[var(--color-card)] border border-[var(--color-border)] rounded-xl px-5 py-3 shadow-md font-mono text-[13px]">
              <div className="w-4 h-4 border-2 border-[var(--color-primary)] border-t-transparent rounded-full animate-spin" />
              Running research pipeline &amp; synthesizing answer...
            </div>
          </div>
        )}
      </div>

      {/* 4. PAPER WORKSPACE COLUMN */}
      <PaperWorkspaceClient
        searchRuns={searchRuns}
        activeSearchRunId={activeSearchRunId}
        onSelectSearchRun={setActiveSearchRunId}
      />

    </div>
  );
}
