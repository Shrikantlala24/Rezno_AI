import { getLLM } from '@/lib/clients/gemini';
import { QueryPlanSchema } from '@/lib/schemas/paper';

const PROMPT = `Convert this research question into arXiv API search queries.

Question: {query}

arXiv search is Lucene keyword matching over titles and abstracts only — there is no full-text index and no semantic understanding. A raw question performs badly.
Your job is to produce queries whose keywords actually appear in the abstracts of the relevant papers.

Write 3-4 query variants that differ in strategy, for example:
- the canonical technical term for the topic (what the papers call themselves)
- a well-known method or model name in this area, if one exists
- a broader phrasing scoped by category

Syntax:
- Field prefixes: all:, ti:, abs:, cat:
- Operators: AND, OR, ANDNOT
- Quote multi-word phrases: abs:"retrieval augmented generation"
- Scope with cat: when the field is obvious (cs.CL, cs.LG, cs.CV, cs.AI, cs.IR, stat.ML)
- Add submittedDate:[YYYYMMDDHHMM TO YYYYMMDDHHMM] ONLY if the question asks for recent/latest work

Rules:
- Use terminology the papers themselves use, not the user's phrasing
- Keep each variant focused; do not AND together many terms or you get zero results
- Vary specificity: at least one narrow variant and one broader variant`;

export async function planQuery(query: string, numQueries: number = 4): Promise<string[]> {
  try {
    const llm = getLLM();
    const structured = llm.withStructuredOutput(QueryPlanSchema);
    const res = await structured.invoke(PROMPT.replace('{query}', query));
    const variants = res.queries.map(q => q.trim()).filter(Boolean);
    return variants.length > 0 ? variants.slice(0, numQueries) : [query];
  } catch {
    return [query];
  }
}
