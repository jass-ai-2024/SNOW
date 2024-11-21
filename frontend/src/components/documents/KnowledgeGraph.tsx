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
import { stratify, tree } from 'd3-hierarchy';


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

function layoutNodesHierarchically(nodes, edges) {
  // Построим граф для проверки циклов
  const graph = new Map();
  nodes.forEach(node => graph.set(node.id, new Set()));
  edges.forEach(edge => graph.get(edge.source).add(edge.target));

  // Функция для проверки цикла
  function hasCycle(node, visited = new Set(), path = new Set()) {
    if (path.has(node)) return true;
    if (visited.has(node)) return false;

    visited.add(node);
    path.add(node);

    const neighbors = graph.get(node);
    for (const neighbor of neighbors) {
      if (hasCycle(neighbor, visited, path)) return true;
    }

    path.delete(node);
    return false;
  }

  // Проверяем и удаляем циклические связи
  const validEdges = edges.filter(edge => {
    const hasLoop = hasCycle(edge.source);
    if (hasLoop) {
      graph.get(edge.source).delete(edge.target);
      return false;
    }
    return true;
  });

  const virtualRootId = 'virtual-root';
  const rootNodes = nodes.filter(node =>
    !validEdges.some(edge => edge.target === node.id)
  );

  const virtualEdges = rootNodes.map(node => ({
    source: virtualRootId,
    target: node.id
  }));

  const nodesWithRoot = [
    { id: virtualRootId, data: { title: 'Root', level: -1 }, position: { x: 0, y: 0 } },
    ...nodes
  ];

  const hierarchy = stratify()
    .id((d: any) => d.id)
    .parentId((d: any) => {
      const parentEdge = [...validEdges, ...virtualEdges].find(e => e.target === d.id);
      return parentEdge ? parentEdge.source : null;
    })(nodesWithRoot);

  const treeLayout = tree()
    .nodeSize([250, 400]);

  const root = treeLayout(hierarchy);

  root.each(node => {
    if (node.id !== virtualRootId) {
      const originalNode = nodes.find(n => n.id === node.id);
      if (originalNode) {
        originalNode.position = {
          x: node.x,
          y: node.y
        };
      }
    }
  });

  return nodes;
}


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
            label: "child",
          markerEnd: {
            type: MarkerType.Arrow,
            width: 15,
            height: 15,
            color: '#94a3b8',
          },
        });
      });

      (doc.relationships || [])
          .filter(targetId => !(doc.children || []).includes(targetId))
          .forEach((targetId: string) => {
            if(doc.relationship_type === "child") {
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
    layoutNodesHierarchically(nodes, edges);

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