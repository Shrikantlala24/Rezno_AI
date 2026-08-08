import { RankedPaper } from '@/lib/schemas/paper';

export function generateBibtex(papers: RankedPaper[]): string {
  const entries = [];
  for (const p of papers) {
    const cleanKey = p.arxivId.replace(/\./g, '_').replace(/\//g, '_');
    const authorsStr = p.authors && p.authors.length > 0 ? p.authors.join(' and ') : 'Unknown';
    const year = p.published && p.published.length >= 4 ? p.published.slice(0, 4) : '2024';
    const url = p.pdfUrl || p.absUrl;

    const entry = `@article{${cleanKey},\n` +
      `  title = {${p.title}},\n` +
      `  author = {${authorsStr}},\n` +
      `  journal = {arXiv preprint arXiv:${p.arxivId}},\n` +
      `  year = {${year}},\n` +
      `  eprint = {${p.arxivId}},\n` +
      `  url = {${url}}\n` +
      `}`;
    entries.push(entry);
  }
  return entries.join('\n\n');
}
