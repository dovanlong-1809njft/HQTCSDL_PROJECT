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

function family(names, relations) {
  return {nodes:names.map(id=>({id,label:id})),edges:relations.map(([source,target,kind="parent_child"],i)=>({id:String(i),source,target,kind}))};
}
for(const [name,tree]of [
  ["couple and one child",family(["a","b","c"],[["a","b","marriage"],["a","c"],["b","c"]])],
  ["couple and siblings",family(["a","b","c","d"],[["a","b","marriage"],["a","c"],["b","c"],["a","d"],["b","d"]])],
  ["three generations and multiple branches",family(["a","b","c","d","e","f"],[["a","b","marriage"],["a","c"],["b","c"],["c","d","marriage"],["c","e"],["d","e"],["a","f"]])],
  ["single parent and unrelated member",family(["a","b","z"],[["a","b"]])],
  ["multiple marriages",family(["a","b","c","d","e"],[["a","b","marriage"],["a","c","marriage"],["a","d"],["b","d"],["a","e"],["c","e"]])],
  ["one member",family(["a"],[])],
])test(name+": stable positions, correct levels and no overlapping cards",()=>{
  const result=layoutTree(tree),pos=new Map(result.nodes.map(n=>[n.id,n.position]));
  assert.equal(result.nodes.length,tree.nodes.length);
  assert.equal(result.edges.length,tree.edges.length);
  for(const e of tree.edges){if(e.kind==="marriage")assert.equal(pos.get(e.source).y,pos.get(e.target).y);else assert.ok(pos.get(e.source).y<pos.get(e.target).y);}
  for(const a of result.nodes)for(const b of result.nodes)if(a.id!==b.id&&a.position.y===b.position.y)assert.ok(Math.abs(a.position.x-b.position.x)>=190);
  assert.deepEqual(layoutTree({nodes:[...tree.nodes].reverse(),edges:[...tree.edges].reverse()}).nodes,result.nodes);
});
test("two real parents share a junction, without adding a marriage",()=>{
  const result=layoutTree(family(["a","b","c"],[["a","c"],["b","c"]]));
  assert.deepEqual(result.edges[0].data.joint,result.edges[1].data.joint);
  assert.ok(result.edges[0].data.joint);
  assert.equal(result.edges.length,2);
});
test("contradictory spouse ranks are flagged without changing edges",()=>{
  const result=layoutTree(family(["a","b","c"],[["a","b"],["b","c"],["a","c","marriage"]]));
  assert.equal(result.hasConflict,true);
  assert.equal(result.edges.length,3);
});
