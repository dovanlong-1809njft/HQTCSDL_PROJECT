import {useState} from "react";
import {useMutation,useQuery,useQueryClient} from "@tanstack/react-query";
import {Link} from "react-router-dom";
import {useAuth} from "@/features/auth/hooks/useAuth";
import {api,getApiErrorMessage} from "@/shared/api/client";
import {buttonClass,Pager,QueryState} from "@/features/heritage/components/FamilyScope";
import {dateTime} from "@/shared/dates";

export function Notifications(){
  const {user}=useAuth(),cache=useQueryClient(),[page,setPage]=useState(1);
  const query=useQuery({queryKey:["notifications",user.id,page],queryFn:async()=>(await api.get("/notifications",{params:{page}})).data,refetchInterval:15000});
  const read=useMutation({mutationFn:(id)=>api.patch(`/notifications/${id}/read`),onSuccess:()=>cache.invalidateQueries({queryKey:["notifications"]})});
  return <section className="max-w-4xl space-y-5"><header className="flex flex-wrap items-start justify-between gap-3"><div><h1 className="text-2xl font-bold text-forest">Thông báo</h1><p className="mt-2 text-sm text-stone-600">Nhắc lịch và thông báo dành cho bạn.{query.data?` ${query.data.unread} chưa đọc.`:""}</p></div><button className={buttonClass} onClick={()=>query.refetch()}>Tải lại</button></header><QueryState query={query}/>{query.data&&!query.data.items.length&&<p className="rounded-xl bg-white p-5">Chưa có thông báo.</p>}{query.data?.items.map((row)=><article key={row.id} className={`space-y-3 rounded-2xl border p-5 ${row.read_at?"border-stone-200 bg-white":"border-leaf bg-sage"}`}><h2 className="font-semibold text-forest">{row.title}</h2><p className="text-sm">{row.body}</p><p className="text-xs text-stone-600">{dateTime(row.created_at)}</p><div className="flex flex-wrap gap-4 text-sm">{row.event_id?<Link className="font-semibold text-forest underline" to={`/events?family=${row.family_id}&event=${row.event_id}`} onClick={()=>{if(!row.read_at)read.mutate(row.id);}}>Xem sự kiện</Link>:<span className="text-stone-600">Sự kiện đã được xóa.</span>}{!row.read_at&&<button disabled={read.isPending} onClick={()=>read.mutate(row.id)}>Đánh dấu đã đọc</button>}</div></article>)}{read.isError&&<p role="alert" className="text-red-700">{getApiErrorMessage(read.error)}</p>}{query.data&&<Pager page={page} total={query.data.total} pageSize={20} onChange={setPage}/>}</section>;
}
