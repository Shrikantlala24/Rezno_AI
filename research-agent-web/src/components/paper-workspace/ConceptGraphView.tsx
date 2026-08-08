'use client';

import React, { useEffect, useRef, useState } from 'react';
import dynamic from 'next/dynamic';
import { ConceptGraph } from '@/lib/schemas/paper';

const ForceGraph2D = dynamic(() => import('react-force-graph-2d'), { ssr: false });

interface ConceptGraphViewProps {
  graph: ConceptGraph | null;
}

export function ConceptGraphView({ graph }: ConceptGraphViewProps) {
  const containerRef = useRef<HTMLDivElement>(null);
  const [dimensions, setDimensions] = useState({ width: 500, height: 600 });

  useEffect(() => {
    if (containerRef.current) {
      setDimensions({
        width: containerRef.current.clientWidth || 500,
        height: containerRef.current.clientHeight || 600,
      });
    }
  }, []);

  if (!graph || !graph.nodes || graph.nodes.length === 0) {
    return (
      <div className="flex-1 flex flex-col items-center justify-center text-[var(--color-muted-foreground)] text-sm py-20">
        No concept graph data available for this search run.
      </div>
    );
  }

  const gData = {
    nodes: graph.nodes.map(n => ({
      id: n.id,
      name: n.label,
      val: n.type === 'paper' ? 12 : 5,
      color: n.type === 'paper' ? '#8B6F4E' : '#646262',
      type: n.type,
    })),
    links: graph.edges.map(e => ({
      source: e.source,
      target: e.target,
      color: e.type === 'MENTIONS' ? 'rgba(100,98,98,0.2)' : 'rgba(139,111,78,0.4)',
    })),
  };

  return (
    <div ref={containerRef} className="w-full h-[600px] border border-[var(--color-border)] rounded-xl overflow-hidden bg-[var(--color-card)] relative">
      <div className="absolute top-3 left-3 z-10 bg-[var(--color-background)] border border-[var(--color-border)] rounded-md px-3 py-1.5 text-[11px] font-mono shadow-xs">
        <span className="inline-block w-2.5 h-2.5 rounded-full bg-[#8B6F4E] mr-1.5" /> Paper Nodes (Click to open PDF)
        <span className="inline-block w-2.5 h-2.5 rounded-full bg-[#646262] ml-3 mr-1.5" /> Concept Nodes
      </div>
      <ForceGraph2D
        width={dimensions.width}
        height={dimensions.height}
        graphData={gData}
        nodeLabel="name"
        nodeColor={(node: any) => node.color}
        nodeVal={(node: any) => node.val}
        linkColor={(link: any) => link.color}
        onNodeClick={(node: any) => {
          if (node.type === 'paper') {
            window.open(`https://arxiv.org/abs/${node.id}`, '_blank');
          }
        }}
      />
    </div>
  );
}
