import { test } from "node:test";
import assert from "node:assert/strict";
import { layoutTree } from "../../apps/web/src/features/family-tree/layout.mjs";
import { generateTree } from "../../packages/mock-data/generate-tv4-tree.mjs";

test("empty graph", () => {
  assert.deepEqual(layoutTree({ nodes: [], edges: [] }), { nodes: [], edges: [], hasCycle: false });
});

test("1023 members, ten generations: no overlaps and parent above child", () => {
  const source = generateTree();
  const graph = layoutTree(source);
  assert.equal(graph.nodes.length, 1023);
  assert.equal(graph.edges.length, source.edges.length);
  assert.equal(graph.hasCycle, false);
  const positions = new Map(graph.nodes.map((node) => [node.id, node.position]));
  assert.equal(new Set(graph.nodes.map((node) => `${node.position.x},${node.position.y}`)).size, 1023);
  for (const edge of graph.edges.filter((edge) => edge.kind === "parent_child")) {
    assert.ok(positions.get(edge.source).y < positions.get(edge.target).y);
  }
  assert.equal(new Set(graph.nodes.map((node) => node.position.y)).size, 10);
  assert.ok(graph.edges.some((edge) => edge.kind === "marriage" && edge.style.strokeDasharray));
});

test("duplicate and dangling references never add duplicate elements", () => {
  const nodes = [{ id: "a", label: "A" }, { id: "b", label: "B" }];
  const edge = { id: "ab", source: "a", target: "b", kind: "parent_child" };
  const graph = layoutTree({ nodes: [...nodes, nodes[0]], edges: [edge, edge, { ...edge, id: "bad", target: "missing" }] });
  assert.equal(graph.nodes.length, 2);
  assert.equal(graph.edges.length, 1);
});

test("legacy cycles are reported and terminate without recursion", () => {
  const graph = layoutTree({ nodes: [{ id: "a" }, { id: "b" }], edges: [
    { id: "ab", source: "a", target: "b", kind: "parent_child" },
    { id: "ba", source: "b", target: "a", kind: "parent_child" },
  ] });
  assert.equal(graph.hasCycle, true);
  assert.equal(graph.nodes.length, 2);
});
