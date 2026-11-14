import { useState } from "react";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { buttonClass, fieldClass, Pager, QueryState } from "@/features/heritage/components/FamilyScope";
import { getApiErrorMessage } from "@/shared/api/client";
import { genealogyApi } from "../api/genealogyApi";

export function MemberPicker({ label, familyId, value, onChange }) {
  const [q, setQ] = useState("");
  const [page, setPage] = useState(1);
  const query = useQuery({ queryKey: ["genealogy", familyId, "pick", q, page], queryFn: () => genealogyApi.list("members", familyId, { q, page, page_size: 30 }) });
  return <fieldset className="min-w-0 space-y-2"><legend className="text-sm font-medium">{label}</legend><input aria-label={`Tìm ${label.toLocaleLowerCase("vi")}`} className={fieldClass} type="search" placeholder="Gõ tên để tìm trong gia đình" value={q} maxLength={200} onChange={(event) => { setQ(event.target.value); setPage(1); }} /><QueryState query={query} /><select aria-label={label} className={fieldClass} required value={value?.id || ""} onChange={(event) => onChange(query.data?.items.find((row) => row.id === event.target.value) || null)}><option value="">Chọn thành viên</option>{value && !query.data?.items.some((row) => row.id === value.id) && <option value={value.id}>{value.name}</option>}{query.data?.items.map((row) => <option key={row.id} value={row.id}>{row.name}{row.birth_date ? ` (${row.birth_date})` : ""}</option>)}</select>{query.data?.total > 30 && <Pager page={page} total={query.data.total} pageSize={30} onChange={setPage} />}</fieldset>;
}

export function Relationships({ familyId, user }) {
  const cache = useQueryClient();
  const [kind, setKind] = useState("parent-child");
  const [first, setFirst] = useState(null);
  const [second, setSecond] = useState(null);
  const [focus, setFocus] = useState(null);
  const [notice, setNotice] = useState("");
  const manage = ["admin", "family_head"].includes(user.role);
  const query = useQuery({ queryKey: ["genealogy", user.id, familyId, "relationships", focus?.id], queryFn: () => genealogyApi.relations(familyId, focus?.id) });
  const changed = () => { cache.invalidateQueries({ queryKey: ["genealogy"] }); cache.invalidateQueries({ queryKey: ["tv4"] }); setNotice("Đã cập nhật quan hệ và cây gia phả."); };
  const add = useMutation({ mutationFn: (payload) => genealogyApi.addRelation(familyId, kind, payload), onSuccess: changed });
  const remove = useMutation({ mutationFn: ({ type, id }) => genealogyApi.removeRelation(familyId, type, id), onSuccess: changed });
  return <section className="space-y-5 rounded-2xl border border-stone-200 bg-white p-5">
    <h2 className="text-lg font-semibold text-forest">Quan hệ gia phả</h2>
    {manage && <form className="space-y-4" onSubmit={(event) => { event.preventDefault(); if (!first || !second) return; const values = new FormData(event.currentTarget); setNotice(""); add.mutate({ first_id: first.id, second_id: second.id, married_date: kind === "marriages" ? values.get("married_date") || null : null }); }}>
      <label className="block max-w-sm text-sm font-medium">Loại quan hệ<select className={`${fieldClass} mt-2`} value={kind} onChange={(event) => { setKind(event.target.value); add.reset(); }}><option value="parent-child">Cha/mẹ – con</option><option value="marriages">Hôn nhân</option></select></label>
      <div className="grid gap-4 sm:grid-cols-2"><MemberPicker label={kind === "parent-child" ? "Cha/mẹ" : "Người thứ nhất"} familyId={familyId} value={first} onChange={setFirst} /><MemberPicker label={kind === "parent-child" ? "Con" : "Người thứ hai"} familyId={familyId} value={second} onChange={setSecond} /></div>
      {kind === "marriages" && <label className="block max-w-sm text-sm font-medium">Ngày kết hôn<input name="married_date" type="date" className={`${fieldClass} mt-2`} /></label>}
      <p className="text-sm text-stone-600">Mỗi người tối đa hai cha/mẹ. Hệ thống kiểm tra chu trình, quan hệ trùng và huyết thống trong ba đời.</p>
      <button className={buttonClass} disabled={add.isPending || !first || !second}>{add.isPending ? "Đang lưu…" : "Thêm quan hệ"}</button>
    </form>}
    {notice && <p role="status" className="rounded-xl bg-sage p-3 text-forest">{notice}</p>}
    {[add, remove].filter((m) => m.isError).map((m, i) => <p role="alert" key={i} className="text-red-700">{getApiErrorMessage(m.error)}</p>)}
    <QueryState query={query} />
    {query.data && <div className="grid gap-5 lg:grid-cols-2">{[["parent-child", "Cha/mẹ – con", query.data.parent_child], ["marriages", "Hôn nhân", query.data.marriages]].map(([type, title, rows]) => <section key={type}><h3 className="font-semibold text-forest">{title} · {rows.length}</h3><ul className="mt-2 max-h-80 divide-y divide-stone-200 overflow-y-auto">{rows.map((row) => <li className="flex items-center justify-between gap-3 py-2 text-sm" key={row.id}><span>{row.first_name} {type === "parent-child" ? "→" : "↔"} {row.second_name}{row.married_date ? ` · ${row.married_date}` : ""}</span>{manage && row.can_manage !== false && <button className="shrink-0 rounded-lg px-3 py-2 text-red-700" disabled={remove.isPending} onClick={() => { if (window.confirm(`Xóa quan hệ giữa ${row.first_name} và ${row.second_name}?`)) remove.mutate({ type, id: row.id }); }}>Xóa<span className="sr-only"> quan hệ {row.first_name} và {row.second_name}</span></button>}</li>)}</ul>{!rows.length && <p className="mt-3 text-sm text-stone-600">Chưa có quan hệ.</p>}</section>)}</div>}
    <div className="border-t border-stone-200 pt-5"><h3 className="mb-3 font-semibold text-forest">Tra cứu tổ tiên và hậu duệ</h3><div className="max-w-md"><MemberPicker label="Thành viên cần tra cứu" familyId={familyId} value={focus} onChange={setFocus} /></div>{focus && query.data && <div className="mt-4 grid gap-4 sm:grid-cols-2">{[["Tổ tiên", query.data.ancestors], ["Hậu duệ", query.data.descendants]].map(([title, rows]) => <div key={title}><h4 className="font-semibold">{title}</h4><ul className="mt-2 max-h-64 overflow-y-auto text-sm">{rows.map((row) => <li key={row.id} className="py-1">{row.name} · cách {row.depth} đời</li>)}</ul>{!rows.length && <p className="text-sm text-stone-600">Chưa ghi nhận.</p>}</div>)}</div>}</div>
  </section>;
}
