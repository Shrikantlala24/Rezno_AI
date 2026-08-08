import arxiv from 'arxiv';
import { ArxivPaper } from '@/lib/schemas/paper';

export async function search(queries: string[], perQuery: number = 80): Promise<ArxivPaper[]> {
  const seen = new Map<string, ArxivPaper>();

  for (const q of queries) {
    try {
      const results = await arxiv.search({
        searchQuery: q,
        maxResults: perQuery,
        sortBy: arxiv.SORT_BY.Relevance,
      });

      for (const result of results) {
        const arxivId = result.id.split('/abs/').pop()?.split('v')[0] || result.id;
        const shortId = result.id.split('/abs/').pop() || arxivId;
        
        const paper: ArxivPaper = {
          arxivId: shortId,
          title: (result.title || '').trim().replace(/\n/g, ' '),
          authors: (result.authors || []).map((a: any) => typeof a === 'string' ? a : a.name),
          summary: (result.summary || '').trim().replace(/\n/g, ' '),
          published: result.published || new Date().toISOString(),
          pdfUrl: result.pdfUrl || `https://arxiv.org/pdf/${shortId}`,
          absUrl: result.id || `https://arxiv.org/abs/${shortId}`,
          primaryCategory: result.primaryCategory || 'cs.CL',
          categories: result.categories || ['cs.CL'],
        };

        if (!seen.has(paper.arxivId)) {
          seen.set(paper.arxivId, paper);
        }
      }
    } catch (e) {
      console.warn(`arXiv query failed for variant ${q}:`, e);
    }
  }

  return Array.from(seen.values());
}
