import { NextResponse } from 'next/server';
import { followUpGeneral } from '@/lib/pipeline/follow-up-general';

export async function POST(req: Request) {
  try {
    const body = await req.json();
    const { question, history } = body;
    if (!question) {
      return NextResponse.json({ error: 'Missing question' }, { status: 400 });
    }

    const answer = await followUpGeneral(question, history || []);
    return NextResponse.json({ answer });
  } catch (e: any) {
    return NextResponse.json({ error: e.message || 'Internal server error' }, { status: 500 });
  }
}
