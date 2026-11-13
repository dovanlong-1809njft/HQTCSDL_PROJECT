import { useState } from "react";
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
    <label className="block text-sm">Thành viên được vinh danh<select className={fieldClass} required value={value} onChange={(e) => onChange(e.target.value)}>
      <option value="">Chọn thành viên</option>{value && !members.data?.items.some((m) => m.id === value) && <option value={value}>Thành viên đã chọn</option>}
      {members.data?.items.map((m) => <option key={m.id} value={m.id}>{m.full_name}</option>)}
    </select></label>
    {members.data && <Pager page={page} total={members.data.total} pageSize={20} onChange={setPage} />}
  </div>;
}

export function HeritageForm({ resource, row, familyId, userId, pending, onSave, onCancel }) {
  const [form, setForm] = useState({ type: "story", title: "", description: "", content: "", media_url: "", member_id: "", date_awarded: "", ...row });
  const [error, setError] = useState("");
  const isItem = resource === "items";
  function set(name, value) { setForm((old) => ({ ...old, [name]: value })); }
  function submit(e) {
    e.preventDefault();
    if (!form.title.trim()) { setError("Bạn cần nhập tiêu đề."); return; }
    if (isItem && ((form.type === "story" && !form.content.trim()) || (form.type === "photo" && !form.media_url.trim()) || (form.type === "document" && !form.content.trim() && !form.media_url.trim()))) {
      setError("Câu chuyện cần nội dung, ảnh cần URL, tài liệu cần ít nhất một trong hai."); return;
    }
    const payload = { title: form.title.trim(), description: form.description?.trim() || null };
    if (isItem) Object.assign(payload, { type: form.type, content: form.content?.trim() || null, media_url: form.media_url?.trim() || null });
    else {
      payload.date_awarded = form.date_awarded || null;
      if (!row) payload.member_id = form.member_id;
    }
    if (row) payload.expected_version = row.version_token;
    setError(""); onSave(payload);
  }
  const input = (name, label, maxLength, area = false) => <label className="block text-sm font-medium">{label}{area
    ? <textarea className={`${fieldClass} mt-1`} rows={name === "content" ? 6 : 3} maxLength={maxLength} value={form[name] || ""} onChange={(e) => set(name, e.target.value)} />
    : <input className={`${fieldClass} mt-1`} required={name === "title"} maxLength={maxLength} value={form[name] || ""} onChange={(e) => set(name, e.target.value)} />}</label>;
  return <form onSubmit={submit} className="space-y-4 rounded-2xl border border-stone-200 bg-white p-5" aria-label={row ? "Chỉnh sửa" : "Thêm mới"}>
    <h2 className="text-lg font-bold text-forest">{row ? "Chỉnh sửa" : "Thêm mới"} {isItem ? "di sản" : "vinh danh"}</h2>
    <fieldset disabled={pending} className="space-y-4">
      {isItem && <label className="block text-sm font-medium">Loại<select className={`${fieldClass} mt-1`} value={form.type} onChange={(e) => set("type", e.target.value)}><option value="document">Tài liệu</option><option value="story">Câu chuyện</option><option value="photo">Ảnh</option></select></label>}
      {!isItem && !row && <MemberPicker familyId={familyId} userId={userId} value={form.member_id} onChange={(value) => set("member_id", value)} />}
      {input("title", "Tiêu đề", 200)}
      {input("description", "Mô tả", isItem ? 500 : 1000, true)}
      {isItem ? <>{input("content", "Nội dung", 200000, true)}{input("media_url", "URL ảnh / tài liệu (HTTPS hoặc /media/)", 500)}<p className="text-xs text-stone-500">Dùng đường dẫn tệp đã được lưu trữ. Hệ thống chưa hỗ trợ tải tệp lên.</p></>
        : <label className="block text-sm">Ngày trao<input type="date" className={`${fieldClass} mt-1`} value={form.date_awarded || ""} onChange={(e) => set("date_awarded", e.target.value)} /></label>}
      {error && <p role="alert" className="text-sm text-red-700">{error}</p>}
      <div className="flex gap-3"><button className={buttonClass} type="submit">{pending ? "Đang lưu…" : "Lưu"}</button><button className="text-sm underline" type="button" onClick={onCancel}>Hủy</button></div>
    </fieldset>
  </form>;
}
