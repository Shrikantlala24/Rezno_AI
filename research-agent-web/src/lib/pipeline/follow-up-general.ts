import { getLLM } from '@/lib/clients/gemini';

const WEB_SEARCH_PROMPT = `You are answering a general question in a research assistant chat using general knowledge.

Question: {question}
Conversation so far: {history}

Answer the question clearly in 2-4 sentences. Do NOT invent arXiv IDs or paper citations.`;

export async function followUpGeneral(
  question: string,
  history: Array<{ role: string; content: string }>
): Promise<string> {
  const transcript = history.slice(-6).map(m => `${m.role}: ${m.content}`).join('\n') || '(none)';

  const res = await getLLM().invoke(
    WEB_SEARCH_PROMPT.replace('{question}', question).replace('{history}', transcript)
  );
  return typeof res.content === 'string' ? res.content : JSON.stringify(res.content);
}
