import { useState } from "react";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { useNavigate } from "react-router-dom";
import { useAuth } from "@/features/auth/hooks/useAuth";
import { api, getApiErrorMessage } from "@/shared/api/client";
import { utcDate } from "@/shared/dates";

const button = "rounded-xl bg-forest px-4 py-2.5 text-sm font-semibold text-white disabled:opacity-50";
const input = "mt-2 w-full rounded-xl border border-stone-300 px-3 py-2.5 text-sm";

export function Backups() {
  const { user, signOut } = useAuth();
  const navigate = useNavigate();
  const queryClient = useQueryClient();
  const [selected, setSelected] = useState(null);
  const [database, setDatabase] = useState("");
  const [password, setPassword] = useState("");
  const [notice, setNotice] = useState("");
  const queryKey = ["admin-backups", user.id];
  const query = useQuery({ queryKey, queryFn: async ({ signal }) => (await api.get("/admin/backups", { signal })).data });
  const create = useMutation({
    mutationFn: async () => (await api.post("/admin/backups", null, { timeout: 300000 })).data,
    onMutate: () => { setNotice(""); restore.reset(); remove.reset(); },
    onSuccess: () => { setNotice("Đã tạo và kiểm tra bản sao lưu thành công."); queryClient.invalidateQueries({ queryKey }); },
  });
  const restore = useMutation({
    mutationFn: async () => (await api.post(`/admin/backups/${selected.id}/restore`, { database, password }, { timeout: 300000 })).data,
    onMutate: () => { setNotice(""); create.reset(); remove.reset(); },
    onSuccess: (data) => {
      setPassword("");
      signOut();
      navigate("/login", { replace: true, state: { restoreMessage: data.message } });
    },
    onError: () => { setPassword(""); queryClient.invalidateQueries({ queryKey }); },
  });
  const remove = useMutation({
    mutationFn: async (row) => api.delete(`/admin/backups/${row.id}`),
    onMutate: () => { setNotice(""); create.reset(); restore.reset(); },
    onSuccess: (_, row) => {
      if (selected?.id === row.id) { setSelected(null); setPassword(""); setDatabase(""); }
      setNotice(`Đã xóa bản sao lưu ${row.file_name}.`);
    },
    onSettled: () => queryClient.invalidateQueries({ queryKey }),
  });
  const busy = create.isPending || restore.isPending || remove.isPending;
  const error = create.error || restore.error || remove.error;

  function selectBackup(row) {
    setSelected(row); setDatabase(""); setPassword(""); setNotice(""); create.reset(); restore.reset(); remove.reset();
  }

  return <section className="space-y-6" aria-busy={busy}>
    <div className="flex flex-wrap items-start justify-between gap-4">
      <div><h1 className="text-2xl font-semibold text-forest">Sao lưu &amp; khôi phục</h1>
        <p className="mt-2 text-sm text-stone-600">Tạo bản sao dữ liệu SQL Server và khôi phục về thời điểm đã lưu.</p>
      </div>
      <button type="button" className={button} disabled={busy || !query.data || query.isError} onClick={() => create.mutate()}>Tạo bản sao lưu</button>
    </div>
    <div className="rounded-2xl border border-stone-200 bg-white p-5 text-sm leading-6">
      <p>Database: <strong>{query.data?.database || "Đang tải…"}</strong></p>
      <p>File .bak được lưu trong thư mục backup mặc định của SQL Server, trên máy chủ. Chỉ các bản do ứng dụng tạo mới xuất hiện bên dưới.</p>
      <p className="mt-2 text-stone-600">Sao lưu này gồm tài khoản, gia phả, bài viết và các dữ liệu trong database. Ảnh, video tải lên cần được sao lưu riêng.</p>
    </div>
    {busy && <p role="status" className="rounded-xl bg-sage p-4 text-sm">{restore.isPending ? "Đang tạo bản an toàn và khôi phục database. Các thao tác dữ liệu tạm dừng." : remove.isPending ? "Đang xóa bản sao lưu…" : "Đang sao lưu và kiểm tra file…"} Vui lòng giữ trang này mở.</p>}
    {notice && <p role="status" className="text-sm text-forest">{notice}</p>}
    {error && <p role="alert" className="text-sm text-red-700">{error.code === "ECONNABORTED" ? "Máy chủ chưa trả kết quả. Hãy tải lại danh sách và kiểm tra trạng thái trước khi thực hiện lại." : getApiErrorMessage(error)}</p>}
    <div className="overflow-hidden rounded-2xl border border-stone-200 bg-white">
      <div className="flex items-center justify-between gap-3 border-b border-stone-100 p-5">
        <h2 className="font-semibold text-forest">Các bản sao lưu</h2>
        <button type="button" className="text-sm underline disabled:opacity-50" disabled={busy || query.isFetching} onClick={() => query.refetch()}>Tải lại</button>
      </div>
      {query.isPending ? <p role="status" className="p-5 text-sm">Đang tải danh sách…</p>
        : query.isError ? <p role="alert" className="p-5 text-sm text-red-700">{getApiErrorMessage(query.error)}</p>
          : query.data.backups.length === 0 ? <p className="p-5 text-sm text-stone-600">Chưa có bản sao lưu. Bấm “Tạo bản sao lưu” để bắt đầu.</p>
            : <div className="overflow-x-auto"><table className="w-full text-left text-sm">
              <caption className="sr-only">Danh sách bản sao lưu SQL Server</caption>
              <thead className="bg-stone-50 text-stone-600"><tr><th scope="col" className="p-4">File</th><th scope="col" className="p-4">Thời gian (Việt Nam, UTC+7)</th><th scope="col" className="p-4">Dung lượng</th><th scope="col" className="p-4">Thao tác</th></tr></thead>
              <tbody className="divide-y divide-stone-100">{query.data.backups.map((row) => <tr key={row.id}>
                <th scope="row" className="max-w-72 break-all p-4 font-mono text-xs font-normal">{row.file_name}</th>
                <td className="whitespace-nowrap p-4">{utcDate(row.created_at).toLocaleString("vi-VN", { timeZone: "Asia/Ho_Chi_Minh", hour12: false })}</td>
                <td className="whitespace-nowrap p-4">{(row.size_bytes / 1048576).toLocaleString("vi-VN", { maximumFractionDigits: 2 })} MB</td>
                <td className="p-4"><div className="flex flex-wrap gap-3">
                  <button type="button" className="font-semibold text-red-700 underline disabled:opacity-50" disabled={busy} onClick={() => selectBackup(row)} aria-label={`Khôi phục ${row.file_name}`}>Khôi phục</button>
                  <button type="button" className="font-semibold text-red-700 underline disabled:opacity-50" disabled={busy} onClick={() => {
                    if (window.confirm(`Xóa vĩnh viễn bản sao lưu ${row.file_name}? Bạn sẽ không thể khôi phục từ bản này sau khi xóa. Dữ liệu database hiện tại vẫn được giữ nguyên.`)) remove.mutate(row);
                  }} aria-label={`Xóa ${row.file_name}`}>Xóa</button>
                </div></td>
              </tr>)}</tbody>
            </table></div>}
    </div>
    {selected && <section className="rounded-2xl border border-red-200 bg-white p-5" aria-labelledby="restore-title">
      <h2 id="restore-title" className="font-semibold text-red-800">Xác nhận khôi phục</h2>
      <p className="mt-3 text-sm leading-6">Khôi phục sẽ <strong>ghi đè toàn bộ database hiện tại</strong> bằng <span className="break-all font-mono">{selected.file_name}</span>. Mọi dữ liệu thêm hoặc sửa sau thời điểm sao lưu sẽ mất. Hệ thống sẽ kiểm tra file và tạo bản sao lưu an toàn trước khi ghi đè.</p>
      <p className="mt-2 text-sm text-stone-600">Sau khi hoàn tất, đăng nhập lại bằng tài khoản và mật khẩu có trong bản sao lưu.</p>
      <form className="mt-5" onSubmit={(event) => { event.preventDefault(); if (!busy && database === query.data?.database && password) restore.mutate(); }}>
        <fieldset disabled={busy} className="grid gap-4 md:grid-cols-2">
          <label className="text-sm font-semibold" htmlFor="restore-database">Nhập tên database: {query.data?.database}
            <input autoFocus id="restore-database" required maxLength={128} className={input} value={database} onChange={(event) => setDatabase(event.target.value)} autoComplete="off" />
          </label>
          <label className="text-sm font-semibold" htmlFor="restore-password">Mật khẩu admin hiện tại
            <input id="restore-password" required type="password" maxLength={128} className={input} value={password} onChange={(event) => setPassword(event.target.value)} autoComplete="current-password" />
          </label>
          <div className="flex flex-wrap gap-3 md:col-span-2">
            <button type="submit" className="rounded-xl bg-red-700 px-4 py-2.5 text-sm font-semibold text-white disabled:opacity-50" disabled={busy || database !== query.data?.database || !password}>Xác nhận ghi đè và khôi phục</button>
            <button type="button" className="rounded-xl border border-stone-300 px-4 py-2.5 text-sm" onClick={() => { setSelected(null); setPassword(""); restore.reset(); }}>Hủy</button>
          </div>
        </fieldset>
      </form>
    </section>}
  </section>;
}
