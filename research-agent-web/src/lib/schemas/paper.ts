import { z } from 'zod';

export const ArxivPaperSchema = z.object({
  arxivId: z.string(),
  title: z.string(),
  authors: z.array(z.string()),
  summary: z.string(),
  published: z.string(),
  pdfUrl: z.string(),
  absUrl: z.string(),
  primaryCategory: z.string(),
  categories: z.array(z.string()),
});

export const RankedPaperSchema = ArxivPaperSchema.extend({
  relevanceScore: z.number(),
  status: z.enum(['unreviewed', 'keep', 'maybe', 'skip']).default('unreviewed'),
  note: z.string().nullable().optional(),
});

export const SupportedClaimSchema = z.object({
  claim: z.string(),
  arxivId: z.string(),
  supportingSentence: z.string(),
});

export const SynthesisSchema = z.object({
  summary: z.string(),
  citations: z.array(z.string()),
  claims: z.array(SupportedClaimSchema),
});

export const QueryPlanSchema = z.object({
  queries: z.array(z.string()).describe('arXiv boolean query variants, 3-4 of them'),
});

export const InsightSchema = z.object({
  arxivId: z.string(),
  concepts: z.array(z.string()),
});

export const InsightSetSchema = z.object({
  insights: z.array(InsightSchema),
});

export const RouteSchema = z.object({
  intent: z.enum(['new_search', 'follow_up_grounded', 'follow_up_general']),
});

export const GraphNodeSchema = z.object({
  id: z.string(),
  label: z.string(),
  type: z.enum(['paper', 'concept']),
});

export const GraphEdgeSchema = z.object({
  source: z.string(),
  target: z.string(),
  type: z.enum(['MENTIONS', 'SIMILAR_TO']),
});

export const ConceptGraphSchema = z.object({
  nodes: z.array(GraphNodeSchema),
  edges: z.array(GraphEdgeSchema),
});

export const SearchRunSchema = z.object({
  id: z.string(),
  query: z.string(),
  queries: z.array(z.string()),
  candidateCount: z.number(),
  papers: z.array(RankedPaperSchema),
  insights: z.array(InsightSchema).default([]),
  graph: ConceptGraphSchema.nullable().optional(),
  synthesis: SynthesisSchema.nullable().optional(),
  timestamp: z.string(),
});

export type ArxivPaper = z.infer<typeof ArxivPaperSchema>;
export type RankedPaper = z.infer<typeof RankedPaperSchema>;
export type SupportedClaim = z.infer<typeof SupportedClaimSchema>;
export type Synthesis = z.infer<typeof SynthesisSchema>;
export type Insight = z.infer<typeof InsightSchema>;
export type Route = z.infer<typeof RouteSchema>;
export type GraphNode = z.infer<typeof GraphNodeSchema>;
export type GraphEdge = z.infer<typeof GraphEdgeSchema>;
export type ConceptGraph = z.infer<typeof ConceptGraphSchema>;
export type SearchRun = z.infer<typeof SearchRunSchema>;
