import { NextResponse } from 'next/server';
import { getCitations } from '@/lib/pipeline/citations';

export async function GET(req: Request, { params }: { params: Promise<{ arxivId: string }> }) {
  try {
    const { arxivId } = await params;
    const data = await getCitations(arxivId);
    return NextResponse.json(data);
  } catch (e: any) {
    return NextResponse.json({ error: e.message || 'Internal server error' }, { status: 500 });
  }
}