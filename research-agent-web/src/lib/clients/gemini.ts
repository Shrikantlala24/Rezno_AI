import { ChatGoogleGenerativeAI } from '@langchain/google-genai';

let _llm: ChatGoogleGenerativeAI | null = null;

export function getLLM(temperature: number = 0.0): ChatGoogleGenerativeAI {
  if (!_llm) {
    const apiKey = process.env.GOOGLE_API_KEY || process.env.GEMINI_API_KEY;
    if (!apiKey) {
      throw new Error('Missing GOOGLE_API_KEY or GEMINI_API_KEY in environment.');
    }
    _llm = new ChatGoogleGenerativeAI({
      model: process.env.LLM_MODEL || 'gemini-2.5-flash',
      temperature,
      apiKey,
    });
  }
  return _llm;
}
