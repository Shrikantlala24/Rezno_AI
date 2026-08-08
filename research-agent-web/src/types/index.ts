export interface ArxivPaper {
  arxivId: string;
  title: string;
  authors: string[];
  summary: string;
  published: string;
  pdfUrl: string;
  absUrl: string;
  primaryCategory: string;
  categories: string[];
}

export interface RankedPaper extends ArxivPaper {
  relevanceScore: number;
  status: 'unreviewed' | 'keep' | 'maybe' | 'skip';
  note?: string | null;
}

export interface SupportedClaim {
  claim: string;
  arxivId: string;
  supportingSentence: string;
}

export interface Synthesis {
  summary: string;
  citations: string[];
  claims: SupportedClaim[];
}

export interface Insight {
  arxivId: string;
  concepts: string[];
}

export interface GraphNode {
  id: string;
  label: string;
  type: 'paper' | 'concept';
}

export interface GraphEdge {
  source: string;
  target: string;
  type: 'MENTIONS' | 'SIMILAR_TO';
}

export interface ConceptGraph {
  nodes: GraphNode[];
  edges: GraphEdge[];
}

export interface SearchRun {
  id: string;
  query: string;
  queries: string[];
  candidateCount: number;
  papers: RankedPaper[];
  insights: Insight[];
  graph?: ConceptGraph | null;
  synthesis?: Synthesis | null;
  timestamp: string;
}

export interface ChatMessage {
  role: 'user' | 'assistant';
  content: string;
  intent?: 'new_search' | 'follow_up_grounded' | 'follow_up_general';
  searchRunId?: string | null;
  isUnsourced?: boolean;
  isFallback?: boolean;
  claims: SupportedClaim[];
  responseLength: 'brief' | 'standard' | 'detailed';
  timestamp?: string;
}
