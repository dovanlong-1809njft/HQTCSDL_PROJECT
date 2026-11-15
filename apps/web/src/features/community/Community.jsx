import {useRef,useState} from "react";
import {useMutation,useQuery,useQueryClient} from "@tanstack/react-query";
import {api,getApiErrorMessage} from "@/shared/api/client";
import {FamilyScope,buttonClass,fieldClass,Pager,QueryState} from "@/features/heritage/components/FamilyScope";
import {dateTime} from "@/shared/dates";

import {MediaGallery} from "@/shared/components/MediaGallery";
import {ReactionPicker,ReactionSummary} from "@/shared/components/ReactionPicker";
import {safeMedia,isVideoUrl} from "@/shared/media.mjs";
import {ImageUploadPicker,useImageUploads} from "./ImageUploadPicker";
function Composer({familyId,user,post,onSaved,onCancel}){
  const uploads=useImageUploads(familyId,{allowVideo:true}),lock=useRef(false);
  const [submitting,setSubmitting]=useState(false);
  const [mediaText,setMediaText]=useState(post?.media_urls.join("\n") || ""),[mediaError,setMediaError]=useState("");
  const urls=mediaText.split(/\r?\n/).map(url=>url.trim()).filter(Boolean);
  const validUrls=urls.filter(url=>safeMedia(url));
  const videoCount=validUrls.filter(isVideoUrl).length+uploads.files.filter(item=>item.kind==="video").length;
  const save=useMutation({mutationFn:({content,media,is_announcement})=>post?api.put(`/community/posts/${post.post_id}`,{content,media,is_announcement}):api.post("/community/posts",{family_id:familyId,content,media,is_announcement}),onSuccess:()=>onSaved()});
  return <form className="space-y-4 rounded-2xl border border-stone-200 bg-white p-5" onSubmit={async(event)=>{
    event.preventDefault();if(lock.current)return;
    const form=event.currentTarget,values=new FormData(form);
    if(urls.some(url=>!safeMedia(url))||urls.length+uploads.files.length>20){setMediaError("Chỉ dùng URL HTTPS hoặc đường dẫn /media/ hợp lệ, tối đa 20 ảnh.");return;}
    lock.current=true;setSubmitting(true);setMediaError("");
    try{
      const uploaded=await uploads.upload();
      await save.mutateAsync({content:values.get("content"),media:[...urls,...uploaded].map(url=>({url,type:isVideoUrl(url)?"video":"image"})),is_announcement:values.get("announcement")==="on"});
      form.reset();setMediaText("");uploads.clear();
    }catch{/* Upload and save errors are shown by their respective controls. */}
    finally{lock.current=false;setSubmitting(false);}
  }}><fieldset disabled={submitting} className="space-y-4">
    <h2 className="font-semibold text-forest">{post?"Sửa bài viết":"Chia sẻ với gia đình"}</h2><label className="block text-sm">Nội dung<textarea className={`${fieldClass} mt-2`} name="content" required maxLength={20000} rows={3} defaultValue={post?.content || ""}/></label>
    <label className="block text-sm">Ảnh đính kèm / video (mỗi dòng một URL HTTPS hoặc /media/)<textarea className={`${fieldClass} mt-2`} name="media" rows={2} value={mediaText} onChange={e=>setMediaText(e.target.value)}/></label>
    <ImageUploadPicker uploads={uploads} urlCount={urls.length} disabled={submitting}/>
    <p className="text-sm text-stone-600">{videoCount?`${validUrls.length+uploads.files.length-videoCount} ảnh · ${videoCount} video đã thêm`:`${validUrls.length+uploads.files.length} ảnh đã thêm`}</p>
    <MediaGallery urls={validUrls} title="Ảnh đính kèm" onRemove={index=>{const removed=validUrls[index];let done=false;setMediaText(urls.filter(url=>{if(!done&&url===removed){done=true;return false;}return true;}).join("\n"));}}/>
    {(mediaError||urls.some(url=>!safeMedia(url)))&&<p role="alert" className="text-red-700">{mediaError||"URL ảnh không hợp lệ. Hãy dùng HTTPS hoặc đường dẫn /media/."}</p>}
    {["admin","family_head"].includes(user.role)&&<label className="flex items-center gap-2 text-sm"><input type="checkbox" name="announcement" defaultChecked={post?.is_announcement}/>Đăng thông báo gia đình</label>}
    {save.isError&&<p role="alert" className="text-red-700">{getApiErrorMessage(save.error)}</p>}<div className="flex gap-3"><button className={buttonClass} disabled={submitting}>{submitting?"Đang lưu…":post?"Lưu bài viết":"Đăng bài"}</button>{onCancel&&<button type="button" onClick={onCancel}>Hủy</button>}</div>
  </fieldset></form>;
}
function PostCard({post,user,onEdit,onChanged}){
  const [commentsOpen,setCommentsOpen]=useState(false),[commentPage,setCommentPage]=useState(1),[report,setReport]=useState(null),[editing,setEditing]=useState(null);
  const cache=useQueryClient();
  const comments=useQuery({queryKey:["comments",user.id,post.post_id,commentPage],queryFn:async()=>(await api.get(`/community/posts/${post.post_id}/comments`,{params:{page:commentPage,page_size:20}})).data,enabled:commentsOpen});
  const write=useMutation({mutationFn:(operation)=>operation(),onSuccess:()=>{setReport(null);setEditing(null);onChanged();cache.invalidateQueries({queryKey:["comments",user.id,post.post_id]});}});
  const manage=post.author_id===user.id||user.role==="admin";
  return <article className="space-y-4 rounded-2xl border border-stone-200 bg-white p-5">
    <header className="flex flex-wrap items-start justify-between gap-3"><div><h2 className="font-semibold text-forest">{post.author_name || "Thành viên"}</h2><p className="mt-1 text-xs text-stone-600">{dateTime(post.created_at)}{post.is_announcement?" · Thông báo gia đình":""}</p></div>{manage&&<div className="flex gap-3 text-sm"><button className="underline" onClick={()=>onEdit(post)}>Sửa bài</button><button className="text-red-700" disabled={write.isPending} onClick={()=>{if(window.confirm("Xóa bài và các bình luận/ảnh/cảm xúc liên quan?"))write.mutate(()=>api.delete(`/community/posts/${post.post_id}`));}}>Xóa bài</button></div>}</header>
    <p className="whitespace-pre-wrap break-words text-stone-800">{post.content}</p>
    <MediaGallery urls={post.media_urls} title="Ảnh bài viết"/>
    <div className="flex flex-wrap items-center gap-3 border-t border-stone-200 pt-3">
      <ReactionSummary counts={post.reaction_counts} total={post.reaction_count}/>
      <ReactionPicker url={`/community/posts/${post.post_id}/reactions`} current={post.my_reaction} label={`bài của ${post.author_name || "thành viên"}`} onSaved={data=>cache.setQueriesData({queryKey:["community",user.id]},old=>old?{...old,items:old.items.map(row=>row.post_id===post.post_id?{...row,my_reaction:data.type,reaction_count:data.reaction_count,reaction_counts:data.reaction_counts}:row)}:old)}/>
      <button className="text-sm font-medium text-forest" onClick={()=>setCommentsOpen(!commentsOpen)}>Bình luận · {post.comment_count}</button><button className="ml-auto text-sm text-stone-600 underline" onClick={()=>setReport({target_id:post.post_id,target_type:"post"})}>Báo cáo bài</button>
    </div>
    {commentsOpen&&<section aria-label="Bình luận" className="space-y-3 border-t border-stone-200 pt-4"><QueryState query={comments}/>{comments.data?.map((row)=><div key={row.id} className="space-y-2 rounded-xl bg-stone-50 p-3"><p className="text-sm font-semibold">{row.author_name || "Thành viên"}</p><p className="whitespace-pre-wrap break-words text-sm">{row.content}</p><div className="flex flex-wrap items-center gap-4 text-xs"><ReactionPicker url={`/community/comments/${row.id}/reactions`} current={row.my_reaction} label={`bình luận của ${row.author_name || "thành viên"}`} onSaved={data=>cache.setQueryData(["comments",user.id,post.post_id,commentPage],old=>old?.map(item=>item.id===row.id?{...item,my_reaction:data.type,reaction_count:data.reaction_count,reaction_counts:data.reaction_counts}:item))}/><ReactionSummary counts={row.reaction_counts} total={row.reaction_count}/>{(row.user_id===user.id||user.role==="admin")&&<><button onClick={()=>setEditing(row)}>Sửa bình luận</button><button disabled={write.isPending} onClick={()=>{if(window.confirm("Xóa bình luận này?"))write.mutate(()=>api.delete(`/community/comments/${row.id}`));}}>Xóa bình luận</button></>}<button onClick={()=>setReport({target_id:row.id,target_type:"comment"})}>Báo cáo bình luận</button></div></div>)}<Pager page={commentPage} total={post.comment_count} pageSize={20} onChange={setCommentPage}/>
      <form key={editing?.id || "new"} className="flex flex-wrap gap-3" onSubmit={(event)=>{event.preventDefault();const form=event.currentTarget,content=new FormData(form).get("content");write.mutate(()=>editing?api.put(`/community/comments/${editing.id}`,{content}):api.post(`/community/posts/${post.post_id}/comments`,{content}),{onSuccess:()=>form.reset()});}}><label className="min-w-0 flex-1 text-sm">{editing?"Sửa bình luận":"Viết bình luận"}<input className={`${fieldClass} mt-2`} name="content" required maxLength={2000} defaultValue={editing?.content || ""}/></label><button className={`${buttonClass} self-end`} disabled={write.isPending}>{editing?"Lưu bình luận":"Gửi bình luận"}</button>{editing&&<button type="button" onClick={()=>setEditing(null)}>Hủy</button>}</form>
    </section>}
    {report&&<form className="space-y-3 rounded-xl bg-stone-50 p-3" onSubmit={(event)=>{event.preventDefault();const reason=new FormData(event.currentTarget).get("reason");write.mutate(()=>api.post("/community/reports",{...report,reason}));}}><label className="block text-sm">Lý do báo cáo<input className={`${fieldClass} mt-2`} name="reason" required maxLength={500}/></label><div className="flex gap-3"><button className={buttonClass} disabled={write.isPending}>Gửi báo cáo</button><button type="button" onClick={()=>setReport(null)}>Hủy</button></div></form>}
    {write.isError&&<p role="alert" className="text-red-700">{getApiErrorMessage(write.error)}</p>}{write.isSuccess&&!report&&<p role="status" className="text-sm text-forest">Đã cập nhật.</p>}
  </article>;
}
function Feed({familyId,user}){
  const cache=useQueryClient(),[page,setPage]=useState(1),[editing,setEditing]=useState(null);
  const query=useQuery({queryKey:["community",user.id,familyId,page],queryFn:async()=>(await api.get("/community/posts",{params:{family_id:familyId,page,page_size:10}})).data});
  const changed=()=>cache.invalidateQueries({queryKey:["community"]});
  return <div className="max-w-4xl space-y-5"><Composer key={editing?.post_id || "new"} familyId={familyId} user={user} post={editing} onSaved={()=>{setEditing(null);setPage(1);changed();}} onCancel={editing?()=>setEditing(null):null}/><QueryState query={query}/>{query.data&&!query.data.items.length&&<p className="rounded-xl bg-white p-5">Chưa có bài viết. Hãy chia sẻ câu chuyện đầu tiên.</p>}{query.data?.items.map((post)=><PostCard key={post.post_id} post={post} user={user} onEdit={(row)=>{setEditing(row);window.scrollTo({top:0,behavior:"auto"});}} onChanged={changed}/>)}{query.data&&<Pager page={page} total={query.data.total} pageSize={10} onChange={setPage}/>}</div>;
}
export function Community(){return <FamilyScope title="Bảng tin gia đình" description="Chia sẻ tin tức, ảnh và những câu chuyện của gia đình.">{(familyId,user)=><Feed key={familyId} familyId={familyId} user={user}/>}</FamilyScope>;}
