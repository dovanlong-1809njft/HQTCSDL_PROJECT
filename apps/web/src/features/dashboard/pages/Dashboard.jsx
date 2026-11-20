import { Link } from "react-router-dom";
import { useQuery } from "@tanstack/react-query";
import { Bar, BarChart, CartesianGrid, Legend, ResponsiveContainer, Tooltip, XAxis, YAxis } from "recharts";
import { useAuth } from "@/features/auth/hooks/useAuth";
import { Icon } from "@/shared/components/Icon";
import { getApiErrorMessage } from "@/shared/api/client";
import { getStatistics } from "../api/dashboardApi";
import { useSiteSettings } from "@/features/admin-config/SiteSettings";

export function Dashboard() {
  const { user } = useAuth();
  const { settings } = useSiteSettings();
  const canViewStatistics = ["admin", "family_head"].includes(user.role);
  const query = useQuery({
    queryKey: ["dashboard-statistics", user.id, user.role],
    queryFn: ({ signal }) => getStatistics(signal),
    enabled: canViewStatistics,
  });
  const rows = query.data ?? [];
  const cards = [
    { label: "Gia đình", icon: "house", value: rows.length },
    { label: "Thành viên", icon: "users", value: rows.reduce((sum, row) => sum + row.member_count, 0) },
    { label: "Bài viết", icon: "message-circle", value: rows.reduce((sum, row) => sum + row.post_count, 0) },
    { label: "Sự kiện", icon: "calendar-days", value: rows.reduce((sum, row) => sum + row.event_count, 0) },
  ];
  const today = new Intl.DateTimeFormat("vi-VN", { day: "numeric", month: "long", year: "numeric", timeZone: "Asia/Ho_Chi_Minh" }).format(new Date());

  return <div className="dashboard">
    <div className="dashboard-heading"><div><p className="section-label">Chào {user.fullName},</p><h1>Không gian gia đình</h1></div><time className="dashboard-date"><Icon name="calendar-days" />{today}</time></div>
    <section className="welcome-panel" aria-label="Câu chuyện gia đình"><div><span className="welcome-label">Từ cội nguồn đến hôm nay</span><h2>Mỗi thế hệ là một phần<br />của câu chuyện gia đình.</h2><p>Kết nối qua gia phả. Gìn giữ qua những kỷ niệm.</p>{user.role !== "guest" && <Link className="btn btn--primary" to="/family-tree">Xem cây gia phả <Icon name="arrow-right" /></Link>}</div><div className="welcome-symbol" aria-hidden="true"><Icon name="network" /></div></section>
    {user.role !== "guest" && <section aria-labelledby="workspace-title"><div className="section-heading"><h2 id="workspace-title">Tiếp nối chuyện nhà</h2><span>Không gian của bạn</span></div><div className="workspace-grid">
      <Link to="/family-tree" className="workspace-card card"><span className="workspace-icon"><Icon name="network" /></span><div><h3>Cây gia phả</h3><p>Tìm hiểu các thế hệ và mối quan hệ trong gia đình.</p><span className="workspace-action">Xem gia phả <Icon name="arrow-up-right" /></span></div><span className="workspace-number" aria-hidden="true">01</span></Link>
      <Link to="/heritage" className="workspace-card card"><span className="workspace-icon warm"><Icon name="book-open" /></span><div><h3>Di sản & Vinh danh</h3><p>Lưu lại câu chuyện, hình ảnh và đóng góp của các thế hệ.</p><span className="workspace-action">Mở kho di sản <Icon name="arrow-up-right" /></span></div><span className="workspace-number" aria-hidden="true">02</span></Link>
    </div></section>}
    {canViewStatistics ? <section aria-labelledby="statistics-title" className="statistics-section"><div className="section-heading"><div><h2 id="statistics-title">Hoạt động gia đình</h2><p>{user.role === "admin" ? "Thống kê các gia đình trong hệ thống." : "Thống kê các gia đình có hồ sơ đã liên kết với bạn."}</p></div><button type="button" disabled={query.isFetching} onClick={() => query.refetch()} className="btn btn--secondary"><Icon name="refresh-cw" />{query.isFetching ? "Đang tải…" : "Làm mới"}</button></div>
      {query.isPending ? <p role="status" className="query-message">Đang tải thống kê…</p>
        : query.isError ? <p role="alert" className="form-error">{getApiErrorMessage(query.error)}</p>
          : rows.length === 0 ? <div className="empty-panel"><Icon name="house" /><p>Chưa có gia đình trong phạm vi thống kê của bạn.</p></div>
            : <><dl className="stat-grid">{cards.map((card) => <div key={card.label} className="stat-card"><dt><span>{card.label}</span><Icon name={card.icon} /></dt><dd>{card.value.toLocaleString("vi-VN")}</dd></div>)}</dl>
              <div className="chart-panel"><div className="section-heading"><h3>Thống kê theo gia đình</h3><span>Thành viên · Bài viết · Sự kiện</span></div><div role="img" aria-label="Biểu đồ số thành viên, bài viết và sự kiện theo gia đình" className="h-80 min-w-0"><ResponsiveContainer width="100%" height="100%"><BarChart data={rows} margin={{ top: 10, right: 10, left: -20, bottom: 10 }}><CartesianGrid stroke="#e5e8df" strokeDasharray="3 3" vertical={false} /><XAxis dataKey="family_name" tick={{ fontSize: 13, fill: "#60695f" }} tickLine={false} axisLine={false} /><YAxis allowDecimals={false} tick={{ fontSize: 13, fill: "#60695f" }} tickLine={false} axisLine={false} /><Tooltip /><Legend /><Bar dataKey="member_count" name="Thành viên" fill="var(--p-accent)" radius={[4, 4, 0, 0]} /><Bar dataKey="post_count" name="Bài viết" fill="#92ad82" radius={[4, 4, 0, 0]} /><Bar dataKey="event_count" name="Sự kiện" fill="#c79666" radius={[4, 4, 0, 0]} /></BarChart></ResponsiveContainer></div>
                <div className="data-table-scroll"><table className="w-full text-left text-sm"><caption className="sr-only">Số liệu hoạt động theo gia đình</caption><thead><tr><th scope="col">Gia đình</th><th scope="col">Thành viên</th><th scope="col">Bài viết</th><th scope="col">Sự kiện</th></tr></thead><tbody>{rows.map((row) => <tr key={row.family_id}><th scope="row">{row.family_name}</th><td>{row.member_count}</td><td>{row.post_count}</td><td>{row.event_count}</td></tr>)}</tbody></table></div>
              </div></>}
    </section> : <aside className="family-note"><Icon name="heart-handshake" /><div><h2>{user.role === "guest" ? `Chào mừng đến với ${settings.site_name}` : "Gia đình bắt đầu từ sự kết nối"}</h2><p>{user.role === "guest" ? "Liên hệ người quản lý gia đình để được xác minh và truy cập gia phả, di sản." : "Chưa thấy gia đình của mình? Liên hệ người quản lý để xác minh và liên kết hồ sơ thành viên."}</p></div></aside>}
    <footer className="workspace-footer"><span>{settings.site_name}</span><span>Gìn giữ hôm nay, tiếp nối mai sau.</span></footer>
  </div>;
}
