import { useState } from "react";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { useAuth } from "@/features/auth/hooks/useAuth";
import { getApiErrorMessage } from "@/shared/api/client";
import { getReports, resolveReport } from "../api/reportsApi";

const PAGE_SIZE = 20;
const statusLabels = { pending: "Chờ xử lý", resolved: "Đã gỡ nội dung", dismissed: "Đã bỏ qua" };
const targetLabels = { post: "Bài viết", comment: "Bình luận", photo: "Ảnh" };

export function Reports() {
  const { user } = useAuth();
  const queryClient = useQueryClient();
  const [status, setStatus] = useState("pending");
  const [offset, setOffset] = useState(0);
  const [notice, setNotice] = useState("");
  const [actionError, setActionError] = useState("");
  const queryKey = ["reported-contents", user.id, user.role];
  const query = useQuery({
    queryKey: [...queryKey, status, offset],
    queryFn: ({ signal }) => getReports({ status, limit: PAGE_SIZE + 1, offset }, signal),
  });
  const rows = (query.data ?? []).slice(0, PAGE_SIZE);
  const resolve = useMutation({
    mutationFn: ({ id, decision }) => resolveReport(id, decision),
    onMutate: () => { setNotice(""); setActionError(""); },
    onSuccess: async (data) => {
      setNotice(data.status === "resolved" ? `Đã gỡ nội dung và đóng ${data.resolved_report_count} báo cáo liên quan.` : "Đã bỏ qua báo cáo. Nội dung được giữ nguyên.");
      setOffset(0);
      await Promise.all([
        queryClient.invalidateQueries({ queryKey }),
        queryClient.invalidateQueries({ queryKey: ["dashboard-statistics"] }),
      ]);
    },
    onError: async (error) => {
      setActionError(getApiErrorMessage(error));
      if ([403, 404, 409].includes(error.response?.status)) await queryClient.invalidateQueries({ queryKey });
    },
  });

  return (
    <section aria-labelledby="reports-title" className="space-y-6">
      <div className="flex flex-wrap items-end justify-between gap-4">
        <div>
          <p className="text-sm font-semibold text-leaf">Kiểm duyệt</p>
          <h1 id="reports-title" className="mt-2 text-2xl font-bold text-forest sm:text-3xl">Báo cáo nội dung</h1>
          <p className="mt-2 text-sm text-stone-500">Xem lý do báo cáo và xử lý bài viết, bình luận hoặc ảnh.</p>
        </div>
        <button type="button" disabled={query.isFetching || resolve.isPending} onClick={() => query.refetch()}
          className="rounded-xl border border-stone-200 bg-white px-4 py-2.5 text-sm font-semibold text-forest hover:bg-sage disabled:opacity-50">
          {query.isFetching ? "Đang tải…" : "Làm mới"}
        </button>
      </div>
      {notice && <p role="status" className="rounded-xl bg-green-50 p-4 text-sm text-green-800">{notice}</p>}
      {actionError && <p role="alert" className="rounded-xl bg-red-50 p-4 text-sm text-red-700">{actionError}</p>}
      <div className="flex flex-wrap items-center gap-3">
        <label htmlFor="report-status" className="text-sm font-semibold">Trạng thái báo cáo</label>
        <select id="report-status" value={status} disabled={resolve.isPending} onChange={(event) => {
          setStatus(event.target.value); setOffset(0); setNotice(""); setActionError("");
        }} className="rounded-xl border border-stone-200 bg-white px-3 py-2.5 text-sm disabled:opacity-50">
          {Object.entries(statusLabels).map(([value, label]) => <option key={value} value={value}>{label}</option>)}
        </select>
      </div>
      {query.isPending ? <p role="status" className="text-sm text-stone-500">Đang tải báo cáo…</p>
        : query.isError ? <p role="alert" className="rounded-xl bg-red-50 p-4 text-sm text-red-700">{getApiErrorMessage(query.error)}</p>
          : rows.length === 0 ? <p className="rounded-2xl border bg-white p-6 text-sm text-stone-500">Không có báo cáo trong trạng thái này.</p>
            : <ul aria-label="Danh sách báo cáo" className="space-y-4">
              {rows.map((row) => <li key={row.report_id} aria-label={`Báo cáo ${row.report_id}`} className="min-w-0 rounded-2xl border border-stone-200 bg-white p-5 shadow-sm">
                <div className="flex flex-wrap items-center justify-between gap-2 text-xs text-stone-500">
                  <span className="rounded-full bg-sage px-3 py-1 font-semibold text-forest">{targetLabels[row.target_type]} · {statusLabels[row.status]}</span>
                  <span>{row.created_at.replace("T", " ").replace("Z", "")} (UTC)</span>
                </div>
                <p className="mt-4 break-words text-sm"><span className="font-semibold">Người báo cáo:</span> {row.reporter_name}</p>
                {row.family_name && <p className="mt-1 text-xs text-stone-500">{row.family_name}</p>}
                <p className="mt-3 whitespace-pre-wrap break-words text-sm"><span className="font-semibold">Lý do:</span> {row.reason}</p>
                <div tabIndex={0} role="region" aria-label={`Nội dung báo cáo ${row.report_id}`} className="mt-4 max-h-52 overflow-auto whitespace-pre-wrap break-all rounded-xl bg-stone-50 p-4 text-sm text-stone-700">
                  {row.target_content ?? "Nội dung không còn tồn tại."}
                  {row.target_type === "photo" && /^https?:\/\//i.test(row.target_content ?? "") && <a href={row.target_content} target="_blank" rel="noopener noreferrer" className="mt-2 block font-semibold text-leaf underline">Mở ảnh để kiểm tra</a>}
                </div>
                {row.status === "pending" && <div className="mt-4 flex flex-wrap gap-3">
                  <button type="button" disabled={resolve.isPending || !row.can_resolve} onClick={() => {
                    if (window.confirm("Gỡ nội dung này? Nội dung sẽ bị xóa vĩnh viễn. Nếu là bài viết, các bình luận, ảnh và phản ứng đi kèm cũng bị xóa; các báo cáo liên quan sẽ được đóng.")) {
                      resolve.mutate({ id: row.report_id, decision: "resolved" });
                    }
                  }} className="rounded-xl bg-red-700 px-4 py-2.5 text-sm font-semibold text-white hover:bg-red-800 disabled:opacity-40">Gỡ nội dung</button>
                  <button type="button" disabled={resolve.isPending} onClick={() => resolve.mutate({ id: row.report_id, decision: "dismissed" })}
                    className="rounded-xl border border-stone-200 px-4 py-2.5 text-sm font-semibold hover:bg-sage disabled:opacity-40">Bỏ qua báo cáo</button>
                  {!row.can_resolve && <p className="w-full text-xs text-stone-500">Nội dung không còn tồn tại hoặc không hỗ trợ gỡ. Bạn vẫn có thể bỏ qua báo cáo.</p>}
                </div>}
              </li>)}
            </ul>}
      {!query.isError && <div className="flex items-center justify-between gap-2 text-sm">
        <span className="text-stone-500">Trang {offset / PAGE_SIZE + 1}</span>
        <div className="flex gap-2">
          <button type="button" disabled={offset === 0 || query.isFetching || resolve.isPending} onClick={() => setOffset(offset - PAGE_SIZE)} className="rounded-lg border bg-white px-3 py-2 hover:bg-sage disabled:opacity-40">Trang trước</button>
          <button type="button" disabled={!query.data || query.data.length <= PAGE_SIZE || query.isFetching || resolve.isPending} onClick={() => setOffset(offset + PAGE_SIZE)} className="rounded-lg border bg-white px-3 py-2 hover:bg-sage disabled:opacity-40">Trang sau</button>
        </div>
      </div>}
    </section>
  );
}
