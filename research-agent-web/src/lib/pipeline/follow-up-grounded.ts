import { getLLM } from '@/lib/clients/gemini';
import { RankedPaper, Synthesis, SynthesisSchema } from '@/lib/schemas/paper';

const FOLLOW_UP_PROMPT = `You are answering a follow-up question about research papers already retrieved.

Papers currently in context:
{papers}

Key concepts across these papers: {concepts}
Conversation history: {history}
Follow-up question: {question}

{length_instruction}

Task:
1. Write an answer grounded ONLY in these abstracts.
2. Provide a list of key claims with supporting arXiv IDs and exact sentences.`;

export async function followUpGrounded(
  question: string,
  history: Array<{ role: string; content: string }>,
  papers: RankedPaper[],
  concepts: string[],
  topN: number = 8,
  responseLength: string = 'standard'
): Promise<Synthesis> {
  const top = papers.slice(0, topN);
  const transcript = history.slice(-6).map(m => `${m.role}: ${m.content}`).join('\n') || '(none)';
  const formatted = top.map(p => `[${p.arxivId}] ${p.title}\nAbstract: ${p.summary.slice(0, 1200)}`).join('\n\n');
  const lengthInstruction = 'Length: Respond in 3-5 sentences.';

  const promptText = FOLLOW_UP_PROMPT
    .replace('{papers}', formatted)
    .replace('{concepts}', concepts.join(', ') || '(none)')
    .replace('{history}', transcript)
    .replace('{question}', question)
    .replace('{length_instruction}', lengthInstruction);

  try {
    const llm = getLLM();
    const structured = llm.withStructuredOutput(SynthesisSchema);
    const res = await structured.invoke(promptText);
    if (!res.citations || res.citations.length === 0) {
      res.citations = top.map(p => p.arxivId);
    }
    return res;
  } catch {
    const res = await getLLM().invoke(promptText);
    return {
      summary: typeof res.content === 'string' ? res.content : JSON.stringify(res.content),
      citations: top.map(p => p.arxivId),
      claims: [],
    };
  }
}
