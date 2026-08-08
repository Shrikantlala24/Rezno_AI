import { ArxivPaper, RankedPaper } from '@/lib/schemas/paper';
import { getLLM } from '@/lib/clients/gemini';

export async function rank(papers: ArxivPaper[], query: string, topK: number = 20): Promise<RankedPaper[]> {
  if (papers.length === 0) return [];

  // Use LLM scoring/ranking or heuristic TF-IDF/length match for TS reliability without heavy C++ python bindings
  const scored = papers.map((p, idx) => {
    const text = `${p.title} ${p.summary}`.toLowerCase();
    const qLower = query.toLowerCase();
    const terms = qLower.split(/\s+/);
    let matches = 0;
    for (const term of terms) {
      if (text.includes(term)) matches++;
    }
    const score = (matches / Math.max(1, terms.length)) + (1 / (idx + 1) * 0.1);
    return { ...p, relevanceScore: Number(score.toFixed(4)), status: 'unreviewed' as const, note: null };
  });

  scored.sort((a, b) => b.relevanceScore - a.relevanceScore);
  return scored.slice(0, topK);
}
