import { useQuery } from "@tanstack/react-query";
import { Bar, BarChart, CartesianGrid, Legend, ResponsiveContainer, Tooltip, XAxis, YAxis } from "recharts";
import { useAuth } from "@/features/auth/hooks/useAuth";
import { getApiErrorMessage } from "@/shared/api/client";
import { getStatistics } from "../api/dashboardApi";

export function Dashboard() {
  const { user } = useAuth();
  const canViewStatistics = ["admin", "family_head"].includes(user.role);
  const query = useQuery({
    queryKey: ["dashboard-statistics", user.id, user.role],
    queryFn: ({ signal }) => getStatistics(signal),
    enabled: canViewStatistics,
  });
  const rows = query.data ?? [];
  const cards = [
    { label: "Gia đình", value: rows.length },
    { label: "Thành viên", value: rows.reduce((sum, row) => sum + row.member_count, 0) },
    { label: "Bài viết", value: rows.reduce((sum, row) => sum + row.post_count, 0) },
    { label: "Sự kiện", value: rows.reduce((sum, row) => sum + row.event_count, 0) },
  ];

  return (
    <section className="space-y-6">
      <div className="flex flex-wrap items-end justify-between gap-4">
        <div>
          <p className="text-sm font-medium text-leaf">Tổng quan gia đình</p>
          <h1 className="mt-2 text-2xl font-bold text-forest sm:text-3xl">Chào mừng, <span className="capitalize">{user.fullName}</span></h1>
          <p className="mt-2 text-sm text-stone-500">{canViewStatistics
            ? user.role === "admin" ? "Thống kê hoạt động của các gia đình trong hệ thống." : "Thống kê các gia đình có hồ sơ đã liên kết với tài khoản của bạn."
            : "Không gian chung để kết nối và lưu giữ những điều thân thương."}</p>
        </div>
        {canViewStatistics && <button type="button" disabled={query.isFetching} onClick={() => query.refetch()}
          className="rounded-xl border border-stone-200 bg-white px-4 py-2.5 text-sm font-semibold text-forest hover:bg-sage disabled:opacity-50">
          {query.isFetching ? "Đang tải…" : "Làm mới"}
        </button>}
      </div>
      {!canViewStatistics ? <div className="rounded-2xl border border-stone-200 bg-white p-6 shadow-sm">
        <h2 className="text-lg font-semibold text-forest">Không gian gia đình</h2>
        <p className="mt-2 text-sm text-stone-500">Kết nối thành viên, gìn giữ ký ức và cùng nhau viết tiếp câu chuyện của gia đình mình.</p>
      </div> : query.isPending ? <p role="status" className="text-sm text-stone-500">Đang tải thống kê…</p>
        : query.isError ? <p role="alert" className="rounded-xl bg-red-50 p-4 text-sm text-red-700">{getApiErrorMessage(query.error)}</p>
          : rows.length === 0 ? <p className="rounded-2xl border bg-white p-6 text-sm text-stone-500">Chưa có gia đình trong phạm vi thống kê của bạn.</p>
            : <>
              <dl className="grid grid-cols-2 gap-4 xl:grid-cols-4">
                {cards.map((card) => <div key={card.label} className="rounded-2xl border border-stone-200 bg-white p-5 shadow-sm">
                  <dt className="text-sm text-stone-500">{card.label}</dt><dd className="mt-2 text-3xl font-bold text-forest">{card.value.toLocaleString("vi-VN")}</dd>
                </div>)}
              </dl>
              <div className="min-w-0 rounded-2xl border border-stone-200 bg-white p-5 shadow-sm">
                <h2 className="mb-5 font-semibold text-forest">Hoạt động theo gia đình</h2>
                <div role="img" aria-label="Biểu đồ số thành viên, bài viết và sự kiện theo gia đình" className="h-80 min-w-0">
                  <ResponsiveContainer width="100%" height="100%">
                    <BarChart data={rows} margin={{ top: 10, right: 10, left: -20, bottom: 10 }}>
                      <CartesianGrid strokeDasharray="3 3" vertical={false} />
                      <XAxis dataKey="family_name" tick={{ fontSize: 11 }} />
                      <YAxis allowDecimals={false} tick={{ fontSize: 11 }} />
                      <Tooltip /><Legend />
                      <Bar dataKey="member_count" name="Thành viên" fill="#2b5143" radius={[4, 4, 0, 0]} />
                      <Bar dataKey="post_count" name="Bài viết" fill="#92ad82" radius={[4, 4, 0, 0]} />
                      <Bar dataKey="event_count" name="Sự kiện" fill="#c79666" radius={[4, 4, 0, 0]} />
                    </BarChart>
                  </ResponsiveContainer>
                </div>
                <div className="mt-5 overflow-x-auto">
                  <table className="w-full text-left text-sm">
                    <caption className="sr-only">Số liệu hoạt động theo gia đình</caption>
                    <thead className="border-b text-stone-500"><tr><th scope="col" className="p-3">Gia đình</th><th scope="col" className="p-3">Thành viên</th><th scope="col" className="p-3">Bài viết</th><th scope="col" className="p-3">Sự kiện</th></tr></thead>
                    <tbody>{rows.map((row) => <tr key={row.family_id} className="border-b border-stone-100 last:border-0">
                      <th scope="row" className="p-3 font-medium text-forest">{row.family_name}</th><td className="p-3">{row.member_count}</td><td className="p-3">{row.post_count}</td><td className="p-3">{row.event_count}</td>
                    </tr>)}</tbody>
                  </table>
                </div>
              </div>
            </>}
    </section>
  );
}
