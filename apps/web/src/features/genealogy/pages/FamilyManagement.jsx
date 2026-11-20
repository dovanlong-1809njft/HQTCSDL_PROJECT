import { useState } from "react";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { Link } from "react-router-dom";
import { useAuth } from "@/features/auth/hooks/useAuth";
import { FamilyScope, buttonClass, fieldClass, Pager, QueryState } from "@/features/heritage/components/FamilyScope";
import { getApiErrorMessage } from "@/shared/api/client";
import { genealogyApi } from "../api/genealogyApi";

function RecordWorkspace({ familyId, user }) {
  const cache = useQueryClient();
  const [resource, setResource] = useState("members");
  const [editing, setEditing] = useState(null);
  const [page, setPage] = useState(1);
  const [q, setQ] = useState("");
  const [notice, setNotice] = useState("");
  const query = useQuery({ queryKey: ["genealogy", user.id, familyId, resource, page, q], queryFn: () => genealogyApi.list(resource, familyId, { page, page_size: 12, q }) });
  const branches = useQuery({ queryKey: ["genealogy", user.id, familyId, "branch-options"], queryFn: () => genealogyApi.branches(familyId) });
  const ownProfile = useQuery({ queryKey: ["genealogy", user.id, "profile"], queryFn: genealogyApi.profile, enabled: user.role === "family_head" });
  const changed = () => { cache.invalidateQueries({ queryKey: ["genealogy"] }); cache.invalidateQueries({ queryKey: ["tv4"] }); };
  const save = useMutation({ mutationFn: ({ id, payload }) => genealogyApi.save(resource, familyId, id, payload), onSuccess: () => { setEditing(null); setNotice("Đã lưu dữ liệu."); changed(); } });
  const remove = useMutation({ mutationFn: ({ type, id }) => genealogyApi.remove(type, familyId, id), onSuccess: () => { setNotice("Đã xóa dữ liệu."); setEditing(null); setPage(1); changed(); } });
  const rename = useMutation({ mutationFn: (name) => genealogyApi.save("families", familyId, familyId, { name }), onSuccess: () => { setNotice("Đã đổi tên gia đình."); changed(); } });
  const families = cache.getQueryData(["tv4", user.id, "families"]) || [];
  return <div className="space-y-5">
    <div className="flex flex-wrap items-end justify-between gap-4 rounded-2xl border border-stone-200 bg-white p-5">
      {user.role === "admin" ? <form className="flex flex-wrap items-end gap-3" onSubmit={(event) => { event.preventDefault(); rename.mutate(new FormData(event.currentTarget).get("name")); }}><label className="text-sm font-medium">Tên gia đình<input className={`${fieldClass} mt-2`} name="name" required minLength={2} maxLength={200} key={families.find((f) => f.id === familyId)?.name} defaultValue={families.find((f) => f.id === familyId)?.name} /></label><button className={buttonClass} disabled={rename.isPending}>Đổi tên</button></form> : <p className="font-semibold text-forest">{families.find((f) => f.id === familyId)?.name}</p>}
      {user.role === "admin" && <button type="button" className="rounded-xl border border-red-200 px-4 py-2 text-sm font-semibold text-red-700" disabled={remove.isPending} onClick={() => { if (window.confirm("Xóa gia đình này? Chỉ gia đình không còn dữ liệu liên quan mới xóa được.")) remove.mutate({ type: "families", id: familyId }); }}>Xóa gia đình</button>}
    </div>
    <div className="flex flex-wrap items-center gap-3"><label className="text-sm font-medium">Quản lý<select className={`${fieldClass} mt-2`} value={resource} onChange={(event) => { setResource(event.target.value); setEditing(null); setPage(1); setQ(""); save.reset(); remove.reset(); }}><option value="members">Thành viên</option><option value="branches">Chi nhánh</option></select></label><Link className="ml-auto text-sm font-semibold text-forest underline" to="/family-tree">Quản lý quan hệ trên cây gia phả →</Link></div>
    {notice && <p role="status" className="rounded-xl bg-sage p-3 text-forest">{notice}</p>}
    {[save, remove, rename].filter((m) => m.isError).map((m, index) => <p role="alert" key={index} className="rounded-xl bg-red-50 p-3 text-red-700">{getApiErrorMessage(m.error)}</p>)}
    <div className="grid items-start gap-5 xl:grid-cols-[minmax(0,1fr)_minmax(280px,360px)]">
      <section className="min-w-0 rounded-2xl border border-stone-200 bg-white p-5">
        <label className="block text-sm font-medium">Tìm {resource === "members" ? "thành viên" : "chi nhánh"}<input className={`${fieldClass} mt-2`} type="search" value={q} maxLength={200} onChange={(event) => { setQ(event.target.value); setPage(1); }} /></label>
        <QueryState query={query} />
        {query.data && <><ul className="mt-3 divide-y divide-stone-200">{query.data.items.map((row) => <li key={row.id} className="flex flex-wrap items-center justify-between gap-3 py-3"><div className="min-w-0"><p className="break-words font-semibold text-forest">{row.name}</p>{resource === "members" && <p className="mt-1 text-sm text-stone-600">{row.birth_date || "Chưa ghi ngày sinh"} · {row.user_id ? "Đã liên kết tài khoản" : "Chưa liên kết"}</p>}</div>{row.can_manage !== false && <div className="flex gap-2"><button className="rounded-xl border border-stone-300 px-3 py-2 text-sm" onClick={() => { setEditing(row); save.reset(); }}>Sửa<span className="sr-only"> {row.name}</span></button><button className="rounded-xl px-3 py-2 text-sm text-red-700" disabled={remove.isPending} onClick={() => { if (window.confirm(`Xóa ${row.name}? Dữ liệu còn liên kết sẽ được giữ lại và báo lỗi.`)) remove.mutate({ type: resource, id: row.id }); }}>Xóa<span className="sr-only"> {row.name}</span></button></div>}</li>)}</ul>{!query.data.items.length && <p className="py-5 text-sm text-stone-600">Chưa có kết quả.</p>}<Pager page={page} total={query.data.total} onChange={setPage} /></>}
      </section>
      {(user.role === "admin" || resource === "members" || editing) && <form key={`${resource}-${editing?.id || "new"}-${ownProfile.data?.member?.branch_id || ""}`} className="space-y-4 rounded-2xl border border-stone-200 bg-white p-5" onSubmit={(event) => {
        event.preventDefault(); const values = new FormData(event.currentTarget); setNotice("");
        const payload = { name: values.get("name"), ...(resource === "members" ? { branch_id: values.get("branch_id") || null, birth_date: values.get("birth_date") || null, location: values.get("location") || null } : {}) };
        save.mutate({ id: editing?.id, payload });
      }}>
        <h2 className="text-lg font-semibold text-forest">{editing ? "Sửa" : "Thêm"} {resource === "members" ? "thành viên" : "chi nhánh"}</h2>
        <label className="block text-sm font-medium">{resource === "members" ? "Họ và tên" : "Tên chi nhánh"}<input className={`${fieldClass} mt-2`} name="name" required minLength={2} maxLength={200} defaultValue={editing?.name || ""} /></label>
        {resource === "members" && <>
          <label className="block text-sm font-medium">Chi nhánh<select key={`${branches.data?.items.length || 0}-${ownProfile.data?.member?.branch_id || ""}`} name="branch_id" aria-label="Chi nhánh" required className={`${fieldClass} mt-2`} defaultValue={editing?.branch_id || (user.role === "family_head" ? ownProfile.data?.member?.branch_id : "") || ""}><option value="">Chọn chi nhánh</option>{branches.data?.items.filter((row) => user.role === "admin" || row.can_manage).map((row) => <option key={row.id} value={row.id}>{row.name}</option>)}</select></label>
          <QueryState query={branches} />
          <label className="block text-sm font-medium">Ngày sinh<input type="date" className={`${fieldClass} mt-2`} name="birth_date" required defaultValue={editing?.birth_date || ""} max={new Date().toISOString().slice(0,10)} /></label>
          <label className="block text-sm font-medium">Nơi ở<input className={`${fieldClass} mt-2`} name="location" required maxLength={300} defaultValue={editing?.location || ""} /></label>
          <p className="text-sm text-stone-600">Liên kết tài khoản được thực hiện qua yêu cầu xác minh và phê duyệt.</p>
        </>}
        <div className="flex flex-wrap gap-3"><button className={buttonClass} disabled={save.isPending || (resource === "members" && !branches.isSuccess)}>{save.isPending ? "Đang lưu…" : editing ? "Lưu thay đổi" : "Thêm mới"}</button>{editing && <button type="button" className="px-3 text-sm underline" onClick={() => setEditing(null)}>Hủy sửa</button>}</div>
      </form>}
    </div>
  </div>;
}

export function FamilyManagement() {
  const { user } = useAuth();
  const cache = useQueryClient();
  const create = useMutation({ mutationFn: (name) => genealogyApi.save("families", null, null, { name }), onSuccess: () => cache.invalidateQueries({ queryKey: ["tv4"] }) });
  return <div className="space-y-6">
    {user.role === "admin" && <form className="flex flex-wrap items-end gap-3 rounded-2xl border border-stone-200 bg-white p-5" onSubmit={(event) => { event.preventDefault(); create.mutate(new FormData(event.currentTarget).get("name")); }}><label className="text-sm font-medium">Tạo gia đình<input className={`${fieldClass} mt-2`} name="name" placeholder="Tên gia đình mới" required minLength={2} maxLength={200} /></label><button className={buttonClass} disabled={create.isPending}>Tạo gia đình</button>{create.isError && <p role="alert" className="text-red-700">{getApiErrorMessage(create.error)}</p>}{create.isSuccess && <p role="status" className="text-sm text-forest">Đã tạo gia đình. Chọn gia đình bên dưới để thêm chi nhánh và thành viên.</p>}</form>}
    <FamilyScope title="Quản lý gia đình" description="Quản lý gia đình, chi nhánh và hồ sơ thành viên theo quyền được cấp.">{(familyId, actor) => <RecordWorkspace key={familyId} familyId={familyId} user={actor} />}</FamilyScope>
  </div>;
}
