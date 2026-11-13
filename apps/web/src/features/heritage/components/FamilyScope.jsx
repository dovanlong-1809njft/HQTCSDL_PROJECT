import { useState } from "react";
import { useQuery } from "@tanstack/react-query";
import { useAuth } from "@/features/auth/hooks/useAuth";
import { getApiErrorMessage } from "@/shared/api/client";
import { heritageApi } from "../api/heritageApi";

export const fieldClass = "w-full rounded-xl border border-stone-300 bg-white px-3 py-2 text-sm text-stone-800 focus:outline-none focus:ring-2 focus:ring-leaf";
export const buttonClass = "rounded-xl bg-forest px-4 py-2 text-sm font-semibold text-white disabled:opacity-50";

export function QueryState({ query }) {
  if (query.isPending) return <p role="status" className="py-5 text-stone-600">Đang tải dữ liệu…</p>;
  if (query.isError) return <div role="alert" className="my-4 rounded-xl bg-red-50 p-4 text-red-800">{getApiErrorMessage(query.error)} <button type="button" className="underline" onClick={() => query.refetch()}>Thử lại</button></div>;
  return null;
}

export function Pager({ page, total, pageSize = 12, onChange }) {
  const pages = Math.max(1, Math.ceil(total / pageSize));
  return <div className="mt-5 flex flex-wrap items-center gap-3 text-sm">
    <button className={buttonClass} disabled={page <= 1} onClick={() => onChange(page - 1)}>Trước</button>
    <span>Trang {page}/{pages} · {total} kết quả</span>
    <button className={buttonClass} disabled={page >= pages} onClick={() => onChange(page + 1)}>Sau</button>
  </div>;
}

export function FamilyScope({ title, description, children }) {
  const { user } = useAuth();
  const [selected, setSelected] = useState("");
  const query = useQuery({ queryKey: ["tv4", user.id, "families"], queryFn: heritageApi.families });
  const familyId = query.data?.some((f) => f.id === selected) ? selected : query.data?.[0]?.id;
  return <section className="min-w-0 space-y-5">
    <header><h1 className="text-2xl font-bold text-forest">{title}</h1><p className="mt-2 text-sm text-stone-600">{description}</p></header>
    <QueryState query={query} />
    {query.isSuccess && !query.data.length && <p className="rounded-2xl bg-white p-5">Chưa có gia đình được liên kết. Hãy liên hệ người quản lý để xác minh hồ sơ.</p>}
    {!!query.data?.length && <><label className="block max-w-md text-sm font-semibold">Gia đình<select className={`${fieldClass} mt-2`} value={familyId} onChange={(e) => setSelected(e.target.value)}>{query.data.map((family) => <option key={family.id} value={family.id}>{family.name}</option>)}</select></label>
      {children(familyId, user)}</>}
  </section>;
}
