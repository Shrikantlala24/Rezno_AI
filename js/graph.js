/**
 * Rezno AI — Interactive Concept Map Controller
 * Powered by force-graph with custom canvas rendering and scholarly styling.
 */
class ConceptGraphController {
  constructor(containerId) {
    this.container = document.getElementById(containerId);
    this.fg = null;
    this.rawNodes = [];
    this.rawEdges = [];
    this.layoutMode = 'force'; // 'force' | 'radial'
    this.showMentions = true;
    this.showSimilar = true;
    this.selectedNodeId = null;

    if (this.container && typeof ForceGraph !== 'undefined') {
      this.initGraph();
    }
  }

  initGraph() {
    if (!this.container) return;
    this.container.innerHTML = '';

    const width = this.container.clientWidth || 800;
    const height = this.container.clientHeight || 540;

    const isDark = document.documentElement.classList.contains('dark');
    const paperColor = isDark ? '#2dd4bf' : '#0d5c52';
    const conceptColor = isDark ? '#94a3b8' : '#52637a';
    const mentionsColor = isDark ? 'rgba(45, 212, 191, 0.35)' : 'rgba(13, 92, 82, 0.25)';
    const similarColor = isDark ? 'rgba(148, 163, 184, 0.3)' : 'rgba(100, 116, 139, 0.35)';

    this.fg = ForceGraph()(this.container)
      .width(width)
      .height(height)
      .backgroundColor('rgba(0,0,0,0)')
      .nodeId('id')
      .nodeLabel(node => `${node.name || node.label || node.id} (${node.type})`)
      .nodeVal(node => (node.type === 'paper' ? 5 : 2.5))
      .nodeRelSize(5)
      .nodeColor(node => {
        if (this.selectedNodeId && node.id === this.selectedNodeId) {
          return isDark ? '#fb7185' : '#b4341b';
        }
        return node.type === 'paper' ? paperColor : conceptColor;
      })
      .nodeCanvasObjectMode(() => 'after')
      .nodeCanvasObject((node, ctx, globalScale) => {
        const label = node.name || node.label || node.id;
        const fontSize = Math.max(11 / globalScale, 3);
        ctx.font = `500 ${fontSize}px -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif`;
        ctx.textAlign = 'left';
        ctx.textBaseline = 'middle';
        ctx.fillStyle = isDark ? '#f0f3f6' : '#14171a';
        
        // Show labels when zoomed in or if it's a paper or active selection
        if (globalScale > 0.75 || node.type === 'paper' || node.id === this.selectedNodeId) {
          const text = label.length > 28 ? label.substring(0, 27) + '…' : label;
          ctx.fillText(text, node.x + 9, node.y);
        }
      })
      .linkColor(link => (link.type === 'SIMILAR_TO' ? similarColor : mentionsColor))
      .linkWidth(link => (link.type === 'SIMILAR_TO' ? 1.8 : 1.2))
      .linkDirectionalParticles(link => (link.type === 'MENTIONS' ? 2 : 0))
      .linkDirectionalParticleSpeed(0.006)
      .linkDirectionalParticleWidth(2)
      .linkDirectionalParticleColor(() => (isDark ? '#2dd4bf' : '#0d5c52'))
      .cooldownTicks(120)
      .onNodeClick((node) => {
        this.handleNodeClick(node);
      })
      .onBackgroundClick(() => {
        this.clearSelection();
      });

    const resizeObserver = new ResizeObserver(() => {
      if (this.fg && this.container) {
        const w = this.container.clientWidth;
        const h = this.container.clientHeight;
        if (w > 0 && h > 0) {
          this.fg.width(w).height(h);
        }
      }
    });
    resizeObserver.observe(this.container);
  }

  updateData(graphData) {
    if (!graphData || !this.fg) return;
    this.rawNodes = graphData.nodes || [];
    this.rawEdges = graphData.edges || [];

    const visibleLinks = this.rawEdges.filter(e => {
      const kind = (e.type || 'MENTIONS').toUpperCase();
      if (kind === 'SIMILAR_TO' && !this.showSimilar) return false;
      if (kind === 'MENTIONS' && !this.showMentions) return false;
      return true;
    }).map(e => ({
      source: e.source,
      target: e.target,
      type: e.type || 'MENTIONS'
    }));

    const nodes = this.rawNodes.map(n => ({
      id: n.id,
      name: n.label || n.name || n.id,
      type: n.type || 'concept',
      pdf_url: n.pdf_url || '',
      abs_url: n.abs_url || ''
    }));

    if (this.layoutMode === 'radial') {
      this.applyRadialLayout(nodes, visibleLinks);
    } else {
      nodes.forEach(n => {
        delete n.fx;
        delete n.fy;
      });
    }

    this.fg.graphData({ nodes, links: visibleLinks });
    this.fg.zoomToFit(400, 30);
  }

  applyRadialLayout(nodes, links) {
    const width = this.container.clientWidth || 800;
    const height = this.container.clientHeight || 540;
    const centerX = 0;
    const centerY = 0;

    const paperNodes = nodes.filter(n => n.type === 'paper');
    const conceptNodes = nodes.filter(n => n.type !== 'paper');

    const innerRadius = Math.min(width, height) * 0.22;
    const outerRadius = Math.min(width, height) * 0.44;

    paperNodes.forEach((n, i) => {
      const angle = (i / (paperNodes.length || 1)) * 2 * Math.PI;
      n.fx = centerX + innerRadius * Math.cos(angle);
      n.fy = centerY + innerRadius * Math.sin(angle);
    });

    conceptNodes.forEach((n, i) => {
      const angle = (i / (conceptNodes.length || 1)) * 2 * Math.PI;
      n.fx = centerX + outerRadius * Math.cos(angle);
      n.fy = centerY + outerRadius * Math.sin(angle);
    });
  }

  setLayoutMode(mode) {
    this.layoutMode = mode;
    this.updateData({ nodes: this.rawNodes, edges: this.rawEdges });
  }

  toggleMentions(visible) {
    this.showMentions = visible;
    this.updateData({ nodes: this.rawNodes, edges: this.rawEdges });
  }

  toggleSimilar(visible) {
    this.showSimilar = visible;
    this.updateData({ nodes: this.rawNodes, edges: this.rawEdges });
  }

  zoomIn() {
    if (!this.fg) return;
    this.fg.zoom(this.fg.zoom() * 1.3, 250);
  }

  zoomOut() {
    if (!this.fg) return;
    this.fg.zoom(this.fg.zoom() / 1.3, 250);
  }

  zoomToFit() {
    if (!this.fg) return;
    this.fg.zoomToFit(300, 30);
  }

  focusNode(nodeId) {
    if (!this.fg) return;
    const node = this.rawNodes.find(n => n.id === nodeId);
    if (!node) return;
    this.selectedNodeId = nodeId;
    window.appState.selectedNodeId = nodeId;
    this.fg.centerAt(node.x, node.y, 500);
    this.fg.zoom(2.2, 500);
    this.handleNodeClick(node);
  }

  handleNodeClick(node) {
    if (!node) return;
    this.selectedNodeId = node.id;
    window.appState.selectedNodeId = node.id;
    this.fg.nodeColor(this.fg.nodeColor());

    const degree = this.rawEdges.filter(e => {
      const s = typeof e.source === 'object' ? e.source.id : e.source;
      const t = typeof e.target === 'object' ? e.target.id : e.target;
      return s === node.id || t === node.id;
    }).length;

    renderNodeSelectionPanel({
      id: node.id,
      label: node.name || node.label || node.id,
      type: node.type,
      degree: degree,
      pdf_url: node.pdf_url,
      abs_url: node.abs_url
    });
  }

  clearSelection() {
    this.selectedNodeId = null;
    window.appState.selectedNodeId = "";
    if (this.fg) {
      this.fg.nodeColor(this.fg.nodeColor());
    }
    renderNodeSelectionPanel(null);
  }

  downloadImage() {
    if (!this.container) return;
    const canvas = this.container.querySelector('canvas');
    if (!canvas) return;
    const link = document.createElement('a');
    link.download = `rezno-concept-map-${Date.now()}.png`;
    link.href = canvas.toDataURL('image/png');
    link.click();
  }

  toggleFullscreen() {
    const frame = this.container.closest('.graph-canvas-frame');
    if (!frame) return;
    if (!document.fullscreenElement) {
      frame.requestFullscreen().catch(() => {});
    } else {
      document.exitFullscreen().catch(() => {});
    }
  }
}

window.ConceptGraphController = ConceptGraphController;
