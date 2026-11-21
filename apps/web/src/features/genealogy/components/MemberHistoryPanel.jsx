import { useState } from "react";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { api, getApiErrorMessage } from "@/shared/api/client";
import { fieldClass, buttonClass, QueryState } from "@/features/heritage/components/FamilyScope";

export function MemberHistoryPanel({ familyId, id, user, onClose }) {
  const cache=useQueryClient();
  const [editor,setEditor]=useState(null);
  const query=useQuery({queryKey:["directory",user.id,familyId,id],queryFn:async()=>(await api.get(`/directory/${id}`,{params:{family_id:familyId}})).data});
  const write=useMutation({mutationFn:(operation)=>operation(),onSuccess:()=>{setEditor(null);cache.invalidateQueries({queryKey:["directory"]});cache.invalidateQueries({queryKey:["genealogy"]});}});
  const fields={educations:[["institution","Trường / cơ sở đào tạo",true],["degree","Bằng cấp",true]],work:[["company","Công ty / đơn vị",true],["position","Chức danh / nghề nghiệp",true]]};
  return <section className="space-y-4 rounded-2xl border border-stone-200 bg-white p-5">
    {onClose&&<button type="button" className="text-sm text-forest underline" onClick={onClose}>← Về danh bạ</button>}<QueryState query={query}/>
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

