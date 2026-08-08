import { planQuery } from '@/lib/pipeline/plan-query';
import { search } from '@/lib/pipeline/search';
import { rank } from '@/lib/pipeline/rank';
import { extractInsights } from '@/lib/pipeline/extract-insights';
import { buildGraph } from '@/lib/pipeline/build-graph';
import { synthesize } from '@/lib/pipeline/synthesize';
import { ConceptGraph, Insight, RankedPaper, Synthesis } from '@/lib/schemas/paper';

export interface PipelineResult {
  query: string;
  queries: string[];
  candidateCount: number;
  papers: RankedPaper[];
  insights: Insight[];
  graph?: ConceptGraph | null;
  synthesis?: Synthesis | null;
}

export async function runPipeline(
  query: string,
  topK: number = 20,
  perQuery: number = 80,
  numQueries: number = 4,
  show: number = 8,
  expand: boolean = true,
  withGraph: boolean = true,
  withSynthesis: boolean = true,
  responseLength: string = 'standard'
): Promise<PipelineResult> {
  const queries = expand ? await planQuery(query, numQueries) : [query];
  const candidates = await search(queries, perQuery);
  const papers = await rank(candidates, query, topK);

  const result: PipelineResult = {
    query,
    queries,
    candidateCount: candidates.length,
    papers,
    insights: [],
    graph: null,
    synthesis: null,
  };

  if (withGraph && papers.length > 0) {
    result.insights = await extractInsights(papers);
    result.graph = buildGraph(papers, result.insights);
  }

  if (withSynthesis) {
    result.synthesis = await synthesize(query, papers, show, responseLength);
  }

  return result;
}
