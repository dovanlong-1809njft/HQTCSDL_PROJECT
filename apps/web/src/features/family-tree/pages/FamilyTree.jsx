import { useMemo, useState } from "react";
import { useQuery } from "@tanstack/react-query";
import ReactFlow, { Background, Controls, MiniMap, Handle, Position, BaseEdge, getSmoothStepPath } from "reactflow";
import "reactflow/dist/style.css";
import { heritageApi } from "@/features/heritage/api/heritageApi";
import { FamilyScope, QueryState } from "@/features/heritage/components/FamilyScope";
import { layoutTree } from "../layout.mjs";
import { Relationships } from "@/features/genealogy/components/Relationships";
import {safeMedia} from "@/shared/media.mjs";

function MemberNode({data}) {
  const [broken,setBroken]=useState(false);
  const avatar=safeMedia(data.avatar);
  return <div className="family-node" style={{padding:10}}>
    <Handle id="parents" type="target" position={Position.Top}/><Handle id="children" type="source" position={Position.Bottom}/>
    <Handle id="left" type="source" position={Position.Left}/><Handle id="left" type="target" position={Position.Left}/>
    <Handle id="right" type="source" position={Position.Right}/><Handle id="right" type="target" position={Position.Right}/>
    <span className="family-node-avatar">{avatar&&!broken?<img src={avatar} alt="" onError={()=>setBroken(true)}/>:"👤"}</span>
    <span><strong>{data.label||"Chưa ghi tên"}</strong><small>{data.birthDate||"Chưa ghi ngày sinh"}</small></span>
  </div>;
}
function FamilyEdge(props) {
  const {sourceX,sourceY,targetX,targetY,data}=props;
  const joint=data?.joint;
  const path=joint&&targetY>joint.y?`M ${sourceX},${sourceY} V ${joint.y} H ${joint.x} V ${targetY-40} H ${targetX} V ${targetY}`:getSmoothStepPath(props)[0];
  return <BaseEdge id={props.id} path={path} style={props.style}/>;
}
function MarriageEdge(props) {
  const {sourceX,sourceY,targetX,targetY}=props;
  const direction=sourceX<targetX?1:-1;
  const lane=Math.min(sourceY,targetY)-70;
  const distant=Math.abs(sourceX-targetX)>80||sourceY!==targetY;
  const path=distant?`M ${sourceX},${sourceY} H ${sourceX+direction*18} V ${lane} H ${targetX-direction*18} V ${targetY} H ${targetX}`:`M ${sourceX},${sourceY} L ${targetX},${targetY}`;
  return <BaseEdge id={props.id} path={path} style={props.style} label={props.label} labelX={(sourceX+targetX)/2} labelY={distant?lane:sourceY}/>;
}
const nodeTypes={member:MemberNode},edgeTypes={family:FamilyEdge,marriage:MarriageEdge};

function TreeCanvas({ data }) {
  const graph = useMemo(() => layoutTree(data), [data]);
  const [animation, setAnimation] = useState(() => data.nodes.length < 300 && !window.matchMedia("(prefers-reduced-motion: reduce)").matches);
  const [selected, setSelected] = useState(null);
  const related=useMemo(()=>new Set(selected?[selected.id,...graph.edges.filter(e=>e.source===selected.id||e.target===selected.id).flatMap(e=>[e.source,e.target])]:[]),[graph,selected]);
  const nodes=useMemo(()=>graph.nodes.map(n=>({...n,selected:n.id===selected?.id,style:{...n.style,opacity:selected&&!related.has(n.id)?0.45:1,boxShadow:n.id===selected?.id?"0 0 0 3px #276244":undefined}})),[graph,selected,related]);
  const edges = useMemo(() => graph.edges.map((edge) => ({ ...edge, animated: animation && edge.kind === "parent_child",style:{...edge.style,strokeWidth:selected&&(edge.source===selected.id||edge.target===selected.id)?3:1.5,opacity:selected&&edge.source!==selected.id&&edge.target!==selected.id?0.2:1} })), [graph, animation,selected]);
  if (!graph.nodes.length) return <p className="rounded-xl bg-white p-5">Gia đình chưa có hồ sơ gia phả.</p>;
  return <div className="space-y-3">
    <div className="flex flex-wrap gap-4 text-sm text-stone-600"><p>{graph.nodes.length} thành viên · {graph.edges.length} quan hệ</p>
      <label><input type="checkbox" checked={animation} onChange={(e) => setAnimation(e.target.checked)} /> Chuyển động quan hệ</label></div>
    <p className="text-sm text-stone-500">Kéo nền để di chuyển, cuộn/chụm để thu phóng. Đường xanh: cha/mẹ–con; đường vàng đứt: hôn nhân.</p>
    {graph.hasCycle && <p role="alert" className="text-red-700">Dữ liệu có chu trình cha–con. Cần TV2 kiểm tra quan hệ; đồ thị vẫn hiển thị các hồ sơ.</p>}
    {graph.hasConflict&&<p role="alert" className="text-red-700">Quan hệ hôn nhân mâu thuẫn với tầng cha mẹ–con. Giữ nguyên quan hệ và ưu tiên phân tầng huyết thống.</p>}
    {graph.hasInvalidRelations&&<p role="alert" className="text-red-700">Có quan hệ tự thân hoặc thiếu hồ sơ liên quan; các đường nối này chưa thể hiển thị. Cần kiểm tra dữ liệu nguồn.</p>}
    <div className="h-[65vh] min-h-[400px] w-full overflow-hidden rounded-2xl border border-stone-200 bg-white" aria-label="Đồ thị gia phả">
      <ReactFlow nodes={nodes} edges={edges} nodeTypes={nodeTypes} edgeTypes={edgeTypes} fitView minZoom={0.01} maxZoom={2}
        nodesDraggable={false} nodesConnectable={false} edgesUpdatable={false} onlyRenderVisibleElements
        onPaneClick={()=>setSelected(null)} onNodeClick={(_, node) => setSelected(node)}>
        <Background color="#dbe4d8" /> <Controls showInteractive={false} />
        {graph.nodes.length < 300 && <MiniMap pannable zoomable />}
      </ReactFlow>
    </div>
    {selected && <p role="status" className="rounded-xl bg-sage p-3 text-sm text-forest">{selected.data.label} · Ngày sinh: {selected.data.birthDate || "Chưa ghi"}</p>}
  </div>;
}

function TreeWorkspace({ familyId, user }) {
  const query = useQuery({ queryKey: ["tv4", user.id, familyId, "family-tree"], queryFn: () => heritageApi.tree(familyId) });
  return <><QueryState query={query} />{query.data && <TreeCanvas data={query.data} />}<Relationships familyId={familyId} user={user} /></>;
}

export function FamilyTree() {
  return <FamilyScope title="Cây gia phả" description="Khám phá quan hệ và kết nối giữa các thế hệ trong gia đình.">{(familyId, user) => <TreeWorkspace key={familyId} familyId={familyId} user={user} />}</FamilyScope>;
}
