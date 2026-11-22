import { useEffect, useRef } from "react";
import { NavLink } from "react-router-dom";
import { Brand } from "@/shared/components/Brand";
import { Icon } from "@/shared/components/Icon";
import { useSiteSettings } from "@/features/admin-config/SiteSettings";

export function Sidebar({ role, open, onClose }) {
  const { settings } = useSiteSettings();
  const aside = useRef(null);
  const canManage = role === "admin" || role === "family_head";
  const links = [
    { label: "Tổng quan", icon: "layout-dashboard", to: "/dashboard" },
    { label: "Hồ sơ của tôi", icon: "users", to: "/profile" },
    { label: "Thông báo", icon: "message-circle", to: "/notifications" },
    ...(role !== "guest"
      ? [
          { label: "Cây gia phả", icon: "network", to: "/family-tree" },
          { label: "Di sản", icon: "book-open", to: "/heritage" },
          { label: "Bảng tin", icon: "message-circle", to: "/community" },
          { label: "Lịch gia đình", icon: "calendar-days", to: "/events" },
          { label: "Danh bạ", icon: "users", to: "/directory" },
          {
            to: "/ai-assistant",
            label: "Trợ lý AI",
            icon: "message-circle",
            roles: ["admin", "family_head", "member"],
          },
        ]
      : []),
  ];

  useEffect(() => {
    if (!open) return;
    const previousFocus = document.activeElement;
    const previousOverflow = document.body.style.overflow;
    const desktop = window.matchMedia("(min-width: 1024px)");
    if (desktop.matches) {
      onClose();
      return;
    }
    document.body.style.overflow = "hidden";
    const controls = [...aside.current.querySelectorAll("a[href], button")];
    controls[0]?.focus();
    function onKey(event) {
      if (event.key === "Escape") onClose();
      if (event.key !== "Tab") return;
      const first = controls[0],
        last = controls.at(-1);
      if (event.shiftKey && document.activeElement === first) {
        event.preventDefault();
        last.focus();
      }
      if (!event.shiftKey && document.activeElement === last) {
        event.preventDefault();
        first.focus();
      }
    }
    function onResize() {
      if (desktop.matches) onClose();
    }
    document.addEventListener("keydown", onKey);
    desktop.addEventListener("change", onResize);
    return () => {
      document.body.style.overflow = previousOverflow;
      document.removeEventListener("keydown", onKey);
      desktop.removeEventListener("change", onResize);
      previousFocus?.focus();
    };
  }, [open, onClose]);

  const navLink = (item) => (
    <NavLink
      key={item.to}
      to={item.to}
      onClick={onClose}
      className={({ isActive }) =>
        `sidebar-link ${isActive ? "is-active" : ""}`
      }
    >
      <Icon name={item.icon} />
      <span>{item.label}</span>
      <Icon name="chevron-right" className="nav-chevron" />
    </NavLink>
  );

  return (
    <>
      {open && (
        <button
          tabIndex={-1}
          aria-label="Đóng menu"
          className="sidebar-backdrop"
          onClick={onClose}
        />
      )}
      <aside
        ref={aside}
        id="app-sidebar"
        className={`app-sidebar ${open ? "is-open" : ""}`}
        role={open ? "dialog" : undefined}
        aria-modal={open ? true : undefined}
        aria-label="Điều hướng chính"
      >
        <div className="sidebar-brand">
          <Brand />
          <button
            className="icon-button drawer-close"
            onClick={onClose}
            aria-label="Đóng menu"
          >
            <Icon name="x" />
          </button>
        </div>
        <div className="sidebar-space">
          <span className="space-mark">
            <Icon name="house" />
          </span>
          <div>
            <p>Không gian gia đình</p>
            <span>Cùng nhau gìn giữ cội nguồn</span>
          </div>
        </div>
        <p className="nav-label">Không gian của bạn</p>
        <nav aria-label="Không gian gia đình">{links.map(navLink)}</nav>

        {canManage && (
          <div className="management-nav">
            <p className="nav-label">Quản lý</p>
            <nav aria-label="Quản lý">
              {navLink({
                label: "Gia đình và thành viên",
                icon: "house",
                to: "/family-management",
              })}
              {role === "admin" &&
                navLink({
                  label: "Cấu hình hệ thống",
                  icon: "settings",
                  to: "/admin-config",
                })}
              {navLink({
                label: "Duyệt thành viên",
                icon: "shield-check",
                to: "/member-approval",
              })}
              {role === "admin" &&
                navLink({
                  label: "Báo cáo nội dung",
                  icon: "flag",
                  to: "/reports",
                })}
              {role === "admin" &&
                navLink({
                  label: "Sao lưu & khôi phục",
                  icon: "shield-check",
                  to: "/admin-backups",
                })}
            </nav>
          </div>
        )}
        <div className="sidebar-footer">
          <Icon name="leaf" />
          <p>
            Mỗi thế hệ,
            <br />
            <span>một phần câu chuyện.</span>
          </p>
          <span className="sidebar-footer-brand">{settings.site_name}</span>
        </div>
      </aside>
    </>
  );
}
