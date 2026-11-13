// Linear graph traversal; independent of React and never reads mock fixtures.
export function layoutTree(tree) {
  const ids = new Set(tree.nodes.map((node) => node.id));
  const uniqueNodes = [...new Map(tree.nodes.map((node) => [node.id, node])).values()];
  const edges = [...new Map(tree.edges.filter((edge) => ids.has(edge.source) && ids.has(edge.target) && edge.source !== edge.target)
    .map((edge) => [edge.id, edge])).values()];
  const children = new Map(uniqueNodes.map((node) => [node.id, []]));
  const degree = new Map(uniqueNodes.map((node) => [node.id, 0]));
  const levels = new Map(uniqueNodes.map((node) => [node.id, 0]));
  for (const edge of edges.filter((edge) => edge.kind === "parent_child")) {
    children.get(edge.source).push(edge.target);
    degree.set(edge.target, degree.get(edge.target) + 1);
  }
  const queue = uniqueNodes.filter((node) => degree.get(node.id) === 0).map((node) => node.id);
  for (let i = 0; i < queue.length; i += 1) {
    const id = queue[i];
    for (const child of children.get(id)) {
      levels.set(child, Math.max(levels.get(child), levels.get(id) + 1));
      degree.set(child, degree.get(child) - 1);
      if (degree.get(child) === 0) queue.push(child);
    }
  }
  const rows = new Map();
  const nodes = uniqueNodes.map((node) => {
    const level = levels.get(node.id);
    const column = rows.get(level) || 0;
    rows.set(level, column + 1);
    return { id: node.id, data: { label: node.label, birthDate: node.birth_date },
      position: { x: column * 230, y: level * 160 },
      style: { width: 190, borderRadius: 12, padding: 12, borderColor: "#62836c", background: "#fff" } };
  });
  return { nodes, edges: edges.map((edge) => ({ ...edge,
    label: edge.kind === "marriage" ? "Hôn nhân" : undefined,
    type: edge.kind === "marriage" ? "straight" : "smoothstep",
    style: edge.kind === "marriage" ? { stroke: "#b7791f", strokeDasharray: "6 4" } : { stroke: "#62836c" },
  })), hasCycle: queue.length !== uniqueNodes.length };
}
