import { NextResponse } from 'next/server';
import { routeQuery } from '@/lib/pipeline/route';

export async function POST(req: Request) {
  try {
    const body = await req.json();
    const { message, papers, history } = body;
    if (!message) {
      return NextResponse.json({ error: 'Missing message' }, { status: 400 });
    }

    const [intent, isFallback] = await routeQuery(message, papers || [], history || []);
    return NextResponse.json({ intent, isFallback });
  } catch (e: any) {
    return NextResponse.json({ error: e.message || 'Internal server error' }, { status: 500 });
  }
}
