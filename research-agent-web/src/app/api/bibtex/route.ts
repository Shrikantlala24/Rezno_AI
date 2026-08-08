import { NextResponse } from 'next/server';
import { generateBibtex } from '@/lib/pipeline/bibtex';

export async function POST(req: Request) {
  try {
    const body = await req.json();
    const { papers } = body;
    if (!papers || !Array.isArray(papers)) {
      return NextResponse.json({ error: 'Missing papers array' }, { status: 400 });
    }

    const bibtex = generateBibtex(papers);
    return NextResponse.json({ bibtex });
  } catch (e: any) {
    return NextResponse.json({ error: e.message || 'Internal server error' }, { status: 500 });
  }
}
