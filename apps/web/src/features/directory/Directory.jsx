import { useState } from "react";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { api, getApiErrorMessage } from "@/shared/api/client";
import { FamilyScope, fieldClass, buttonClass, Pager, QueryState } from "@/features/heritage/components/FamilyScope";
import { genealogyApi } from "@/features/genealogy/api/genealogyApi";

import {MemberHistoryPanel} from "@/features/genealogy/components/MemberHistoryPanel";
function DirectoryWorkspace({familyId,user}) {
  const [filters,setFilters]=useState({}),[page,setPage]=useState(1),[selected,setSelected]=useState(null);
  const query=useQuery({queryKey:["directory",user.id,familyId,filters,page],queryFn:async()=>(await api.get("/directory",{params:{family_id:familyId,page,...filters}})).data});
  const branches=useQuery({queryKey:["genealogy",user.id,familyId,"directory-branches"],queryFn:()=>genealogyApi.branches(familyId)});
  if(selected)return <MemberHistoryPanel familyId={familyId} user={user} id={selected} onClose={()=>setSelected(null)}/>;
  return <div className="space-y-5"><form className="grid gap-4 rounded-2xl border border-stone-200 bg-white p-5 sm:grid-cols-2 xl:grid-cols-3" onSubmit={(event)=>{event.preventDefault();setFilters(Object.fromEntries([...new FormData(event.currentTarget)].filter(([,value])=>value!=="")));setPage(1);}}>
    {[["q","Họ và tên"],["occupation","Nghề nghiệp / đơn vị"],["education","Trường / bằng cấp"],["location","Nơi ở"]].map(([name,label])=><label className="text-sm font-medium" key={name}>{label}<input className={`${fieldClass} mt-2`} name={name} maxLength={name==="location"?300:200} defaultValue={filters[name] || ""}/></label>)}
    <label className="text-sm font-medium">Thế hệ<input className={`${fieldClass} mt-2`} name="generation" type="number" min={1} max={1000} defaultValue={filters.generation || ""}/></label>
    <label className="text-sm font-medium">Chi nhánh<select className={`${fieldClass} mt-2`} name="branch_id" defaultValue={filters.branch_id || ""}><option value="">Tất cả chi</option>{branches.data?.items.map((row)=><option key={row.id} value={row.id}>{row.name}</option>)}</select></label>
    <label className="flex items-center gap-2 text-sm"><input type="checkbox" name="current_job" value="true" defaultChecked={filters.current_job==="true"}/>Chỉ công việc hiện tại</label><button className={`${buttonClass} justify-self-start`} type="submit">Tìm thành viên</button>
  </form><QueryState query={query}/>
    {query.data && <><p className="text-sm text-stone-600">{query.data.total} thành viên</p><div className="grid gap-4 md:grid-cols-2 xl:grid-cols-3">{query.data.items.map((row)=><button key={row.id} className="rounded-2xl border border-stone-200 bg-white p-5 text-left" onClick={()=>setSelected(row.id)}><h2 className="font-semibold text-forest">{row.name}</h2><p className="mt-2 text-sm">Thế hệ {row.generation} · {row.birth_date || "Chưa ghi ngày sinh"}</p><p className="mt-2 text-sm text-stone-600">{row.location || "Chưa ghi nơi ở"}</p><p className="mt-1 text-sm">{[row.position,row.company].filter(Boolean).join(" · ") || "Chưa ghi công việc"}</p><p className="mt-1 text-sm text-stone-600">{row.institution || "Chưa ghi học vấn"}</p></button>)}</div><Pager page={page} total={query.data.total} onChange={setPage}/></>}
  </div>;
}
export function Directory(){return <FamilyScope title="Danh bạ gia đình" description="Tìm người thân theo nơi ở, nghề nghiệp, học vấn và thế hệ.">{(familyId,user)=><DirectoryWorkspace key={familyId} familyId={familyId} user={user}/>}</FamilyScope>;}
