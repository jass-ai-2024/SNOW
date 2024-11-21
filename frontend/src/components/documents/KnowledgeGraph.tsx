import React, {useCallback, useMemo} from 'react';
import ReactFlow, {
  Background,
  Controls,
  MiniMap,
  Handle,
  Position,
  useNodesState,
  useEdgesState,
  Node,
  Edge,
  NodeProps,
  MarkerType
} from 'reactflow';
import 'reactflow/dist/style.css';
import {stratify, tree} from "d3";

interface NodeData {
  title: string;
  level: number;
}

type CustomNode = Node<NodeData>;
type CustomEdge = Edge;


const CustomNode = ({ data }: NodeProps<NodeData>) => {
  const getNodeColor = (level: number) => {
    const colors = ['#60a5fa', '#34d399', '#a78bfa', '#f472b6', '#fbbf24'];
    return colors[level % colors.length];
  };

  return (
    <div className="relative">
      <Handle
        type="target"
        position={Position.Top}
        className="!bg-white !w-2 !h-2 !border-2"
        style={{ borderColor: getNodeColor(data.level) }}
      />

      {/* Outer circle with shadow */}
      <div
        className="w-16 h-16 rounded-full flex items-center justify-center shadow-md"
        style={{
          background: getNodeColor(data.level),
          border: '2px solid white',
          width: 200,
          height: 200,
          borderRadius: 100,
          justifyContent: "center",
          alignItems: "center",
          verticalAlign: "middle",
            display: "flex"
        }}
      >
        {/* Title with ellipsis */}
        <div
          className="text-white text-sm font-medium px-2 truncate max-w-[56px]"
          title={data.title}
            style={{textAlign: "center", color: "white", stroke: "1px solid black"}}
        >
          {data.title}
        </div>
      </div>

      <Handle
        type="source"
        position={Position.Bottom}
        className="!bg-white !w-2 !h-2 !border-2"
        style={{ borderColor: getNodeColor(data.level) }}
      />
    </div>
  );
};

const nodeTypes = {
  custom: CustomNode,
};

const KnowledgeGraph: React.FC<{ data: any }> = ({ data }) => {
  const { nodes: initialNodes, edges: initialEdges } = useMemo(() => {
    const nodes: CustomNode[] = [];
    const edges: CustomEdge[] = [];

    // Create nodes
    Object.entries(data.hierarchy).forEach(([docId, doc]: [string, any]) => {
      nodes.push({
        id: docId,
        type: 'custom',
        position: { x: 0, y: 0 },
        data: {
          title: doc.title,
          level: doc.level
        }
      });

      console.log(doc);

      // Create edges
      (doc.children || []).forEach((targetId: string) => {
        edges.push({
          id: `${docId}-${targetId}`,
          source: docId,
          target: targetId,
          type: 'bezier', // Changed to default for straight lines
          style: {
            strokeWidth: 1.5,
            stroke: '#94a3b8'
          },
            label: "children",
          markerEnd: {
            type: MarkerType.Arrow,
            width: 15,
            height: 15,
            color: '#94a3b8',
          },
        });
      });

      (doc.relationships || []).forEach((targetId: string) => {
        if (doc.relationship_type !== "related") {
          return;
        }

        edges.push({
          id: `${docId}-${targetId}`,
          source: docId,
          target: targetId,
          type: 'bezier', // Changed to default for straight lines
          style: {
            strokeWidth: 1.5,
            stroke: '#94a3b8'
          },
            label: "related",
          markerEnd: {
            type: MarkerType.Arrow,
            width: 15,
            height: 15,
            color: '#94a3b8',
          },
        });
      });
    });

    // Layout nodes
    nodes.forEach((node: CustomNode) => {
      const horizontalSpacing = 200;
      const verticalSpacing = 150;

      node.position = {
        x: node.data.level * horizontalSpacing + (Math.random() * 50 - 25),
        y: (node.id.length % 3) * verticalSpacing + (Math.random() * 50 - 25)
      };
    });

    return { nodes, edges };
  }, [data]);

  const [nodes, setNodes, onNodesChange] = useNodesState(initialNodes);
  const [edges, setEdges, onEdgesChange] = useEdgesState(initialEdges);

  const proOptions = { hideAttribution: true };

  return (
    <ReactFlow
      nodes={nodes}
      edges={edges}
      onNodesChange={onNodesChange}
      onEdgesChange={onEdgesChange}
      nodeTypes={nodeTypes}
      fitView
      proOptions={proOptions}
      defaultEdgeOptions={{
        type: 'default',
        style: { stroke: '#94a3b8' },
      }}
    >
      <Background color="#f1f5f9" gap={16} />
      <Controls
        className="bg-white border-none shadow-md rounded-md"
        showInteractive={false}
      />
      <MiniMap
        nodeColor={(node: CustomNode) => {
          const colors = ['#60a5fa', '#34d399', '#a78bfa', '#f472b6', '#fbbf24'];
          return colors[node.data.level % colors.length];
        }}
        maskColor="rgb(241, 245, 249, 0.8)"
        className="bg-white shadow-md rounded-md"
        zoomable
        pannable
      />
    </ReactFlow>
  );
};

const KnowledgeGraphWrapper: React.FC<{ data: any }> = ({ data }) => {
  return (
    <div style={{width: "100%", height: "80%", position: "absolute"}}>
      <KnowledgeGraph data={data} />
    </div>
  );
};

export default KnowledgeGraphWrapper;