import { NextResponse } from 'next/server';
import { runPipeline } from '@/lib/pipeline/pipeline';

export async function POST(req: Request) {
  try {
    const body = await req.json();
    const { query, topK, responseLength } = body;
    if (!query) {
      return NextResponse.json({ error: 'Missing query' }, { status: 400 });
    }

    const result = await runPipeline(
      query,
      topK || 20,
      80,
      4,
      8,
      true,
      true,
      true,
      responseLength || 'standard'
    );

    return NextResponse.json({
      id: `run-${Date.now()}`,
      query,
      queries: result.queries,
      candidateCount: result.candidateCount,
      papers: result.papers,
      insights: result.insights,
      graph: result.graph,
      synthesis: result.synthesis,
      timestamp: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit', second: '2-digit' }),
    });
  } catch (e: any) {
    return NextResponse.json({ error: e.message || 'Internal server error' }, { status: 500 });
  }
}
