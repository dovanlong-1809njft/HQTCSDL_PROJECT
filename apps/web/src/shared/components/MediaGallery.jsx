import {useEffect, useRef, useState} from "react";
import {createPortal} from "react-dom";
import {safeMedia,isVideoUrl} from "../media.mjs";
import {isPrivateMedia,loadPrivateImage} from "../privateMedia";

function Picture({url, title}) {
  const video=isVideoUrl(url);
  const [state, setState] = useState("loading");
  const [source,setSource] = useState(isPrivateMedia(url)?null:url);
  useEffect(()=>{
    if(!isPrivateMedia(url))return;
    const controller=new AbortController();let disposed=false,objectUrl;
    loadPrivateImage(url,controller.signal).then(value=>{
      objectUrl=value;if(disposed)URL.revokeObjectURL(value);else setSource(value);
    }).catch(()=>{if(!disposed)setState("error");});
    return ()=>{disposed=true;controller.abort();if(objectUrl)URL.revokeObjectURL(objectUrl);};
  },[url]);
  return <span className="media-picture">
    {state === "loading" && <span role="status" className="media-message">{video?"Đang tải video…":"Đang tải ảnh…"}</span>}
    {state === "error" ? <span className="media-message">{video?"Không tải được video. Bạn có thể mở liên kết gốc.":"Không tải được ảnh. Bạn có thể mở liên kết gốc."}</span> :
      source&&(video?<video src={source} aria-label={title} controls playsInline preload="metadata" onLoadedData={()=>setState("ready")} onError={()=>setState("error")}/>:<img src={source} alt={title} loading="lazy" referrerPolicy="no-referrer" onLoad={()=>setState("ready")} onError={()=>setState("error")}/>)}
  </span>;
}
function OriginalLink({url}) {
  const [error,setError]=useState(false),[pending,setPending]=useState(false);
  if(!isPrivateMedia(url))return <a href={url} target="_blank" rel="noopener noreferrer">Mở ảnh gốc</a>;
  return <span><button type="button" disabled={pending} onClick={async()=>{
    setPending(true);setError(false);
    try{const objectUrl=await loadPrivateImage(url);const link=document.createElement("a");link.href=objectUrl;link.download=url.split("/").pop();link.click();setTimeout(()=>URL.revokeObjectURL(objectUrl),30000);}
    catch{setError(true);}finally{setPending(false);}
  }}>{pending?"Đang tải…":"Tải ảnh"}</button>{error&&<span role="alert">Không tải được ảnh.</span>}</span>;
}
function Viewer({urls, initial, title, close}) {
  const [index, setIndex] = useState(initial);
  const dialog = useRef(null);
  useEffect(()=>{
    const focus = document.activeElement, overflow = document.body.style.overflow;
    document.body.style.overflow = "hidden";
    dialog.current.showModal();
    return ()=>{document.body.style.overflow = overflow; focus?.focus();};
  }, []);
  return createPortal(<dialog ref={dialog} className="media-viewer" aria-label="Xem ảnh lớn" onCancel={close} onClick={e=>{if(e.target === e.currentTarget) close();}}>
    <div className="media-viewer-actions"><span>{index+1} / {urls.length}</span><OriginalLink key={urls[index]} url={urls[index]}/><button autoFocus onClick={close} aria-label="Đóng ảnh">✕ Đóng</button></div>
    <Picture key={urls[index]} url={urls[index]} title={title}/>
    {urls.length>1 && <div className="media-viewer-actions"><button onClick={()=>setIndex((index-1+urls.length)%urls.length)}>← Ảnh trước</button><button onClick={()=>setIndex((index+1)%urls.length)}>Ảnh tiếp →</button></div>}
  </dialog>, document.body);
}
export function MediaGallery({urls=[], title="Ảnh gia đình", onRemove}) {
  const images = urls.filter(url=>safeMedia(url));
  const [selected, setSelected] = useState(null);
  if (!images.length) return null;
  return <div className="media-gallery-wrap">
    <div className={`media-gallery ${images.length===1 ? "media-single" : ""}`}>
      {images.slice(0,4).map((url,i)=><div className="media-tile" key={`${url}-${i}`}>
        {isVideoUrl(url)?<div className="media-open"><Picture url={url} title={`Video ${i+1}`}/><button type="button" className="p-2 text-sm text-forest" onClick={()=>setSelected(i)}>Xem video lớn{i===3&&images.length>4?` · +${images.length-4} tệp khác`:""}</button></div>:<button type="button" className="media-open" aria-label={`Xem ${title} ${i+1}`} onClick={()=>setSelected(i)}><Picture url={url} title={`${title} ${i+1}`}/>{i===3&&images.length>4&&<span className="media-more">+{images.length-4}</span>}</button>}
        {onRemove&&<button type="button" className="media-remove" aria-label={`Xóa ảnh ${i+1}`} onClick={()=>onRemove(i)}>✕</button>}
      </div>)}
    </div>
    {onRemove && images.length>4 && <ul>{images.slice(4).map((url,i)=><li className="flex min-w-0 gap-2 text-sm" key={`${url}-${i}`}><span className="truncate">Ảnh {i+5}: {url}</span><button type="button" onClick={()=>onRemove(i+4)} aria-label={`Xóa ảnh ${i+5}`}>Xóa</button></li>)}</ul>}
    {selected!==null && <Viewer urls={images} initial={selected} title={title} close={()=>setSelected(null)}/>}
  </div>;
}
