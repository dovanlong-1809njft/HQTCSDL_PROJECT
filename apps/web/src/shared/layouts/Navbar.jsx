import { useLocation } from "react-router-dom";
import { useAuth } from "@/features/auth/hooks/useAuth";
import { Icon } from "@/shared/components/Icon";

const pageNames = { "/directory":"Danh bạ", "/community":"Bảng tin", "/events":"Lịch gia đình", "/notifications":"Thông báo", "/dashboard": "Tổng quan", "/profile": "Hồ sơ của tôi", "/family-management": "Gia đình và thành viên", "/family-tree": "Cây gia phả", "/heritage": "Di sản", "/admin-config": "Cấu hình hệ thống", "/member-approval": "Duyệt thành viên", "/reports": "Báo cáo nội dung" };
const roles = { admin: "Quản trị viên", family_head: "Trưởng chi", member: "Thành viên", guest: "Khách" };

export function Navbar({ onMenuClick, sidebarOpen }) {
  const { user, signOut } = useAuth();
  const { pathname } = useLocation();
  const initials = (user?.fullName || "G").trim().slice(0, 1).toLocaleUpperCase("vi");

  return <header className="app-navbar">
    <div className="navbar-location"><button onClick={onMenuClick} aria-label="Mở menu" aria-controls="app-sidebar" aria-expanded={sidebarOpen} className="icon-button mobile-menu"><Icon name="menu" /></button><span className="breadcrumb-parent">Không gian gia đình</span><Icon name="chevron-right" className="breadcrumb-parent" /><span>{pageNames[pathname] || "FamilyConnect"}</span></div>
    <div className="navbar-account"><span className="account-avatar" aria-hidden="true">{initials}</span><div className="account-info"><p>{user?.fullName || "Thành viên"}</p><span>{roles[user?.role] || "Thành viên"}</span></div><button onClick={signOut} className="icon-button" aria-label="Đăng xuất" title="Đăng xuất"><Icon name="log-out" /></button></div>
  </header>;
}
