import {useEffect,useRef,useState} from "react";
import {api,getApiErrorMessage} from "@/shared/api/client";

const MAX_FILE=8*1024*1024, MAX_VIDEO=50*1024*1024, MAX_BATCH=100*1024*1024;
export function useImageUploads(familyId,{allowVideo=false,maxFiles=20}={}) {
  const [files,setFiles]=useState([]),[error,setError]=useState(""),[progress,setProgress]=useState(null);
  const live=useRef([]),controller=useRef(null);
  useEffect(()=>()=>{controller.current?.abort();live.current.forEach(item=>URL.revokeObjectURL(item.preview));},[]);
  function update(next){live.current=next;setFiles(next);}
  function add(selected,urlCount){
    const incoming=Array.from(selected);
    if(!incoming.length)return;
    if(incoming.length+live.current.length+urlCount>maxFiles){setError(`Tối đa ${maxFiles} tệp đính kèm, bao gồm URL.`);return;}
    const video=file=>allowVideo&&/\.(mp4|webm)$/i.test(file.name)&&["video/mp4","video/webm"].includes(file.type);
    if(incoming.some(file=>!video(file)&&(! /\.(jpe?g|png|webp)$/i.test(file.name)||!['image/jpeg','image/png','image/webp'].includes(file.type)))){setError(allowVideo?"Chỉ chọn ảnh JPG, PNG, WebP hoặc video MP4, WebM.":"Chỉ chọn ảnh JPG, PNG hoặc WebP.");return;}
    if(incoming.some(file=>file.size>(video(file)?MAX_VIDEO:MAX_FILE))){setError("Mỗi ảnh tối đa 8 MB, mỗi video tối đa 50 MB.");return;}
    if([...live.current.map(item=>item.file),...incoming].reduce((sum,file)=>sum+file.size,0)>MAX_BATCH){setError("Tổng tệp từ máy tính tối đa 100 MB.");return;}
    setError("");update([...live.current,...incoming.map(file=>({file,kind:video(file)?"video":"image",preview:URL.createObjectURL(file),url:null}))]);
  }
  function remove(index){URL.revokeObjectURL(live.current[index].preview);update(live.current.filter((_,i)=>i!==index));setError("");}
  async function upload(){
    const pending=live.current.filter(item=>!item.url);
    if(!pending.length)return live.current.map(item=>item.url);
    const body=new FormData();pending.forEach(item=>body.append("files",item.file));
    controller.current=new AbortController();setProgress(0);setError("");
    try{
      const {data}=await api.post("/community/uploads",body,{params:{family_id:familyId},headers:{"Content-Type":undefined},signal:controller.current.signal,timeout:300000,
        onUploadProgress:event=>setProgress(Math.min(100,Math.round(event.loaded/(event.total||1)*100)))});
      if(data.items?.length!==pending.length||data.items.some(item=>!item.url?.startsWith("/media/uploads/")))throw new Error("Invalid upload response");
      let offset=0;const next=live.current.map(item=>item.url?item:{...item,url:data.items[offset++].url});update(next);
      return next.map(item=>item.url);
    }catch(error){setError(getApiErrorMessage(error));throw error;}finally{setProgress(null);}
  }
  function clear(){live.current.forEach(item=>URL.revokeObjectURL(item.preview));update([]);setError("");}
  return {files,error,progress,add,remove,upload,clear,allowVideo,maxFiles};
}

export function ImageUploadPicker({uploads,urlCount,disabled}) {
  const input=useRef(null);
  const videoInput=useRef(null);
  return <section aria-label="Tải ảnh từ máy tính" className="space-y-3 rounded-xl border border-dashed border-stone-300 p-4"
    onDragOver={event=>{event.preventDefault();}} onDrop={event=>{event.preventDefault();if(!disabled)uploads.add(event.dataTransfer.files,urlCount);}}>
    <input ref={input} type="file" multiple accept="image/jpeg,image/png,image/webp,.jpg,.jpeg,.png,.webp" className="sr-only" aria-label="Chọn các tệp ảnh" disabled={disabled}
      onChange={event=>{uploads.add(event.target.files,urlCount);event.target.value="";}}/>
    <button type="button" className="rounded-xl border border-stone-300 px-4 py-2 text-sm font-semibold text-forest" disabled={disabled} onClick={()=>input.current.click()}>Chọn ảnh từ máy tính</button>
    {uploads.allowVideo&&<><input ref={videoInput} type="file" multiple={uploads.maxFiles>1} accept="video/mp4,video/webm,.mp4,.webm" className="sr-only" aria-label="Chọn các tệp video" disabled={disabled} onChange={event=>{uploads.add(event.target.files,urlCount);event.target.value="";}}/><button type="button" className="ml-2 rounded-xl border border-stone-300 px-4 py-2 text-sm font-semibold text-forest" disabled={disabled} onClick={()=>videoInput.current.click()}>Chọn video từ máy tính</button></>}
    <p className="text-xs text-stone-600">Hoặc kéo thả vào đây. JPG, PNG, WebP · 8 MB/ảnh{uploads.allowVideo?" · MP4, WebM · 50 MB/video, tối đa 5 phút":""} · tối đa {uploads.maxFiles} tệp. Tổng 100 MB/lần.</p>
    {!!uploads.files.length&&<div className="grid grid-cols-2 gap-3 sm:grid-cols-3">{uploads.files.map((item,index)=><div key={item.preview} className="relative min-w-0">
      {item.kind==="video"?<video src={item.preview} controls playsInline preload="metadata" aria-label={`Video từ máy tính ${index+1}`} className="h-32 w-full rounded-xl object-contain"/>:<img src={item.preview} alt={`Ảnh từ máy tính ${index+1}`} className="h-32 w-full rounded-xl object-cover"/>}
      <button type="button" className="media-remove" disabled={disabled} aria-label={`Xóa ${item.kind==="video"?"video":"ảnh"} từ máy tính ${index+1}`} onClick={()=>uploads.remove(index)}>✕</button>
      <p className="truncate text-xs">{item.file.name}</p>
    </div>)}</div>}
    {uploads.progress!==null&&<div role="status"><label className="block text-sm">{uploads.progress===100?"Đang kiểm tra và lưu tệp…":`Đang tải tệp: ${uploads.progress}%`}<progress className="w-full" max={100} value={uploads.progress}/></label></div>}
    {uploads.error&&<p role="alert" className="text-sm text-red-700">{uploads.error}</p>}
  </section>;
}
