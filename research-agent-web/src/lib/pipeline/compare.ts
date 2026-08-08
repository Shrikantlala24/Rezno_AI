import { SearchRun, RankedPaper } from '@/lib/schemas/paper';

export interface ComparisonResult {
  sharedPapers: RankedPaper[];
  uniqueToARun: RankedPaper[];
  uniqueToBRun: RankedPaper[];
  sharedConcepts: string[];
  uniqueToAConcepts: string[];
  uniqueToBConcepts: string[];
}

export function compareSearches(runA: SearchRun, runB: SearchRun): ComparisonResult {
  const papersA = runA.papers || [];
  const papersB = runB.papers || [];

  const mapB = new Map(papersB.map(p => [p.arxivId, p]));
  const mapA = new Map(papersA.map(p => [p.arxivId, p]));

  const sharedPapers = papersA.filter(p => mapB.has(p.arxivId));
  const uniqueToARun = papersA.filter(p => !mapB.has(p.arxivId));
  const uniqueToBRun = papersB.filter(p => !mapA.has(p.arxivId));

  const conceptsA = new Set(runA.insights?.flatMap(i => i.concepts) || []);
  const conceptsB = new Set(runB.insights?.flatMap(i => i.concepts) || []);

  const sharedConcepts: string[] = [];
  const uniqueToAConcepts: string[] = [];
  const uniqueToBConcepts: string[] = [];

  for (const c of conceptsA) {
    if (conceptsB.has(c)) sharedConcepts.push(c);
    else uniqueToAConcepts.push(c);
  }

  for (const c of conceptsB) {
    if (!conceptsA.has(c)) uniqueToBConcepts.push(c);
  }

  return {
    sharedPapers,
    uniqueToARun,
    uniqueToBRun,
    sharedConcepts,
    uniqueToAConcepts,
    uniqueToBConcepts,
  };
}
