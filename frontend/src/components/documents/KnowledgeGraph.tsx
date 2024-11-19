import React, { useMemo } from 'react';
import Plot from 'react-plotly.js';
import { Data, Layout } from 'plotly.js';

interface Node {
  id: string;
  title: string;
  summary: string;
  relationships: string[];
  relationship_type: string;
  key_concepts: string[];
}

const KnowledgeGraph: React.FC<{ data: any }> = ({ data }) => {
  const { nodes, edges } = useMemo(() => {
    const nodes: Node[] = [];
    const edges: { from: string; to: string }[] = [];
    const processed = new Set();

    Object.values(data.documents).forEach((doc: any) => {
      if (doc.hierarchy) {
        nodes.push({
          id: doc.metadata.doc_id,
          title: doc.hierarchy.title || doc.metadata.file_name,
          summary: doc.hierarchy.summary || '',
          relationships: doc.hierarchy.relationships || [],
          relationship_type: doc.hierarchy.relationship_type || '',
          key_concepts: doc.hierarchy.key_concepts || []
        });

        if (!processed.has(doc.metadata.doc_id)) {
          (doc.hierarchy.relationships || []).forEach((relatedId: string) => {
            edges.push({ from: doc.metadata.doc_id, to: relatedId });
          });
          processed.add(doc.metadata.doc_id);
        }
      }
    });

    return { nodes, edges };
  }, [data]);

  // Calculate node positions in a circle
  const nodePositions = nodes.map((_, i) => ({
    x: Math.cos(2 * Math.PI * i / nodes.length),
    y: Math.sin(2 * Math.PI * i / nodes.length)
  }));

  // Create node scatter plot
  const nodesTrace: Data = {
    type: 'scatter',
    x: nodePositions.map(p => p.x),
    y: nodePositions.map(p => p.y),
    mode: 'text+markers',
    text: nodes.map(n => n.title),
    textposition: 'top center',
    hovertext: nodes.map(n =>
      `${n.title}\n\nSummary: ${n.summary}\n\nKey Concepts: ${n.key_concepts.join(', ')}`
    ),
    hoverinfo: 'text',
    marker: {
      size: 20,
      color: nodes.map(n => ['parent', 'child', 'sibling'].indexOf(n.relationship_type)),
      colorscale: 'Viridis'
    }
  };

  // Create edges
  const edgesTraces: any = edges.map(edge => {
    const fromNode = nodes.findIndex(n => n.id === edge.from);
    const toNode = nodes.findIndex(n => n.id === edge.to);

    if (fromNode === -1 || toNode === -1) return null;

    return {
      type: 'scatter',
      x: [nodePositions[fromNode].x, nodePositions[toNode].x],
      y: [nodePositions[fromNode].y, nodePositions[toNode].y],
      mode: 'lines',
      line: {
        color: '#a0a0a0',
        width: 1
      },
      hoverinfo: 'none'
    } as Data;
  }).filter(Boolean);

  const plotLayout: Partial<Layout> = {
    title: 'Knowledge Graph',
    showlegend: false,
    hovermode: 'closest',
    margin: { l: 50, r: 50, b: 50, t: 50 },
    xaxis: {
      showgrid: false,
      zeroline: false,
      showticklabels: false,
      range: [-1.5, 1.5]
    },
    yaxis: {
      showgrid: false,
      zeroline: false,
      showticklabels: false,
      range: [-1.5, 1.5]
    },
    width: 800,
    height: 600
  };

  return (
    <Plot
      data={[...edgesTraces, nodesTrace]}
      layout={plotLayout}
      useResizeHandler
      style={{ width: '100%', height: '600px' }}
    />
  );
};

export default KnowledgeGraph;