'use client';

import React, { useState } from 'react';
import { 
  IconChevronRight, 
  IconInfoCircle, 
  IconSend 
} from '@tabler/icons-react';
import { ChatMessage } from '@/types';

interface ConversationProps {
  messages: ChatMessage[];
  onSendMessage: (content: string) => void;
  responseLength: string;
}

export function ConversationClient({
  messages,
  onSendMessage,
  responseLength,
}: ConversationProps) {
  const [inputVal, setInputVal] = useState('');
  const [showEvidenceMap, setShowEvidenceMap] = useState<Record<number, boolean>>({});

  const toggleEvidence = (idx: number) => {
    setShowEvidenceMap(prev => ({ ...prev, [idx]: !prev[idx] }));
  };

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    if (!inputVal.trim()) return;
    onSendMessage(inputVal);
    setInputVal('');
  };

  return (
    <main className="flex-1 flex flex-col h-screen border-r border-[var(--color-border)] bg-[var(--color-background)]">
      <header className="flex items-center justify-between px-7 py-5 border-b border-[var(--color-border)] shrink-0 bg-[var(--color-background)]">
        <h1 className="font-mono text-[15px] font-semibold tracking-tight">Conversation</h1>
        <div className="flex items-center gap-1.5 text-[11.5px] text-[var(--color-muted-foreground)]">
          <span className="w-1.5 h-1.5 rounded-full bg-[var(--color-foreground)] animate-pulse" />
          Live
        </div>
      </header>

      <div className="flex-1 p-7 overflow-y-auto flex flex-col gap-6">
        {messages.map((msg, idx) => (
          <div key={idx} className={`flex gap-3 max-w-[540px] ${msg.role === 'user' ? 'self-end flex-row-reverse' : 'self-start'}`}>
            <div className={`w-[26px] h-[26px] rounded-full flex-shrink-0 flex items-center justify-center font-mono text-[11px] font-semibold ${msg.role === 'user' ? 'bg-[#8B6F4E] text-white' : 'bg-[var(--color-foreground)] text-[var(--color-background)]'}`}>
              {msg.role === 'user' ? 'U' : 'R'}
            </div>
            
            <div className="flex flex-col">
              {msg.role === 'user' ? (
                <div className="bg-[var(--color-secondary)] border border-[var(--color-border)] rounded-[10px_10px_2px_10px] px-3.5 py-2.5 text-[13.5px] flex items-center gap-3">
                  <span>{msg.content}</span>
                  <span className="text-[10.5px] text-[var(--color-muted-foreground)] whitespace-nowrap">{msg.timestamp}</span>
                </div>
              ) : (
                <div>
                  <div className="text-[14px] leading-[1.75] text-[var(--color-foreground)] whitespace-pre-wrap">
                    {msg.content}
                  </div>

                  {msg.claims && msg.claims.length > 0 && (
                    <div className="mt-2.5">
                      <button 
                        onClick={() => toggleEvidence(idx)}
                        className="flex items-center gap-1.5 text-[12px] text-[var(--color-muted-foreground)] border border-[var(--color-border)] rounded-lg px-3 py-2 bg-[var(--color-secondary)] hover:text-[var(--color-foreground)] transition-colors cursor-pointer"
                      >
                        <IconChevronRight className={`w-3.5 h-3.5 transition-transform ${showEvidenceMap[idx] ? 'rotate-90' : ''}`} />
                        View Evidence &amp; Supporting Quotes ({msg.claims.length})
                      </button>
                      
                      {showEvidenceMap[idx] && (
                        <div className="mt-2 p-3 bg-[var(--color-card)] border border-[var(--color-border)] rounded-lg text-[12px] flex flex-col gap-2">
                          {msg.claims.map((c, ci) => (
                            <div key={ci} className="border-b border-[var(--color-border)] pb-2 last:border-0 last:pb-0">
                              <div className="font-mono font-semibold text-[var(--color-primary)]">{c.arxivId}</div>
                              <div className="text-[var(--color-foreground)] mt-0.5">{c.claim}</div>
                              <div className="italic text-[var(--color-muted-foreground)] mt-0.5">"{c.supportingSentence}"</div>
                            </div>
                          ))}
                        </div>
                      )}
                    </div>
                  )}

                  {msg.isUnsourced && (
                    <div className="mt-2.5 flex items-center gap-1.5 text-[11.5px] italic text-[var(--color-muted-foreground)]">
                      <IconInfoCircle className="w-3.5 h-3.5 shrink-0" />
                      Answered using live web search — not from your retrieved papers
                    </div>
                  )}
                </div>
              )}
            </div>
          </div>
        ))}
      </div>

      <form onSubmit={handleSubmit} className="mx-7 mb-5 border border-[var(--color-border)] rounded-xl p-3 flex items-center justify-between bg-[var(--color-card)] shadow-xs">
        <input 
          type="text" 
          placeholder="Ask a research question…" 
          value={inputVal}
          onChange={(e) => setInputVal(e.target.value)}
          className="bg-transparent border-0 outline-none text-[13px] text-[var(--color-foreground)] placeholder-[var(--color-muted-foreground)] flex-1 px-1"
        />
        <div className="flex items-center gap-2.5">
          <span className="font-mono text-[10.5px] text-[var(--color-muted-foreground)] border border-[var(--color-border)] rounded-[5px] px-1.5 py-0.5">
            ⌘↵
          </span>
          <button 
            type="submit"
            className="w-7 h-7 rounded-[7px] bg-[#8B6F4E] flex items-center justify-center text-white hover:opacity-90 transition-opacity cursor-pointer"
          >
            <IconSend className="w-3.5 h-3.5 stroke-[2]" />
          </button>
        </div>
      </form>
    </main>
  );
}
