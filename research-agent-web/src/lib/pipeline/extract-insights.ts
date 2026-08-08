import { getLLM } from '@/lib/clients/gemini';
import { InsightSetSchema, RankedPaper, Insight } from '@/lib/schemas/paper';

const PROMPT = `Extract the key technical concepts from each paper abstract below.

{papers}

For each paper, return 3-6 concepts: methods, architectures, techniques, tasks, or problems the paper is about.
Use lowercase except for proper model or method names (BERT, LoRA, FlashAttention).
Return one entry per paper, using the exact arxiv_id shown in brackets.`;

export async function extractInsights(papers: RankedPaper[]): Promise<Insight[]> {
  if (!papers || papers.length === 0) return [];

  const formatted = papers.map(p => `[${p.arxivId}] ${p.title}\n${p.summary.slice(0, 1000)}`).join('\n\n');

  try {
    const llm = getLLM();
    const structured = llm.withStructuredOutput(InsightSetSchema);
    const result = await structured.invoke(PROMPT.replace('{papers}', formatted));
    
    const valid = new Set(papers.map(p => p.arxivId));
    return result.insights
      .filter(i => valid.has(i.arxivId))
      .map(i => ({
        arxivId: i.arxivId,
        concepts: i.concepts.map(c => c.trim()).filter(Boolean),
      }));
  } catch {
    return [];
  }
}
