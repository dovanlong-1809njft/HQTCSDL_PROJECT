import {MediaGallery} from "@/shared/components/MediaGallery";
import {safeMedia,isImageUrl,isVideoUrl} from "@/shared/media.mjs";
import {ImageUploadPicker,useImageUploads} from "@/features/community/ImageUploadPicker";
import {getApiErrorMessage} from "@/shared/api/client";
import { useRef,useState } from "react";
import { useQuery } from "@tanstack/react-query";
import { heritageApi } from "../api/heritageApi";
import { buttonClass, fieldClass, Pager, QueryState } from "./FamilyScope";

function MemberPicker({ familyId, userId, value, onChange }) {
  const [q, setQ] = useState("");
  const [page, setPage] = useState(1);
  const members = useQuery({ queryKey: ["tv4", userId, familyId, "members", q, page],
    queryFn: () => heritageApi.list("members", familyId, { q, page, page_size: 20 }) });
  return <div className="space-y-2"><label className="block text-sm">Tìm thành viên<input className={fieldClass} value={q} onChange={(e) => { setQ(e.target.value); setPage(1); }} /></label>
    <QueryState query={members} />
    <label className="block text-sm">Thành viên được vinh danh<select aria-label="Thành viên được vinh danh" className={fieldClass} required value={value} onChange={(e) => onChange(e.target.value)}>
      <option value="">Chọn thành viên</option>{value && !members.data?.items.some((m) => m.id === value) && <option value={value}>Thành viên đã chọn</option>}
      {members.data?.items.map((m) => <option key={m.id} value={m.id}>{m.full_name}</option>)}
    </select></label>
    {members.data && <Pager page={page} total={members.data.total} pageSize={20} onChange={setPage} />}
  </div>;
}

export function HeritageForm({ resource, row, familyId, userId, pending, onSave, onCancel }) {
  const [form, setForm] = useState({ title: "", description: "", content: "", media_url: "", member_id: "", date_awarded: "", ...row,type:isVideoUrl(row?.media_url)?"video":row?.type||"story" });
  const uploads=useImageUploads(familyId,{allowVideo:form.type!=="photo",maxFiles:1});
  const lock=useRef(false),[uploading,setUploading]=useState(false);
  const [error, setError] = useState("");
  const isItem = resource === "items";
  function set(name, value) { setForm((old) => ({ ...old, [name]: value })); }
  async function submit(e) {
    e.preventDefault();
    if(lock.current||pending)return;
    if (!form.title.trim()) { setError("Bạn cần nhập tiêu đề."); return; }
    if (!form.description?.trim()) { setError("Bạn cần nhập mô tả."); return; }
    if (!isItem && (!form.date_awarded || (!row && !form.member_id))) { setError("Bạn cần chọn thành viên và ngày trao vinh danh."); return; }
    const hasFile=uploads.files.length>0;
    if (isItem && ((form.type === "story" && !form.content?.trim()) || (["photo","video"].includes(form.type) && !form.media_url?.trim()&&!hasFile) || (form.type === "document" && !form.content?.trim() && !form.media_url?.trim()&&!hasFile))) {
      setError("Câu chuyện cần nội dung, ảnh cần URL, tài liệu cần ít nhất một trong hai."); return;
    }
    if(isItem && !hasFile && form.media_url?.trim() && !safeMedia(form.media_url.trim())){setError("URL phải dùng HTTPS hoặc đường dẫn nội bộ hợp lệ.");return;}
    if(isItem&&form.type==="video"&&(hasFile?uploads.files[0].kind!=="video":!isVideoUrl(form.media_url))){setError("Hãy chọn video MP4/WebM hoặc nhập URL trực tiếp kết thúc bằng .mp4 hoặc .webm.");return;}
    if(isItem&&form.type==="photo"&&hasFile&&uploads.files[0].kind==="video"){setError("Loại Ảnh không nhận video. Hãy đổi sang loại Video.");return;}
    const payload = { title: form.title.trim(), description: form.description.trim() };
    if (isItem) Object.assign(payload, { type: form.type==="video"?"document":form.type, content: form.content?.trim() || null, media_url: form.media_url?.trim() || null });
    else {
      payload.date_awarded = form.date_awarded || null;
      if (!row) payload.member_id = form.member_id;
    }
    if (row) payload.expected_version = row.version_token;
    setError("");lock.current=true;setUploading(true);
    try{if(isItem&&hasFile)payload.media_url=(await uploads.upload())[0];await onSave(payload);}
    catch(error){setError(getApiErrorMessage(error));}
    finally{lock.current=false;setUploading(false);}
  }
  const input = (name, label, maxLength, area = false) => {
    const required = ["title", "description"].includes(name) || (name === "content" && form.type === "story")
      || (name === "media_url" && ["photo", "video"].includes(form.type) && !uploads.files.length);
    return <label className="block text-sm font-medium">{label}{area
      ? <textarea aria-label={label} className={`${fieldClass} mt-1`} required={required} rows={name === "content" ? 6 : 3} maxLength={maxLength} value={form[name] || ""} onChange={(e) => set(name, e.target.value)} />
      : <input aria-label={label} className={`${fieldClass} mt-1`} required={required} maxLength={maxLength} value={form[name] || ""} onChange={(e) => set(name, e.target.value)} />}</label>;
  };
  return <form onSubmit={submit} className="space-y-4 rounded-2xl border border-stone-200 bg-white p-5" aria-label={row ? "Chỉnh sửa" : "Thêm mới"}>
    <h2 className="text-lg font-bold text-forest">{row ? "Chỉnh sửa" : "Thêm mới"} {isItem ? "di sản" : "vinh danh"}</h2>
    <fieldset disabled={pending||uploading} className="space-y-4">
      {isItem && <label className="block text-sm font-medium">Loại<select aria-label="Loại" className={`${fieldClass} mt-1`} value={form.type} onChange={(e) => set("type", e.target.value)}><option value="document">Tài liệu</option><option value="story">Câu chuyện</option><option value="photo">Ảnh</option><option value="video">Video</option></select></label>}
      {!isItem && !row && <MemberPicker familyId={familyId} userId={userId} value={form.member_id} onChange={(value) => set("member_id", value)} />}
      {input("title", "Tiêu đề", 200)}
      {input("description", "Mô tả", isItem ? 500 : 1000, true)}
      {isItem ? <>{input("content", "Nội dung", 200000, true)}<ImageUploadPicker uploads={uploads} urlCount={0} disabled={pending||uploading}/>{input("media_url", "URL ảnh / video / tài liệu (HTTPS hoặc /media/)", 500)}{(form.type==="photo"||isImageUrl(form.media_url)||isVideoUrl(form.media_url))&&<MediaGallery key={form.media_url} urls={[form.media_url]} title={form.title||"Ảnh di sản"}/>}<p className="text-xs text-stone-500">Chọn một ảnh/video hoặc dùng URL. Tệp chọn từ máy sẽ thay thế URL khi lưu. Video cần MP4 hoặc WebM, tối đa 5 phút.</p></>
        : <label className="block text-sm">Ngày trao<input type="date" required className={`${fieldClass} mt-1`} value={form.date_awarded || ""} onChange={(e) => set("date_awarded", e.target.value)} /></label>}
      {error && <p role="alert" className="text-sm text-red-700">{error}</p>}
      <div className="flex gap-3"><button className={buttonClass} type="submit">{pending||uploading ? "Đang lưu…" : "Lưu"}</button><button className="text-sm underline" type="button" onClick={onCancel}>Hủy</button></div>
    </fieldset>
  </form>;
}
