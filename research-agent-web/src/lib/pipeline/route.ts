import { getLLM } from '@/lib/clients/gemini';
import { RouteSchema, RankedPaper } from '@/lib/schemas/paper';

const PROMPT = `Classify the user's message in a research-paper chat.

Papers currently loaded in the conversation:
{papers}

Recent conversation:
{history}

User's new message: {message}

Choose one:
- "follow_up_grounded": the message asks about, compares, clarifies, or drills into the papers already loaded, or about specific findings/abstracts in loaded papers.
- "follow_up_general": the message asks a general conceptual, background, or foundational question that is not specific to the loaded paper abstracts and does NOT require searching arXiv.
- "new_search": the message asks about a topic the loaded papers do not cover, and answering it requires searching arXiv for different research papers.`;

export async function routeQuery(message: string, papers: RankedPaper[], history: Array<{ role: string; content: string }> = []): Promise<[string, boolean]> {
  if (!papers || papers.length === 0) {
    return ['new_search', false];
  }

  const titles = papers.slice(0, 10).map(p => `- [${p.arxivId}] ${p.title}`).join('\n');
  const transcript = history.slice(-6).map(m => `${m.role}: ${m.content.slice(0, 300)}`).join('\n') || '(none)';

  try {
    const llm = getLLM();
    const structured = llm.withStructuredOutput(RouteSchema);
    const res = await structured.invoke(
      PROMPT.replace('{papers}', titles).replace('{history}', transcript).replace('{message}', message)
    );
    return [res.intent, false];
  } catch {
    return ['follow_up_general', true];
  }
}
