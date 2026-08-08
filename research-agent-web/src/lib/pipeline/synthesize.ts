import { getLLM } from '@/lib/clients/gemini';
import { RankedPaper, Synthesis, SynthesisSchema } from '@/lib/schemas/paper';

const LENGTH_INSTRUCTIONS: Record<string, string> = {
  brief: 'Length: Respond in 1-2 sentences only. Be concise and direct.',
  standard: 'Length: Respond in 3-5 sentences. Include a reasonable set of supporting claims.',
  detailed: 'Length: Provide a thorough 5-8 sentence synthesis. Surface as many supported claims as possible.',
};

const PROMPT = `You are synthesizing a research summary for the research question below.

Question: {query}

Papers:
{papers}

{length_instruction}

Task:
1. Write a prose summary answering the question, citing papers inline by arxiv_id in square brackets (e.g. [2401.12345]).
2. Provide a list of key claims made in your answer with supporting sentences.`;

export async function synthesize(
  query: string,
  papers: RankedPaper[],
  topN: number = 8,
  responseLength: string = 'standard'
): Promise<Synthesis> {
  const top = papers.slice(0, topN);
  if (top.length === 0) {
    return { summary: 'No papers found for this query.', citations: [], claims: [] };
  }

  const formatted = top.map(p => `[${p.arxivId}] ${p.title}\nAbstract: ${p.summary.slice(0, 1200)}`).join('\n\n');
  const lengthInstruction = LENGTH_INSTRUCTIONS[responseLength] || LENGTH_INSTRUCTIONS['standard'];

  try {
    const llm = getLLM();
    const structured = llm.withStructuredOutput(SynthesisSchema);
    const res = await structured.invoke(
      PROMPT.replace('{query}', query).replace('{papers}', formatted).replace('{length_instruction}', lengthInstruction)
    );
    if (!res.citations || res.citations.length === 0) {
      res.citations = top.map(p => p.arxivId);
    }
    return res;
  } catch {
    const res = await getLLM().invoke(
      PROMPT.replace('{query}', query).replace('{papers}', formatted).replace('{length_instruction}', lengthInstruction)
    );
    return {
      summary: typeof res.content === 'string' ? res.content : JSON.stringify(res.content),
      citations: top.map(p => p.arxivId),
      claims: [],
    };
  }
}
