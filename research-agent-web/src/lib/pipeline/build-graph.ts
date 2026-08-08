import { ConceptGraph, GraphEdge, GraphNode, Insight, RankedPaper } from '@/lib/schemas/paper';

export function buildGraph(papers: RankedPaper[], insights: Insight[], k: number = 3): ConceptGraph {
  if (!papers || papers.length === 0) {
    return { nodes: [], edges: [] };
  }

  const nodes: GraphNode[] = papers.map(p => ({
    id: p.arxivId,
    label: p.title,
    type: 'paper',
  }));

  const edges: GraphEdge[] = [];
  const seenConcepts = new Set<string>();
  const knownPapers = new Set(papers.map(p => p.arxivId));

  for (const insight of insights) {
    if (!knownPapers.has(insight.arxivId)) continue;
    for (const concept of insight.concepts) {
      const nodeId = `concept::${concept.toLowerCase()}`;
      if (!seenConcepts.has(nodeId)) {
        seenConcepts.add(nodeId);
        nodes.push({ id: nodeId, label: concept, type: 'concept' });
      }
      edges.push({ source: insight.arxivId, target: nodeId, type: 'MENTIONS' });
    }
  }

  // Add SIMILAR_TO edges between papers
  for (let i = 0; i < papers.length; i++) {
    for (let j = i + 1; j < Math.min(papers.length, i + 1 + k); j++) {
      edges.push({
        source: papers[i].arxivId,
        target: papers[j].arxivId,
        type: 'SIMILAR_TO',
      });
    }
  }

  return { nodes, edges };
}
