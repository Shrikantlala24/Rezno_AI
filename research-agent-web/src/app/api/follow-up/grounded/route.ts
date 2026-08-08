import { NextResponse } from 'next/server';
import { followUpGrounded } from '@/lib/pipeline/follow-up-grounded';

export async function POST(req: Request) {
  try {
    const body = await req.json();
    const { question, history, papers, concepts, responseLength } = body;
    if (!question) {
      return NextResponse.json({ error: 'Missing question' }, { status: 400 });
    }

    const synthesis = await followUpGrounded(
      question,
      history || [],
      papers || [],
      concepts || [],
      8,
      responseLength || 'standard'
    );

    return NextResponse.json(synthesis);
  } catch (e: any) {
    return NextResponse.json({ error: e.message || 'Internal server error' }, { status: 500 });
  }
}
