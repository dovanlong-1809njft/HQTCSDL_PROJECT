import { useState } from "react";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { useAuth } from "@/features/auth/hooks/useAuth";
import { getApiErrorMessage } from "@/shared/api/client";
import { getPendingVerifications, reviewVerification } from "../api/memberApprovalApi";

const PAGE_SIZE = 20;

export function MemberApproval() {
  const { user } = useAuth();
  const queryClient = useQueryClient();
  const [offset, setOffset] = useState(0);
  const [notice, setNotice] = useState("");
  const [actionError, setActionError] = useState("");
  const queryKey = ["pending-verifications", user.id, user.role];
  const query = useQuery({
    queryKey: [...queryKey, offset],
    queryFn: ({ signal }) => getPendingVerifications({ limit: PAGE_SIZE, offset }, signal),
  });
  const rows = query.data ?? [];
  const review = useMutation({
    mutationFn: ({ id, decision }) => reviewVerification(id, decision),
    onMutate: () => { setNotice(""); setActionError(""); },
    onSuccess: async (data) => {
      setNotice(data.status === "approved" ? "Đã duyệt xác minh thành viên." : "Đã từ chối yêu cầu xác minh.");
      if (offset > 0) setOffset(0);
      // Approval can reject competing requests on other pages, too.
      await queryClient.invalidateQueries({ queryKey });
    },
    onError: async (error) => {
      setActionError(getApiErrorMessage(error));
      if ([403, 404, 409].includes(error.response?.status)) {
        await queryClient.invalidateQueries({ queryKey });
      }
    },
  });

  return (
    <section aria-labelledby="approval-title" className="space-y-6">
      <div className="flex flex-wrap items-end justify-between gap-4">
        <div>
          <p className="text-sm font-semibold text-leaf">Quản lý thành viên</p>
          <h1 id="approval-title" className="mt-2 text-2xl font-bold text-forest sm:text-3xl">Duyệt thành viên</h1>
          <p className="mt-2 text-sm text-stone-500">{user.role === "admin" ? "Xem và xử lý các yêu cầu xác minh đang chờ." : "Xem và xử lý yêu cầu xác minh thuộc chi bạn quản lý."}</p>
        </div>
        <button type="button" disabled={query.isFetching || review.isPending} onClick={() => query.refetch()}
          className="rounded-xl border border-stone-200 bg-white px-4 py-2.5 text-sm font-semibold text-forest hover:bg-sage disabled:opacity-50">
          {query.isFetching ? "Đang tải…" : "Làm mới"}
        </button>
      </div>
      {notice && <p role="status" className="rounded-xl border border-green-200 bg-green-50 px-4 py-3 text-sm text-green-800">{notice}</p>}
      {actionError && <p role="alert" className="rounded-xl border border-red-200 bg-red-50 px-4 py-3 text-sm text-red-700">{actionError}</p>}

      <div className="overflow-hidden rounded-2xl border border-stone-200 bg-white shadow-sm">
        <div className="flex flex-wrap items-center justify-between gap-2 border-b border-stone-100 px-5 py-4">
          <h2 className="font-semibold text-forest">Yêu cầu chờ xác minh</h2>
          <span className="rounded-full bg-sage px-3 py-1 text-xs font-medium text-leaf">Chờ xử lý</span>
        </div>
        {query.isPending ? <p role="status" className="p-6 text-sm text-stone-500">Đang tải yêu cầu…</p>
          : query.isError ? <p role="alert" className="p-6 text-sm text-red-700">{getApiErrorMessage(query.error)}</p>
            : rows.length === 0 ? <div className="p-8 text-center"><p className="font-semibold text-forest">Không có yêu cầu chờ xác minh</p><p className="mt-2 text-sm text-stone-500">Các yêu cầu trong phạm vi quản lý sẽ xuất hiện tại đây.</p></div>
              : <div className="overflow-x-auto">
                <table className="w-full text-left text-sm">
                  <caption className="sr-only">Yêu cầu xác minh thành viên đang chờ duyệt</caption>
                  <thead className="bg-stone-50 text-xs text-stone-500"><tr>
                    <th scope="col" className="px-5 py-3">Người đăng ký</th>
                    <th scope="col" className="px-5 py-3">Hồ sơ xác minh</th>
                    <th scope="col" className="px-5 py-3">Gia đình / Chi</th>
                    <th scope="col" className="whitespace-nowrap px-5 py-3">Ngày gửi (UTC)</th>
                    <th scope="col" className="px-5 py-3">Thao tác</th>
                  </tr></thead>
                  <tbody className="divide-y divide-stone-100">
                    {rows.map((row) => <tr key={row.verification_id} className="hover:bg-stone-50/60">
                      <td className="min-w-44 px-5 py-4 align-top"><p className="font-semibold text-forest">{row.user_full_name}</p><p className="mt-1 break-all text-xs text-stone-500">{row.user_email}</p>{!row.user_is_active && <p className="mt-2 text-xs font-medium text-red-600">Tài khoản đang bị khóa</p>}</td>
                      <th scope="row" className="min-w-40 px-5 py-4 align-top font-normal"><p className="font-semibold">{row.member_full_name}</p>{row.birth_date && <p className="mt-1 text-xs text-stone-500">Ngày sinh: {row.birth_date}</p>}{row.linked_user_id && <p className="mt-2 text-xs text-earth">Hồ sơ đã có tài khoản liên kết</p>}</th>
                      <td className="min-w-36 px-5 py-4 align-top"><p>{row.family_name}</p><p className="mt-1 text-xs text-stone-500">{row.branch_name ?? "Chưa phân chi"}</p></td>
                      <td className="whitespace-nowrap px-5 py-4 align-top text-xs text-stone-500">{row.requested_at.replace("T", " ").replace("Z", "")}</td>
                      <td className="px-5 py-4 align-top"><div className="flex gap-2">
                        <button type="button" disabled={review.isPending || !row.user_is_active} aria-label={`Duyệt ${row.user_full_name}`}
                          onClick={() => review.mutate({ id: row.verification_id, decision: "approved" })}
                          className="whitespace-nowrap rounded-lg bg-forest px-3 py-2 text-xs font-semibold text-white hover:bg-[#1d4034] disabled:opacity-40">
                          {review.isPending && review.variables.id === row.verification_id && review.variables.decision === "approved" ? "Đang duyệt…" : "Duyệt"}
                        </button>
                        <button type="button" disabled={review.isPending} aria-label={`Từ chối ${row.user_full_name}`}
                          onClick={() => review.mutate({ id: row.verification_id, decision: "rejected" })}
                          className="whitespace-nowrap rounded-lg border border-red-200 px-3 py-2 text-xs font-semibold text-red-600 hover:bg-red-50 disabled:opacity-40">
                          {review.isPending && review.variables.id === row.verification_id && review.variables.decision === "rejected" ? "Đang xử lý…" : "Từ chối"}
                        </button>
                      </div></td>
                    </tr>)}
                  </tbody>
                </table>
              </div>}
        {!query.isError && <div className="flex items-center justify-between border-t border-stone-100 px-5 py-4 text-sm">
          <span className="text-stone-500">Trang {offset / PAGE_SIZE + 1}</span>
          <div className="flex gap-2">
            <button type="button" disabled={offset === 0 || query.isFetching || review.isPending} onClick={() => setOffset(offset - PAGE_SIZE)} className="rounded-lg border px-3 py-2 hover:bg-sage disabled:opacity-40">Trang trước</button>
            <button type="button" disabled={rows.length < PAGE_SIZE || query.isFetching || review.isPending} onClick={() => setOffset(offset + PAGE_SIZE)} className="rounded-lg border px-3 py-2 hover:bg-sage disabled:opacity-40">Trang sau</button>
          </div>
        </div>}
      </div>
    </section>
  );
}
