// Deterministic synthetic stress fixture. Not imported by application code or seeded into SQL.
import { writeFileSync } from "node:fs";

const uuid = (n) => `00000000-0000-4000-8000-${String(n).padStart(12, "0")}`;
export function generateTree(size = 1023) {
  const nodes = Array.from({ length: size }, (_, index) => ({ id: uuid(index + 1), label: `Thành viên thử ${index + 1}`, birth_date: null }));
  const edges = nodes.slice(1).map((node, index) => ({ id: `parent-${index + 2}`, source: uuid(Math.floor((index + 2) / 2)), target: node.id, kind: "parent_child" }));
  // Separate spouse nodes at the leaf generation, with no extra ancestry.
  for (let i = Math.floor(size / 2) + 1; i < size; i += 2) edges.push({ id: `marriage-${i}`, source: uuid(i), target: uuid(i + 1), kind: "marriage" });
  return { family_id: uuid(999999), nodes, edges };
}

if (process.argv[1] && new URL(import.meta.url).pathname.toLowerCase().endsWith(process.argv[1].replaceAll("\\", "/").split("/").pop().toLowerCase())) {
  writeFileSync(new URL("./tv4-family-tree-large.json", import.meta.url), JSON.stringify(generateTree(), null, 2) + "\n");
}
