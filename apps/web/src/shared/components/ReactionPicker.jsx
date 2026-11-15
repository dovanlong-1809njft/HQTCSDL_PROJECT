import {useEffect, useLayoutEffect, useRef, useState} from "react";
import {useMutation} from "@tanstack/react-query";
import {api,getApiErrorMessage} from "@/shared/api/client";

export const reactions = {Like:["👍","Thích"],Love:["❤️","Yêu thích"],Haha:["😆","Vui"],Wow:["😮","Ngạc nhiên"],Sad:["😢","Buồn"],Angry:["😡","Giận"]};
export function ReactionSummary({counts={}, total=0}) {
  const top = Object.entries(counts).filter(([key,count])=>reactions[key]&&count>0).sort((a,b)=>b[1]-a[1]).slice(0,3);
  return <span className="reaction-summary" aria-label={`${total} cảm xúc`}>{top.map(([key])=><span key={key} title={reactions[key][1]}>{reactions[key][0]}</span>)} {total} cảm xúc</span>;
}
export function ReactionPicker({url, current, onSaved, label="nội dung"}) {
  const [open,setOpen]=useState(false);
  const [position,setPosition]=useState({});
  const root=useRef(null), busy=useRef(false);
  const palette=useRef(null);
  useLayoutEffect(()=>{
    if(!open)return;
    const place=()=>{
      const anchor=root.current.getBoundingClientRect(),menu=palette.current.getBoundingClientRect();
      setPosition({position:"fixed",left:Math.max(8,Math.min(anchor.left,window.innerWidth-menu.width-8)),top:anchor.top>=menu.height+8?anchor.top-menu.height:anchor.bottom,bottom:"auto"});
    };
    place();window.addEventListener("scroll",place,true);window.addEventListener("resize",place);
    return ()=>{window.removeEventListener("scroll",place,true);window.removeEventListener("resize",place);};
  },[open]);
  const mutation=useMutation({mutationFn:async(type)=>(await api.put(url,{type})).data,
    onSuccess:data=>{onSaved(data);setOpen(false);},onSettled:()=>{busy.current=false;}});
  useEffect(()=>{
    if(!open)return;
    const outside=e=>{if(!root.current?.contains(e.target))setOpen(false);};
    const escape=e=>{if(e.key==="Escape"){setOpen(false);root.current?.querySelector("button")?.focus();}};
    document.addEventListener("pointerdown",outside);document.addEventListener("keydown",escape);
    return ()=>{document.removeEventListener("pointerdown",outside);document.removeEventListener("keydown",escape);};
  },[open]);
  function choose(type){if(busy.current)return;busy.current=true;mutation.mutate(type===current?null:type);}
  const selected=reactions[current]||reactions.Like;
  return <span className="reaction-control" ref={root} onMouseEnter={()=>setOpen(true)} onMouseLeave={()=>setOpen(false)}>
    <button type="button" className="reaction-main" aria-label={`${selected[1]} cho ${label}`} aria-pressed={!!current} disabled={mutation.isPending} onClick={()=>choose(current||"Like")}>{selected[0]} {selected[1]}</button>
    <button type="button" className="reaction-toggle" aria-label={`Chọn cảm xúc cho ${label}`} aria-expanded={open} onClick={()=>setOpen(true)}>⌃</button>
    {open&&<span ref={palette} style={position} className="reaction-palette" role="group" aria-label="Chọn cảm xúc">{Object.entries(reactions).map(([type,[icon,name]])=><button type="button" key={type} title={name} aria-label={name} aria-pressed={type===current} disabled={mutation.isPending} onClick={()=>choose(type)}>{icon}</button>)}</span>}
    {mutation.isError&&<span role="alert" className="reaction-error">{getApiErrorMessage(mutation.error)}</span>}
  </span>;
}
