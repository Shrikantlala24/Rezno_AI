export async function getCitations(arxivId: string): Promise<{ references: any[]; citations: any[] }> {
  const cleanId = arxivId.split('v')[0];
  try {
    const resp = await fetch(`https://api.semanticscholar.org/graph/v1/paper/arXiv:${cleanId}?fields=citations,references`, {
      headers: { 'User-Agent': 'ResearchAgentPrototype/1.0' },
    });
    if (!resp.ok) return { references: [], citations: [] };
    const data = await resp.json();

    const parseItem = (item: any) => {
      const extIds = item.externalIds || {};
      const itemArxiv = extIds.ArXiv || extIds.arXiv || item.paperId || '';
      const authors = (item.authors || []).map((a: any) => a.name).filter(Boolean);
      return {
        arxivId: itemArxiv,
        title: item.title || 'Untitled',
        authors,
        year: String(item.year || ''),
        raw: item,
      };
    };

    const references = (data.references || []).filter((r: any) => r && r.title).map(parseItem);
    const citations = (data.citations || []).filter((c: any) => c && c.title).map(parseItem);

    return { references, citations };
  } catch {
    return { references: [], citations: [] };
  }
}
