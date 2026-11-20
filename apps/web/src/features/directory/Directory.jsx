import { useState } from "react";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { api, getApiErrorMessage } from "@/shared/api/client";
import { FamilyScope, fieldClass, buttonClass, Pager, QueryState } from "@/features/heritage/components/FamilyScope";
import { genealogyApi } from "@/features/genealogy/api/genealogyApi";

function MemberDetail({ familyId, id, user, onClose }) {
  const cache=useQueryClient();
  const [editor,setEditor]=useState(null);
  const query=useQuery({queryKey:["directory",user.id,familyId,id],queryFn:async()=>(await api.get(`/directory/${id}`,{params:{family_id:familyId}})).data});
  const write=useMutation({mutationFn:(operation)=>operation(),onSuccess:()=>{setEditor(null);cache.invalidateQueries({queryKey:["directory"]});}});
  const fields={educations:[["institution","Trường / cơ sở đào tạo",true],["degree","Bằng cấp",true]],work:[["company","Công ty / đơn vị",true],["position","Chức danh / nghề nghiệp",true]]};
  return <section className="space-y-4 rounded-2xl border border-stone-200 bg-white p-5">
    <button type="button" className="text-sm text-forest underline" onClick={onClose}>← Về danh bạ</button><QueryState query={query}/>
    {query.data && <><h2 className="text-xl font-semibold text-forest">{query.data.name}</h2><p className="text-sm text-stone-600">{query.data.birth_date || "Chưa ghi ngày sinh"} · {query.data.location || "Chưa ghi nơi ở"} · {query.data.branch_name || "Chưa phân chi"}</p>
      {["educations","work"].map((resource)=><section key={resource} className="space-y-3 border-t border-stone-200 pt-4"><div className="flex flex-wrap items-center justify-between gap-3"><h3 className="font-semibold text-forest">{resource==="educations"?"Học vấn":"Công việc"}</h3>{query.data.can_edit && <button className={buttonClass} onClick={()=>{write.reset();setEditor({resource});}}>Thêm {resource==="educations"?"học vấn":"công việc"}</button>}</div>
        {!query.data[resource].length && <p className="text-sm text-stone-600">Chưa có thông tin.</p>}
        {query.data[resource].map((row)=><div key={row.id} className="flex flex-wrap justify-between gap-3 rounded-xl bg-stone-50 p-3"><div><p className="font-medium">{resource==="educations"?row.institution:row.company}</p><p className="text-sm">{resource==="educations"?row.degree:row.position}</p><p className="mt-1 text-xs text-stone-600">{row.start_date || "Chưa rõ"} → {row.end_date || "Hiện tại"}</p></div>{query.data.can_edit && <div className="flex gap-3"><button className="text-sm underline" onClick={()=>{write.reset();setEditor({resource,...row});}}>Sửa<span className="sr-only"> {row.institution || row.company}</span></button><button className="text-sm text-red-700" disabled={write.isPending} onClick={()=>{if(window.confirm("Xóa thông tin này?"))write.mutate(()=>api.delete(`/directory/${id}/${resource}/${row.id}`));}}>Xóa<span className="sr-only"> {row.institution || row.company}</span></button></div>}</div>)}
      </section>)}
      {editor && <form key={editor.id || editor.resource} className="space-y-4 rounded-xl bg-sage p-4" onSubmit={(event)=>{event.preventDefault();const values=new FormData(event.currentTarget);const payload=Object.fromEntries([...values].map(([key,value])=>[key,value || null]));write.mutate(()=>api[editor.id?"put":"post"](`/directory/${id}/${editor.resource}${editor.id?`/${editor.id}`:""}`,payload));}}>
        <h3 className="font-semibold">{editor.id?"Sửa":"Thêm"} {editor.resource==="educations"?"học vấn":"công việc"}</h3>
        {fields[editor.resource].map(([name,label,required])=><label className="block text-sm font-medium" key={name}>{label}<input name={name} className={`${fieldClass} mt-2`} required={required} maxLength={200} defaultValue={editor[name] || ""}/></label>)}
        <div className="grid gap-4 sm:grid-cols-2">{[["start_date","Ngày bắt đầu"],["end_date","Ngày kết thúc (để trống nếu đang tiếp tục)"]].map(([name,label])=><label className="block text-sm" key={name}>{label}<input className={`${fieldClass} mt-2`} name={name} type="date" required={name==="start_date"} min={name==="end_date"?editor.start_date || undefined:undefined} defaultValue={editor[name] || ""}/></label>)}</div>
        <div className="flex gap-3"><button className={buttonClass} disabled={write.isPending}>Lưu thông tin</button><button type="button" onClick={()=>setEditor(null)}>Hủy</button></div>
      </form>}
    </>}{write.isError && <p role="alert" className="text-red-700">{getApiErrorMessage(write.error)}</p>}
  </section>;
}

function DirectoryWorkspace({familyId,user}) {
  const [filters,setFilters]=useState({}),[page,setPage]=useState(1),[selected,setSelected]=useState(null);
  const query=useQuery({queryKey:["directory",user.id,familyId,filters,page],queryFn:async()=>(await api.get("/directory",{params:{family_id:familyId,page,...filters}})).data});
  const branches=useQuery({queryKey:["genealogy",user.id,familyId,"directory-branches"],queryFn:()=>genealogyApi.branches(familyId)});
  if(selected)return <MemberDetail familyId={familyId} user={user} id={selected} onClose={()=>setSelected(null)}/>;
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
