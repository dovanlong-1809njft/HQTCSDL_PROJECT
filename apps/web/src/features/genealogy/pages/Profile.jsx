import {MemberHistoryPanel} from "../components/MemberHistoryPanel";
import { useState } from "react";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { useAuth } from "@/features/auth/hooks/useAuth";
import { buttonClass, fieldClass, QueryState } from "@/features/heritage/components/FamilyScope";
import { getApiErrorMessage } from "@/shared/api/client";
import { genealogyApi } from "../api/genealogyApi";

const statuses = { pending: "Chờ duyệt", approved: "Đã xác minh", rejected: "Đã từ chối" };

export function Profile() {
  const { user, updateUser } = useAuth();
  const cache = useQueryClient();
  const [notice, setNotice] = useState("");
  const query = useQuery({ queryKey: ["genealogy", user.id, "profile"], queryFn: genealogyApi.profile });
  const saved = (data) => {
    updateUser(data.user);
    cache.setQueryData(["genealogy", user.id, "profile"], data);
    cache.invalidateQueries({ queryKey: ["tv4"] });
  };
  const save = useMutation({ mutationFn: genealogyApi.saveProfile, onSuccess: (data) => { saved(data); setNotice("Đã lưu hồ sơ."); } });
  const search = useMutation({ mutationFn: genealogyApi.candidates });
  const verify = useMutation({ mutationFn: genealogyApi.verify, onSuccess: (data) => { saved(data); search.reset(); setNotice("Đã gửi yêu cầu. Người quản lý sẽ duyệt hồ sơ của bạn."); } });
  const data = query.data;
  const pending = data?.verifications.some((v) => v.status === "pending");
  return <section className="max-w-4xl space-y-6">
    <header><h1 className="text-2xl font-bold text-forest">Hồ sơ của tôi</h1><p className="mt-2 text-stone-600">Cập nhật thông tin và liên kết với hồ sơ gia phả của bạn.</p></header>
    <QueryState query={query} />
    {notice && <p role="status" className="rounded-xl bg-sage p-4 text-forest">{notice}</p>}
    {data && <>
      <form key={JSON.stringify([data.user.full_name, data.member])} className="space-y-4 rounded-2xl border border-stone-200 bg-white p-5" onSubmit={(event) => {
        event.preventDefault(); setNotice(""); const values = new FormData(event.currentTarget);
        save.mutate({ name: values.get("name"), birth_date: data.member ? values.get("birth_date") || null : null, location: data.member ? values.get("location") || null : null });
      }}>
        <h2 className="text-lg font-semibold text-forest">Thông tin cá nhân</h2>
        <p className="text-sm text-stone-600">Email đăng nhập: {data.user.email}</p>
        <label className="block text-sm font-medium">Họ và tên<input className={`${fieldClass} mt-2`} name="name" required minLength={2} maxLength={200} defaultValue={data.member?.name || data.user.full_name} autoComplete="name" /></label>
        {data.member && <>
          <p className="text-sm">{data.member.family_name} · {data.member.branch_name || "Chưa phân chi"}</p>
          <div className="grid gap-4 sm:grid-cols-2"><label className="block text-sm font-medium">Ngày sinh<input type="date" name="birth_date" required className={`${fieldClass} mt-2`} defaultValue={data.member.birth_date || ""} max={new Date().toISOString().slice(0,10)} /></label><label className="block text-sm font-medium">Nơi ở<input name="location" required className={`${fieldClass} mt-2`} maxLength={300} defaultValue={data.member.location || ""} autoComplete="address-level2" /></label></div>
        </>}
        {save.isError && <p role="alert" className="text-red-700">{getApiErrorMessage(save.error)}</p>}
        <button className={buttonClass} disabled={save.isPending}>{save.isPending ? "Đang lưu…" : "Lưu hồ sơ"}</button>
      </form>
      {data.member ? <MemberHistoryPanel key={data.member.id} id={data.member.id} familyId={data.member.family_id} user={user}/> : <p className="rounded-xl bg-white p-4">Liên kết hồ sơ gia phả trước khi thêm học vấn và nghề nghiệp.</p>}
      {!data.member && user.role !== "guest" && <section className="space-y-4 rounded-2xl border border-stone-200 bg-white p-5">
        <h2 className="text-lg font-semibold text-forest">Liên kết hồ sơ gia phả</h2>
        <p className="text-sm text-stone-600">Nhập đúng tên gia đình và họ tên trong gia phả. Nếu chưa có hồ sơ, hãy nhờ người quản lý tạo trước.</p>
        <form className="grid gap-4 sm:grid-cols-2" onSubmit={(event) => { event.preventDefault(); const values = new FormData(event.currentTarget); search.mutate({ family_name: values.get("family_name"), full_name: values.get("full_name"), ...(values.get("birth_date") ? { birth_date: values.get("birth_date") } : {}) }); }}>
          <label className="text-sm font-medium">Tên gia đình<input className={`${fieldClass} mt-2`} name="family_name" required minLength={2} maxLength={200} /></label>
          <label className="text-sm font-medium">Họ tên trong gia phả<input className={`${fieldClass} mt-2`} name="full_name" required minLength={2} maxLength={200} defaultValue={data.user.full_name} /></label>
          <label className="text-sm font-medium">Ngày sinh (nếu biết)<input className={`${fieldClass} mt-2`} type="date" name="birth_date" /></label>
          <div className="self-end"><button className={buttonClass} disabled={search.isPending || pending}>{search.isPending ? "Đang tìm…" : "Tìm hồ sơ"}</button></div>
        </form>
        {pending && <p role="status" className="text-sm text-forest">Bạn đã có yêu cầu đang chờ duyệt.</p>}
        {search.isError && <p role="alert" className="text-red-700">{getApiErrorMessage(search.error)}</p>}
        {search.isSuccess && !search.data.length && <p role="status">Không có hồ sơ chưa liên kết khớp thông tin này.</p>}
        {search.data?.map((row) => <div key={row.id} className="flex flex-wrap items-center justify-between gap-3 border-t border-stone-200 pt-3"><div><p className="font-semibold">{row.name}</p><p className="text-sm text-stone-600">{row.family_name} · {row.branch_name || "Chưa phân chi"}</p></div><button type="button" className={buttonClass} disabled={pending || verify.isPending} onClick={() => verify.mutate(row.id)}>Gửi yêu cầu xác minh</button></div>)}
        {verify.isError && <p role="alert" className="text-red-700">{getApiErrorMessage(verify.error)}</p>}
      </section>}
      {!!data.verifications.length && <section className="rounded-2xl border border-stone-200 bg-white p-5"><h2 className="text-lg font-semibold text-forest">Lịch sử xác minh</h2><ul className="mt-3 divide-y divide-stone-200">{data.verifications.map((row) => <li key={row.id} className="flex flex-wrap justify-between gap-3 py-3"><span>{row.name} · {row.family_name}</span><span className="text-sm font-semibold text-forest">{statuses[row.status]}</span></li>)}</ul></section>}
    </>}
  </section>;
}
