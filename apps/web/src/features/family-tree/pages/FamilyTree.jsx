import { useMemo, useState } from "react";
import { useQuery } from "@tanstack/react-query";
import ReactFlow, { Background, Controls, MiniMap } from "reactflow";
import "reactflow/dist/style.css";
import { heritageApi } from "@/features/heritage/api/heritageApi";
import { FamilyScope, QueryState } from "@/features/heritage/components/FamilyScope";
import { layoutTree } from "../layout.mjs";

function TreeCanvas({ data }) {
  const graph = useMemo(() => layoutTree(data), [data]);
  const [animation, setAnimation] = useState(() => data.nodes.length < 300 && !window.matchMedia("(prefers-reduced-motion: reduce)").matches);
  const [selected, setSelected] = useState(null);
  const edges = useMemo(() => graph.edges.map((edge) => ({ ...edge, animated: animation && edge.kind === "parent_child" })), [graph, animation]);
  if (!graph.nodes.length) return <p className="rounded-xl bg-white p-5">Gia đình chưa có hồ sơ gia phả.</p>;
  return <div className="space-y-3">
    <div className="flex flex-wrap gap-4 text-sm text-stone-600"><p>{graph.nodes.length} thành viên · {graph.edges.length} quan hệ</p>
      <label><input type="checkbox" checked={animation} onChange={(e) => setAnimation(e.target.checked)} /> Chuyển động quan hệ</label></div>
    <p className="text-sm text-stone-500">Kéo nền để di chuyển, cuộn/chụm để thu phóng. Đường xanh: cha/mẹ–con; đường vàng đứt: hôn nhân.</p>
    {graph.hasCycle && <p role="alert" className="text-red-700">Dữ liệu có chu trình cha–con. Cần TV2 kiểm tra quan hệ; đồ thị vẫn hiển thị các hồ sơ.</p>}
    <div className="h-[65vh] min-h-[400px] w-full overflow-hidden rounded-2xl border border-stone-200 bg-white" aria-label="Đồ thị gia phả">
      <ReactFlow nodes={graph.nodes} edges={edges} fitView minZoom={0.01} maxZoom={2}
        nodesDraggable={false} nodesConnectable={false} edgesUpdatable={false} onlyRenderVisibleElements
        onNodeClick={(_, node) => setSelected(node)}>
        <Background color="#dbe4d8" /> <Controls showInteractive={false} />
        {graph.nodes.length < 300 && <MiniMap pannable zoomable />}
      </ReactFlow>
    </div>
    {selected && <p role="status" className="rounded-xl bg-sage p-3 text-sm text-forest">{selected.data.label} · Ngày sinh: {selected.data.birthDate || "Chưa ghi"}</p>}
  </div>;
}

function TreeWorkspace({ familyId, user }) {
  const query = useQuery({ queryKey: ["tv4", user.id, familyId, "family-tree"], queryFn: () => heritageApi.tree(familyId) });
  return <><QueryState query={query} />{query.data && <TreeCanvas data={query.data} />}</>;
}

export function FamilyTree() {
  return <FamilyScope title="Cây gia phả" description="Khám phá quan hệ và kết nối giữa các thế hệ trong gia đình.">{(familyId, user) => <TreeWorkspace key={familyId} familyId={familyId} user={user} />}</FamilyScope>;
}
