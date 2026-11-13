import { useState } from "react";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { getApiErrorMessage } from "@/shared/api/client";
import { heritageApi } from "../api/heritageApi";
import { FamilyScope, Pager, QueryState, buttonClass, fieldClass } from "../components/FamilyScope";
import { HeritageForm } from "../components/HeritageForm";

const labels = { items: "Di sản", honors: "Vinh danh", ranking: "Bảng xếp hạng" };
const types = { story: "Câu chuyện", document: "Tài liệu", photo: "Ảnh" };
// Never render javascript/data/protocol-relative URLs from legacy database rows.
export function safeMedia(value) {
  if (!value || /[\s\\]/.test(value)) return null;
  if (value.startsWith("/") && !value.startsWith("//")) return value;
  try { const u = new URL(value); return u.protocol === "https:" && !u.username && !u.password ? value : null; } catch { return null; }
}

function Detail({ familyId, userId, resource, id, onClose }) {
  const query = useQuery({ queryKey: ["tv4", userId, familyId, resource, id], queryFn: () => heritageApi.get(resource, familyId, id) });
  const row = query.data;
  const media = safeMedia(row?.media_url);
  return <section className="rounded-2xl border border-stone-200 bg-white p-5" aria-label="Chi tiết">
    <button onClick={onClose} className="float-right text-sm underline">Đóng chi tiết</button><QueryState query={query} />
    {row && <><h2 className="pr-24 text-xl font-bold text-forest">{row.title}</h2><p className="mt-3 whitespace-pre-wrap break-words">{row.description}</p>
      <p className="mt-3 whitespace-pre-wrap break-words">{row.content}</p>
      {media && <>{row.type === "photo" && <img loading="lazy" referrerPolicy="no-referrer" src={media} alt={row.title} className="my-4 max-h-96 max-w-full rounded-xl object-contain" />}
        <a className="mt-3 inline-block text-leaf underline" href={media} target="_blank" rel="noopener noreferrer" referrerPolicy="no-referrer">Mở ảnh / tài liệu</a></>}
      {row.full_name && <p className="mt-3">Thành viên: {row.full_name} · Ngày trao: {row.date_awarded || "Chưa ghi"}</p>}</>}
  </section>;
}

function Workspace({ familyId, user }) {
  const cache = useQueryClient();
  const [resource, setResource] = useState("items");
  const [page, setPage] = useState(1);
  const [q, setQ] = useState("");
  const [itemType, setItemType] = useState("");
  const [editor, setEditor] = useState(null);
  const [detail, setDetail] = useState(null);
  const [deleting, setDeleting] = useState(null);
  const [notice, setNotice] = useState("");
  const manager = ["admin", "family_head"].includes(user.role);
  const query = useQuery({ queryKey: ["tv4", user.id, familyId, resource, page, q, itemType],
    queryFn: () => heritageApi.list(resource, familyId, { page, page_size: 12, q, ...(resource === "items" && itemType ? { item_type: itemType } : {}) }) });
  const mutation = useMutation({
    mutationFn: ({ action, payload, row }) => action === "delete" ? heritageApi.remove(resource, familyId, row)
      : editor?.id ? heritageApi.update(resource, familyId, editor.id, payload) : heritageApi.create(resource, familyId, payload),
    onSuccess: () => { setEditor(null); setDeleting(null); setDetail(null); setNotice("Đã lưu thay đổi."); setPage(1); cache.invalidateQueries({ queryKey: ["tv4", user.id, familyId] }); },
    onError: (error) => { setNotice(getApiErrorMessage(error)); if (error.response?.status === 409) cache.invalidateQueries({ queryKey: ["tv4", user.id, familyId] }); },
  });
  function tab(value) { if (mutation.isPending) return; setResource(value); setPage(1); setQ(""); setEditor(null); setDetail(null); setDeleting(null); setNotice(""); }
  function editable(row) { return resource === "items" ? manager || row.created_by_user_id === user.id : manager; }
  return <div className="space-y-5">
    <nav aria-label="Di sản và vinh danh" className="flex flex-wrap gap-2">{Object.entries(labels).map(([key, label]) => <button key={key} disabled={mutation.isPending} aria-pressed={resource === key} onClick={() => tab(key)} className={resource === key ? buttonClass : "rounded-xl border border-stone-300 bg-white px-4 py-2 text-sm"}>{label}</button>)}</nav>
    <div className="flex flex-wrap items-end gap-3">
      <label className="min-w-0 flex-1 text-sm">{resource === "ranking" ? "Tìm thành viên" : "Tìm tiêu đề"}<input className={`${fieldClass} mt-1`} maxLength={200} value={q} onChange={(e) => { setQ(e.target.value); setPage(1); }} /></label>
      {resource === "items" && <label className="text-sm">Loại<select className={`${fieldClass} mt-1`} value={itemType} onChange={(e) => { setItemType(e.target.value); setPage(1); }}><option value="">Tất cả</option>{Object.entries(types).map(([key, label]) => <option value={key} key={key}>{label}</option>)}</select></label>}
      {resource !== "ranking" && (resource === "items" || manager) && <button disabled={mutation.isPending} className={buttonClass} onClick={() => { setEditor({}); setNotice(""); }}>Thêm {resource === "items" ? "di sản" : "vinh danh"}</button>}
    </div>
    {notice && <p role="status" className={`rounded-xl p-3 text-sm ${mutation.isError ? "bg-red-50 text-red-800" : "bg-sage text-forest"}`}>{notice}</p>}
    {editor && <HeritageForm key={`${resource}-${editor.id || "new"}`} resource={resource} row={editor.id ? editor : null} familyId={familyId} userId={user.id} pending={mutation.isPending}
      onSave={(payload) => { if (!mutation.isPending) mutation.mutate({ action: "save", payload }); }} onCancel={() => setEditor(null)} />}
    {deleting && <div role="alertdialog" aria-label="Xác nhận xóa" className="rounded-xl border border-red-300 bg-white p-4"><p>Xóa “{deleting.title}”? Thao tác này sẽ xóa bản ghi.</p><div className="mt-3 flex gap-4"><button disabled={mutation.isPending} className={buttonClass} onClick={() => mutation.mutate({ action: "delete", row: deleting })}>Xác nhận xóa</button><button disabled={mutation.isPending} onClick={() => setDeleting(null)}>Hủy</button></div></div>}
    {detail && <Detail familyId={familyId} userId={user.id} resource={resource} id={detail} onClose={() => setDetail(null)} />}
    <QueryState query={query} />
    {query.isSuccess && !query.data.items.length && <p className="rounded-xl bg-white p-5">Chưa có kết quả phù hợp.</p>}
    {query.isSuccess && resource === "ranking" && <div className="overflow-x-auto rounded-xl bg-white"><table className="w-full text-left text-sm"><caption className="p-3 text-left text-stone-600">Đồng hạng theo số danh hiệu; bao gồm thành viên chưa có danh hiệu.</caption><thead><tr><th className="p-3">Hạng</th><th className="p-3">Thành viên</th><th className="p-3">Danh hiệu</th></tr></thead><tbody>{query.data.items.map((row) => <tr key={row.member_id} className="border-t border-stone-100"><td className="p-3">{row.rank}</td><td className="p-3">{row.full_name}</td><td className="p-3">{row.honor_count}</td></tr>)}</tbody></table></div>}
    {query.isSuccess && resource !== "ranking" && <div className="grid gap-4 md:grid-cols-2 xl:grid-cols-3">{query.data.items.map((row) => <article key={row.id} className="min-w-0 rounded-2xl border border-stone-200 bg-white p-5">
      <p className="text-xs font-semibold text-leaf">{resource === "items" ? types[row.type] : row.full_name}</p><h2 className="mt-2 break-words font-bold text-forest">{row.title}</h2><p className="mt-2 line-clamp-3 break-words text-sm text-stone-600">{row.description}</p>
      <div className="mt-4 flex flex-wrap gap-4 text-sm"><button className="text-leaf underline" onClick={() => setDetail(row.id)}>Chi tiết</button>{editable(row) && <><button disabled={mutation.isPending} onClick={() => { setEditor(row); setNotice(""); }}>Sửa</button><button disabled={mutation.isPending} className="text-red-700" onClick={() => setDeleting(row)}>Xóa</button></>}</div>
    </article>)}</div>}
    {query.data && <Pager page={page} total={query.data.total} onChange={setPage} />}
  </div>;
}

export function Heritage() {
  return <FamilyScope title="Di sản & Vinh danh" description="Lưu giữ ký ức, tư liệu và ghi nhận đóng góp của các thế hệ.">{(familyId, user) => <Workspace key={`${user.id}-${familyId}`} familyId={familyId} user={user} />}</FamilyScope>;
}
